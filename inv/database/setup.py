"""Database setup and table creation"""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .models import Base
from .connection import db


def create_tables():
    """Create all database tables"""
    try:
        engine = db.get_engine()
        
        # Create all tables defined in models
        Base.metadata.create_all(engine)
        
        # Add CHECK constraints via raw SQL (skip for SQLite in testing)
        with engine.connect() as conn:
            # SQLite handles constraints differently than other databases
            if not str(engine.url).startswith('sqlite'):
                constraints = [
                    "ALTER TABLE items ADD CONSTRAINT check_condition CHECK (condition IN ('DS', 'VNDS', 'Used'))",
                    "ALTER TABLE items ADD CONSTRAINT check_box_status CHECK (box_status IN ('box', 'tag', 'both', 'neither'))",
                    "ALTER TABLE items ADD CONSTRAINT check_status CHECK (status IN ('available', 'sold', 'held', 'deleted'))",
                    "ALTER TABLE items ADD CONSTRAINT check_ownership_type CHECK (ownership_type IN ('owned', 'consignment'))",
                    "ALTER TABLE items ADD CONSTRAINT unique_sku_variant UNIQUE (sku, variant_id)"
                ]
                
                for constraint in constraints:
                    try:
                        conn.execute(text(constraint))
                    except SQLAlchemyError:
                        # Constraint might already exist, continue
                        pass
                
                conn.commit()
        
        return True
        
    except SQLAlchemyError as e:
        raise Exception(f"Failed to create database tables: {e}")


def drop_tables():
    """Drop all database tables (for testing)"""
    try:
        engine = db.get_engine()
        Base.metadata.drop_all(engine)
        return True
    except SQLAlchemyError as e:
        raise Exception(f"Failed to drop database tables: {e}")


def reset_database():
    """Reset database by dropping and recreating all tables"""
    drop_tables()
    create_tables()
    return True