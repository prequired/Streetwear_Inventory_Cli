"""Intake command implementation for consignment item processing"""

import click
from pathlib import Path

from ..database.connection import get_db_session
from ..database.models import Item
from ..utils.validation import (
    validate_brand_name, validate_model_name, validate_color_name,
    normalize_size, validate_size, validate_condition, validate_box_status,
    validate_price
)
from ..utils.sku import generate_sku
from ..utils.locations import get_location_by_code, show_location_picker, get_default_location
from ..utils.consignment import find_or_create_consigner, get_consigner_by_name, list_all_consigners
from ..utils.config import get_config
from ..utils.database_init import with_database


@click.command()
@with_database
@click.option('--consigner', required=True, help='Consigner name')
@click.option('--phone', help='Consigner phone number (required for new consigners)')
@click.option('--email', help='Consigner email address (optional)')
@click.option('--batch', default=1, type=int, help='Number of items to intake')
@click.option('--split', type=int, help='Override default split percentage (0-100)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive intake mode')
def intake(consigner, phone, email, batch, split, interactive):
    """Process consignment intake for one or more items
    
    Usage:
      inv intake --consigner="John Doe" --phone="555-1234"
      inv intake --batch=3 --consigner="Mike Chen" --phone="555-5678"
      inv intake --interactive
    
    Options:
      --consigner     Consigner name (required)
      --phone         Phone number (required for new consigners)
      --email         Email address (optional)
      --batch         Number of items to intake (default: 1)
      --split         Custom split percentage (default: use consigner's default)
      --interactive   Interactive mode with step-by-step guidance
    """
    
    try:
        if interactive:
            _interactive_intake()
            return
        
        # Find or create consigner
        click.echo(f"🤝 Processing intake for consigner: {consigner}")
        
        try:
            # Get default split from config if not specified
            config = get_config()
            config_default_split = config.get('defaults', {}).get('consignment_split', 70)
            
            consigner_obj = find_or_create_consigner(
                name=consigner,
                phone=phone,
                email=email,
                default_split=split or config_default_split
            )
            
            if consigner_obj.id:  # Existing consigner
                click.echo(f"   Found existing consigner: {consigner_obj.name} ({consigner_obj.phone})")
            else:  # New consigner (though this shouldn't happen with current logic)
                click.echo(f"   Created new consigner: {consigner_obj.name}")
            
        except ValueError as e:
            # Handle disambiguation or missing phone
            if "Multiple consigners found" in str(e):
                # Show options and let user choose
                matches = get_consigner_by_name(consigner)
                click.echo(f"❌ {e}")
                click.echo("Available consigners:")
                for i, match in enumerate(matches, 1):
                    click.echo(f"  {i}. {match.name} ({match.phone})")
                return
            else:
                click.echo(f"❌ {e}")
                return
        
        # Determine split percentage
        split_percentage = split or consigner_obj.default_split_percentage
        click.echo(f"   Split: {split_percentage}% to consigner, {100-split_percentage}% to store")
        
        # Process intake for each item in batch
        click.echo(f"\n📦 Processing {batch} item(s):")
        
        successful_intakes = []
        
        for i in range(batch):
            click.echo(f"\n--- Item {i+1} of {batch} ---")
            
            item_result = _process_single_item_intake(consigner_obj, split_percentage)
            if item_result:
                successful_intakes.append(item_result)
            else:
                if not click.confirm("Continue with next item?"):
                    break
        
        # Summary
        if successful_intakes:
            click.echo(f"\n✅ Successfully processed {len(successful_intakes)} item(s):")
            for sku, details in successful_intakes:
                click.echo(f"  • {sku}: {details}")
        else:
            click.echo("❌ No items were successfully processed.")
    
    except Exception as e:
        click.echo(f"❌ Intake error: {e}")
        import traceback
        traceback.print_exc()


def _process_single_item_intake(consigner, split_percentage):
    """Process intake for a single item"""
    try:
        # Get item details
        click.echo("Enter item details:")
        
        brand = click.prompt("Brand")
        model = click.prompt("Model")
        size = click.prompt("Size")
        color = click.prompt("Color/Colorway")
        condition = click.prompt("Condition", type=click.Choice(['DS', 'VNDS', 'Used']))
        current_price = click.prompt("Current asking price")
        box_status = click.prompt("Box status", type=click.Choice(['box', 'tag', 'both', 'neither']))
        notes = click.prompt("Notes (optional)", default="")
        
        # Validate inputs
        try:
            brand = validate_brand_name(brand)
            model = validate_model_name(model)
            color = validate_color_name(color)
            size = normalize_size(size)
            
            if not (validate_size(size, "shoe") or validate_size(size, "clothing")):
                click.echo(f"❌ Invalid size '{size}'. Must be a valid shoe or clothing size.")
                return None
            
            current_price_decimal = validate_price(current_price)
            
        except ValueError as e:
            click.echo(f"❌ Validation error: {e}")
            return None
        
        # Handle location
        location_obj = get_default_location()
        if not location_obj:
            location_obj = show_location_picker()
            if not location_obj:
                click.echo("❌ Location selection required.")
                return None
        
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
                purchase_price=0,  # Consignment items have no purchase cost
                location_id=location_obj.id,
                notes=notes if notes else None,
                status='available',
                ownership_type='consignment',
                consigner_id=consigner.id,
                split_percentage=split_percentage
            )
            
            session.add(item)
            session.commit()
            session.refresh(item)
            
            # Create photos directory
            config = get_config()
            photos_path = Path(config.get('photos', {}).get('storage_path', './photos'))
            item_photos_dir = photos_path / sku
            item_photos_dir.mkdir(parents=True, exist_ok=True)
            
            # Return success info
            details = f"{brand} {model}, Size {size}, ${current_price_decimal:.2f}"
            click.echo(f"✅ Added consignment item {sku}: {details}")
            
            return (sku, details)
    
    except Exception as e:
        click.echo(f"❌ Error processing item: {e}")
        return None


def _interactive_intake():
    """Interactive intake mode with guided workflow"""
    click.echo("🤝 Interactive Consignment Intake")
    click.echo("=" * 40)
    
    # Step 1: Consigner information
    click.echo("\n1. Consigner Information")
    
    # Check if we want to use existing consigner
    if click.confirm("Use existing consigner?"):
        consigners = list_all_consigners()
        if not consigners:
            click.echo("No existing consigners found.")
            use_existing = False
        else:
            click.echo("Available consigners:")
            for i, consigner in enumerate(consigners, 1):
                click.echo(f"  {i}. {consigner['name']} ({consigner['phone']})")
            
            try:
                choice = click.prompt("Select consigner number", type=int)
                if 1 <= choice <= len(consigners):
                    selected = consigners[choice - 1]
                    consigner_name = selected['name']
                    consigner_phone = selected['phone']
                    consigner_email = selected['email']
                    use_existing = True
                else:
                    click.echo("Invalid selection.")
                    use_existing = False
            except:
                use_existing = False
    else:
        use_existing = False
    
    if not use_existing:
        # New consigner
        consigner_name = click.prompt("Consigner name")
        consigner_phone = click.prompt("Phone number")
        consigner_email = click.prompt("Email (optional)", default="")
        consigner_email = consigner_email if consigner_email else None
    
    # Step 2: Split percentage
    click.echo("\n2. Consignment Terms")
    config = get_config()
    config_default_split = config.get('defaults', {}).get('consignment_split', 70)
    default_split = click.prompt("Split percentage for consigner", type=int, default=config_default_split)
    
    # Step 3: Batch size
    click.echo("\n3. Intake Details")
    batch_size = click.prompt("Number of items to intake", type=int, default=1)
    
    # Execute the intake
    ctx = click.get_current_context()
    ctx.invoke(intake, 
               consigner=consigner_name,
               phone=consigner_phone, 
               email=consigner_email,
               batch=batch_size,
               split=default_split,
               interactive=False)


@click.command(name='list-consigners')
@with_database
@click.option('--stats', is_flag=True, help='Include statistics for each consigner')
@click.option('--search', help='Search consigners by name, phone, or email')
def list_consigners(stats, search):
    """List all consigners
    
    Usage:
      inv list-consigners
      inv list-consigners --stats
      inv list-consigners --search="john"
    """
    
    try:
        if search:
            from ..utils.consignment import search_consigners
            consigners = search_consigners(search)
            
            if not consigners:
                click.echo(f"No consigners found matching '{search}'")
                return
            
            click.echo(f"🔍 Found {len(consigners)} consigner(s) matching '{search}':")
        else:
            consigners_data = list_all_consigners(include_stats=stats)
            click.echo(f"👥 All Consigners ({len(consigners_data)}):")
            
            if not consigners_data:
                click.echo("No consigners found.")
                return
        
        if search:
            # Simple list for search results
            for consigner in consigners:
                click.echo(f"  • {consigner.name} ({consigner.phone})")
                if consigner.email:
                    click.echo(f"    Email: {consigner.email}")
        else:
            # Full list with optional stats
            click.echo("-" * 60)
            
            for consigner_data in consigners_data:
                click.echo(f"Name: {consigner_data['name']}")
                click.echo(f"Phone: {consigner_data['phone']}")
                if consigner_data['email']:
                    click.echo(f"Email: {consigner_data['email']}")
                click.echo(f"Default Split: {consigner_data['default_split']}%")
                click.echo(f"Member Since: {consigner_data['created_date'].strftime('%Y-%m-%d')}")
                
                if stats and 'stats' in consigner_data:
                    s = consigner_data['stats']
                    click.echo(f"Items: {s['total_items']} total, {s['available_items']} available, {s['sold_items']} sold")
                    click.echo(f"Value: ${s['total_current_value']:.2f} current, ${s['total_sold_value']:.2f} sold")
                    click.echo(f"Payouts: ${s['total_payouts']:.2f}")
                
                click.echo("-" * 60)
    
    except Exception as e:
        click.echo(f"❌ Error listing consigners: {e}")


@click.command(name='consigner-report')
@with_database
@click.argument('consigner_name')
@click.option('--phone', help='Phone number for disambiguation')
def consigner_report(consigner_name, phone):
    """Generate detailed report for a consigner
    
    Usage:
      inv consigner-report "John Doe"
      inv consigner-report "John" --phone="555-1234"
    """
    
    try:
        from ..utils.consignment import generate_consigner_report
        
        # Find consigner
        if phone:
            from ..utils.consignment import get_consigner_by_phone
            consigner = get_consigner_by_phone(phone)
        else:
            matches = get_consigner_by_name(consigner_name)
            if len(matches) == 0:
                click.echo(f"❌ No consigner found with name '{consigner_name}'")
                return
            elif len(matches) > 1:
                click.echo(f"❌ Multiple consigners found with name '{consigner_name}'. Please provide phone number.")
                for match in matches:
                    click.echo(f"  • {match.name} ({match.phone})")
                return
            else:
                consigner = matches[0]
        
        if not consigner:
            click.echo(f"❌ Consigner not found")
            return
        
        # Generate report
        report = generate_consigner_report(consigner.id)
        
        # Display report
        click.echo(f"📊 Consigner Report: {consigner.name}")
        click.echo("=" * 50)
        click.echo(f"Phone: {consigner.phone}")
        if consigner.email:
            click.echo(f"Email: {consigner.email}")
        click.echo(f"Default Split: {consigner.default_split_percentage}%")
        click.echo(f"Member Since: {consigner.created_date.strftime('%Y-%m-%d')}")
        
        # Statistics
        stats = report['stats']
        click.echo("\n📈 Statistics:")
        click.echo(f"  Total Items: {stats['total_items']}")
        click.echo(f"  Available: {stats['available_items']}")
        click.echo(f"  Sold: {stats['sold_items']}")
        click.echo(f"  Held: {stats['held_items']}")
        click.echo(f"  Current Value: ${stats['total_current_value']:.2f}")
        click.echo(f"  Total Sales: ${stats['total_sold_value']:.2f}")
        click.echo(f"  Total Payouts: ${stats['total_payouts']:.2f}")
        
        # Recent activity
        if report['recent_activity']:
            click.echo("\n🕒 Recent Activity:")
            for item in report['recent_activity']:
                status_emoji = {"available": "✅", "sold": "💰", "held": "⏸️"}.get(item.status, "❓")
                click.echo(f"  {status_emoji} {item.sku}: {item.brand} {item.model} - ${item.current_price:.2f}")
    
    except Exception as e:
        click.echo(f"❌ Error generating report: {e}")