"""Add command implementation for adding new inventory items"""

import click
import os
from pathlib import Path
from decimal import Decimal

from ..database.connection import get_db_session
from ..database.models import Item
from ..utils.validation import (
    validate_brand_name, validate_model_name, validate_color_name,
    normalize_size, validate_size, validate_condition, validate_box_status,
    validate_price, get_validation_errors
)
from ..utils.sku import generate_sku
from ..utils.locations import get_location_by_code, show_location_picker, get_default_location
from ..utils.config import get_config
from ..utils.database_init import with_database


@click.command()
@with_database
@click.argument('brand')
@click.argument('model')
@click.argument('size')
@click.argument('color')
@click.argument('condition')
@click.argument('current_price')
@click.argument('purchase_price')
@click.argument('box_status')
@click.argument('location', required=False)
@click.option('--notes', '-n', help='Additional notes about the item')
@click.option('--consignment', is_flag=True, help='Mark as consignment item')
def add(brand, model, size, color, condition, current_price, purchase_price, box_status, location, notes, consignment):
    """Add a new item to inventory
    
    Usage:
      inv add nike "air jordan 1" 10 chicago DS 250 200 box
      inv add nike "air jordan 1" 10 chicago DS 250 200 box store-floor-A1
    
    Arguments:
      BRAND           Brand name (e.g. nike, adidas, supreme)
      MODEL           Model name (use quotes for spaces)
      SIZE            Size (e.g. 10, 10.5, M, L)
      COLOR           Color/colorway
      CONDITION       Condition: DS, VNDS, or Used
      CURRENT_PRICE   Current selling price
      PURCHASE_PRICE  Purchase/cost price
      BOX_STATUS      Box status: box, tag, both, or neither
      LOCATION        Location code (optional, will prompt if not provided)
    """
    
    try:
        # Validate all input parameters except size (we'll do size separately)
        item_data = {
            'brand': brand,
            'model': model,
            'color': color,
            'condition': condition,
            'current_price': current_price,
            'purchase_price': purchase_price,
            'box_status': box_status
        }
        
        # Get validation errors (excluding size)
        try:
            validate_brand_name(brand)
            validate_model_name(model)
            validate_color_name(color)
            validate_price(current_price)
            validate_price(purchase_price)
        except ValueError as e:
            click.echo(f"❌ {e}")
            return
        
        # Validate and normalize inputs
        brand = validate_brand_name(brand)
        model = validate_model_name(model)
        color = validate_color_name(color)
        size = normalize_size(size)
        
        # Validate size for appropriate category (try both shoe and clothing)
        if not (validate_size(size, "shoe") or validate_size(size, "clothing")):
            click.echo(f"❌ Invalid size '{size}'. Must be a valid shoe or clothing size.")
            return
        
        # Validate condition
        if not validate_condition(condition):
            click.echo(f"❌ Invalid condition '{condition}'. Must be: DS, VNDS, Used")
            return
        
        # Validate box status
        if not validate_box_status(box_status):
            click.echo(f"❌ Invalid box status '{box_status}'. Must be: box, tag, both, neither")
            return
        
        # Validate prices
        try:
            current_price_decimal = validate_price(current_price)
            purchase_price_decimal = validate_price(purchase_price)
        except ValueError as e:
            click.echo(f"❌ {e}")
            return
        
        # Handle location
        location_obj = None
        if location:
            # Location provided, validate it exists
            location_obj = get_location_by_code(location)
            if not location_obj:
                click.echo(f"❌ Location '{location}' not found.")
                return
        else:
            # No location provided, try default first
            location_obj = get_default_location()
            
            if not location_obj:
                # Show location picker
                location_obj = show_location_picker()
                if not location_obj:
                    click.echo("❌ Location selection required to add item.")
                    return
        
        # Generate SKU
        sku = generate_sku(brand)
        
        # Create item record
        with get_db_session() as session:
            item = Item(
                sku=sku,
                variant_id=1,
                brand=brand,
                model=model,
                size=size,
                color=color,
                condition=condition,
                box_status=box_status,
                current_price=current_price_decimal,
                purchase_price=purchase_price_decimal,
                location_id=location_obj.id,
                notes=notes,
                status='available',
                ownership_type='consignment' if consignment else 'owned'
            )
            
            session.add(item)
            session.commit()
            session.refresh(item)
            
            # Create photos directory
            config = get_config()
            photos_path = Path(config.get('photos', {}).get('storage_path', './photos'))
            item_photos_dir = photos_path / sku
            item_photos_dir.mkdir(parents=True, exist_ok=True)
            
            # Display success message
            click.echo(f"✅ Added item {sku}")
            click.echo(f"Brand: {brand}")
            click.echo(f"Model: {model}")
            click.echo(f"Size: {size}")
            click.echo(f"Color: {color}")
            click.echo(f"Condition: {condition}")
            click.echo(f"Price: ${current_price_decimal:.2f}")
            click.echo(f"Location: {location_obj.code}")
            
            if notes:
                click.echo(f"Notes: {notes}")
            
            if consignment:
                click.echo("Type: Consignment")
            
            click.echo(f"Photos directory: {item_photos_dir}")
    
    except Exception as e:
        click.echo(f"❌ Error adding item: {e}")
        import traceback
        traceback.print_exc()


@click.command()
@with_database
@click.argument('sku')
@click.option('--interactive', '-i', is_flag=True, help='Interactive variant creation')
def add_variant(sku, interactive):
    """Add a variant of an existing item (different size)
    
    Usage:
      inv add-variant NIK001
      inv add-variant NIK001 --interactive
    """
    
    try:
        # Find the base item
        with get_db_session() as session:
            base_item = session.query(Item).filter(Item.sku == sku).first()
            
            if not base_item:
                click.echo(f"❌ Item with SKU '{sku}' not found.")
                return
            
            click.echo(f"Adding variant for: {base_item.brand} {base_item.model}")
            
            if interactive:
                # Interactive mode - prompt for all fields
                size = click.prompt("Size")
                color = click.prompt("Color", default=base_item.color)
                condition = click.prompt("Condition", default=base_item.condition)
                current_price = click.prompt("Current price", default=str(base_item.current_price))
                purchase_price = click.prompt("Purchase price", default=str(base_item.purchase_price))
                box_status = click.prompt("Box status", default=base_item.box_status)
                notes = click.prompt("Notes (optional)", default="")
            else:
                # Quick mode - copy most fields, only ask for size
                size = click.prompt("Size for variant")
                color = base_item.color
                condition = base_item.condition
                current_price = str(base_item.current_price)
                purchase_price = str(base_item.purchase_price)
                box_status = base_item.box_status
                notes = ""
            
            # Validate inputs
            size = normalize_size(size)
            if not validate_size(size):
                click.echo(f"❌ Invalid size '{size}'")
                return
            
            # Generate variant SKU
            from ..utils.sku import get_next_variant_id
            base_sku = sku.split('-')[0]  # Remove variant suffix if present
            variant_id = get_next_variant_id(base_sku)
            variant_sku = f"{base_sku}-{variant_id}" if variant_id > 1 else base_sku
            
            # Validate prices
            try:
                current_price_decimal = validate_price(current_price)
                purchase_price_decimal = validate_price(purchase_price)
            except ValueError as e:
                click.echo(f"❌ {e}")
                return
            
            # Create variant
            variant_item = Item(
                sku=variant_sku,
                variant_id=variant_id,
                brand=base_item.brand,
                model=base_item.model,
                size=size,
                color=color,
                condition=condition,
                box_status=box_status,
                current_price=current_price_decimal,
                purchase_price=purchase_price_decimal,
                location_id=base_item.location_id,
                notes=notes,
                status='available',
                ownership_type=base_item.ownership_type,
                consigner_id=base_item.consigner_id,
                split_percentage=base_item.split_percentage
            )
            
            session.add(variant_item)
            session.commit()
            session.refresh(variant_item)
            
            # Create photos directory for variant
            config = get_config()
            photos_path = Path(config.get('photos', {}).get('storage_path', './photos'))
            variant_photos_dir = photos_path / variant_sku
            variant_photos_dir.mkdir(parents=True, exist_ok=True)
            
            click.echo(f"✅ Added variant {variant_sku}")
            click.echo(f"Size: {size}")
            click.echo(f"Price: ${current_price_decimal:.2f}")
            
    except Exception as e:
        click.echo(f"❌ Error adding variant: {e}")