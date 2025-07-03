"""Main CLI entry point for streetwear inventory management"""

import click
import sys
from pathlib import Path

from .utils.config import create_default_config, save_config, load_config, get_config_path, validate_config_file
from .database.connection import db
from .database.setup import create_tables
from .commands.add import add, add_variant
from .commands.location import location, update_location_cmd, find_location
from .commands.search import search, show
from .commands.edit import edit, update_status, move
from .commands.intake import intake, list_consigners, consigner_report
from .commands.consign import consign, consign_sold, payout_summary, hold_item
from .commands.photos import (
    add_photo, list_photos, remove_photo, set_primary_photo, copy_photos,
    photo_stats, optimize_photos, find_duplicate_photos_cmd, remove_exif_cmd, bulk_add_photos
)
from .commands.api import api_server, api_test, api_docs, generate_api_client
from .commands.export import (
    export_inventory, export_consigners, export_locations, 
    backup_database, export_template
)


@click.group()
def cli():
    """Streetwear Inventory Management CLI"""
    pass


@cli.command()
def setup():
    """Interactive setup wizard to configure the application"""
    click.echo("🔧 Streetwear Inventory CLI Setup Wizard")
    click.echo("=" * 50)
    
    # Check if config already exists
    config_path = get_config_path()
    if config_path.exists():
        if not click.confirm("Configuration file already exists. Overwrite?"):
            click.echo("Setup cancelled.")
            return
    
    # Create default config structure
    config = create_default_config()
    
    # Get database configuration
    click.echo("\n📊 Database Configuration")
    config['database']['url'] = click.prompt(
        "Database URL", 
        type=str,
        default="sqlite:///streetwear_inventory.db",
        help="Example: sqlite:///streetwear_inventory.db"
    )
    
    # Get default settings
    click.echo("\n⚙️  Default Settings")
    default_location = click.prompt(
        "Default location code (optional)", 
        type=str, 
        default="",
        show_default=False
    )
    if default_location:
        config['defaults']['location'] = default_location
    
    consignment_split = click.prompt(
        "Default consignment split percentage", 
        type=int, 
        default=70,
        show_default=True
    )
    config['defaults']['consignment_split'] = consignment_split
    
    # Brand prefixes
    click.echo("\n🏷️  Brand Prefixes")
    click.echo("Configure 3-letter prefixes for SKU generation:")
    
    # Show current defaults
    for brand, prefix in config['brand_prefixes'].items():
        new_prefix = click.prompt(
            f"{brand.title()} prefix", 
            type=str, 
            default=prefix,
            show_default=True
        )
        if len(new_prefix) != 3:
            click.echo(f"Warning: '{new_prefix}' is not 3 characters. Using default.")
        else:
            config['brand_prefixes'][brand] = new_prefix.upper()
    
    # Add more brands
    while click.confirm("Add another brand prefix?"):
        brand = click.prompt("Brand name", type=str).lower()
        prefix = click.prompt("3-letter prefix", type=str)
        if len(prefix) == 3:
            config['brand_prefixes'][brand] = prefix.upper()
        else:
            click.echo("Prefix must be exactly 3 characters. Skipping.")
    
    # Photo storage
    click.echo("\n📸 Photo Storage")
    storage_path = click.prompt(
        "Photo storage path", 
        type=str, 
        default=config['photos']['storage_path'],
        show_default=True
    )
    config['photos']['storage_path'] = storage_path
    
    # Save configuration
    try:
        save_config(config)
        click.echo(f"\n✅ Configuration saved to {config_path}")
    except Exception as e:
        click.echo(f"\n❌ Failed to save configuration: {e}")
        sys.exit(1)
    
    # Initialize database connection
    click.echo("\n🔌 Testing database connection...")
    try:
        db.initialize(config)
        if db.test_connection():
            click.echo("✅ Database connection successful")
        else:
            click.echo("❌ Database connection failed")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Database connection error: {e}")
        sys.exit(1)
    
    # Create database tables
    click.echo("\n🗄️  Creating database tables...")
    try:
        create_tables()
        click.echo("✅ Database tables created successfully")
    except Exception as e:
        click.echo(f"❌ Failed to create database tables: {e}")
        sys.exit(1)
    
    # Create photos directory
    photos_dir = Path(storage_path)
    photos_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Photos directory created: {photos_dir}")
    
    click.echo("\n🎉 Setup complete! You can now use the inventory CLI.")
    click.echo("Try: inv test-connection")


@cli.command('test-connection')
def test_connection():
    """Test database connection"""
    try:
        config = load_config()
        db.initialize(config)
        
        if db.test_connection():
            click.echo("✅ Database connection successful")
        else:
            click.echo("❌ Database connection failed")
            sys.exit(1)
            
    except FileNotFoundError:
        click.echo("❌ Configuration file not found. Run 'inv setup' first.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Connection error: {e}")
        sys.exit(1)


@cli.command('validate-config')
def validate_config():
    """Validate the current configuration file"""
    try:
        config_path = get_config_path()
        
        if not config_path.exists():
            click.echo("❌ Configuration file not found. Run 'inv setup' first.")
            sys.exit(1)
        
        click.echo(f"🔍 Validating configuration: {config_path}")
        
        # Validate structure
        errors = validate_config_file()
        
        if not errors:
            click.echo("✅ Configuration is valid!")
            
            # Show current config summary
            config = load_config()
            click.echo("\n📋 Current Configuration:")
            click.echo(f"  Database: {config['database']['url']}")
            click.echo(f"  Photo Storage: {config['photos']['storage_path']}")
            click.echo(f"  Default Split: {config['defaults']['consignment_split']}%")
            click.echo(f"  Brand Prefixes: {len(config['brand_prefixes'])} configured")
            
            # Test database connection
            click.echo("\n🔌 Testing database connection...")
            try:
                db.initialize(config)
                if db.test_connection():
                    click.echo("✅ Database connection successful")
                else:
                    click.echo("⚠️  Database connection failed")
            except Exception as e:
                click.echo(f"⚠️  Database connection error: {e}")
            
        else:
            click.echo("❌ Configuration errors found:")
            for error in errors:
                click.echo(f"  • {error}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Validation error: {e}")
        sys.exit(1)


# Register commands
cli.add_command(add)
cli.add_command(add_variant)
cli.add_command(location)
cli.add_command(update_location_cmd)
cli.add_command(find_location)
cli.add_command(search)
cli.add_command(show)
cli.add_command(edit)
cli.add_command(update_status)
cli.add_command(move)
cli.add_command(intake)
cli.add_command(list_consigners)
cli.add_command(consigner_report)
cli.add_command(consign)
cli.add_command(consign_sold)
cli.add_command(payout_summary)
cli.add_command(hold_item)
cli.add_command(add_photo)
cli.add_command(list_photos)
cli.add_command(remove_photo)
cli.add_command(set_primary_photo)
cli.add_command(copy_photos)
cli.add_command(photo_stats)
cli.add_command(optimize_photos)
cli.add_command(find_duplicate_photos_cmd)
cli.add_command(remove_exif_cmd)
cli.add_command(bulk_add_photos)
cli.add_command(api_server)
cli.add_command(api_test)
cli.add_command(api_docs)
cli.add_command(generate_api_client)
cli.add_command(export_inventory)
cli.add_command(export_consigners)
cli.add_command(export_locations)
cli.add_command(backup_database)
cli.add_command(export_template)


def main():
    """Main entry point for the CLI"""
    cli()


if __name__ == '__main__':
    main()