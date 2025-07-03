"""Data export commands for inventory management"""

import click
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from ..database.connection import get_db_session
from ..database.models import Item, Location, Consigner
from ..utils.consignment import calculate_consigner_stats
from ..utils.photos import PhotoManager
from ..utils.database_init import with_database

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@click.command()
@with_database
@click.argument('format_type', type=click.Choice(['csv', 'json', 'excel']))
@click.option('--output', '-o', help='Output file path (auto-generated if not provided)')
@click.option('--filter-brand', help='Filter by brand')
@click.option('--filter-status', help='Filter by status')
@click.option('--filter-condition', help='Filter by condition')
@click.option('--filter-location', help='Filter by location code')
@click.option('--ownership-type', type=click.Choice(['owned', 'consignment']), help='Filter by ownership type')
@click.option('--include-photos', is_flag=True, help='Include photo information')
@click.option('--include-consigner', is_flag=True, help='Include consigner details')
@click.option('--date-from', help='Include items added after this date (YYYY-MM-DD)')
@click.option('--date-to', help='Include items added before this date (YYYY-MM-DD)')
def export_inventory(format_type, output, filter_brand, filter_status, filter_condition, 
                    filter_location, ownership_type, include_photos, include_consigner,
                    date_from, date_to):
    """Export inventory data to various formats
    
    Usage:
      inv export-inventory csv
      inv export-inventory json --output=backup.json
      inv export-inventory excel --filter-brand=nike --include-photos
      inv export-inventory csv --filter-status=available --ownership-type=consignment
      inv export-inventory json --date-from=2024-01-01 --date-to=2024-12-31
    
    Supported formats:
      csv   - Comma-separated values
      json  - JavaScript Object Notation  
      excel - Excel spreadsheet (requires pandas)
    """
    
    try:
        # Check Excel dependencies
        if format_type == 'excel' and not PANDAS_AVAILABLE:
            click.echo("❌ Excel export requires pandas. Install with: pip install pandas openpyxl")
            return
        
        # Generate output filename if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filters = []
            if filter_brand:
                filters.append(f"brand_{filter_brand}")
            if filter_status:
                filters.append(f"status_{filter_status}")
            if ownership_type:
                filters.append(f"type_{ownership_type}")
            
            filter_str = "_".join(filters)
            filter_str = f"_{filter_str}" if filter_str else ""
            
            output = f"inventory_export{filter_str}_{timestamp}.{format_type}"
        
        output_path = Path(output)
        
        # Prepare photo manager if needed
        photo_manager = PhotoManager() if include_photos else None
        
        # Query database with filters
        with get_db_session() as session:
            from sqlalchemy.orm import joinedload
            
            query = session.query(Item).options(
                joinedload(Item.location),
                joinedload(Item.consigner)
            )
            
            # Apply filters
            if filter_brand:
                query = query.filter(Item.brand.ilike(f'%{filter_brand}%'))
            if filter_status:
                query = query.filter(Item.status == filter_status)
            if filter_condition:
                query = query.filter(Item.condition == filter_condition)
            if filter_location:
                query = query.join(Location).filter(Location.code == filter_location.upper())
            if ownership_type:
                query = query.filter(Item.ownership_type == ownership_type)
            
            # Date filters
            if date_from:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Item.date_added >= from_date)
            if date_to:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Item.date_added <= to_date)
            
            items = query.all()
            
            # Convert items to export format within session
            export_data = []
            for item in items:
                item_data = _item_to_export_dict(
                    item, 
                    include_photos=include_photos,
                    include_consigner=include_consigner,
                    photo_manager=photo_manager
                )
                export_data.append(item_data)
        
        if not export_data:
            click.echo("📭 No items found matching the specified criteria")
            return
        
        # Export based on format
        if format_type == 'csv':
            _export_csv(export_data, output_path)
        elif format_type == 'json':
            _export_json(export_data, output_path)
        elif format_type == 'excel':
            _export_excel(export_data, output_path)
        
        click.echo(f"✅ Exported {len(export_data)} items to {output_path}")
        click.echo(f"   Format: {format_type.upper()}")
        click.echo(f"   File size: {output_path.stat().st_size:,} bytes")
        
        # Show applied filters
        filters_applied = []
        if filter_brand:
            filters_applied.append(f"brand={filter_brand}")
        if filter_status:
            filters_applied.append(f"status={filter_status}")
        if filter_condition:
            filters_applied.append(f"condition={filter_condition}")
        if filter_location:
            filters_applied.append(f"location={filter_location}")
        if ownership_type:
            filters_applied.append(f"ownership={ownership_type}")
        if date_from:
            filters_applied.append(f"from={date_from}")
        if date_to:
            filters_applied.append(f"to={date_to}")
        
        if filters_applied:
            click.echo(f"   Filters: {', '.join(filters_applied)}")
    
    except ValueError as e:
        click.echo(f"❌ Invalid date format: {e}")
        click.echo("   Use YYYY-MM-DD format for dates")
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")


@click.command(name='export-consigners')
@with_database
@click.argument('format_type', type=click.Choice(['csv', 'json', 'excel']))
@click.option('--output', '-o', help='Output file path')
@click.option('--include-stats', is_flag=True, help='Include detailed statistics')
@click.option('--include-items', is_flag=True, help='Include items for each consigner')
def export_consigners(format_type, output, include_stats, include_items):
    """Export consigner data
    
    Usage:
      inv export-consigners csv
      inv export-consigners json --include-stats --include-items
      inv export-consigners excel --output=consigners.xlsx
    """
    
    try:
        if format_type == 'excel' and not PANDAS_AVAILABLE:
            click.echo("❌ Excel export requires pandas. Install with: pip install pandas openpyxl")
            return
        
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"consigners_export_{timestamp}.{format_type}"
        
        output_path = Path(output)
        
        with get_db_session() as session:
            consigners = session.query(Consigner).all()
        
        if not consigners:
            click.echo("📭 No consigners found")
            return
        
        export_data = []
        for consigner in consigners:
            consigner_data = {
                'id': consigner.id,
                'name': consigner.name,
                'phone': consigner.phone,
                'email': consigner.email,
                'default_split_percentage': consigner.default_split_percentage,
                'created_date': consigner.created_date.isoformat() if consigner.created_date else None
            }
            
            if include_stats:
                stats = calculate_consigner_stats(consigner.id)
                consigner_data.update({
                    'total_items': stats['total_items'],
                    'available_items': stats['available_items'],
                    'sold_items': stats['sold_items'],
                    'held_items': stats['held_items'],
                    'total_current_value': float(stats['total_current_value']),
                    'total_sold_value': float(stats['total_sold_value']),
                    'total_payouts': float(stats['total_payouts'])
                })
            
            if include_items:
                with get_db_session() as session:
                    items = session.query(Item).filter(Item.consigner_id == consigner.id).all()
                    consigner_data['items'] = [
                        {
                            'sku': item.sku,
                            'brand': item.brand,
                            'model': item.model,
                            'size': item.size,
                            'condition': item.condition,
                            'current_price': float(item.current_price),
                            'status': item.status,
                            'date_added': item.date_added.isoformat() if item.date_added else None
                        }
                        for item in items
                    ]
            
            export_data.append(consigner_data)
        
        # Export
        if format_type == 'csv':
            _export_csv(export_data, output_path)
        elif format_type == 'json':
            _export_json(export_data, output_path)
        elif format_type == 'excel':
            _export_excel(export_data, output_path)
        
        click.echo(f"✅ Exported {len(consigners)} consigners to {output_path}")
    
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")


@click.command(name='export-locations')
@with_database
@click.argument('format_type', type=click.Choice(['csv', 'json', 'excel']))
@click.option('--output', '-o', help='Output file path')
@click.option('--include-items', is_flag=True, help='Include item counts')
def export_locations(format_type, output, include_items):
    """Export location data
    
    Usage:
      inv export-locations csv
      inv export-locations json --include-items
      inv export-locations excel --output=locations.xlsx
    """
    
    try:
        if format_type == 'excel' and not PANDAS_AVAILABLE:
            click.echo("❌ Excel export requires pandas. Install with: pip install pandas openpyxl")
            return
        
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"locations_export_{timestamp}.{format_type}"
        
        output_path = Path(output)
        
        with get_db_session() as session:
            locations = session.query(Location).all()
        
        if not locations:
            click.echo("📭 No locations found")
            return
        
        export_data = []
        for location in locations:
            location_data = {
                'id': location.id,
                'code': location.code,
                'type': location.location_type,
                'name': location.description,
                'created_date': location.created_date.isoformat() if location.created_date else None
            }
            
            if include_items:
                with get_db_session() as session:
                    total_items = session.query(Item).filter(Item.location_id == location.id).count()
                    available_items = session.query(Item).filter(
                        Item.location_id == location.id,
                        Item.status == 'available'
                    ).count()
                    
                    location_data.update({
                        'total_items': total_items,
                        'available_items': available_items
                    })
            
            export_data.append(location_data)
        
        # Export
        if format_type == 'csv':
            _export_csv(export_data, output_path)
        elif format_type == 'json':
            _export_json(export_data, output_path)
        elif format_type == 'excel':
            _export_excel(export_data, output_path)
        
        click.echo(f"✅ Exported {len(locations)} locations to {output_path}")
    
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")


@click.command(name='backup-database')
@with_database
@click.option('--output', '-o', help='Backup file path')
@click.option('--compress', is_flag=True, help='Compress the backup')
@click.option('--include-photos', is_flag=True, help='Include photos in backup')
def backup_database(output, compress, include_photos):
    """Create complete database backup
    
    Usage:
      inv backup-database
      inv backup-database --output=backup.json --compress
      inv backup-database --include-photos
    """
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not output:
            output = f"streetwear_inventory_backup_{timestamp}.json"
            if compress:
                output += ".gz"
        
        output_path = Path(output)
        
        click.echo("📦 Creating database backup...")
        
        # Export all data
        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'includes_photos': include_photos
            },
            'items': [],
            'locations': [],
            'consigners': []
        }
        
        photo_manager = PhotoManager() if include_photos else None
        
        with get_db_session() as session:
            # Export items
            items = session.query(Item).all()
            for item in items:
                item_data = _item_to_export_dict(
                    item, 
                    include_photos=include_photos,
                    include_consigner=True,
                    photo_manager=photo_manager
                )
                backup_data['items'].append(item_data)
            
            # Export locations
            locations = session.query(Location).all()
            for location in locations:
                backup_data['locations'].append({
                    'id': location.id,
                    'code': location.code,
                    'type': location.location_type,
                    'name': location.description,
                    'created_date': location.created_date.isoformat() if location.created_date else None
                })
            
            # Export consigners
            consigners = session.query(Consigner).all()
            for consigner in consigners:
                backup_data['consigners'].append({
                    'id': consigner.id,
                    'name': consigner.name,
                    'phone': consigner.phone,
                    'email': consigner.email,
                    'default_split_percentage': consigner.default_split_percentage,
                    'created_date': consigner.created_date.isoformat() if consigner.created_date else None
                })
        
        # Write backup
        if compress:
            import gzip
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
        
        # Show summary
        click.echo(f"✅ Backup completed: {output_path}")
        click.echo(f"   Items: {len(backup_data['items'])}")
        click.echo(f"   Locations: {len(backup_data['locations'])}")
        click.echo(f"   Consigners: {len(backup_data['consigners'])}")
        click.echo(f"   File size: {output_path.stat().st_size:,} bytes")
        click.echo(f"   Compressed: {'Yes' if compress else 'No'}")
        click.echo(f"   Photos included: {'Yes' if include_photos else 'No'}")
        
        if include_photos:
            photo_stats = photo_manager.get_storage_stats()
            click.echo(f"   Photo files: {photo_stats['total_files']}")
            click.echo(f"   Photo size: {photo_stats['total_size_mb']} MB")
    
    except Exception as e:
        click.echo(f"❌ Backup failed: {e}")


@click.command(name='export-template')
@click.argument('format_type', type=click.Choice(['csv', 'excel']))
@click.option('--output', '-o', help='Template file path')
@click.option('--include-examples', is_flag=True, help='Include example data')
def export_template(format_type, output, include_examples):
    """Generate import template files
    
    Usage:
      inv export-template csv
      inv export-template excel --include-examples
      inv export-template csv --output=import_template.csv
    """
    
    try:
        if format_type == 'excel' and not PANDAS_AVAILABLE:
            click.echo("❌ Excel templates require pandas. Install with: pip install pandas openpyxl")
            return
        
        if not output:
            output = f"import_template.{format_type}"
        
        output_path = Path(output)
        
        # Define template columns
        template_data = [
            {
                'sku': 'NIK001' if include_examples else '',
                'brand': 'nike' if include_examples else '',
                'model': 'air jordan 1' if include_examples else '',
                'size': '10' if include_examples else '',
                'color': 'chicago' if include_examples else '',
                'condition': 'DS' if include_examples else '',
                'box_status': 'box' if include_examples else '',
                'current_price': '250.00' if include_examples else '',
                'purchase_price': '200.00' if include_examples else '',
                'location_code': 'STORE-01' if include_examples else '',
                'status': 'available' if include_examples else '',
                'ownership_type': 'owned' if include_examples else '',
                'notes': 'Example item' if include_examples else '',
                'consigner_name': '' if not include_examples else '',
                'consigner_phone': '' if not include_examples else '',
                'split_percentage': '' if not include_examples else ''
            }
        ]
        
        # Add header row if no examples
        if not include_examples:
            template_data = [template_data[0]]  # Keep the empty template
        
        # Export template
        if format_type == 'csv':
            _export_csv(template_data, output_path)
        elif format_type == 'excel':
            _export_excel(template_data, output_path)
        
        click.echo(f"✅ Generated import template: {output_path}")
        click.echo(f"   Format: {format_type.upper()}")
        if include_examples:
            click.echo("   Includes example data")
        click.echo("   Edit this file and use import commands to add data")
    
    except Exception as e:
        click.echo(f"❌ Template generation failed: {e}")


def _item_to_export_dict(item, include_photos=False, include_consigner=False, photo_manager=None):
    """Convert Item model to export dictionary"""
    data = {
        'sku': item.sku,
        'variant_id': item.variant_id,
        'brand': item.brand,
        'model': item.model,
        'size': item.size,
        'color': item.color,
        'condition': item.condition,
        'box_status': item.box_status,
        'current_price': float(item.current_price),
        'purchase_price': float(item.purchase_price) if item.purchase_price else None,
        'sold_price': float(item.sold_price) if item.sold_price else None,
        'location_code': item.location.code if item.location else None,
        'location_name': item.location.description if item.location else None,
        'status': item.status,
        'ownership_type': item.ownership_type,
        'notes': item.notes,
        'date_added': item.date_added.isoformat() if item.date_added else None,
        'sold_date': item.sold_date.isoformat() if item.sold_date else None,
        'split_percentage': item.split_percentage
    }
    
    if include_consigner and item.consigner:
        data.update({
            'consigner_name': item.consigner.name,
            'consigner_phone': item.consigner.phone,
            'consigner_email': item.consigner.email
        })
    
    if include_photos and photo_manager:
        photos = photo_manager.list_photos(item.sku)
        data.update({
            'photo_count': len(photos),
            'primary_photo': photos[0]['filename'] if photos else None,
            'all_photos': [p['filename'] for p in photos]
        })
    
    return data


def _export_csv(data: List[Dict], output_path: Path):
    """Export data to CSV"""
    if not data:
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def _export_json(data: List[Dict], output_path: Path):
    """Export data to JSON"""
    export_obj = {
        'exported_at': datetime.now().isoformat(),
        'total_records': len(data),
        'data': data
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_obj, f, indent=2, default=str)


def _export_excel(data: List[Dict], output_path: Path):
    """Export data to Excel"""
    if not PANDAS_AVAILABLE:
        raise RuntimeError("pandas is required for Excel export")
    
    df = pd.DataFrame(data)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Data']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width