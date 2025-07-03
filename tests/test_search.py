"""Test search command functionality"""

import pytest
import tempfile
import os
from click.testing import CliRunner

from inv.cli import cli
from inv.utils.config import save_config, create_default_config


@pytest.fixture
def temp_config_and_db_with_items():
    """Create temporary config and database with test items"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create test config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_search.db'
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            db.initialize(config)
            create_tables()
            
            # Create test location
            from inv.utils.locations import create_location
            create_location('TEST-LOC', 'test', 'Test Location')
            
            # Add test items
            runner = CliRunner()
            
            # Nike items
            runner.invoke(cli, ['add', 'nike', 'air jordan 1', '10', 'chicago', 'DS', '250', '200', 'box', 'TEST-LOC'])
            runner.invoke(cli, ['add', 'nike', 'air jordan 1', '9', 'bred', 'DS', '275', '225', 'box', 'TEST-LOC'])
            runner.invoke(cli, ['add', 'nike', 'air force 1', '10', 'white', 'VNDS', '120', '100', 'box', 'TEST-LOC'])
            
            # Adidas items
            runner.invoke(cli, ['add', 'adidas', 'yeezy boost 350', '9.5', 'cream', 'DS', '180', '150', 'neither', 'TEST-LOC'])
            runner.invoke(cli, ['add', 'adidas', 'stan smith', '10', 'white', 'Used', '90', '70', 'box', 'TEST-LOC'])
            
            # Supreme item
            runner.invoke(cli, ['add', 'supreme', 'box logo tee', 'L', 'white', 'DS', '120', '80', 'tag', 'TEST-LOC'])
            
            yield temp_dir
            
        finally:
            os.chdir(original_cwd)


class TestSearchCommand:
    """Test the search command functionality"""
    
    def test_search_command_help(self):
        """Test search command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--help'])
        assert result.exit_code == 0
        assert 'Search inventory items' in result.output
    
    def test_search_all_items(self, temp_config_and_db_with_items):
        """Test searching all items"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output
        assert 'NIK002' in result.output
        assert 'NIK003' in result.output
        assert 'ADI001' in result.output
        assert 'ADI002' in result.output
        assert 'SUP001' in result.output
        assert 'Showing 1-6 of 6 (end)' in result.output
    
    def test_search_by_brand(self, temp_config_and_db_with_items):
        """Test searching by brand"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--brand=nike'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output
        assert 'NIK002' in result.output
        assert 'NIK003' in result.output
        assert 'ADI001' not in result.output
        assert 'SUP001' not in result.output
    
    def test_search_by_text(self, temp_config_and_db_with_items):
        """Test text search"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', 'jordan'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output  # air jordan 1
        assert 'NIK002' in result.output  # air jordan 1
        assert 'NIK003' not in result.output  # air force 1
        assert 'ADI001' not in result.output
    
    def test_search_by_size(self, temp_config_and_db_with_items):
        """Test searching by size"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--size=10'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output  # size 10
        assert 'NIK003' in result.output  # size 10
        assert 'ADI002' in result.output  # size 10
        assert 'NIK002' not in result.output  # size 9
        assert 'ADI001' not in result.output  # size 9.5
    
    def test_search_by_condition(self, temp_config_and_db_with_items):
        """Test searching by condition"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--condition=DS'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output
        assert 'NIK002' in result.output
        assert 'ADI001' in result.output
        assert 'SUP001' in result.output
        assert 'NIK003' not in result.output  # VNDS
        assert 'ADI002' not in result.output  # Used
    
    def test_search_available_only(self, temp_config_and_db_with_items):
        """Test searching available items only"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--available'])
        
        assert result.exit_code == 0
        # All items should be available by default
        assert 'NIK001' in result.output
        assert 'ADI001' in result.output
        assert 'SUP001' in result.output
    
    def test_search_by_price_range(self, temp_config_and_db_with_items):
        """Test searching by price range"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--min-price=200'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output  # $250
        assert 'NIK002' in result.output  # $275
        assert 'NIK003' not in result.output  # $120
        assert 'ADI001' not in result.output  # $180
    
    def test_search_count_only(self, temp_config_and_db_with_items):
        """Test search with count only"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--count'])
        
        assert result.exit_code == 0
        assert 'Total items: 6' in result.output
        assert 'NIK001' not in result.output  # Should not show details
    
    def test_search_by_sku(self, temp_config_and_db_with_items):
        """Test searching by SKU"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--sku=NIK001'])
        
        assert result.exit_code == 0
        assert 'NIK001' in result.output
        assert 'NIK002' not in result.output
    
    def test_search_no_results(self, temp_config_and_db_with_items):
        """Test search with no results"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', 'nonexistent'])
        
        assert result.exit_code == 0
        assert 'No items found' in result.output
    
    def test_search_detailed(self, temp_config_and_db_with_items):
        """Test detailed search results"""
        runner = CliRunner()
        result = runner.invoke(cli, ['search', '--brand=nike', '--detailed'])
        
        assert result.exit_code == 0
        assert 'SKU: NIK001' in result.output
        assert 'Brand: nike' in result.output
        assert 'Model: air jordan 1' in result.output
        assert 'Current Price: $250.00' in result.output
        assert 'Purchase Price: $200.00' in result.output


class TestShowCommand:
    """Test the show command functionality"""
    
    def test_show_command_help(self):
        """Test show command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['show', '--help'])
        assert result.exit_code == 0
        assert 'Show detailed information for a specific item' in result.output
    
    def test_show_existing_item(self, temp_config_and_db_with_items):
        """Test showing existing item"""
        runner = CliRunner()
        result = runner.invoke(cli, ['show', 'NIK001'])
        
        assert result.exit_code == 0
        assert 'SKU: NIK001' in result.output
        assert 'Brand: nike' in result.output
        assert 'Model: air jordan 1' in result.output
        assert 'Size: 10' in result.output
        assert 'Color: chicago' in result.output
        assert 'Current Price: $250.00' in result.output
        assert '📸 No photos' in result.output
    
    def test_show_nonexistent_item(self, temp_config_and_db_with_items):
        """Test showing non-existent item"""
        runner = CliRunner()
        result = runner.invoke(cli, ['show', 'NIK999'])
        
        assert result.exit_code == 0
        assert '❌ Item with SKU \'NIK999\' not found' in result.output