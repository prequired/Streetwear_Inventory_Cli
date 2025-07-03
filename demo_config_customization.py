#!/usr/bin/env python3
"""Demo script showing how to customize configuration for different use cases"""

import os
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from inv.cli import cli
from inv.utils.config import save_config, load_config, create_default_config


def demo_brand_customization():
    """Show how to add custom brand prefixes"""
    print("📋 Demo: Custom Brand Prefixes")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Show default config
            config = create_default_config()
            print("Default brand prefixes:")
            for brand, prefix in config['brand_prefixes'].items():
                print(f"  {brand}: {prefix}")
            
            # Add custom brands
            config['brand_prefixes'].update({
                'off-white': 'OFW',
                'fear-of-god': 'FOG',
                'stone-island': 'STI',
                'balenciaga': 'BAL'
            })
            config['database']['url'] = 'sqlite:///demo_brands.db'
            config['defaults'] = {'location': 'DEMO-LOC'}
            save_config(config)
            
            print("\nCustomized brand prefixes:")
            for brand, prefix in config['brand_prefixes'].items():
                print(f"  {brand}: {prefix}")
            
            # Initialize and test
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('DEMO-LOC', 'demo', 'Demo Location')
            
            runner = CliRunner()
            
            # Test custom brand
            result = runner.invoke(cli, [
                'add', 'off-white', 'chicago 1', '10', 'white', 'DS', '2000', '1500', 'box', 'DEMO-LOC'
            ])
            
            if 'OFW001' in result.output:
                print("\n✅ Custom Off-White brand prefix working: OFW001")
            
            # Test another custom brand
            result = runner.invoke(cli, [
                'add', 'fear-of-god', 'essentials hoodie', 'L', 'cream', 'DS', '200', '150', 'tag', 'DEMO-LOC'
            ])
            
            if 'FOG001' in result.output:
                print("✅ Custom Fear of God brand prefix working: FOG001")
                
        finally:
            os.chdir(original_cwd)


def demo_split_customization():
    """Show how different consignment splits work"""
    print("\n💰 Demo: Custom Consignment Splits")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # High-end consigner setup (higher split)
            print("Scenario: High-end consigner (85% split)")
            config = create_default_config()
            config['database']['url'] = 'sqlite:///demo_splits.db'
            config['defaults'] = {
                'location': 'DEMO-LOC',
                'consignment_split': 85  # High-end consigners get better split
            }
            save_config(config)
            
            # Initialize
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('DEMO-LOC', 'demo', 'Demo Location')
            
            runner = CliRunner()
            
            # Add high-end consignment
            result = runner.invoke(cli, [
                'intake',
                '--consigner', 'VIP Customer',
                '--phone', '(555) 001-0001',
                '--email', 'vip@example.com'
            ], input='supreme\nbox logo hoodie\nL\nred\nDS\n500\ntag\nAuthenticated by StockX\n')
            
            if 'Split: 85% to consigner' in result.output:
                print("✅ VIP consigner gets 85% split from config")
                
                # Show payout calculation
                if result.exit_code == 0:
                    sku_line = [line for line in result.output.split('\n') if 'Added consignment item' in line][0]
                    sku = sku_line.split()[4].rstrip(':')
                    
                    # Simulate sale
                    sale_result = runner.invoke(cli, [
                        'consign-sold', sku, '500.00', '--platform', 'store'
                    ])
                    
                    if 'Consigner Payout: $425.00' in sale_result.output:
                        print("✅ High split payout: $425.00 (85% of $500)")
                        print("✅ Store keeps: $75.00 (15% of $500)")
            
        finally:
            os.chdir(original_cwd)


def demo_storage_customization():
    """Show how to customize photo storage location"""
    print("\n📸 Demo: Custom Photo Storage")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Setup config with custom photo storage
            config = create_default_config()
            config['database']['url'] = 'sqlite:///demo_photos.db'
            config['photos']['storage_path'] = './premium_photos'  # Custom path
            config['defaults'] = {'location': 'DEMO-LOC'}
            save_config(config)
            
            print(f"Custom photo storage path: {config['photos']['storage_path']}")
            
            # Test PhotoManager uses custom path
            from inv.utils.photos import PhotoManager
            photo_manager = PhotoManager()
            
            print(f"PhotoManager storage path: {photo_manager.storage_path}")
            
            if photo_manager.storage_path.name == 'premium_photos':
                print("✅ PhotoManager using custom storage directory")
                
                if photo_manager.storage_path.exists():
                    print("✅ Custom photo directory created automatically")
                    
        finally:
            os.chdir(original_cwd)


def demo_database_customization():
    """Show how different database configurations work"""
    print("\n💾 Demo: Custom Database Locations")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create production-like config
            config = create_default_config()
            
            # Production database in data directory
            data_dir = Path('./data')
            data_dir.mkdir(exist_ok=True)
            
            config['database']['url'] = f'sqlite:///{data_dir}/production_inventory.db'
            config['defaults'] = {'location': 'WAREHOUSE-A1'}
            save_config(config)
            
            print(f"Production database: {config['database']['url']}")
            
            # Initialize
            from inv.database.connection import db
            from inv.database.setup import create_tables
            from inv.utils.locations import create_location
            
            db.initialize(config)
            create_tables()
            create_location('WAREHOUSE-A1', 'warehouse', 'Main Warehouse Section A1')
            
            # Verify database file created in correct location
            db_file = data_dir / 'production_inventory.db'
            if db_file.exists():
                print(f"✅ Database created at: {db_file}")
                print(f"✅ Database size: {db_file.stat().st_size} bytes")
            else:
                print("❌ Database not created at expected location")
                
        finally:
            os.chdir(original_cwd)


def show_config_file_example():
    """Show what a fully customized config file looks like"""
    print("\n📄 Example: Complete Custom Config File")
    print("=" * 50)
    
    example_config = {
        'database': {
            'url': 'sqlite:///data/my_store_inventory.db'
        },
        'brand_prefixes': {
            'nike': 'NIK',
            'adidas': 'ADI',
            'supreme': 'SUP',
            'jordan': 'JOR',
            'off-white': 'OFW',
            'fear-of-god': 'FOG',
            'stone-island': 'STI',
            'balenciaga': 'BAL',
            'yeezy': 'YZY',
            'travis-scott': 'TRS',
            'fragment': 'FRG'
        },
        'defaults': {
            'location': 'MAIN-FLOOR',
            'consignment_split': 75  # Custom default split
        },
        'photos': {
            'storage_path': './store_photos'
        }
    }
    
    print("Example config.yaml:")
    print("-" * 20)
    
    import yaml
    print(yaml.dump(example_config, default_flow_style=False, indent=2))
    
    print("-" * 20)
    print("This config would:")
    print("• Store database in ./data/ directory")
    print("• Support 11 different brands with custom prefixes")
    print("• Use 75% as default consignment split")
    print("• Store photos in ./store_photos/ directory")
    print("• Default all items to MAIN-FLOOR location")


if __name__ == "__main__":
    print("🎯 Configuration Customization Demo")
    print("=" * 60)
    print("This demo shows how config.yaml affects system behavior\n")
    
    demo_brand_customization()
    demo_split_customization()
    demo_storage_customization() 
    demo_database_customization()
    show_config_file_example()
    
    print("\n" + "=" * 60)
    print("🎉 Demo complete!")
    print("\nTo customize your setup:")
    print("1. Edit config.yaml in your working directory")
    print("2. Modify brand_prefixes, defaults, photos, or database settings")
    print("3. Changes take effect immediately for new operations")
    print("4. Use 'inv validate-config' to check your configuration")