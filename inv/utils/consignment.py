"""Consignment management utilities"""

from typing import Optional, List
from sqlalchemy.orm import Session
from decimal import Decimal

from ..database.connection import get_db_session
from ..database.models import Consigner, Item
from ..utils.validation import validate_phone, validate_email, validate_percentage
from ..utils.pricing import calculate_consignment_payout


def get_consigner_by_phone(phone: str) -> Optional[Consigner]:
    """Get consigner by phone number"""
    with get_db_session() as session:
        return session.query(Consigner).filter(
            Consigner.phone == phone
        ).first()


def get_consigner_by_name(name: str) -> List[Consigner]:
    """Get consigners by name (may return multiple if names are similar)"""
    with get_db_session() as session:
        return session.query(Consigner).filter(
            Consigner.name.ilike(f"%{name}%")
        ).all()


def find_or_create_consigner(name: str, phone: str = None, email: str = None, 
                           default_split: int = 70) -> Consigner:
    """Find existing consigner or create new one"""
    
    # If phone provided, look up by phone first
    if phone:
        normalized_phone = validate_phone(phone)
        existing = get_consigner_by_phone(normalized_phone)
        if existing:
            return existing
    
    # Look up by name
    name_matches = get_consigner_by_name(name)
    if len(name_matches) == 1:
        return name_matches[0]
    elif len(name_matches) > 1:
        if phone:
            # Multiple name matches but we have phone to disambiguate
            for match in name_matches:
                if match.phone == validate_phone(phone):
                    return match
        else:
            # Multiple matches, need disambiguation
            raise ValueError(f"Multiple consigners found with name '{name}'. Please provide phone number.")
    
    # No matches found, create new consigner
    if not phone:
        raise ValueError("Phone number required to create new consigner")
    
    # Validate inputs
    normalized_phone = validate_phone(phone)
    if email and not validate_email(email):
        raise ValueError("Invalid email address")
    if not validate_percentage(default_split):
        raise ValueError("Split percentage must be between 0 and 100")
    
    with get_db_session() as session:
        consigner = Consigner(
            name=name.strip(),
            phone=normalized_phone,
            email=email,
            default_split_percentage=default_split
        )
        
        session.add(consigner)
        session.commit()
        session.refresh(consigner)
        
        return consigner


def get_consigner_items(consigner_id: int, status: str = None) -> List[Item]:
    """Get all items for a consigner"""
    with get_db_session() as session:
        query = session.query(Item).filter(Item.consigner_id == consigner_id)
        
        if status:
            query = query.filter(Item.status == status)
        
        return query.order_by(Item.date_added.desc()).all()


def calculate_consigner_stats(consigner_id: int) -> dict:
    """Calculate statistics for a consigner"""
    items = get_consigner_items(consigner_id)
    
    stats = {
        'total_items': len(items),
        'available_items': len([i for i in items if i.status == 'available']),
        'sold_items': len([i for i in items if i.status == 'sold']),
        'held_items': len([i for i in items if i.status == 'held']),
        'total_current_value': Decimal('0'),
        'total_sold_value': Decimal('0'),
        'total_payouts': Decimal('0')
    }
    
    for item in items:
        if item.status == 'available':
            stats['total_current_value'] += item.current_price
        elif item.status == 'sold' and item.sold_price:
            stats['total_sold_value'] += item.sold_price
            
            # Calculate payout for this item
            platform_fee = Decimal('10')  # Default platform fee
            split_percentage = item.split_percentage or 70
            payout = calculate_consignment_payout(
                item.sold_price, platform_fee, split_percentage
            )
            stats['total_payouts'] += payout
    
    return stats


def list_all_consigners(include_stats: bool = False) -> List[dict]:
    """List all consigners with optional statistics"""
    with get_db_session() as session:
        consigners = session.query(Consigner).order_by(Consigner.name).all()
        
        result = []
        for consigner in consigners:
            consigner_data = {
                'id': consigner.id,
                'name': consigner.name,
                'phone': consigner.phone,
                'email': consigner.email,
                'default_split': consigner.default_split_percentage,
                'created_date': consigner.created_date
            }
            
            if include_stats:
                consigner_data['stats'] = calculate_consigner_stats(consigner.id)
            
            result.append(consigner_data)
        
        return result


def update_consigner(consigner_id: int, **kwargs) -> Optional[Consigner]:
    """Update consigner information"""
    with get_db_session() as session:
        consigner = session.query(Consigner).filter(Consigner.id == consigner_id).first()
        
        if not consigner:
            return None
        
        # Validate updates
        if 'phone' in kwargs:
            kwargs['phone'] = validate_phone(kwargs['phone'])
        
        if 'email' in kwargs and kwargs['email']:
            if not validate_email(kwargs['email']):
                raise ValueError("Invalid email address")
        
        if 'default_split_percentage' in kwargs:
            if not validate_percentage(kwargs['default_split_percentage']):
                raise ValueError("Split percentage must be between 0 and 100")
        
        # Apply updates
        for field, value in kwargs.items():
            if hasattr(consigner, field):
                setattr(consigner, field, value)
        
        session.commit()
        session.refresh(consigner)
        
        return consigner


def generate_consigner_report(consigner_id: int) -> dict:
    """Generate detailed report for a consigner"""
    with get_db_session() as session:
        consigner = session.query(Consigner).filter(Consigner.id == consigner_id).first()
        
        if not consigner:
            raise ValueError("Consigner not found")
        
        items = get_consigner_items(consigner_id)
        stats = calculate_consigner_stats(consigner_id)
        
        # Group items by status
        items_by_status = {
            'available': [i for i in items if i.status == 'available'],
            'sold': [i for i in items if i.status == 'sold'],
            'held': [i for i in items if i.status == 'held']
        }
        
        return {
            'consigner': consigner,
            'stats': stats,
            'items_by_status': items_by_status,
            'recent_activity': items[:10]  # Most recent 10 items
        }


def calculate_pending_payouts() -> List[dict]:
    """Calculate all pending payouts for consignment items"""
    with get_db_session() as session:
        # Get all sold consignment items
        sold_items = session.query(Item).filter(
            Item.ownership_type == 'consignment',
            Item.status == 'sold',
            Item.sold_price.isnot(None)
        ).all()
        
        payouts_by_consigner = {}
        
        for item in sold_items:
            consigner_id = item.consigner_id
            if consigner_id not in payouts_by_consigner:
                payouts_by_consigner[consigner_id] = {
                    'consigner': item.consigner,
                    'items': [],
                    'total_payout': Decimal('0')
                }
            
            # Calculate payout for this item
            platform_fee = Decimal('10')  # Default
            split_percentage = item.split_percentage or 70
            payout = calculate_consignment_payout(
                item.sold_price, platform_fee, split_percentage
            )
            
            payouts_by_consigner[consigner_id]['items'].append({
                'item': item,
                'payout': payout
            })
            payouts_by_consigner[consigner_id]['total_payout'] += payout
        
        return list(payouts_by_consigner.values())


def search_consigners(query: str) -> List[Consigner]:
    """Search consigners by name, phone, or email"""
    with get_db_session() as session:
        search_term = f"%{query.lower()}%"
        
        return session.query(Consigner).filter(
            Consigner.name.ilike(search_term) |
            Consigner.phone.ilike(search_term) |
            Consigner.email.ilike(search_term)
        ).order_by(Consigner.name).all()