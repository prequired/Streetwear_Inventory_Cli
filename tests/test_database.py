"""Test database models and connections"""

import pytest
from decimal import Decimal
from datetime import datetime

from inv.database.models import Item, Location, Consigner, Photo
from inv.database.connection import DatabaseConnection, db
from inv.database.setup import create_tables, drop_tables
from inv.utils.config import create_default_config


class TestDatabaseModels:
    """Test SQLAlchemy models"""
    
    def test_location_model(self, db_session):
        """Test Location model creation and relationships"""
        location = Location(
            code="STORE-A1",
            location_type="store-floor",
            description="Store Floor Section A1",
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        assert location.id is not None
        assert location.code == "STORE-A1"
        assert location.is_active is True
        assert location.created_date is not None
    
    def test_consigner_model(self, db_session):
        """Test Consigner model creation"""
        consigner = Consigner(
            name="John Doe",
            phone="(555) 123-4567",
            email="john@example.com",
            default_split_percentage=70
        )
        db_session.add(consigner)
        db_session.commit()
        
        assert consigner.id is not None
        assert consigner.name == "John Doe"
        assert consigner.phone == "(555) 123-4567"
        assert consigner.default_split_percentage == 70
    
    def test_item_model(self, db_session):
        """Test Item model creation with all fields"""
        # Create location first
        location = Location(code="TEST-LOC", location_type="test")
        db_session.add(location)
        db_session.flush()
        
        item = Item(
            sku="TST001",
            variant_id=1,
            brand="TestBrand",
            model="Test Model",
            size="10",
            color="Black",
            condition="DS",
            box_status="box",
            current_price=Decimal("250.00"),
            purchase_price=Decimal("200.00"),
            location_id=location.id,
            notes="Test item",
            status="available",
            ownership_type="owned"
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.sku == "TST001"
        assert item.brand == "TestBrand"
        assert item.current_price == Decimal("250.00")
        assert item.location_id == location.id
        assert item.status == "available"
    
    def test_item_with_consignment(self, db_session):
        """Test Item model with consignment fields"""
        # Create consigner
        consigner = Consigner(name="Jane Doe", phone="(555) 987-6543")
        db_session.add(consigner)
        db_session.flush()
        
        item = Item(
            sku="CON001",
            brand="ConsignBrand",
            model="Consign Model",
            size="9",
            color="Red",
            condition="VNDS",
            box_status="neither",
            current_price=Decimal("180.00"),
            purchase_price=Decimal("0.00"),
            ownership_type="consignment",
            consigner_id=consigner.id,
            split_percentage=70
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.ownership_type == "consignment"
        assert item.consigner_id == consigner.id
        assert item.split_percentage == 70
    
    def test_photo_model(self, db_session):
        """Test Photo model and relationship with Item"""
        item = Item(
            sku="PHO001",
            brand="PhotoBrand",
            model="Photo Model",
            size="11",
            color="Blue",
            condition="Used",
            box_status="tag",
            current_price=Decimal("150.00"),
            purchase_price=Decimal("100.00")
        )
        db_session.add(item)
        db_session.flush()
        
        photo = Photo(
            item_id=item.id,
            file_path="/photos/PHO001/01_front.jpg",
            photo_type="front",
            display_order=1
        )
        db_session.add(photo)
        db_session.commit()
        
        assert photo.id is not None
        assert photo.item_id == item.id
        assert photo.file_path == "/photos/PHO001/01_front.jpg"
        assert photo.display_order == 1
    
    def test_relationships(self, db_session):
        """Test model relationships"""
        # Create related objects
        location = Location(code="REL-LOC", location_type="test")
        consigner = Consigner(name="Rel Test", phone="(555) 111-2222")
        db_session.add_all([location, consigner])
        db_session.flush()
        
        item = Item(
            sku="REL001",
            brand="RelBrand",
            model="Rel Model",
            size="8",
            color="Green",
            condition="DS",
            box_status="both",
            current_price=Decimal("300.00"),
            purchase_price=Decimal("250.00"),
            location_id=location.id,
            consigner_id=consigner.id
        )
        db_session.add(item)
        db_session.flush()
        
        photo = Photo(item_id=item.id, file_path="/test.jpg")
        db_session.add(photo)
        db_session.commit()
        
        # Test relationships
        assert item.location == location
        assert item.consigner == consigner
        assert len(item.photos) == 1
        assert item.photos[0] == photo
        
        assert location.items == [item]
        assert consigner.items == [item]


class TestDatabaseConnection:
    """Test database connection functionality"""
    
    def test_database_connection_singleton(self):
        """Test that DatabaseConnection is a singleton"""
        db1 = DatabaseConnection()
        db2 = DatabaseConnection()
        assert db1 is db2
    
    def test_initialize_with_config(self, temp_config):
        """Test database initialization with config"""
        config = create_default_config()
        config['database']['url'] = 'sqlite:///:memory:'
        
        db_instance = DatabaseConnection()
        result = db_instance.initialize(config)
        assert result is True
    
    def test_initialize_missing_config(self):
        """Test initialization with missing config values"""
        config = {'database': {'url': ''}}
        
        db_instance = DatabaseConnection()
        with pytest.raises(ValueError, match="Database URL must be provided"):
            db_instance.initialize(config)
    
    def test_get_session_without_init(self):
        """Test getting session without initialization"""
        db_instance = DatabaseConnection()
        db_instance._session_factory = None
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            db_instance.get_session()
    
    def test_get_engine_without_init(self):
        """Test getting engine without initialization"""
        db_instance = DatabaseConnection()
        db_instance._engine = None
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            db_instance.get_engine()


class TestDatabaseSetup:
    """Test database setup functionality"""
    
    def test_create_tables(self, mock_db_connection):
        """Test table creation"""
        result = create_tables()
        assert result is True
    
    def test_drop_tables(self, mock_db_connection):
        """Test table dropping"""
        result = drop_tables()
        assert result is True