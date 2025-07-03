#!/usr/bin/env python3
"""Test script to verify config file actually affects system behavior"""

import os
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from inv.cli import cli
from inv.utils.config import save_config, create_default_config, load_config


def test_brand_prefix_config():
    """Test that brand prefixes from config are actually used"""
    print("🔍 Testing brand prefix configuration...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create custom config with different brand prefixes
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_config.db'
            config['brand_prefixes'] = {
                'nike': 'NKE',  # Changed from NIK
                'adidas': 'ADS',  # Changed from ADI
                'supreme': 'SPR',  # Changed from SUP
                'testbrand': 'TST'  # New brand
            }
            config['defaults'] = {'location': 'TEST-LOC'}
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('TEST-LOC', 'test', 'Test Location')
            
            runner = CliRunner()
            
            # Test Nike with custom prefix NKE
            result = runner.invoke(cli, [
                'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
            ])
            
            if result.exit_code == 0:
                if 'NKE001' in result.output:
                    print("✅ Nike brand prefix correctly using NKE from config")
                elif 'NIK001' in result.output:
                    print("❌ Nike brand prefix still using default NIK (config not applied)")
                else:
                    print(f"⚠️  Unexpected Nike SKU format: {result.output}")
            else:
                print(f"❌ Failed to add Nike item: {result.output}")
            
            # Test Adidas with custom prefix ADS
            result = runner.invoke(cli, [
                'add', 'adidas', 'test shoe', '9', 'black', 'DS', '120', '90', 'box', 'TEST-LOC'
            ])
            
            if result.exit_code == 0:
                if 'ADS001' in result.output:
                    print("✅ Adidas brand prefix correctly using ADS from config")
                elif 'ADI001' in result.output:
                    print("❌ Adidas brand prefix still using default ADI (config not applied)")
                else:
                    print(f"⚠️  Unexpected Adidas SKU format: {result.output}")
            else:
                print(f"❌ Failed to add Adidas item: {result.output}")
            
            # Test new brand with custom prefix
            result = runner.invoke(cli, [
                'add', 'testbrand', 'test item', 'L', 'red', 'DS', '50', '30', 'tag', 'TEST-LOC'
            ])
            
            if result.exit_code == 0:
                if 'TST001' in result.output:
                    print("✅ New brand prefix correctly using TST from config")
                else:
                    print(f"⚠️  Unexpected new brand SKU format: {result.output}")
            else:
                print(f"❌ Failed to add new brand item: {result.output}")
                
        finally:
            os.chdir(original_cwd)


def test_database_url_config():
    """Test that database URL from config is actually used"""
    print("\n🔍 Testing database URL configuration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create config with custom database filename
            config = create_default_config()
            custom_db_name = 'custom_inventory_database.db'
            config['database']['url'] = f'sqlite:///{custom_db_name}'
            config['defaults'] = {'location': 'TEST-LOC'}
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('TEST-LOC', 'test', 'Test Location')
            
            # Add an item to ensure database is created and used
            runner = CliRunner()
            result = runner.invoke(cli, [
                'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
            ])
            
            if result.exit_code == 0:
                # Check if custom database file was created
                if Path(custom_db_name).exists():
                    print(f"✅ Custom database file '{custom_db_name}' was created and used")
                else:
                    print(f"❌ Custom database file '{custom_db_name}' was not created")
                    
                # Check if default database file was NOT created
                if not Path('streetwear_inventory.db').exists():
                    print("✅ Default database file was not created (config working)")
                else:
                    print("❌ Default database file was created (config not working)")
            else:
                print(f"❌ Failed to add item: {result.output}")
                
        finally:
            os.chdir(original_cwd)


def test_consignment_split_config():
    """Test that default consignment split from config is used"""
    print("\n🔍 Testing consignment split configuration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create config with custom default split
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_split.db'
            config['defaults'] = {
                'location': 'TEST-LOC',
                'consignment_split': 80  # Changed from default 70
            }
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('TEST-LOC', 'test', 'Test Location')
            
            runner = CliRunner()
            
            # Add consignment item without specifying split (should use config default)
            result = runner.invoke(cli, [
                'intake',
                '--consigner', 'Test Consigner',
                '--phone', '(555) 123-4567'
            ], input='nike\ntest shoe\n10\nwhite\nDS\n100\nbox\n\n')
            
            if result.exit_code == 0:
                if 'Split: 80% to consigner' in result.output:
                    print("✅ Consignment split correctly using 80% from config")
                elif 'Split: 70% to consigner' in result.output:
                    print("❌ Consignment split still using default 70% (config not applied)")
                else:
                    print(f"⚠️  Unexpected split format in output: {result.output}")
            else:
                print(f"❌ Failed to process consignment: {result.output}")
                
        finally:
            os.chdir(original_cwd)


def test_photos_storage_config():
    """Test that photos storage path from config is used"""
    print("\n🔍 Testing photos storage path configuration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create config with custom photos path
            custom_photos_path = './custom_photo_storage'
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_photos.db'
            config['photos']['storage_path'] = custom_photos_path
            config['defaults'] = {'location': 'TEST-LOC'}
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('TEST-LOC', 'test', 'Test Location')
            
            # Test PhotoManager uses config path
            from inv.utils.photos import PhotoManager
            photo_manager = PhotoManager()
            
            expected_path = Path(custom_photos_path).resolve()
            actual_path = photo_manager.storage_path.resolve()
            
            if actual_path == expected_path:
                print(f"✅ PhotoManager correctly using custom path '{custom_photos_path}' from config")
            else:
                print(f"❌ PhotoManager using '{actual_path}' instead of config path '{expected_path}'")
                
            # Verify the directory was created
            if photo_manager.storage_path.exists():
                print("✅ Custom photos directory was created")
            else:
                print("❌ Custom photos directory was not created")
                
        finally:
            os.chdir(original_cwd)


def test_config_file_reload():
    """Test that changes to config file are picked up"""
    print("\n🔍 Testing config file reload functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create initial config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_reload.db'
            config['brand_prefixes']['nike'] = 'NK1'
            config['defaults'] = {'location': 'TEST-LOC'}
            save_config(config)
            
            # Load config and verify initial value
            loaded_config = load_config()
            if loaded_config['brand_prefixes']['nike'] == 'NK1':
                print("✅ Initial config loaded correctly")
            else:
                print("❌ Initial config not loaded correctly")
                return
            
            # Modify config file directly
            config['brand_prefixes']['nike'] = 'NK2'
            save_config(config)
            
            # Load config with force_reload=True
            reloaded_config = load_config(force_reload=True)
            if reloaded_config['brand_prefixes']['nike'] == 'NK2':
                print("✅ Config changes picked up with force_reload=True")
            else:
                print("❌ Config changes not picked up with force_reload=True")
            
            # Load config without force_reload (should use cache)
            cached_config = load_config(force_reload=False)
            if cached_config['brand_prefixes']['nike'] == 'NK2':
                print("✅ Config caching working correctly")
            else:
                print("❌ Config caching not working correctly")
                
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    print("🧪 Testing Config File Effects\n")
    print("=" * 50)
    
    test_brand_prefix_config()
    test_database_url_config() 
    test_consignment_split_config()
    test_photos_storage_config()
    test_config_file_reload()
    
    print("\n" + "=" * 50)
    print("🏁 Config testing complete!")