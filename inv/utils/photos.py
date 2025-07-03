"""Photo management utilities including EXIF removal and organization"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image
import hashlib
from datetime import datetime

from ..utils.config import get_config


class PhotoManager:
    """Manages photo operations for inventory items"""
    
    def __init__(self):
        config = get_config()
        self.storage_path = Path(config.get('photos', {}).get('storage_path', './photos'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        
        # Maximum image dimensions for optimization
        self.max_width = 1920
        self.max_height = 1920
        self.jpeg_quality = 85
    
    def get_item_photos_dir(self, sku: str) -> Path:
        """Get photos directory for specific item"""
        return self.storage_path / sku.upper()
    
    def create_item_photos_dir(self, sku: str) -> Path:
        """Create photos directory for item if it doesn't exist"""
        photos_dir = self.get_item_photos_dir(sku)
        photos_dir.mkdir(parents=True, exist_ok=True)
        return photos_dir
    
    def add_photo(self, sku: str, source_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Add photo to item, removing EXIF and optimizing"""
        source_path = Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source photo not found: {source_path}")
        
        if source_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported image format: {source_path.suffix}")
        
        # Create item photos directory
        photos_dir = self.create_item_photos_dir(sku)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}{source_path.suffix.lower()}"
        
        dest_path = photos_dir / filename
        
        # Process image: remove EXIF, optimize, resize if needed
        try:
            with Image.open(source_path) as img:
                # Remove EXIF data by creating new image
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG compatibility
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGB')
                    elif img.mode in ('RGBA', 'LA'):
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                
                # Resize if too large
                if img.width > self.max_width or img.height > self.max_height:
                    img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                
                # Save with optimization
                save_kwargs = {'optimize': True}
                if dest_path.suffix.lower() in ['.jpg', '.jpeg']:
                    save_kwargs['quality'] = self.jpeg_quality
                    save_kwargs['format'] = 'JPEG'
                
                img.save(dest_path, **save_kwargs)
            
            # Get file info
            file_info = self._get_photo_info(dest_path)
            
            return {
                'success': True,
                'filename': filename,
                'path': str(dest_path),
                'size_bytes': file_info['size_bytes'],
                'dimensions': file_info['dimensions'],
                'format': file_info['format']
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to process image: {e}")
    
    def remove_photo(self, sku: str, filename: str) -> bool:
        """Remove photo from item"""
        photos_dir = self.get_item_photos_dir(sku)
        photo_path = photos_dir / filename
        
        if photo_path.exists():
            photo_path.unlink()
            return True
        return False
    
    def list_photos(self, sku: str) -> List[Dict[str, Any]]:
        """List all photos for an item"""
        photos_dir = self.get_item_photos_dir(sku)
        
        if not photos_dir.exists():
            return []
        
        photos = []
        for photo_path in photos_dir.iterdir():
            if photo_path.is_file() and photo_path.suffix.lower() in self.supported_formats:
                photo_info = self._get_photo_info(photo_path)
                photos.append(photo_info)
        
        # Sort by creation time (newest first)
        photos.sort(key=lambda x: x['created_at'], reverse=True)
        return photos
    
    def get_primary_photo(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get primary (first) photo for item"""
        photos = self.list_photos(sku)
        return photos[0] if photos else None
    
    def set_primary_photo(self, sku: str, filename: str) -> bool:
        """Set photo as primary by renaming to have earliest timestamp"""
        photos_dir = self.get_item_photos_dir(sku)
        photo_path = photos_dir / filename
        
        if not photo_path.exists():
            return False
        
        # Rename to make it primary (earliest timestamp)
        new_filename = f"00000000_000000{photo_path.suffix}"
        new_path = photos_dir / new_filename
        
        # If primary already exists, rename it
        if new_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = photos_dir / f"{timestamp}{new_path.suffix}"
            new_path.rename(backup_path)
        
        photo_path.rename(new_path)
        return True
    
    def copy_photos_to_item(self, source_sku: str, dest_sku: str) -> int:
        """Copy all photos from one item to another (for variants)"""
        source_dir = self.get_item_photos_dir(source_sku)
        dest_dir = self.create_item_photos_dir(dest_sku)
        
        if not source_dir.exists():
            return 0
        
        copied_count = 0
        for photo_path in source_dir.iterdir():
            if photo_path.is_file() and photo_path.suffix.lower() in self.supported_formats:
                dest_path = dest_dir / photo_path.name
                shutil.copy2(photo_path, dest_path)
                copied_count += 1
        
        return copied_count
    
    def cleanup_orphaned_photos(self) -> Dict[str, int]:
        """Remove photo directories for items that no longer exist"""
        from ..database.connection import get_db_session
        from ..database.models import Item
        
        # Get all existing SKUs
        with get_db_session() as session:
            existing_skus = {item.sku for item in session.query(Item.sku).all()}
        
        removed_dirs = 0
        removed_files = 0
        
        for item_dir in self.storage_path.iterdir():
            if item_dir.is_dir() and item_dir.name not in existing_skus:
                # Remove orphaned directory
                file_count = len([f for f in item_dir.iterdir() if f.is_file()])
                shutil.rmtree(item_dir)
                removed_dirs += 1
                removed_files += file_count
        
        return {
            'removed_directories': removed_dirs,
            'removed_files': removed_files
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get photo storage statistics"""
        total_files = 0
        total_size = 0
        directories = 0
        
        for item_dir in self.storage_path.iterdir():
            if item_dir.is_dir():
                directories += 1
                for photo_path in item_dir.iterdir():
                    if photo_path.is_file():
                        total_files += 1
                        total_size += photo_path.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'directories': directories,
            'storage_path': str(self.storage_path)
        }
    
    def _get_photo_info(self, photo_path: Path) -> Dict[str, Any]:
        """Get information about a photo file"""
        try:
            stat = photo_path.stat()
            
            # Get image dimensions and format
            with Image.open(photo_path) as img:
                dimensions = f"{img.width}x{img.height}"
                format_name = img.format
            
            return {
                'filename': photo_path.name,
                'path': str(photo_path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'dimensions': dimensions,
                'format': format_name,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception as e:
            return {
                'filename': photo_path.name,
                'path': str(photo_path),
                'error': str(e)
            }
    
    def optimize_photos_batch(self, sku: str = None) -> Dict[str, Any]:
        """Optimize photos for one item or all items"""
        optimized_count = 0
        saved_bytes = 0
        errors = []
        
        if sku:
            # Optimize photos for specific item
            items_to_process = [sku]
        else:
            # Optimize photos for all items
            items_to_process = [d.name for d in self.storage_path.iterdir() if d.is_dir()]
        
        for item_sku in items_to_process:
            photos_dir = self.get_item_photos_dir(item_sku)
            
            if not photos_dir.exists():
                continue
                
            for photo_path in photos_dir.iterdir():
                if photo_path.is_file() and photo_path.suffix.lower() in self.supported_formats:
                    try:
                        original_size = photo_path.stat().st_size
                        
                        # Re-optimize image
                        temp_path = photo_path.with_suffix('.tmp')
                        
                        with Image.open(photo_path) as img:
                            # Remove EXIF and optimize
                            if img.mode in ('RGBA', 'LA', 'P'):
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGB')
                                elif img.mode in ('RGBA', 'LA'):
                                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                    img = rgb_img
                            
                            save_kwargs = {'optimize': True}
                            if photo_path.suffix.lower() in ['.jpg', '.jpeg']:
                                save_kwargs['quality'] = self.jpeg_quality
                                save_kwargs['format'] = 'JPEG'
                            
                            img.save(temp_path, **save_kwargs)
                        
                        new_size = temp_path.stat().st_size
                        
                        # Replace original if smaller
                        if new_size < original_size:
                            temp_path.replace(photo_path)
                            saved_bytes += (original_size - new_size)
                            optimized_count += 1
                        else:
                            temp_path.unlink()
                            
                    except Exception as e:
                        errors.append(f"{item_sku}/{photo_path.name}: {e}")
        
        return {
            'optimized_count': optimized_count,
            'saved_bytes': saved_bytes,
            'saved_mb': round(saved_bytes / 1024 / 1024, 2),
            'errors': errors
        }


def remove_exif_data(image_path: str, output_path: str = None) -> str:
    """Remove EXIF data from image file"""
    manager = PhotoManager()
    
    source_path = Path(image_path)
    if not output_path:
        output_path = source_path.with_name(f"no_exif_{source_path.name}")
    
    output_path = Path(output_path)
    
    try:
        with Image.open(source_path) as img:
            # Create new image without EXIF
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(list(img.getdata()))
            
            # Save optimized
            save_kwargs = {'optimize': True}
            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = manager.jpeg_quality
                save_kwargs['format'] = 'JPEG'
            
            clean_img.save(output_path, **save_kwargs)
        
        return str(output_path)
        
    except Exception as e:
        raise RuntimeError(f"Failed to remove EXIF data: {e}")


def get_image_hash(image_path: str) -> str:
    """Generate hash for image to detect duplicates"""
    with open(image_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash


def find_duplicate_photos(directory: str = None) -> Dict[str, List[str]]:
    """Find duplicate photos in directory"""
    manager = PhotoManager()
    search_dir = Path(directory) if directory else manager.storage_path
    
    hash_map = {}
    duplicates = {}
    
    for photo_path in search_dir.rglob('*'):
        if photo_path.is_file() and photo_path.suffix.lower() in manager.supported_formats:
            try:
                photo_hash = get_image_hash(str(photo_path))
                
                if photo_hash in hash_map:
                    # Duplicate found
                    if photo_hash not in duplicates:
                        duplicates[photo_hash] = [hash_map[photo_hash]]
                    duplicates[photo_hash].append(str(photo_path))
                else:
                    hash_map[photo_hash] = str(photo_path)
                    
            except Exception:
                continue  # Skip files that can't be processed
    
    return duplicates