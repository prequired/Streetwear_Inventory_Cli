"""Pytest configuration and fixtures"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from inv.database.models import Base
from inv.database.connection import DatabaseConnection
from inv.utils.config import save_config, create_default_config


@pytest.fixture
def temp_config():
    """Create a temporary config file for testing"""
    config = create_default_config()
    config['database']['url'] = 'sqlite:///test.db'
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config, f)
        config_path = f.name
    
    # Set config path for tests
    original_cwd = os.getcwd()
    test_dir = os.path.dirname(config_path)
    os.chdir(test_dir)
    
    yield config_path
    
    # Cleanup
    os.chdir(original_cwd)
    os.unlink(config_path)


@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    
    yield SessionLocal
    
    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_db):
    """Get a test database session"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_db_connection(monkeypatch, test_db):
    """Mock database connection for testing"""
    def mock_get_session():
        return test_db()
    
    def mock_test_connection():
        return True
    
    def mock_get_engine():
        return test_db().bind
    
    monkeypatch.setattr('inv.database.connection.db.get_session', mock_get_session)
    monkeypatch.setattr('inv.database.connection.db.test_connection', mock_test_connection)
    monkeypatch.setattr('inv.database.connection.db.get_engine', mock_get_engine)
    
    return test_db