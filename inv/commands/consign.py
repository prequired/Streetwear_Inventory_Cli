"""Consignment management command implementation"""

import click
from decimal import Decimal
from typing import List

from ..database.connection import get_db_session
from ..database.models import Item, Consigner
from ..utils.consignment import (
    get_consigner_by_name, get_consigner_by_phone, calculate_pending_payouts,
    get_consigner_items, calculate_consigner_stats
)
from ..utils.pricing import calculate_consignment_payout
from ..utils.validation import validate_price
from ..utils.database_init import with_database


@click.command()
@with_database
@click.argument('consigner_name')
@click.option('--phone', help='Phone number for disambiguation')
@click.option('--mark-paid', is_flag=True, help='Mark payouts as paid (for record keeping)')
@click.option('--show-items', is_flag=True, help='Show individual items in payout calculation')
def consign(consigner_name, phone, mark_paid, show_items):
    """Calculate and process consignment payouts
    
    Usage:
      inv consign "John Doe"
      inv consign "John" --phone="555-1234"
      inv consign "Mike Chen" --show-items
      inv consign "Sarah Jones" --mark-paid
    
    Options:
      --phone       Phone number for disambiguation
      --mark-paid   Mark payouts as paid (future feature)
      --show-items  Show detailed breakdown of individual items
    """
    
    try:
        # Find consigner
        if phone:
            consigner = get_consigner_by_phone(phone)
            if not consigner:
                click.echo(f"❌ No consigner found with phone '{phone}'")
                return
        else:
            matches = get_consigner_by_name(consigner_name)
            if len(matches) == 0:
                click.echo(f"❌ No consigner found with name '{consigner_name}'")
                return
            elif len(matches) > 1:
                click.echo(f"❌ Multiple consigners found with name '{consigner_name}'. Please provide phone number:")
                for match in matches:
                    click.echo(f"  • {match.name} ({match.phone})")
                return
            else:
                consigner = matches[0]
        
        click.echo(f"💰 Consignment Payout Report: {consigner.name}")
        click.echo("=" * 60)
        click.echo(f"Phone: {consigner.phone}")
        if consigner.email:
            click.echo(f"Email: {consigner.email}")
        click.echo(f"Default Split: {consigner.default_split_percentage}%")
        
        # Get sold items requiring payout
        sold_items = get_consigner_items(consigner.id, status='sold')
        
        if not sold_items:
            click.echo("\n📭 No sold items found for this consigner.")
            return
        
        # Calculate payouts
        total_payout = Decimal('0')
        total_sales = Decimal('0')
        platform_fees = Decimal('0')
        
        click.echo(f"\n📊 Sold Items ({len(sold_items)}):")
        click.echo("-" * 60)
        
        payout_items = []
        
        for item in sold_items:
            if not item.sold_price:
                continue
                
            # Calculate payout for this item
            platform_fee = Decimal('10')  # Default platform fee
            split_percentage = item.split_percentage or consigner.default_split_percentage
            
            payout = calculate_consignment_payout(
                item.sold_price, platform_fee, split_percentage
            )
            
            total_sales += item.sold_price
            total_payout += payout
            platform_fees += platform_fee
            
            payout_items.append({
                'item': item,
                'payout': payout,
                'platform_fee': platform_fee,
                'split_percentage': split_percentage
            })
            
            if show_items:
                click.echo(f"• {item.sku}: {item.brand} {item.model}")
                click.echo(f"  Size: {item.size} | Condition: {item.condition}")
                click.echo(f"  Sold Price: ${item.sold_price:.2f}")
                click.echo(f"  Platform Fee: ${platform_fee:.2f}")
                click.echo(f"  Split: {split_percentage}% to consigner")
                click.echo(f"  Payout: ${payout:.2f}")
                if item.sold_date:
                    click.echo(f"  Sold Date: {item.sold_date.strftime('%Y-%m-%d')}")
                click.echo()
        
        # Summary
        click.echo("\n💵 Payout Summary:")
        click.echo("-" * 30)
        click.echo(f"Total Sales Value:    ${total_sales:.2f}")
        click.echo(f"Platform Fees:        ${platform_fees:.2f}")
        click.echo(f"Store Revenue:        ${total_sales - total_payout - platform_fees:.2f}")
        click.echo(f"Consigner Payout:     ${total_payout:.2f}")
        
        # Show current statistics
        stats = calculate_consigner_stats(consigner.id)
        
        click.echo(f"\n📈 Consigner Statistics:")
        click.echo("-" * 30)
        click.echo(f"Total Items:          {stats['total_items']}")
        click.echo(f"Available Items:      {stats['available_items']}")
        click.echo(f"Sold Items:           {stats['sold_items']}")
        click.echo(f"Held Items:           {stats['held_items']}")
        click.echo(f"Current Inventory:    ${stats['total_current_value']:.2f}")
        click.echo(f"Lifetime Sales:       ${stats['total_sold_value']:.2f}")
        click.echo(f"Lifetime Payouts:     ${stats['total_payouts']:.2f}")
        
        if mark_paid:
            click.echo(f"\n⚠️  --mark-paid functionality not yet implemented")
            click.echo("This feature will track payout history in future versions.")
    
    except Exception as e:
        click.echo(f"❌ Error processing consignment: {e}")
        import traceback
        traceback.print_exc()


@click.command(name='consign-sold')
@with_database
@click.argument('sku')
@click.argument('sold_price', type=float)
@click.option('--buyer', help='Buyer information (optional)')
@click.option('--platform', default='store', type=click.Choice(['store', 'ebay', 'goat', 'stockx', 'grailed', 'depop']), help='Sales platform')
@click.option('--platform-fee', type=float, help='Platform fee amount (overrides default)')
def consign_sold(sku, sold_price, buyer, platform, platform_fee):
    """Mark a consignment item as sold and calculate payout
    
    Usage:
      inv consign-sold NIK001 250.00
      inv consign-sold SUP005 120.00 --platform=ebay --platform-fee=15.50
      inv consign-sold ADI003 180.00 --buyer="John Smith"
    
    Options:
      --buyer         Buyer information (optional)
      --platform      Sales platform (default: store)
      --platform-fee  Platform fee amount (overrides default)
    """
    
    try:
        sold_price_decimal = validate_price(str(sold_price))
        
        with get_db_session() as session:
            # Find the item
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
            
            if item.ownership_type != 'consignment':
                click.echo(f"❌ Item {sku} is not a consignment item")
                return
            
            if item.status == 'sold':
                click.echo(f"❌ Item {sku} is already marked as sold")
                return
            
            # Calculate platform fee
            if platform_fee:
                fee = Decimal(str(platform_fee))
            else:
                # Default platform fees
                default_fees = {
                    'store': Decimal('0'),
                    'ebay': sold_price_decimal * Decimal('0.125'),  # ~12.5%
                    'goat': sold_price_decimal * Decimal('0.095'),   # ~9.5%
                    'stockx': sold_price_decimal * Decimal('0.095'), # ~9.5%
                    'grailed': sold_price_decimal * Decimal('0.06'), # 6%
                    'depop': sold_price_decimal * Decimal('0.10')    # 10%
                }
                fee = default_fees.get(platform, Decimal('10'))
            
            # Calculate consigner payout
            split_percentage = item.split_percentage or 70
            payout = calculate_consignment_payout(sold_price_decimal, fee, split_percentage)
            
            # Update item status
            from datetime import datetime
            item.status = 'sold'
            item.sold_price = sold_price_decimal
            item.sold_date = datetime.now()
            
            # Store platform and buyer info in notes if provided
            sale_notes = []
            if platform != 'store':
                sale_notes.append(f"Platform: {platform}")
            if buyer:
                sale_notes.append(f"Buyer: {buyer}")
            if fee > 0:
                sale_notes.append(f"Platform fee: ${fee:.2f}")
            
            if sale_notes:
                existing_notes = item.notes or ""
                sale_info = " | ".join(sale_notes)
                item.notes = f"{existing_notes} | {sale_info}".strip(" | ")
            
            session.commit()
            session.refresh(item)
            
            # Display results
            click.echo(f"✅ Marked {sku} as SOLD")
            click.echo(f"   Item: {item.brand} {item.model} (Size {item.size})")
            click.echo(f"   Sold Price: ${sold_price_decimal:.2f}")
            click.echo(f"   Platform: {platform}")
            if fee > 0:
                click.echo(f"   Platform Fee: ${fee:.2f}")
            click.echo(f"   Consigner Split: {split_percentage}%")
            click.echo(f"   Consigner Payout: ${payout:.2f}")
            click.echo(f"   Store Revenue: ${sold_price_decimal - payout - fee:.2f}")
            
            # Show consigner info
            if item.consigner:
                click.echo(f"\n👤 Consigner: {item.consigner.name} ({item.consigner.phone})")
    
    except ValueError as e:
        click.echo(f"❌ Invalid price: {e}")
    except Exception as e:
        click.echo(f"❌ Error marking item as sold: {e}")


@click.command(name='payout-summary')
@with_database
@click.option('--pending-only', is_flag=True, help='Show only pending payouts')
@click.option('--consigner', help='Filter by specific consigner name')
@click.option('--min-amount', type=float, help='Minimum payout amount to show')
def payout_summary(pending_only, consigner, min_amount):
    """Generate summary of all consignment payouts
    
    Usage:
      inv payout-summary
      inv payout-summary --pending-only
      inv payout-summary --consigner="John Doe"
      inv payout-summary --min-amount=50.00
    """
    
    try:
        payouts = calculate_pending_payouts()
        
        if not payouts:
            click.echo("📭 No consignment payouts found.")
            return
        
        # Filter results
        if consigner:
            payouts = [p for p in payouts if consigner.lower() in p['consigner'].name.lower()]
        
        if min_amount:
            min_decimal = Decimal(str(min_amount))
            payouts = [p for p in payouts if p['total_payout'] >= min_decimal]
        
        if not payouts:
            click.echo("📭 No payouts match the specified criteria.")
            return
        
        # Sort by payout amount (descending)
        payouts.sort(key=lambda x: x['total_payout'], reverse=True)
        
        click.echo(f"💰 Consignment Payout Summary ({len(payouts)} consigners)")
        click.echo("=" * 70)
        
        total_owed = Decimal('0')
        total_items = 0
        
        for payout_data in payouts:
            consigner = payout_data['consigner']
            items = payout_data['items']
            total_payout = payout_data['total_payout']
            
            total_owed += total_payout
            total_items += len(items)
            
            click.echo(f"\n👤 {consigner.name} ({consigner.phone})")
            click.echo(f"   Items Sold: {len(items)}")
            click.echo(f"   Total Payout: ${total_payout:.2f}")
            
            if consigner.email:
                click.echo(f"   Email: {consigner.email}")
        
        click.echo("\n" + "=" * 70)
        click.echo(f"📊 TOTALS:")
        click.echo(f"   Consigners: {len(payouts)}")
        click.echo(f"   Items: {total_items}")
        click.echo(f"   Total Owed: ${total_owed:.2f}")
    
    except Exception as e:
        click.echo(f"❌ Error generating payout summary: {e}")


@click.command(name='hold-item')
@with_database
@click.argument('sku')
@click.option('--reason', help='Reason for holding (optional)')
@click.option('--release', is_flag=True, help='Release item from hold')
def hold_item(sku, reason, release):
    """Place consignment item on hold or release from hold
    
    Usage:
      inv hold-item NIK001 --reason="Needs cleaning"
      inv hold-item SUP005 --reason="Damage assessment"
      inv hold-item ADI003 --release
    """
    
    try:
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
            
            if item.ownership_type != 'consignment':
                click.echo(f"❌ Item {sku} is not a consignment item")
                return
            
            if release:
                if item.status != 'held':
                    click.echo(f"❌ Item {sku} is not currently on hold")
                    return
                
                item.status = 'available'
                # Remove hold reason from notes if it exists
                if item.notes and reason:
                    item.notes = item.notes.replace(f"HOLD: {reason}", "").strip(" | ")
                
                session.commit()
                click.echo(f"✅ Released {sku} from hold")
                click.echo(f"   Status: {item.status}")
            else:
                if item.status == 'sold':
                    click.echo(f"❌ Cannot hold sold item {sku}")
                    return
                
                item.status = 'held'
                if reason:
                    existing_notes = item.notes or ""
                    hold_note = f"HOLD: {reason}"
                    item.notes = f"{existing_notes} | {hold_note}".strip(" | ")
                
                session.commit()
                click.echo(f"⏸️  Placed {sku} on hold")
                click.echo(f"   Status: {item.status}")
                if reason:
                    click.echo(f"   Reason: {reason}")
                
                # Show consigner info
                if item.consigner:
                    click.echo(f"   Consigner: {item.consigner.name}")
    
    except Exception as e:
        click.echo(f"❌ Error updating item hold status: {e}")