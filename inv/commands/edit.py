"""Edit command implementation for modifying existing inventory items"""

import click
from datetime import datetime
from decimal import Decimal

from ..database.connection import get_db_session
from ..database.models import Item
from ..utils.validation import (
    validate_price, validate_condition, validate_box_status, 
    validate_item_status
)
from ..utils.locations import get_location_by_code
from ..utils.database_init import with_database
from ..utils.pricing import round_price_up


@click.command()
@with_database
@click.argument('sku')
@click.option('--price', type=str, help='Update current price')
@click.option('--status', type=click.Choice(['available', 'sold', 'held', 'deleted']), 
              help='Update item status')
@click.option('--sold-price', type=str, help='Set sold price (required when marking as sold)')
@click.option('--sold-platform', type=str, help='Platform where item was sold')
@click.option('--condition', type=click.Choice(['DS', 'VNDS', 'Used']), 
              help='Update condition')
@click.option('--location', type=str, help='Move item to different location (location code)')
@click.option('--notes', type=str, help='Update notes')
@click.option('--box-status', type=click.Choice(['box', 'tag', 'both', 'neither']), 
              help='Update box status')
@click.option('--round-price', is_flag=True, help='Round price up to nearest $5')
@click.option('--interactive', '-i', is_flag=True, help='Interactive edit mode')
def edit(sku, price, status, sold_price, sold_platform, condition, location, 
         notes, box_status, round_price, interactive):
    """Edit an existing inventory item
    
    Usage:
      inv edit NIK001 --price=300 --status=sold --sold-price=275
      inv edit NIK001 --condition=VNDS --notes="Minor scuffing"
      inv edit NIK001 --location=store-floor-B2
      inv edit NIK001 --interactive
    
    Arguments:
      SKU             Item SKU to edit
    """
    
    try:
        with get_db_session() as session:
            # Find the item
            item = session.query(Item).filter(Item.sku.ilike(f"%{sku.upper()}%")).first()
            
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found.")
                return
            
            # Show current item details
            click.echo(f"📝 Editing item {item.sku}: {item.brand} {item.model}")
            click.echo(f"Current: Size {item.size}, {item.condition}, ${item.current_price:.2f}, {item.status}")
            
            if interactive:
                # Interactive edit mode
                _interactive_edit(session, item)
                return
            
            # Track what was updated
            updates = []
            
            # Validate status change first (affects other validations)
            if status and status != item.status:
                if status == 'sold':
                    if not sold_price:
                        click.echo("❌ --sold-price is required when marking item as sold")
                        return
                    
                    try:
                        sold_price_decimal = validate_price(sold_price)
                        item.sold_price = sold_price_decimal
                        item.sold_date = datetime.now()
                        updates.append(f"sold price: ${sold_price_decimal:.2f}")
                        
                        if sold_platform:
                            item.sold_platform = sold_platform
                            updates.append(f"platform: {sold_platform}")
                        
                    except ValueError as e:
                        click.echo(f"❌ Invalid sold price: {e}")
                        return
                
                elif item.status == 'sold' and status != 'sold':
                    # Moving from sold to another status - clear sale fields
                    item.sold_price = None
                    item.sold_date = None
                    item.sold_platform = None
                    updates.append("cleared sale information")
                
                item.status = status
                updates.append(f"status: {status}")
            
            # Update current price
            if price:
                try:
                    price_decimal = validate_price(price)
                    
                    if round_price:
                        price_decimal = round_price_up(price_decimal)
                        updates.append(f"price: ${price_decimal:.2f} (rounded up)")
                    else:
                        updates.append(f"price: ${price_decimal:.2f}")
                    
                    item.current_price = price_decimal
                    
                except ValueError as e:
                    click.echo(f"❌ Invalid price: {e}")
                    return
            
            # Update condition
            if condition and condition != item.condition:
                item.condition = condition
                updates.append(f"condition: {condition}")
            
            # Update box status
            if box_status and box_status != item.box_status:
                item.box_status = box_status
                updates.append(f"box status: {box_status}")
            
            # Update location
            if location:
                location_obj = get_location_by_code(location.upper())
                if not location_obj:
                    click.echo(f"❌ Location '{location}' not found.")
                    return
                
                if location_obj.id != item.location_id:
                    old_location = item.location.code if item.location else "No Location"
                    item.location_id = location_obj.id
                    updates.append(f"location: {old_location} → {location_obj.code}")
            
            # Update notes
            if notes is not None:  # Allow empty string to clear notes
                if notes != (item.notes or ""):
                    item.notes = notes if notes else None
                    updates.append(f"notes: {'updated' if notes else 'cleared'}")
            
            # Check if any updates were made
            if not updates:
                click.echo("❌ No changes specified. Use --help to see available options.")
                return
            
            # Special validation for consignment items
            if item.ownership_type == 'consignment':
                if status == 'sold':
                    # Calculate consignment payout
                    payout = _calculate_consignment_payout(
                        item.sold_price, 
                        sold_platform or 'Unknown',
                        item.split_percentage or 70
                    )
                    click.echo(f"💰 Consignment payout: ${payout:.2f}")
            
            # Commit changes
            session.commit()
            session.refresh(item)
            
            # Show success message
            click.echo(f"✅ Updated {item.sku}:")
            for update in updates:
                click.echo(f"  • {update}")
            
            # Show consignment details if applicable
            if item.ownership_type == 'consignment' and item.consigner:
                click.echo(f"  • Consigner: {item.consigner.name}")
    
    except Exception as e:
        click.echo(f"❌ Error editing item: {e}")
        import traceback
        traceback.print_exc()


def _interactive_edit(session, item):
    """Interactive edit mode with prompts"""
    click.echo("\n🖊️  Interactive Edit Mode")
    click.echo("Press Enter to keep current value, or type new value:")
    
    updates = []
    
    # Edit price
    current_price_str = str(item.current_price)
    new_price = click.prompt(f"Current price [{current_price_str}]", 
                           default=current_price_str, show_default=False)
    
    if new_price != current_price_str:
        try:
            price_decimal = validate_price(new_price)
            
            # Ask about rounding
            if click.confirm("Round price up to nearest $5?"):
                price_decimal = round_price_up(price_decimal)
                updates.append(f"price: ${price_decimal:.2f} (rounded up)")
            else:
                updates.append(f"price: ${price_decimal:.2f}")
            
            item.current_price = price_decimal
        except ValueError as e:
            click.echo(f"❌ Invalid price: {e}")
            return
    
    # Edit condition
    new_condition = click.prompt(f"Condition [{item.condition}]", 
                               default=item.condition, show_default=False)
    if new_condition != item.condition:
        if validate_condition(new_condition):
            item.condition = new_condition
            updates.append(f"condition: {new_condition}")
        else:
            click.echo("❌ Invalid condition. Not updated.")
    
    # Edit status
    new_status = click.prompt(f"Status [{item.status}]", 
                            default=item.status, show_default=False)
    if new_status != item.status:
        if validate_item_status(new_status):
            if new_status == 'sold':
                sold_price = click.prompt("Sold price", type=str)
                sold_platform = click.prompt("Sold platform (optional)", default="")
                
                try:
                    sold_price_decimal = validate_price(sold_price)
                    item.sold_price = sold_price_decimal
                    item.sold_date = datetime.now()
                    item.sold_platform = sold_platform if sold_platform else None
                    updates.append(f"sold: ${sold_price_decimal:.2f}")
                    if sold_platform:
                        updates.append(f"platform: {sold_platform}")
                except ValueError as e:
                    click.echo(f"❌ Invalid sold price: {e}")
                    return
            
            item.status = new_status
            updates.append(f"status: {new_status}")
        else:
            click.echo("❌ Invalid status. Not updated.")
    
    # Edit notes
    current_notes = item.notes or ""
    new_notes = click.prompt(f"Notes [{current_notes[:50] + '...' if len(current_notes) > 50 else current_notes}]", 
                           default=current_notes, show_default=False)
    if new_notes != current_notes:
        item.notes = new_notes if new_notes else None
        updates.append(f"notes: {'updated' if new_notes else 'cleared'}")
    
    # Edit location
    current_location = item.location.code if item.location else "No Location"
    new_location = click.prompt(f"Location [{current_location}]", 
                              default=current_location, show_default=False)
    if new_location != current_location and new_location != "No Location":
        location_obj = get_location_by_code(new_location.upper())
        if location_obj:
            item.location_id = location_obj.id
            updates.append(f"location: {current_location} → {location_obj.code}")
        else:
            click.echo(f"❌ Location '{new_location}' not found. Not updated.")
    
    # Confirm and save
    if updates:
        click.echo("\nPending changes:")
        for update in updates:
            click.echo(f"  • {update}")
        
        if click.confirm("\nSave changes?"):
            session.commit()
            session.refresh(item)
            click.echo("✅ Changes saved successfully.")
        else:
            session.rollback()
            click.echo("❌ Changes discarded.")
    else:
        click.echo("No changes made.")


def _calculate_consignment_payout(sold_price, platform, split_percentage):
    """Calculate consignment payout"""
    from ..utils.pricing import calculate_consignment_payout
    
    # Platform fees (simplified)
    platform_fees = {
        'stockx': 12.5,
        'goat': 12.0,
        'ebay': 13.0,
        'grailed': 8.0,
        'depop': 10.0,
        'mercari': 10.0
    }
    
    platform_fee = platform_fees.get(platform.lower(), 10.0)  # Default 10%
    
    return calculate_consignment_payout(sold_price, platform_fee, split_percentage)


@click.command()
@with_database
@click.argument('sku')
@click.option('--status', type=click.Choice(['available', 'sold', 'held']), 
              required=True, help='New status for the item')
@click.option('--sold-price', type=str, help='Sold price (required for sold status)')
@click.option('--sold-platform', type=str, help='Platform where sold')
def update_status(sku, status, sold_price, sold_platform):
    """Quick status update for an item
    
    Usage:
      inv update-status NIK001 --status=sold --sold-price=275 --sold-platform=StockX
      inv update-status NIK001 --status=available
      inv update-status NIK001 --status=held
    """
    
    try:
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku.ilike(f"%{sku.upper()}%")).first()
            
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found.")
                return
            
            old_status = item.status
            
            if status == 'sold':
                if not sold_price:
                    click.echo("❌ --sold-price is required when marking item as sold")
                    return
                
                try:
                    sold_price_decimal = validate_price(sold_price)
                    item.sold_price = sold_price_decimal
                    item.sold_date = datetime.now()
                    item.sold_platform = sold_platform
                    
                    # Calculate consignment payout if applicable
                    if item.ownership_type == 'consignment':
                        payout = _calculate_consignment_payout(
                            sold_price_decimal,
                            sold_platform or 'Unknown',
                            item.split_percentage or 70
                        )
                        click.echo(f"💰 Consignment payout: ${payout:.2f}")
                    
                except ValueError as e:
                    click.echo(f"❌ Invalid sold price: {e}")
                    return
            
            elif old_status == 'sold' and status != 'sold':
                # Clear sale information when moving from sold
                item.sold_price = None
                item.sold_date = None
                item.sold_platform = None
            
            item.status = status
            session.commit()
            
            click.echo(f"✅ Updated {item.sku} status: {old_status} → {status}")
            
            if status == 'sold':
                click.echo(f"  • Sold for: ${item.sold_price:.2f}")
                if item.sold_platform:
                    click.echo(f"  • Platform: {item.sold_platform}")
    
    except Exception as e:
        click.echo(f"❌ Error updating status: {e}")


@click.command()
@with_database  
@click.argument('sku')
@click.argument('location_code')
def move(sku, location_code):
    """Move an item to a different location
    
    Usage:
      inv move NIK001 STORE-FLOOR-A1
    """
    
    try:
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku.ilike(f"%{sku.upper()}%")).first()
            
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found.")
                return
            
            location = get_location_by_code(location_code.upper())
            if not location:
                click.echo(f"❌ Location '{location_code}' not found.")
                return
            
            old_location = item.location.code if item.location else "No Location"
            item.location_id = location.id
            session.commit()
            
            click.echo(f"✅ Moved {item.sku}: {old_location} → {location.code}")
    
    except Exception as e:
        click.echo(f"❌ Error moving item: {e}")