"""Location command implementation for managing inventory locations"""

import click
from ..utils.locations import (
    create_location, list_locations, get_location_by_code, 
    update_location, deactivate_location, move_item_to_location,
    get_location_stats, validate_location_code, suggest_location_code
)
from ..utils.database_init import with_database


@click.command()
@with_database
@click.option('--create', is_flag=True, help='Create a new location')
@click.option('--list', 'list_locations_flag', is_flag=True, help='List all locations')
@click.option('--show-inactive', is_flag=True, help='Include inactive locations in list')
@click.option('--stats', is_flag=True, help='Show location statistics')
@click.option('--code', help='Location code')
@click.option('--type', 'location_type', help='Location type (e.g., store-floor, warehouse, storage)')
@click.option('--description', help='Location description')
@click.option('--move', help='Move item (specify SKU)')
@click.option('--to', 'to_location', help='Target location for move operation')
@click.option('--deactivate', help='Deactivate location (specify code)')
@click.option('--suggest', is_flag=True, help='Suggest location code based on type and description')
def location(create, list_locations_flag, show_inactive, stats, code, location_type, 
            description, move, to_location, deactivate, suggest):
    """Manage inventory locations
    
    Usage:
      inv location --create --code=store-floor-A1 --type=store-floor --description="Store Floor Section A1"
      inv location --list
      inv location --stats
      inv location --move=NIK001 --to=warehouse-B2
      inv location --deactivate=old-storage
    """
    
    try:
        if create:
            # Create new location
            if not code:
                click.echo("❌ Location code is required when creating a location")
                return
            
            if not validate_location_code(code):
                click.echo("❌ Invalid location code format. Use letters, numbers, hyphens, and underscores only.")
                return
            
            try:
                location_obj = create_location(
                    code=code,
                    location_type=location_type,
                    description=description
                )
                
                click.echo(f"✅ Created location: {location_obj.code}")
                if location_obj.location_type:
                    click.echo(f"Type: {location_obj.location_type}")
                if location_obj.description:
                    click.echo(f"Description: {location_obj.description}")
                    
            except ValueError as e:
                click.echo(f"❌ {e}")
                
        elif list_locations_flag:
            # List all locations
            locations = list_locations(show_inactive=show_inactive)
            
            if not locations:
                click.echo("No locations found.")
                return
            
            click.echo("📍 Locations:")
            click.echo("-" * 50)
            
            for loc in locations:
                status = "Active" if loc.is_active else "Inactive"
                type_str = f" ({loc.location_type})" if loc.location_type else ""
                desc_str = f" - {loc.description}" if loc.description else ""
                
                click.echo(f"{loc.code}{type_str}{desc_str} [{status}]")
                
        elif stats:
            # Show location statistics
            stats_data = get_location_stats()
            
            if not stats_data:
                click.echo("No location statistics available.")
                return
            
            click.echo("📊 Location Statistics:")
            click.echo("-" * 50)
            
            total_items = sum(data['item_count'] for data in stats_data.values())
            
            for location_code, data in sorted(stats_data.items()):
                desc = f" ({data['description']})" if data['description'] else ""
                click.echo(f"{location_code}{desc}: {data['item_count']} items")
            
            click.echo("-" * 50)
            click.echo(f"Total items: {total_items}")
            
        elif move and to_location:
            # Move item to different location
            from ..database.connection import get_db_session
            from ..database.models import Item
            
            with get_db_session() as session:
                item = session.query(Item).filter(Item.sku == move).first()
                if not item:
                    click.echo(f"❌ Item with SKU '{move}' not found.")
                    return
                
                target_location = get_location_by_code(to_location)
                if not target_location:
                    click.echo(f"❌ Location '{to_location}' not found.")
                    return
                
                # Update item location
                item.location_id = target_location.id
                session.commit()
                
                click.echo(f"✅ Moved {move} to {to_location}")
                
        elif deactivate:
            # Deactivate location
            if deactivate_location(deactivate):
                click.echo(f"✅ Deactivated location: {deactivate}")
            else:
                click.echo(f"❌ Location '{deactivate}' not found.")
                
        elif suggest:
            # Suggest location code
            if not location_type:
                location_type = click.prompt("Location type")
                
            description_input = click.prompt("Description (optional)", default="")
            suggested = suggest_location_code(location_type, description_input if description_input else None)
            
            click.echo(f"💡 Suggested location code: {suggested}")
            
            if click.confirm("Create location with this code?"):
                try:
                    location_obj = create_location(
                        code=suggested,
                        location_type=location_type,
                        description=description_input if description_input else None
                    )
                    click.echo(f"✅ Created location: {location_obj.code}")
                except ValueError as e:
                    click.echo(f"❌ {e}")
                    
        else:
            # Show help if no action specified
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@click.command(name='update-location')
@with_database
@click.argument('code')
@click.option('--type', 'new_type', help='New location type')
@click.option('--description', 'new_description', help='New description')
@click.option('--activate', is_flag=True, help='Reactivate location')
def update_location_cmd(code, new_type, new_description, activate):
    """Update an existing location
    
    Usage:
      inv update-location store-floor-A1 --description="Updated description"
      inv update-location old-storage --activate
    """
    
    try:
        updates = {}
        
        if new_type:
            updates['location_type'] = new_type
        if new_description:
            updates['description'] = new_description
        if activate:
            updates['is_active'] = True
            
        if not updates:
            click.echo("❌ No updates specified. Use --type, --description, or --activate")
            return
            
        location_obj = update_location(code, **updates)
        
        if location_obj:
            click.echo(f"✅ Updated location: {location_obj.code}")
            if new_type:
                click.echo(f"Type: {location_obj.location_type}")
            if new_description:
                click.echo(f"Description: {location_obj.description}")
            if activate:
                click.echo("Status: Active")
        else:
            click.echo(f"❌ Location '{code}' not found.")
            
    except Exception as e:
        click.echo(f"❌ Error updating location: {e}")


@click.command(name='find-location')
@with_database
@click.argument('search_term')
def find_location(search_term):
    """Find locations by code or description
    
    Usage:
      inv find-location "store"
      inv find-location "A1"
    """
    
    try:
        locations = list_locations()
        
        # Filter locations by search term
        matching_locations = []
        search_lower = search_term.lower()
        
        for loc in locations:
            if (search_lower in loc.code.lower() or 
                (loc.description and search_lower in loc.description.lower()) or
                (loc.location_type and search_lower in loc.location_type.lower())):
                matching_locations.append(loc)
        
        if not matching_locations:
            click.echo(f"No locations found matching '{search_term}'")
            return
        
        click.echo(f"🔍 Found {len(matching_locations)} location(s) matching '{search_term}':")
        click.echo("-" * 50)
        
        for loc in matching_locations:
            type_str = f" ({loc.location_type})" if loc.location_type else ""
            desc_str = f" - {loc.description}" if loc.description else ""
            click.echo(f"{loc.code}{type_str}{desc_str}")
            
    except Exception as e:
        click.echo(f"❌ Error searching locations: {e}")