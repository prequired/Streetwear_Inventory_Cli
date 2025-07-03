"""Test location command functionality"""

import pytest
import tempfile
import os
from click.testing import CliRunner

from inv.cli import cli
from inv.utils.config import save_config, create_default_config


@pytest.fixture
def temp_config_and_db():
    """Create temporary config and database for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create test config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_locations.db'
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            db.initialize(config)
            create_tables()
            
            yield temp_dir
            
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def temp_config_and_db_with_locations():
    """Create temporary config and database with test locations"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create test config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_locations.db'
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            db.initialize(config)
            create_tables()
            
            # Create test locations
            runner = CliRunner()
            runner.invoke(cli, ['location', '--create', '--code=STORE-A1', '--type=store-floor', '--description=Store Floor Section A1'])
            runner.invoke(cli, ['location', '--create', '--code=WAREHOUSE-B2', '--type=warehouse', '--description=Warehouse Section B2'])
            runner.invoke(cli, ['location', '--create', '--code=STORAGE-C3', '--type=storage', '--description=Storage Room C3'])
            
            yield temp_dir
            
        finally:
            os.chdir(original_cwd)


class TestLocationCommand:
    """Test the location command functionality"""
    
    def test_location_command_help(self):
        """Test location command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--help'])
        assert result.exit_code == 0
        assert 'Manage inventory locations' in result.output
    
    def test_create_location(self, temp_config_and_db):
        """Test creating a new location"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'location', '--create', '--code=TEST-LOC', '--type=test', '--description=Test Location'
        ])
        
        assert result.exit_code == 0
        assert '✅ Created location: TEST-LOC' in result.output
        assert 'Type: test' in result.output
        assert 'Description: Test Location' in result.output
    
    def test_create_location_no_code(self, temp_config_and_db):
        """Test creating location without code"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--create'])
        
        assert result.exit_code == 0
        assert '❌ Location code is required' in result.output
    
    def test_create_location_invalid_code(self, temp_config_and_db):
        """Test creating location with invalid code"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'location', '--create', '--code=INVALID CODE!', '--type=test'
        ])
        
        assert result.exit_code == 0
        assert '❌ Invalid location code format' in result.output
    
    def test_create_duplicate_location(self, temp_config_and_db):
        """Test creating duplicate location"""
        runner = CliRunner()
        
        # Create first location
        result1 = runner.invoke(cli, [
            'location', '--create', '--code=DUPLICATE', '--type=test'
        ])
        assert '✅ Created location: DUPLICATE' in result1.output
        
        # Try to create duplicate
        result2 = runner.invoke(cli, [
            'location', '--create', '--code=DUPLICATE', '--type=test'
        ])
        assert result2.exit_code == 0
        assert 'already exists' in result2.output
    
    def test_list_locations_empty(self, temp_config_and_db):
        """Test listing locations when none exist"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--list'])
        
        assert result.exit_code == 0
        assert 'No locations found' in result.output
    
    def test_list_locations(self, temp_config_and_db_with_locations):
        """Test listing locations"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--list'])
        
        assert result.exit_code == 0
        assert '📍 Locations:' in result.output
        assert 'STORE-A1 (store-floor) - Store Floor Section A1 [Active]' in result.output
        assert 'WAREHOUSE-B2 (warehouse) - Warehouse Section B2 [Active]' in result.output
        assert 'STORAGE-C3 (storage) - Storage Room C3 [Active]' in result.output
    
    def test_location_stats_empty(self, temp_config_and_db_with_locations):
        """Test location statistics with no items"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--stats'])
        
        assert result.exit_code == 0
        assert '📊 Location Statistics:' in result.output
        assert 'STORE-A1' in result.output
        assert ': 0 items' in result.output
        assert 'Total items: 0' in result.output
    
    def test_deactivate_location(self, temp_config_and_db_with_locations):
        """Test deactivating a location"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--deactivate=STORAGE-C3'])
        
        assert result.exit_code == 0
        assert '✅ Deactivated location: STORAGE-C3' in result.output
    
    def test_deactivate_nonexistent_location(self, temp_config_and_db_with_locations):
        """Test deactivating non-existent location"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--deactivate=NONEXISTENT'])
        
        assert result.exit_code == 0
        assert '❌ Location \'NONEXISTENT\' not found' in result.output
    
    def test_suggest_location_code(self, temp_config_and_db):
        """Test location code suggestion"""
        runner = CliRunner()
        result = runner.invoke(cli, ['location', '--suggest'], input='warehouse\nSection D4\nn\n')
        
        assert result.exit_code == 0
        assert '💡 Suggested location code:' in result.output


class TestUpdateLocationCommand:
    """Test the update-location command functionality"""
    
    def test_update_location_command_help(self):
        """Test update-location command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['update-location', '--help'])
        assert result.exit_code == 0
        assert 'Update an existing location' in result.output
    
    def test_update_location_description(self, temp_config_and_db_with_locations):
        """Test updating location description"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'update-location', 'STORE-A1', '--description=Updated Store Floor Section A1'
        ])
        
        assert result.exit_code == 0
        assert '✅ Updated location: STORE-A1' in result.output
        assert 'Description: Updated Store Floor Section A1' in result.output
    
    def test_update_nonexistent_location(self, temp_config_and_db_with_locations):
        """Test updating non-existent location"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'update-location', 'NONEXISTENT', '--description=Test'
        ])
        
        assert result.exit_code == 0
        assert '❌ Location \'NONEXISTENT\' not found' in result.output
    
    def test_update_location_no_changes(self, temp_config_and_db_with_locations):
        """Test updating location with no changes specified"""
        runner = CliRunner()
        result = runner.invoke(cli, ['update-location', 'STORE-A1'])
        
        assert result.exit_code == 0
        assert '❌ No updates specified' in result.output


class TestFindLocationCommand:
    """Test the find-location command functionality"""
    
    def test_find_location_command_help(self):
        """Test find-location command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['find-location', '--help'])
        assert result.exit_code == 0
        assert 'Find locations by code or description' in result.output
    
    def test_find_location_by_code(self, temp_config_and_db_with_locations):
        """Test finding location by code"""
        runner = CliRunner()
        result = runner.invoke(cli, ['find-location', 'STORE'])
        
        assert result.exit_code == 0
        assert '🔍 Found 1 location(s) matching \'STORE\':' in result.output
        assert 'STORE-A1' in result.output
    
    def test_find_location_by_description(self, temp_config_and_db_with_locations):
        """Test finding location by description"""
        runner = CliRunner()
        result = runner.invoke(cli, ['find-location', 'Warehouse'])
        
        assert result.exit_code == 0
        assert '🔍 Found 1 location(s) matching \'Warehouse\':' in result.output
        assert 'WAREHOUSE-B2' in result.output
    
    def test_find_location_no_results(self, temp_config_and_db_with_locations):
        """Test finding location with no results"""
        runner = CliRunner()
        result = runner.invoke(cli, ['find-location', 'NONEXISTENT'])
        
        assert result.exit_code == 0
        assert 'No locations found matching \'NONEXISTENT\'' in result.output


class TestLocationUtilities:
    """Test location utility functions"""
    
    def test_location_code_validation(self):
        """Test location code validation"""
        from inv.utils.locations import validate_location_code
        
        # Valid codes
        assert validate_location_code('STORE-A1') is True
        assert validate_location_code('WAREHOUSE_B2') is True
        assert validate_location_code('SECTION123') is True
        
        # Invalid codes
        assert validate_location_code('') is False
        assert validate_location_code('INVALID CODE!') is False
        assert validate_location_code('A' * 51) is False  # Too long
    
    def test_suggest_location_code_function(self):
        """Test location code suggestion function"""
        from inv.utils.locations import suggest_location_code
        
        # Test with type only
        suggestion1 = suggest_location_code('warehouse')
        assert 'WARE' in suggestion1
        
        # Test with type and description
        suggestion2 = suggest_location_code('store-floor', 'Section A1')
        assert 'STOR' in suggestion2
        assert 'SEC' in suggestion2