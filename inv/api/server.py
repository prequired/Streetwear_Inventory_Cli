"""Simple REST API server for inventory management"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

try:
    from flask import Flask, request, jsonify, abort
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from ..database.connection import get_db_session
from ..database.models import Item, Location, Consigner
from ..utils.config import get_config
from ..utils.photos import PhotoManager


class InventoryAPI:
    """REST API for inventory management"""
    
    def __init__(self, debug=False):
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask is required for API server. Install with: pip install flask flask-cors")
        
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.debug = debug
        
        # Load configuration
        self.config = get_config()
        self.photo_manager = PhotoManager()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes"""
        
        @self.app.route('/', methods=['GET'])
        def index():
            return jsonify({
                'name': 'Streetwear Inventory API',
                'version': '1.0.0',
                'endpoints': {
                    'items': '/api/items',
                    'locations': '/api/locations',
                    'consigners': '/api/consigners',
                    'search': '/api/search',
                    'stats': '/api/stats'
                }
            })
        
        @self.app.route('/api/items', methods=['GET'])
        def list_items():
            """Get all items with optional filtering"""
            try:
                # Query parameters
                brand = request.args.get('brand')
                condition = request.args.get('condition')
                status = request.args.get('status', 'available')
                location_id = request.args.get('location_id')
                ownership_type = request.args.get('ownership_type')
                limit = int(request.args.get('limit', 100))
                offset = int(request.args.get('offset', 0))
                
                with get_db_session() as session:
                    query = session.query(Item)
                    
                    # Apply filters
                    if brand:
                        query = query.filter(Item.brand.ilike(f'%{brand}%'))
                    if condition:
                        query = query.filter(Item.condition == condition)
                    if status:
                        query = query.filter(Item.status == status)
                    if location_id:
                        query = query.filter(Item.location_id == location_id)
                    if ownership_type:
                        query = query.filter(Item.ownership_type == ownership_type)
                    
                    # Count total
                    total = query.count()
                    
                    # Apply pagination
                    items = query.offset(offset).limit(limit).all()
                    
                    # Convert to JSON
                    items_data = []
                    for item in items:
                        item_dict = self._item_to_dict(item)
                        # Add photos
                        photos = self.photo_manager.list_photos(item.sku)
                        item_dict['photos'] = [p['filename'] for p in photos]
                        item_dict['primary_photo'] = photos[0]['filename'] if photos else None
                        items_data.append(item_dict)
                    
                    return jsonify({
                        'items': items_data,
                        'total': total,
                        'limit': limit,
                        'offset': offset
                    })
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/items/<sku>', methods=['GET'])
        def get_item(sku):
            """Get single item by SKU"""
            try:
                with get_db_session() as session:
                    item = session.query(Item).filter(Item.sku == sku.upper()).first()
                    
                    if not item:
                        abort(404)
                    
                    item_dict = self._item_to_dict(item)
                    
                    # Add photos
                    photos = self.photo_manager.list_photos(item.sku)
                    item_dict['photos'] = photos
                    
                    return jsonify(item_dict)
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/items/<sku>', methods=['PUT'])
        def update_item(sku):
            """Update item"""
            try:
                data = request.get_json()
                
                with get_db_session() as session:
                    item = session.query(Item).filter(Item.sku == sku.upper()).first()
                    
                    if not item:
                        abort(404)
                    
                    # Update allowed fields
                    allowed_fields = [
                        'current_price', 'status', 'notes', 'condition',
                        'location_id', 'sold_price'
                    ]
                    
                    for field in allowed_fields:
                        if field in data:
                            if field in ['current_price', 'sold_price'] and data[field] is not None:
                                setattr(item, field, Decimal(str(data[field])))
                            else:
                                setattr(item, field, data[field])
                    
                    # Item updated (no last_updated field in current model)
                    
                    session.commit()
                    session.refresh(item)
                    
                    return jsonify(self._item_to_dict(item))
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/locations', methods=['GET'])
        def list_locations():
            """Get all locations"""
            try:
                with get_db_session() as session:
                    locations = session.query(Location).all()
                    
                    locations_data = []
                    for location in locations:
                        location_dict = self._location_to_dict(location)
                        
                        # Add item count
                        item_count = session.query(Item).filter(
                            Item.location_id == location.id,
                            Item.status == 'available'
                        ).count()
                        location_dict['item_count'] = item_count
                        
                        locations_data.append(location_dict)
                    
                    return jsonify({'locations': locations_data})
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/consigners', methods=['GET'])
        def list_consigners():
            """Get all consigners"""
            try:
                with get_db_session() as session:
                    consigners = session.query(Consigner).all()
                    
                    consigners_data = []
                    for consigner in consigners:
                        consigner_dict = self._consigner_to_dict(consigner)
                        
                        # Add item counts
                        total_items = session.query(Item).filter(Item.consigner_id == consigner.id).count()
                        available_items = session.query(Item).filter(
                            Item.consigner_id == consigner.id,
                            Item.status == 'available'
                        ).count()
                        sold_items = session.query(Item).filter(
                            Item.consigner_id == consigner.id,
                            Item.status == 'sold'
                        ).count()
                        
                        consigner_dict['stats'] = {
                            'total_items': total_items,
                            'available_items': available_items,
                            'sold_items': sold_items
                        }
                        
                        consigners_data.append(consigner_dict)
                    
                    return jsonify({'consigners': consigners_data})
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/search', methods=['GET'])
        def search_items():
            """Search items"""
            try:
                query_text = request.args.get('q', '')
                limit = int(request.args.get('limit', 50))
                
                if not query_text:
                    return jsonify({'items': [], 'total': 0})
                
                with get_db_session() as session:
                    # Search in brand, model, color, and notes
                    search_filter = f'%{query_text}%'
                    items = session.query(Item).filter(
                        (Item.brand.ilike(search_filter)) |
                        (Item.model.ilike(search_filter)) |
                        (Item.color.ilike(search_filter)) |
                        (Item.notes.ilike(search_filter))
                    ).limit(limit).all()
                    
                    items_data = []
                    for item in items:
                        item_dict = self._item_to_dict(item)
                        # Add primary photo
                        photos = self.photo_manager.list_photos(item.sku)
                        item_dict['primary_photo'] = photos[0]['filename'] if photos else None
                        items_data.append(item_dict)
                    
                    return jsonify({
                        'items': items_data,
                        'total': len(items_data),
                        'query': query_text
                    })
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """Get inventory statistics"""
            try:
                with get_db_session() as session:
                    # Basic counts
                    total_items = session.query(Item).count()
                    available_items = session.query(Item).filter(Item.status == 'available').count()
                    sold_items = session.query(Item).filter(Item.status == 'sold').count()
                    held_items = session.query(Item).filter(Item.status == 'held').count()
                    
                    # Value calculations
                    available_value = session.query(Item).filter(
                        Item.status == 'available'
                    ).with_entities(Item.current_price).all()
                    total_available_value = sum(item.current_price for item in available_value)
                    
                    sold_value = session.query(Item).filter(
                        Item.status == 'sold',
                        Item.sold_price.isnot(None)
                    ).with_entities(Item.sold_price).all()
                    total_sold_value = sum(item.sold_price for item in sold_value)
                    
                    # Ownership breakdown
                    owned_items = session.query(Item).filter(Item.ownership_type == 'owned').count()
                    consignment_items = session.query(Item).filter(Item.ownership_type == 'consignment').count()
                    
                    # Brand breakdown
                    brand_counts = {}
                    brands = session.query(Item.brand).distinct().all()
                    for brand_row in brands:
                        brand = brand_row[0]
                        count = session.query(Item).filter(
                            Item.brand == brand,
                            Item.status == 'available'
                        ).count()
                        if count > 0:
                            brand_counts[brand] = count
                    
                    # Photo stats
                    photo_stats = self.photo_manager.get_storage_stats()
                    
                    return jsonify({
                        'inventory': {
                            'total_items': total_items,
                            'available_items': available_items,
                            'sold_items': sold_items,
                            'held_items': held_items,
                            'owned_items': owned_items,
                            'consignment_items': consignment_items
                        },
                        'values': {
                            'available_value': float(total_available_value),
                            'sold_value': float(total_sold_value)
                        },
                        'brands': brand_counts,
                        'photos': photo_stats,
                        'generated_at': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/webhook/item-updated', methods=['POST'])
        def webhook_item_updated():
            """Webhook endpoint for item updates"""
            try:
                data = request.get_json()
                
                # Log webhook (in production, you might want to send to external service)
                webhook_log = {
                    'timestamp': datetime.now().isoformat(),
                    'event': 'item_updated',
                    'data': data,
                    'source_ip': request.remote_addr
                }
                
                # You could implement webhook forwarding here
                # For now, just return success
                return jsonify({
                    'status': 'received',
                    'webhook_id': webhook_log['timestamp']
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Resource not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    def _item_to_dict(self, item) -> Dict[str, Any]:
        """Convert Item model to dictionary"""
        return {
            'sku': item.sku,
            'variant_id': item.variant_id,
            'brand': item.brand,
            'model': item.model,
            'size': item.size,
            'color': item.color,
            'condition': item.condition,
            'box_status': item.box_status,
            'current_price': float(item.current_price),
            'purchase_price': float(item.purchase_price) if item.purchase_price else None,
            'sold_price': float(item.sold_price) if item.sold_price else None,
            'location': {
                'id': item.location.id,
                'code': item.location.code,
                'name': item.location.description
            } if item.location else None,
            'status': item.status,
            'ownership_type': item.ownership_type,
            'notes': item.notes,
            'date_added': item.date_added.isoformat() if item.date_added else None,
            'sold_date': item.sold_date.isoformat() if item.sold_date else None,
            'consigner': {
                'id': item.consigner.id,
                'name': item.consigner.name,
                'phone': item.consigner.phone
            } if item.consigner else None,
            'split_percentage': item.split_percentage
        }
    
    def _location_to_dict(self, location) -> Dict[str, Any]:
        """Convert Location model to dictionary"""
        return {
            'id': location.id,
            'code': location.code,
            'type': location.location_type,
            'name': location.description,
            'created_date': location.created_date.isoformat() if location.created_date else None
        }
    
    def _consigner_to_dict(self, consigner) -> Dict[str, Any]:
        """Convert Consigner model to dictionary"""
        return {
            'id': consigner.id,
            'name': consigner.name,
            'phone': consigner.phone,
            'email': consigner.email,
            'default_split_percentage': consigner.default_split_percentage,
            'created_date': consigner.created_date.isoformat() if consigner.created_date else None
        }
    
    def run(self, host='127.0.0.1', port=5000):
        """Run the API server"""
        self.app.run(host=host, port=port, debug=self.debug)


def create_api_server(debug=False):
    """Factory function to create API server"""
    return InventoryAPI(debug=debug)