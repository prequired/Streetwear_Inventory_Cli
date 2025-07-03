"""Test add command functionality"""

import pytest
import tempfile
import os
from decimal import Decimal
from click.testing import CliRunner

from inv.cli import cli
from inv.database.models import Item, Location
from inv.utils.config import save_config, create_default_config


@pytest.fixture
def temp_config_and_db():
    """Create temporary config and database for testing"""
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create test config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_add.db'
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            db.initialize(config)
            create_tables()
            
            # Create test location
            from inv.utils.locations import create_location
            create_location('TEST-LOC', 'test', 'Test Location')
            
            yield temp_dir
            
        finally:
            os.chdir(original_cwd)


class TestAddCommand:
    """Test the add command functionality"""
    
    def test_add_command_help(self):
        """Test add command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['add', '--help'])
        assert result.exit_code == 0
        assert 'Add a new item to inventory' in result.output
    
    def test_add_basic_item(self, temp_config_and_db):
        """Test adding a basic item"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'air jordan 1', '10', 'chicago', 'DS', '250', '200', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '✅ Added item NIK001' in result.output
        assert 'Brand: nike' in result.output
        assert 'Model: air jordan 1' in result.output
        assert 'Size: 10' in result.output
        assert 'Price: $250.00' in result.output
    
    def test_add_item_with_notes(self, temp_config_and_db):
        """Test adding item with notes"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'adidas', 'yeezy boost 350', '9.5', 'cream', 'VNDS', '180', '150', 'neither', 'TEST-LOC',
            '--notes', 'Small scuff on toe'
        ])
        
        assert result.exit_code == 0
        assert '✅ Added item ADI001' in result.output
        assert 'Notes: Small scuff on toe' in result.output
    
    def test_add_consignment_item(self, temp_config_and_db):
        """Test adding consignment item"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'supreme', 'box logo tee', 'L', 'white', 'DS', '120', '0', 'tag', 'TEST-LOC',
            '--consignment'
        ])
        
        assert result.exit_code == 0
        assert '✅ Added item SUP001' in result.output
        assert 'Type: Consignment' in result.output
    
    def test_add_clothing_size(self, temp_config_and_db):
        """Test adding item with clothing size"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'supreme', 'hoodie', 'XL', 'black', 'Used', '80', '60', 'neither', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '✅ Added item SUP001' in result.output
        assert 'Size: XL' in result.output
    
    def test_add_invalid_condition(self, temp_config_and_db):
        """Test adding item with invalid condition"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'black', 'NEW', '100', '80', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '❌ Invalid condition' in result.output
    
    def test_add_invalid_box_status(self, temp_config_and_db):
        """Test adding item with invalid box status"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'black', 'DS', '100', '80', 'none', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '❌ Invalid box status' in result.output
    
    def test_add_invalid_size(self, temp_config_and_db):
        """Test adding item with invalid size"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '99', 'black', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '❌ Invalid size' in result.output
    
    def test_add_invalid_price(self, temp_config_and_db):
        """Test adding item with invalid price"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'black', 'DS', 'abc', '80', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '❌ Invalid price format' in result.output
    
    def test_add_invalid_location(self, temp_config_and_db):
        """Test adding item with invalid location"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'black', 'DS', '100', '80', 'box', 'INVALID-LOC'
        ])
        
        assert result.exit_code == 0
        assert '❌ Location \'INVALID-LOC\' not found' in result.output
    
    def test_sku_generation(self, temp_config_and_db):
        """Test SKU generation and increment"""
        runner = CliRunner()
        
        # Add first Nike item
        result1 = runner.invoke(cli, [
            'add', 'nike', 'air jordan 1', '10', 'chicago', 'DS', '250', '200', 'box', 'TEST-LOC'
        ])
        assert '✅ Added item NIK001' in result1.output
        
        # Add second Nike item
        result2 = runner.invoke(cli, [
            'add', 'nike', 'air force 1', '9', 'white', 'DS', '120', '100', 'box', 'TEST-LOC'
        ])
        assert '✅ Added item NIK002' in result2.output
        
        # Add Adidas item
        result3 = runner.invoke(cli, [
            'add', 'adidas', 'stan smith', '10', 'white', 'DS', '90', '70', 'box', 'TEST-LOC'
        ])
        assert '✅ Added item ADI001' in result3.output
    
    def test_brand_prefix_generation(self, temp_config_and_db):
        """Test brand prefix generation for new brands"""
        runner = CliRunner()
        
        # Add item from new brand
        result = runner.invoke(cli, [
            'add', 'newbalance', 'test shoe', '10', 'gray', 'DS', '150', '120', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '✅ Added item' in result.output
        # Should generate NEW prefix for newbalance
    
    def test_photos_directory_creation(self, temp_config_and_db):
        """Test that photos directory is created"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'black', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert 'Photos directory: photos/NIK001' in result.output
        
        # Check if directory was actually created
        import os
        assert os.path.exists('photos/NIK001')


class TestAddVariantCommand:
    """Test the add-variant command functionality"""
    
    def test_add_variant_command_help(self):
        """Test add-variant command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['add-variant', '--help'])
        assert result.exit_code == 0
        assert 'Add a variant of an existing item' in result.output
    
    def test_add_variant_nonexistent_item(self, temp_config_and_db):
        """Test adding variant for non-existent item"""
        runner = CliRunner()
        result = runner.invoke(cli, ['add-variant', 'NIK999'], input='10.5\n')
        
        assert result.exit_code == 0
        assert '❌ Item with SKU \'NIK999\' not found' in result.output