"""Location management utilities"""

import click
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database.connection import get_db_session
from ..database.models import Location
from .config import get_config


def get_all_active_locations() -> List[Location]:
    """Get all active locations from database"""
    with get_db_session() as session:
        return session.query(Location).filter(
            Location.is_active == True
        ).order_by(Location.code).all()


def get_location_by_code(code: str) -> Optional[Location]:
    """Get location by code"""
    with get_db_session() as session:
        return session.query(Location).filter(
            Location.code == code,
            Location.is_active == True
        ).first()


def get_default_location() -> Optional[Location]:
    """Get default location from config"""
    config = get_config()
    default_code = config.get('defaults', {}).get('location', '')
    
    if default_code:
        return get_location_by_code(default_code)
    
    return None


def show_location_picker() -> Optional[Location]:
    """Show interactive location picker and return selected location"""
    locations = get_all_active_locations()
    
    if not locations:
        click.echo("❌ No active locations found. Please create a location first.")
        return None
    
    click.echo("📍 Select location:")
    
    for i, location in enumerate(locations, 1):
        description = f" ({location.description})" if location.description else ""
        click.echo(f"{i}. {location.code}{description}")
    
    while True:
        try:
            choice = click.prompt(f"\nEnter location number (1-{len(locations)})", type=int)
            
            if 1 <= choice <= len(locations):
                selected_location = locations[choice - 1]
                click.echo(f"Selected: {selected_location.code}")
                return selected_location
            else:
                click.echo(f"❌ Invalid choice. Please enter a number between 1 and {len(locations)}")
                
        except (ValueError, click.Abort):
            click.echo("❌ Invalid input. Please enter a number.")
            return None


def create_location(code: str, location_type: str = None, description: str = None) -> Location:
    """Create a new location"""
    # Validate code format
    if not code or len(code.strip()) == 0:
        raise ValueError("Location code cannot be empty")
    
    code = code.strip().upper()
    
    # Check if location already exists
    existing = get_location_by_code(code)
    if existing:
        raise ValueError(f"Location with code '{code}' already exists")
    
    with get_db_session() as session:
        location = Location(
            code=code,
            location_type=location_type,
            description=description,
            is_active=True
        )
        
        session.add(location)
        session.commit()
        session.refresh(location)
        
        return location


def update_location(code: str, **kwargs) -> Optional[Location]:
    """Update an existing location"""
    with get_db_session() as session:
        location = session.query(Location).filter(
            Location.code == code
        ).first()
        
        if not location:
            return None
        
        # Update fields
        for field, value in kwargs.items():
            if hasattr(location, field):
                setattr(location, field, value)
        
        session.commit()
        session.refresh(location)
        
        return location


def deactivate_location(code: str) -> bool:
    """Deactivate a location (soft delete)"""
    with get_db_session() as session:
        location = session.query(Location).filter(
            Location.code == code
        ).first()
        
        if not location:
            return False
        
        location.is_active = False
        session.commit()
        
        return True


def list_locations(show_inactive: bool = False) -> List[Location]:
    """List all locations"""
    with get_db_session() as session:
        query = session.query(Location)
        
        if not show_inactive:
            query = query.filter(Location.is_active == True)
        
        return query.order_by(Location.code).all()


def move_item_to_location(item_id: int, location_code: str) -> bool:
    """Move an item to a different location"""
    location = get_location_by_code(location_code)
    if not location:
        return False
    
    with get_db_session() as session:
        from ..database.models import Item
        
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return False
        
        item.location_id = location.id
        session.commit()
        
        return True


def get_location_stats() -> dict:
    """Get statistics about items in each location"""
    with get_db_session() as session:
        from ..database.models import Item
        from sqlalchemy import func
        
        # Query items count by location
        results = session.query(
            Location.code,
            Location.description,
            func.count(Item.id).label('item_count')
        ).outerjoin(Item).group_by(
            Location.id, Location.code, Location.description
        ).filter(
            Location.is_active == True
        ).all()
        
        stats = {}
        for code, description, count in results:
            stats[code] = {
                'description': description,
                'item_count': count or 0
            }
        
        return stats


def validate_location_code(code: str) -> bool:
    """Validate location code format"""
    if not code:
        return False
    
    code = code.strip()
    
    # Must not be empty
    if len(code) == 0:
        return False
    
    # Must not be too long
    if len(code) > 50:
        return False
    
    # Must contain only valid characters (letters, numbers, hyphens, underscores)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', code):
        return False
    
    return True


def suggest_location_code(location_type: str, description: str = None) -> str:
    """Suggest a location code based on type and description"""
    if not location_type:
        location_type = "GENERAL"
    
    # Generate base code from type
    type_prefix = location_type.upper().replace(' ', '').replace('-', '')[:4]
    
    # Add description suffix if provided
    if description:
        desc_suffix = description.upper().replace(' ', '').replace('-', '')[:3]
        base_code = f"{type_prefix}-{desc_suffix}"
    else:
        base_code = type_prefix
    
    # Ensure uniqueness by adding number if needed
    counter = 1
    suggested_code = base_code
    
    while get_location_by_code(suggested_code):
        suggested_code = f"{base_code}-{counter:02d}"
        counter += 1
    
    return suggested_code