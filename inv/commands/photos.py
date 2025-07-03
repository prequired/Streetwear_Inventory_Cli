"""Photo management commands for inventory items"""

import click
from pathlib import Path
from typing import List

from ..database.connection import get_db_session
from ..database.models import Item
from ..utils.photos import PhotoManager, remove_exif_data, find_duplicate_photos
from ..utils.database_init import with_database


@click.command()
@with_database
@click.argument('sku')
@click.argument('photo_path')
@click.option('--filename', help='Custom filename for the photo')
@click.option('--primary', is_flag=True, help='Set as primary photo')
def add_photo(sku, photo_path, filename, primary):
    """Add photo to inventory item
    
    Usage:
      inv add-photo NIK001 /path/to/photo.jpg
      inv add-photo SUP005 ./image.png --filename="front_view.png"
      inv add-photo ADI003 photo.jpg --primary
    
    The photo will be processed to remove EXIF data and optimized for storage.
    """
    
    try:
        # Verify item exists
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
        
        manager = PhotoManager()
        
        # Add photo
        result = manager.add_photo(sku.upper(), photo_path, filename)
        
        if result['success']:
            click.echo(f"✅ Added photo to {sku.upper()}")
            click.echo(f"   Filename: {result['filename']}")
            click.echo(f"   Size: {result['size_bytes']:,} bytes")
            click.echo(f"   Dimensions: {result['dimensions']}")
            click.echo(f"   Format: {result['format']}")
            
            if primary:
                if manager.set_primary_photo(sku.upper(), result['filename']):
                    click.echo("   Set as primary photo ⭐")
                else:
                    click.echo("   ⚠️  Failed to set as primary photo")
        else:
            click.echo(f"❌ Failed to add photo: {result.get('error', 'Unknown error')}")
    
    except FileNotFoundError as e:
        click.echo(f"❌ Photo file not found: {e}")
    except ValueError as e:
        click.echo(f"❌ Invalid photo format: {e}")
    except Exception as e:
        click.echo(f"❌ Error adding photo: {e}")


@click.command(name='list-photos')
@with_database
@click.argument('sku')
@click.option('--details', is_flag=True, help='Show detailed photo information')
def list_photos(sku, details):
    """List photos for inventory item
    
    Usage:
      inv list-photos NIK001
      inv list-photos SUP005 --details
    """
    
    try:
        # Verify item exists
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
        
        manager = PhotoManager()
        photos = manager.list_photos(sku.upper())
        
        if not photos:
            click.echo(f"📷 No photos found for {sku.upper()}")
            return
        
        click.echo(f"📷 Photos for {sku.upper()} ({len(photos)} total):")
        click.echo("-" * 50)
        
        for i, photo in enumerate(photos, 1):
            primary_marker = "⭐ " if i == 1 else "   "
            click.echo(f"{primary_marker}{photo['filename']}")
            
            if details:
                click.echo(f"      Size: {photo['size_mb']} MB ({photo['size_bytes']:,} bytes)")
                click.echo(f"      Dimensions: {photo['dimensions']}")
                click.echo(f"      Format: {photo['format']}")
                click.echo(f"      Created: {photo['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                if 'error' in photo:
                    click.echo(f"      ❌ Error: {photo['error']}")
                click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error listing photos: {e}")


@click.command(name='remove-photo')
@with_database
@click.argument('sku')
@click.argument('filename')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def remove_photo(sku, filename, confirm):
    """Remove photo from inventory item
    
    Usage:
      inv remove-photo NIK001 photo.jpg
      inv remove-photo SUP005 front_view.png --confirm
    """
    
    try:
        # Verify item exists
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
        
        manager = PhotoManager()
        photos = manager.list_photos(sku.upper())
        
        # Check if photo exists
        photo_exists = any(p['filename'] == filename for p in photos)
        if not photo_exists:
            click.echo(f"❌ Photo '{filename}' not found for {sku.upper()}")
            return
        
        # Confirm deletion
        if not confirm:
            if not click.confirm(f"Delete photo '{filename}' from {sku.upper()}?"):
                click.echo("Cancelled.")
                return
        
        # Remove photo
        if manager.remove_photo(sku.upper(), filename):
            click.echo(f"✅ Removed photo '{filename}' from {sku.upper()}")
        else:
            click.echo(f"❌ Failed to remove photo '{filename}'")
    
    except Exception as e:
        click.echo(f"❌ Error removing photo: {e}")


@click.command(name='set-primary-photo')
@with_database
@click.argument('sku')
@click.argument('filename')
def set_primary_photo(sku, filename):
    """Set photo as primary for inventory item
    
    Usage:
      inv set-primary-photo NIK001 best_angle.jpg
      inv set-primary-photo SUP005 front_view.png
    """
    
    try:
        # Verify item exists
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
        
        manager = PhotoManager()
        photos = manager.list_photos(sku.upper())
        
        # Check if photo exists
        photo_exists = any(p['filename'] == filename for p in photos)
        if not photo_exists:
            click.echo(f"❌ Photo '{filename}' not found for {sku.upper()}")
            return
        
        # Set as primary
        if manager.set_primary_photo(sku.upper(), filename):
            click.echo(f"⭐ Set '{filename}' as primary photo for {sku.upper()}")
        else:
            click.echo(f"❌ Failed to set '{filename}' as primary photo")
    
    except Exception as e:
        click.echo(f"❌ Error setting primary photo: {e}")


@click.command(name='copy-photos')
@with_database
@click.argument('source_sku')
@click.argument('dest_sku')
def copy_photos(source_sku, dest_sku):
    """Copy photos from one item to another (useful for variants)
    
    Usage:
      inv copy-photos NIK001 NIK002
      inv copy-photos SUP005 SUP006
    """
    
    try:
        # Verify both items exist
        with get_db_session() as session:
            source_item = session.query(Item).filter(Item.sku == source_sku.upper()).first()
            dest_item = session.query(Item).filter(Item.sku == dest_sku.upper()).first()
            
            if not source_item:
                click.echo(f"❌ Source item '{source_sku}' not found")
                return
            
            if not dest_item:
                click.echo(f"❌ Destination item '{dest_sku}' not found")
                return
        
        manager = PhotoManager()
        copied_count = manager.copy_photos_to_item(source_sku.upper(), dest_sku.upper())
        
        if copied_count > 0:
            click.echo(f"✅ Copied {copied_count} photo(s) from {source_sku.upper()} to {dest_sku.upper()}")
        else:
            click.echo(f"📷 No photos found to copy from {source_sku.upper()}")
    
    except Exception as e:
        click.echo(f"❌ Error copying photos: {e}")


@click.command(name='photo-stats')
@with_database
@click.option('--cleanup', is_flag=True, help='Remove orphaned photo directories')
def photo_stats(cleanup):
    """Show photo storage statistics
    
    Usage:
      inv photo-stats
      inv photo-stats --cleanup
    """
    
    try:
        manager = PhotoManager()
        
        if cleanup:
            click.echo("🧹 Cleaning up orphaned photos...")
            cleanup_result = manager.cleanup_orphaned_photos()
            click.echo(f"   Removed {cleanup_result['removed_directories']} directories")
            click.echo(f"   Removed {cleanup_result['removed_files']} files")
            click.echo()
        
        stats = manager.get_storage_stats()
        
        click.echo("📊 Photo Storage Statistics:")
        click.echo("-" * 30)
        click.echo(f"Storage Path: {stats['storage_path']}")
        click.echo(f"Total Files: {stats['total_files']:,}")
        click.echo(f"Total Size: {stats['total_size_mb']} MB ({stats['total_size_bytes']:,} bytes)")
        click.echo(f"Item Directories: {stats['directories']}")
        
        if stats['total_files'] > 0:
            avg_file_size = stats['total_size_bytes'] / stats['total_files']
            click.echo(f"Average File Size: {avg_file_size / 1024 / 1024:.2f} MB")
    
    except Exception as e:
        click.echo(f"❌ Error getting photo stats: {e}")


@click.command(name='optimize-photos')
@with_database
@click.argument('sku', required=False)
@click.option('--all', 'optimize_all', is_flag=True, help='Optimize photos for all items')
def optimize_photos(sku, optimize_all):
    """Optimize photos to reduce file size
    
    Usage:
      inv optimize-photos NIK001
      inv optimize-photos --all
    """
    
    try:
        manager = PhotoManager()
        
        if optimize_all:
            click.echo("🔧 Optimizing all photos...")
            result = manager.optimize_photos_batch()
        elif sku:
            # Verify item exists
            with get_db_session() as session:
                item = session.query(Item).filter(Item.sku == sku.upper()).first()
                if not item:
                    click.echo(f"❌ Item with SKU '{sku}' not found")
                    return
            
            click.echo(f"🔧 Optimizing photos for {sku.upper()}...")
            result = manager.optimize_photos_batch(sku.upper())
        else:
            click.echo("❌ Please provide SKU or use --all flag")
            return
        
        click.echo(f"✅ Optimization complete:")
        click.echo(f"   Files optimized: {result['optimized_count']}")
        click.echo(f"   Space saved: {result['saved_mb']} MB ({result['saved_bytes']:,} bytes)")
        
        if result['errors']:
            click.echo(f"⚠️  Errors ({len(result['errors'])}):")
            for error in result['errors'][:5]:  # Show first 5 errors
                click.echo(f"   {error}")
            if len(result['errors']) > 5:
                click.echo(f"   ... and {len(result['errors']) - 5} more")
    
    except Exception as e:
        click.echo(f"❌ Error optimizing photos: {e}")


@click.command(name='find-duplicate-photos')
@with_database
@click.option('--directory', help='Search in specific directory (default: photos storage)')
@click.option('--remove', is_flag=True, help='Remove duplicate photos (keeps first occurrence)')
def find_duplicate_photos_cmd(directory, remove):
    """Find duplicate photos in storage
    
    Usage:
      inv find-duplicate-photos
      inv find-duplicate-photos --directory=/path/to/photos
      inv find-duplicate-photos --remove
    """
    
    try:
        click.echo("🔍 Searching for duplicate photos...")
        duplicates = find_duplicate_photos(directory)
        
        if not duplicates:
            click.echo("✅ No duplicate photos found!")
            return
        
        total_duplicates = sum(len(files) - 1 for files in duplicates.values())
        click.echo(f"🔍 Found {len(duplicates)} groups with {total_duplicates} duplicate files:")
        click.echo("-" * 60)
        
        removed_count = 0
        saved_bytes = 0
        
        for hash_value, file_list in duplicates.items():
            click.echo(f"\nDuplicate group ({len(file_list)} files):")
            
            for i, file_path in enumerate(file_list):
                file_size = Path(file_path).stat().st_size
                status = "KEEP" if i == 0 else "DUPLICATE"
                click.echo(f"  [{status}] {file_path} ({file_size:,} bytes)")
                
                if remove and i > 0:  # Remove duplicates (keep first)
                    try:
                        Path(file_path).unlink()
                        removed_count += 1
                        saved_bytes += file_size
                        click.echo(f"         ❌ REMOVED")
                    except Exception as e:
                        click.echo(f"         ⚠️  Error removing: {e}")
        
        if remove:
            click.echo(f"\n✅ Cleanup complete:")
            click.echo(f"   Files removed: {removed_count}")
            click.echo(f"   Space saved: {saved_bytes / 1024 / 1024:.2f} MB")
        else:
            click.echo(f"\n💡 Use --remove flag to delete duplicate files")
    
    except Exception as e:
        click.echo(f"❌ Error finding duplicates: {e}")


@click.command(name='remove-exif')
@click.argument('input_path')
@click.argument('output_path', required=False)
def remove_exif_cmd(input_path, output_path):
    """Remove EXIF metadata from image file
    
    Usage:
      inv remove-exif photo.jpg
      inv remove-exif input.jpg clean_output.jpg
    """
    
    try:
        result_path = remove_exif_data(input_path, output_path)
        
        # Get file sizes
        original_size = Path(input_path).stat().st_size
        clean_size = Path(result_path).stat().st_size
        saved_bytes = original_size - clean_size
        
        click.echo(f"✅ EXIF data removed")
        click.echo(f"   Original: {original_size:,} bytes")
        click.echo(f"   Clean: {clean_size:,} bytes")
        click.echo(f"   Saved: {saved_bytes:,} bytes ({saved_bytes/original_size*100:.1f}%)")
        click.echo(f"   Output: {result_path}")
        
    except FileNotFoundError:
        click.echo(f"❌ Input file not found: {input_path}")
    except Exception as e:
        click.echo(f"❌ Error removing EXIF data: {e}")


@click.command(name='bulk-add-photos')
@with_database
@click.argument('sku')
@click.argument('photos_directory')
@click.option('--pattern', default='*', help='File pattern to match (e.g., "*.jpg")')
@click.option('--set-primary', type=int, help='Set photo number as primary (1-based)')
def bulk_add_photos(sku, photos_directory, pattern, set_primary):
    """Add multiple photos to item from directory
    
    Usage:
      inv bulk-add-photos NIK001 /path/to/photos/
      inv bulk-add-photos SUP005 ./photos/ --pattern="*.jpg"
      inv bulk-add-photos ADI003 ./photos/ --set-primary=1
    """
    
    try:
        # Verify item exists
        with get_db_session() as session:
            item = session.query(Item).filter(Item.sku == sku.upper()).first()
            if not item:
                click.echo(f"❌ Item with SKU '{sku}' not found")
                return
        
        photos_dir = Path(photos_directory)
        if not photos_dir.exists():
            click.echo(f"❌ Directory not found: {photos_directory}")
            return
        
        manager = PhotoManager()
        
        # Find matching files
        photo_files = list(photos_dir.glob(pattern))
        photo_files = [f for f in photo_files if f.suffix.lower() in manager.supported_formats]
        
        if not photo_files:
            click.echo(f"📷 No photos found matching pattern '{pattern}'")
            return
        
        # Sort files for consistent ordering
        photo_files.sort()
        
        click.echo(f"📷 Adding {len(photo_files)} photos to {sku.upper()}...")
        
        added_count = 0
        errors = []
        
        for i, photo_path in enumerate(photo_files, 1):
            try:
                result = manager.add_photo(sku.upper(), str(photo_path))
                
                if result['success']:
                    click.echo(f"   ✅ {i:2d}. {photo_path.name} ({result['size_bytes']:,} bytes)")
                    added_count += 1
                    
                    # Set as primary if requested
                    if set_primary == i:
                        if manager.set_primary_photo(sku.upper(), result['filename']):
                            click.echo(f"        ⭐ Set as primary photo")
                else:
                    errors.append(f"{photo_path.name}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                errors.append(f"{photo_path.name}: {e}")
        
        click.echo(f"\n✅ Added {added_count} of {len(photo_files)} photos")
        
        if errors:
            click.echo(f"⚠️  Errors ({len(errors)}):")
            for error in errors[:3]:  # Show first 3 errors
                click.echo(f"   {error}")
            if len(errors) > 3:
                click.echo(f"   ... and {len(errors) - 3} more")
    
    except Exception as e:
        click.echo(f"❌ Error adding photos: {e}")