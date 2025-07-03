"""Database connection management for SQLite"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from ..utils.config import get_config


class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config: dict = None):
        """Initialize database connection with config"""
        if config is None:
            config = get_config()
        
        database_url = config['database']['url']
        
        if not database_url:
            raise ValueError("Database URL must be provided in config")
        
        # Handle different database URL formats
        if database_url.startswith('sqlite://'):
            # SQLite URL
            pass  # Use as-is
        elif not database_url.startswith('sqlite://'):
            # Default to SQLite for any other format
            database_url = f"sqlite:///{database_url}"
        
        try:
            self._engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False  # Set to True for SQL debugging
            )
            self._session_factory = sessionmaker(bind=self._engine)
            return True
        except SQLAlchemyError as e:
            raise ConnectionError(f"Failed to connect to database: {e}")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
    
    def get_engine(self):
        """Get the SQLAlchemy engine"""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine


# Global database connection instance
db = DatabaseConnection()


def get_db_session() -> Session:
    """Convenience function to get database session"""
    return db.get_session()


def test_database_connection() -> bool:
    """Test if database connection is working"""
    return db.test_connection()