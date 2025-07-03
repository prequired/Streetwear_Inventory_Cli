"""Search command implementation with pagination and variant grouping"""

import click
from typing import List, Dict, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from ..database.connection import get_db_session
from ..database.models import Item, Location
from ..utils.database_init import with_database


def group_by_sku(items: List[Item]) -> Dict[str, List[Item]]:
    """Group items by base SKU"""
    grouped = {}
    for item in items:
        base_sku = item.sku.split('-')[0]  # NIK001-2 → NIK001
        if base_sku not in grouped:
            grouped[base_sku] = []
        grouped[base_sku].append(item)
    return grouped


def get_variant_sizes(items: List[Item]) -> str:
    """Get comma-separated list of sizes for variants"""
    sizes = [item.size for item in items]
    return ", ".join(sorted(set(sizes)))


def get_price_range(items: List[Item]) -> str:
    """Get price range string for multiple items"""
    if not items:
        return "$0"
    
    prices = [item.current_price for item in items]
    min_price = min(prices)
    max_price = max(prices)
    
    if min_price == max_price:
        return f"${min_price:.2f}"
    else:
        return f"${min_price:.2f} - ${max_price:.2f}"


def display_search_results(results: List[Item], show_count_only: bool = False):
    """Display search results with pagination and variant grouping"""
    
    if show_count_only:
        click.echo(f"Total items: {len(results)}")
        return
    
    if not results:
        click.echo("No items found.")
        return
    
    # Group by SKU to show variants
    grouped_results = group_by_sku(results)
    
    page_size = 20
    total_groups = len(grouped_results)
    
    for page_start in range(0, total_groups, page_size):
        page_end = min(page_start + page_size, total_groups)
        page_groups = list(grouped_results.items())[page_start:page_end]
        
        # Display current page
        for sku, items in page_groups:
            if len(items) == 1:
                item = items[0]
                location_code = item.location.code if item.location else "No Location"
                click.echo(f"{sku} - {item.brand} {item.model} | Size {item.size} | ${item.current_price:.2f} | {location_code}")
            else:
                # Multiple variants
                first_item = items[0]
                variant_count = len(items)
                sizes = get_variant_sizes(items)
                price_range = get_price_range(items)
                click.echo(f"{sku} {variant_count} variants - {first_item.brand} {first_item.model} | Sizes: {sizes} | {price_range}")
        
        # Pagination prompt
        if page_end < total_groups:
            if not click.confirm(f"\nShowing {page_start + 1}-{page_end} of {total_groups}. Show next 20?"):
                break
        else:
            click.echo(f"\nShowing {page_start + 1}-{page_end} of {total_groups} (end)")


@click.command()
@with_database
@click.argument('query', required=False)
@click.option('--brand', help='Filter by brand')
@click.option('--model', help='Filter by model')
@click.option('--size', help='Filter by size')
@click.option('--color', help='Filter by color')
@click.option('--condition', help='Filter by condition (DS, VNDS, Used)')
@click.option('--location', help='Filter by location code')
@click.option('--available', is_flag=True, help='Show only available items')
@click.option('--sold', is_flag=True, help='Show only sold items')
@click.option('--held', is_flag=True, help='Show only held items')
@click.option('--consignment', is_flag=True, help='Show only consignment items')
@click.option('--owned', is_flag=True, help='Show only owned items')
@click.option('--min-price', type=float, help='Minimum price filter')
@click.option('--max-price', type=float, help='Maximum price filter')
@click.option('--count', is_flag=True, help='Show count only')
@click.option('--sku', help='Search by SKU')
@click.option('--detailed', is_flag=True, help='Show detailed information')
def search(query, brand, model, size, color, condition, location, available, sold, held, 
          consignment, owned, min_price, max_price, count, sku, detailed):
    """Search inventory items
    
    Usage:
      inv search                    # Show all items
      inv search "jordan"           # Search all fields for "jordan"
      inv search --brand=nike       # Filter by brand
      inv search --available        # Show only available items
      inv search --brand=nike --available --min-price=200
    """
    
    try:
        with get_db_session() as session:
            # Build query with joins
            query_obj = session.query(Item).options(
                joinedload(Item.location),
                joinedload(Item.consigner)
            )
            
            filters = []
            
            # Text search across multiple fields
            if query:
                search_term = f"%{query.lower()}%"
                text_filters = [
                    Item.brand.ilike(search_term),
                    Item.model.ilike(search_term),
                    Item.color.ilike(search_term),
                    Item.sku.ilike(search_term)
                ]
                filters.append(or_(*text_filters))
            
            # SKU search
            if sku:
                sku_search = f"%{sku.upper()}%"
                filters.append(Item.sku.ilike(sku_search))
            
            # Brand filter
            if brand:
                filters.append(Item.brand.ilike(f"%{brand}%"))
            
            # Model filter
            if model:
                filters.append(Item.model.ilike(f"%{model}%"))
            
            # Size filter
            if size:
                filters.append(Item.size == size)
            
            # Color filter
            if color:
                filters.append(Item.color.ilike(f"%{color}%"))
            
            # Condition filter
            if condition:
                filters.append(Item.condition == condition.upper())
            
            # Location filter
            if location:
                query_obj = query_obj.join(Location)
                filters.append(Location.code.ilike(f"%{location.upper()}%"))
            
            # Status filters
            if available:
                filters.append(Item.status == 'available')
            elif sold:
                filters.append(Item.status == 'sold')
            elif held:
                filters.append(Item.status == 'held')
            
            # Ownership filters
            if consignment:
                filters.append(Item.ownership_type == 'consignment')
            elif owned:
                filters.append(Item.ownership_type == 'owned')
            
            # Price filters
            if min_price is not None:
                filters.append(Item.current_price >= min_price)
            if max_price is not None:
                filters.append(Item.current_price <= max_price)
            
            # Apply all filters
            if filters:
                query_obj = query_obj.filter(and_(*filters))
            
            # Order by SKU
            query_obj = query_obj.order_by(Item.sku)
            
            # Execute query
            results = query_obj.all()
            
            # Display results
            if detailed and not count:
                display_detailed_results(results)
            else:
                display_search_results(results, show_count_only=count)
    
    except Exception as e:
        click.echo(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()


def display_detailed_results(results: List[Item]):
    """Display detailed search results"""
    if not results:
        click.echo("No items found.")
        return
    
    click.echo(f"Found {len(results)} item(s):")
    click.echo("=" * 80)
    
    for item in results:
        location_code = item.location.code if item.location else "No Location"
        consigner_name = item.consigner.name if item.consigner else "N/A"
        
        click.echo(f"SKU: {item.sku}")
        click.echo(f"Brand: {item.brand}")
        click.echo(f"Model: {item.model}")
        click.echo(f"Size: {item.size}")
        click.echo(f"Color: {item.color}")
        click.echo(f"Condition: {item.condition}")
        click.echo(f"Box Status: {item.box_status}")
        click.echo(f"Current Price: ${item.current_price:.2f}")
        click.echo(f"Purchase Price: ${item.purchase_price:.2f}")
        click.echo(f"Status: {item.status}")
        click.echo(f"Location: {location_code}")
        click.echo(f"Ownership: {item.ownership_type}")
        
        if item.ownership_type == 'consignment':
            click.echo(f"Consigner: {consigner_name}")
            click.echo(f"Split: {item.split_percentage}%")
        
        if item.notes:
            click.echo(f"Notes: {item.notes}")
        
        if item.sold_date:
            click.echo(f"Sold: ${item.sold_price:.2f} on {item.sold_date.strftime('%Y-%m-%d')}")
            click.echo(f"Platform: {item.sold_platform}")
        
        click.echo(f"Added: {item.date_added.strftime('%Y-%m-%d %H:%M')}")
        click.echo("-" * 80)


@click.command()
@with_database
@click.argument('sku')
@click.option('--edit', is_flag=True, help='Edit item details')
def show(sku, edit):
    """Show detailed information for a specific item
    
    Usage:
      inv show NIK001
      inv show NIK001 --edit
    """
    
    try:
        with get_db_session() as session:
            item = session.query(Item).options(
                joinedload(Item.location),
                joinedload(Item.consigner),
                joinedload(Item.photos)
            ).filter(Item.sku.ilike(f"%{sku.upper()}%")).first()
            
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found.")
                return
            
            # Display detailed info
            display_detailed_results([item])
            
            # Show photos if available
            if item.photos:
                click.echo("📸 Photos:")
                for photo in item.photos:
                    click.echo(f"  {photo.file_path} ({photo.photo_type})")
            else:
                click.echo("📸 No photos")
            
            # Edit mode
            if edit:
                click.echo("\n🖊️  Edit mode (press Enter to keep current value)")
                
                # Edit basic fields
                new_price = click.prompt(f"Current price [{item.current_price}]", 
                                       default=str(item.current_price))
                new_condition = click.prompt(f"Condition [{item.condition}]", 
                                           default=item.condition)
                new_notes = click.prompt(f"Notes [{item.notes or 'None'}]", 
                                       default=item.notes or "")
                
                # Update item
                try:
                    from ..utils.validation import validate_price, validate_condition
                    
                    if new_price != str(item.current_price):
                        item.current_price = validate_price(new_price)
                    
                    if new_condition != item.condition:
                        if validate_condition(new_condition):
                            item.condition = new_condition
                        else:
                            click.echo("❌ Invalid condition. Not updated.")
                    
                    if new_notes != (item.notes or ""):
                        item.notes = new_notes if new_notes else None
                    
                    session.commit()
                    click.echo("✅ Item updated successfully.")
                    
                except Exception as e:
                    click.echo(f"❌ Update failed: {e}")
                    session.rollback()
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")