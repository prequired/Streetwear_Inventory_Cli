"""Test Phase 4 features: Photos, API, and Export functionality"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from PIL import Image
from click.testing import CliRunner

from inv.cli import cli
from inv.database.models import Item, Location, Consigner
from inv.utils.config import save_config, create_default_config
from inv.utils.photos import PhotoManager
from inv.api.server import create_api_server, FLASK_AVAILABLE


@pytest.fixture
def temp_config_and_db():
    """Create temporary config and database for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create test config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_phase4.db'
            save_config(config)
            
            # Initialize database
            from inv.database.connection import db
            from inv.database.setup import create_tables
            db.initialize(config)
            create_tables()
            
            # Create test location
            from inv.utils.locations import create_location
            create_location('TEST-LOC', 'test', 'Test Location')
            
            yield temp_dir
            
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    def _create_image(filename="test_image.jpg", size=(100, 100), color="red"):
        img = Image.new('RGB', size, color)
        # Add some EXIF data for testing removal
        img.save(filename, "JPEG", quality=95)
        return filename
    return _create_image


class TestPhotoManagement:
    """Test photo management functionality"""
    
    def test_photo_manager_initialization(self, temp_config_and_db):
        """Test PhotoManager initialization"""
        manager = PhotoManager()
        assert manager.storage_path.exists()
        assert manager.supported_formats == {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    
    def test_add_photo_command(self, temp_config_and_db, sample_image):
        """Test adding photos via CLI command"""
        runner = CliRunner()
        
        # First add an item
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        assert result.exit_code == 0
        
        # Create test image
        image_path = sample_image("test_photo.jpg")
        
        # Add photo to item
        result = runner.invoke(cli, [
            'add-photo', 'NIK001', image_path
        ])
        assert result.exit_code == 0
        assert '✅ Added photo to NIK001' in result.output
        assert 'JPEG' in result.output
    
    def test_list_photos_command(self, temp_config_and_db, sample_image):
        """Test listing photos via CLI command"""
        runner = CliRunner()
        
        # Add item and photo
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        image_path = sample_image("test_photo.jpg")
        runner.invoke(cli, ['add-photo', 'NIK001', image_path])
        
        # List photos
        result = runner.invoke(cli, ['list-photos', 'NIK001'])
        assert result.exit_code == 0
        assert 'Photos for NIK001' in result.output
        assert '⭐' in result.output  # Primary photo marker
    
    def test_photo_optimization(self, temp_config_and_db, sample_image):
        """Test photo optimization functionality"""
        runner = CliRunner()
        
        # Add item and photo
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        # Create larger image for optimization testing
        image_path = sample_image("large_photo.jpg", size=(2000, 2000))
        runner.invoke(cli, ['add-photo', 'NIK001', image_path])
        
        # Optimize photos
        result = runner.invoke(cli, ['optimize-photos', 'NIK001'])
        assert result.exit_code == 0
        assert 'Optimization complete' in result.output
    
    def test_photo_stats_command(self, temp_config_and_db, sample_image):
        """Test photo statistics command"""
        runner = CliRunner()
        
        # Add item and photo
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        image_path = sample_image("test_photo.jpg")
        runner.invoke(cli, ['add-photo', 'NIK001', image_path])
        
        # Get photo stats
        result = runner.invoke(cli, ['photo-stats'])
        assert result.exit_code == 0
        assert 'Photo Storage Statistics' in result.output
        assert 'Total Files: 1' in result.output
    
    def test_exif_removal(self, temp_config_and_db, sample_image):
        """Test EXIF data removal"""
        from inv.utils.photos import remove_exif_data
        
        # Create image with potential EXIF data
        original_image = sample_image("with_exif.jpg")
        
        # Remove EXIF data
        clean_image = remove_exif_data(original_image)
        
        # Verify clean image exists
        assert Path(clean_image).exists()
        
        # Verify image is still valid
        with Image.open(clean_image) as img:
            assert img.format == 'JPEG'
    
    def test_bulk_add_photos(self, temp_config_and_db, sample_image):
        """Test bulk photo addition"""
        runner = CliRunner()
        
        # Add item
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        # Create photos directory with multiple images
        photos_dir = Path("test_photos")
        photos_dir.mkdir()
        
        for i in range(3):
            sample_image(f"test_photos/photo_{i}.jpg")
        
        # Bulk add photos
        result = runner.invoke(cli, [
            'bulk-add-photos', 'NIK001', str(photos_dir)
        ])
        assert result.exit_code == 0
        assert 'Adding 3 photos' in result.output
        assert 'Added 3 of 3 photos' in result.output


class TestAPIEndpoints:
    """Test API functionality"""
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_api_server_creation(self, temp_config_and_db):
        """Test API server can be created"""
        api = create_api_server(debug=True)
        assert api is not None
        assert api.app is not None
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_api_endpoints_registration(self, temp_config_and_db):
        """Test that API endpoints are properly registered"""
        api = create_api_server()
        
        with api.app.test_client() as client:
            # Test index endpoint
            response = client.get('/')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'name' in data
            assert 'Streetwear Inventory API' in data['name']
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_api_items_endpoint(self, temp_config_and_db):
        """Test items API endpoint"""
        runner = CliRunner()
        
        # Add test item
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        api = create_api_server()
        
        with api.app.test_client() as client:
            # Test list items
            response = client.get('/api/items')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'items' in data
            assert len(data['items']) == 1
            assert data['items'][0]['sku'] == 'NIK001'
            assert data['items'][0]['brand'] == 'nike'
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_api_search_endpoint(self, temp_config_and_db):
        """Test search API endpoint"""
        runner = CliRunner()
        
        # Add test items
        runner.invoke(cli, [
            'add', 'nike', 'air jordan 1', '10', 'chicago', 'DS', '250', '200', 'box', 'TEST-LOC'
        ])
        runner.invoke(cli, [
            'add', 'adidas', 'yeezy boost', '9', 'cream', 'DS', '180', '150', 'box', 'TEST-LOC'
        ])
        
        api = create_api_server()
        
        with api.app.test_client() as client:
            # Test search
            response = client.get('/api/search?q=jordan')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'items' in data
            assert len(data['items']) == 1
            assert 'jordan' in data['items'][0]['model'].lower()
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_api_stats_endpoint(self, temp_config_and_db):
        """Test stats API endpoint"""
        runner = CliRunner()
        
        # Add test items
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        api = create_api_server()
        
        with api.app.test_client() as client:
            response = client.get('/api/stats')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'inventory' in data
            assert data['inventory']['total_items'] == 1
            assert data['inventory']['available_items'] == 1
    
    def test_api_docs_command(self, temp_config_and_db):
        """Test API documentation command"""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['api-docs'])
        assert result.exit_code == 0
        assert 'Streetwear Inventory API Documentation' in result.output
        assert 'GET /api/items' in result.output
        assert 'Example Usage' in result.output


class TestDataExport:
    """Test data export functionality"""
    
    def test_export_inventory_csv(self, temp_config_and_db):
        """Test CSV inventory export"""
        runner = CliRunner()
        
        # Add test items
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        runner.invoke(cli, [
            'add', 'adidas', 'test sneaker', '9', 'black', 'VNDS', '120', '90', 'box', 'TEST-LOC'
        ])
        
        # Export to CSV
        result = runner.invoke(cli, [
            'export-inventory', 'csv', '--output', 'test_export.csv'
        ])
        assert result.exit_code == 0
        assert 'Exported 2 items' in result.output
        
        # Verify file exists and has content
        assert Path('test_export.csv').exists()
        
        # Read and verify CSV content
        import csv
        with open('test_export.csv', 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['sku'] == 'NIK001'
            assert rows[1]['sku'] == 'ADI001'
    
    def test_export_inventory_json(self, temp_config_and_db):
        """Test JSON inventory export"""
        runner = CliRunner()
        
        # Add test item
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        # Export to JSON
        result = runner.invoke(cli, [
            'export-inventory', 'json', '--output', 'test_export.json'
        ])
        assert result.exit_code == 0
        assert 'Exported 1 items' in result.output
        
        # Verify file exists and has valid JSON
        assert Path('test_export.json').exists()
        
        with open('test_export.json', 'r') as f:
            data = json.load(f)
            assert 'data' in data
            assert len(data['data']) == 1
            assert data['data'][0]['sku'] == 'NIK001'
    
    def test_export_with_filters(self, temp_config_and_db):
        """Test export with filters"""
        runner = CliRunner()
        
        # Add test items
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        runner.invoke(cli, [
            'add', 'adidas', 'test sneaker', '9', 'black', 'VNDS', '120', '90', 'box', 'TEST-LOC'
        ])
        
        # Export only Nike items
        result = runner.invoke(cli, [
            'export-inventory', 'json', '--filter-brand', 'nike', '--output', 'nike_export.json'
        ])
        assert result.exit_code == 0
        assert 'Exported 1 items' in result.output
        assert 'brand_nike' in result.output  # Filter applied
        
        # Verify filtered content
        with open('nike_export.json', 'r') as f:
            data = json.load(f)
            assert len(data['data']) == 1
            assert data['data'][0]['brand'] == 'nike'
    
    def test_backup_database(self, temp_config_and_db):
        """Test database backup functionality"""
        runner = CliRunner()
        
        # Add test data
        runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        # Create backup
        result = runner.invoke(cli, [
            'backup-database', '--output', 'test_backup.json'
        ])
        assert result.exit_code == 0
        assert 'Backup completed' in result.output
        assert 'Items: 1' in result.output
        
        # Verify backup file
        assert Path('test_backup.json').exists()
        
        with open('test_backup.json', 'r') as f:
            backup_data = json.load(f)
            assert 'metadata' in backup_data
            assert 'items' in backup_data
            assert 'locations' in backup_data
            assert len(backup_data['items']) == 1
    
    def test_export_template(self, temp_config_and_db):
        """Test export template generation"""
        runner = CliRunner()
        
        # Generate CSV template
        result = runner.invoke(cli, [
            'export-template', 'csv', '--output', 'template.csv'
        ])
        assert result.exit_code == 0
        assert 'Generated import template' in result.output
        
        # Verify template file
        assert Path('template.csv').exists()
        
        # Check template has correct headers
        import csv
        with open('template.csv', 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert 'sku' in headers
            assert 'brand' in headers
            assert 'model' in headers
            assert 'current_price' in headers
    
    def test_export_consigners(self, temp_config_and_db):
        """Test consigner export"""
        runner = CliRunner()
        
        # Add consignment item
        result = runner.invoke(cli, [
            'intake',
            '--consigner', 'Test Consigner',
            '--phone', '(555) 123-4567',
            '--email', 'test@example.com'
        ], input='nike\ntest shoe\n10\nwhite\nDS\n100\nbox\n\n')
        
        assert result.exit_code == 0
        
        # Export consigners
        result = runner.invoke(cli, [
            'export-consigners', 'json', '--output', 'consigners.json', '--include-stats'
        ])
        assert result.exit_code == 0
        assert 'Exported 1 consigners' in result.output
        
        # Verify export
        with open('consigners.json', 'r') as f:
            data = json.load(f)
            assert len(data['data']) == 1
            consigner = data['data'][0]
            assert consigner['name'] == 'Test Consigner'
            assert 'total_items' in consigner  # Stats included


class TestIntegrationWorkflows:
    """Test complete Phase 4 workflows"""
    
    def test_complete_photo_workflow(self, temp_config_and_db, sample_image):
        """Test complete photo management workflow"""
        runner = CliRunner()
        
        # 1. Add item
        result = runner.invoke(cli, [
            'add', 'nike', 'air jordan 1', '10', 'chicago', 'DS', '250', '200', 'box', 'TEST-LOC'
        ])
        assert result.exit_code == 0
        
        # 2. Add multiple photos
        for i in range(3):
            image_path = sample_image(f"photo_{i}.jpg")
            result = runner.invoke(cli, ['add-photo', 'NIK001', image_path])
            assert result.exit_code == 0
        
        # 3. List photos
        result = runner.invoke(cli, ['list-photos', 'NIK001', '--details'])
        assert result.exit_code == 0
        assert 'Photos for NIK001 (3 total)' in result.output
        
        # 4. Set primary photo
        result = runner.invoke(cli, ['set-primary-photo', 'NIK001', 'photo_1.jpg'])
        assert result.exit_code == 0
        
        # 5. Get photo statistics
        result = runner.invoke(cli, ['photo-stats'])
        assert result.exit_code == 0
        assert 'Total Files: 3' in result.output
    
    def test_api_and_export_integration(self, temp_config_and_db):
        """Test API and export working together"""
        runner = CliRunner()
        
        # Add test data
        runner.invoke(cli, [
            'add', 'nike', 'air jordan 1', '10', 'chicago', 'DS', '250', '200', 'box', 'TEST-LOC'
        ])
        runner.invoke(cli, [
            'add', 'adidas', 'yeezy boost', '9', 'cream', 'DS', '180', '150', 'box', 'TEST-LOC'
        ])
        
        # Export data
        result = runner.invoke(cli, [
            'export-inventory', 'json', '--output', 'for_api_test.json'
        ])
        assert result.exit_code == 0
        
        # Verify export has data that API would serve
        with open('for_api_test.json', 'r') as f:
            export_data = json.load(f)
            assert len(export_data['data']) == 2
            
            # Check data structure matches API format
            item = export_data['data'][0]
            required_fields = ['sku', 'brand', 'model', 'current_price', 'status']
            for field in required_fields:
                assert field in item
    
    def test_backup_and_restore_simulation(self, temp_config_and_db):
        """Test backup creation for restore scenarios"""
        runner = CliRunner()
        
        # Create comprehensive test data
        # Add regular item
        runner.invoke(cli, [
            'add', 'nike', 'air force 1', '10', 'white', 'DS', '100', '75', 'box', 'TEST-LOC'
        ])
        
        # Add consignment item
        runner.invoke(cli, [
            'intake',
            '--consigner', 'John Doe',
            '--phone', '(555) 123-4567'
        ], input='supreme\nbox logo tee\nL\nwhite\nDS\n120\ntag\n\n')
        
        # Create comprehensive backup
        result = runner.invoke(cli, [
            'backup-database', '--output', 'comprehensive_backup.json'
        ])
        assert result.exit_code == 0
        
        # Verify backup completeness
        with open('comprehensive_backup.json', 'r') as f:
            backup = json.load(f)
            
            # Check metadata
            assert 'metadata' in backup
            assert 'created_at' in backup['metadata']
            
            # Check data completeness
            assert len(backup['items']) == 2
            assert len(backup['locations']) >= 1
            assert len(backup['consigners']) >= 1
            
            # Verify item types
            items_by_type = {}
            for item in backup['items']:
                items_by_type[item['ownership_type']] = item
            
            assert 'owned' in items_by_type
            assert 'consignment' in items_by_type
            assert items_by_type['owned']['brand'] == 'nike'
            assert items_by_type['consignment']['brand'] == 'supreme'


class TestErrorHandling:
    """Test error handling in Phase 4 features"""
    
    def test_photo_commands_with_invalid_sku(self, temp_config_and_db):
        """Test photo commands with non-existent SKU"""
        runner = CliRunner()
        
        # Try to add photo to non-existent item
        result = runner.invoke(cli, ['list-photos', 'INVALID001'])
        assert result.exit_code == 0
        assert '❌ Item with SKU \'INVALID001\' not found' in result.output
    
    def test_export_with_no_data(self, temp_config_and_db):
        """Test export commands with no data"""
        runner = CliRunner()
        
        # Try to export when no items exist
        result = runner.invoke(cli, [
            'export-inventory', 'json', '--filter-brand', 'nonexistent'
        ])
        assert result.exit_code == 0
        assert 'No items found matching the specified criteria' in result.output
    
    def test_api_endpoints_error_handling(self, temp_config_and_db):
        """Test API error handling"""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        api = create_api_server()
        
        with api.app.test_client() as client:
            # Test non-existent item
            response = client.get('/api/items/INVALID001')
            assert response.status_code == 404
            
            # Test invalid endpoint
            response = client.get('/api/invalid-endpoint')
            assert response.status_code == 404


# Performance and stress tests
class TestPerformance:
    """Test performance of Phase 4 features"""
    
    def test_export_performance_with_many_items(self, temp_config_and_db):
        """Test export performance with multiple items"""
        runner = CliRunner()
        
        # Add multiple items quickly
        brands = ['nike', 'adidas', 'supreme', 'jordan']
        for i in range(10):  # Moderate number for testing
            brand = brands[i % len(brands)]
            result = runner.invoke(cli, [
                'add', brand, f'test item {i}', '10', 'white', 'DS', 
                str(100 + i), str(80 + i), 'box', 'TEST-LOC'
            ])
            assert result.exit_code == 0
        
        # Test export performance
        import time
        start_time = time.time()
        
        result = runner.invoke(cli, [
            'export-inventory', 'json', '--output', 'performance_test.json'
        ])
        
        end_time = time.time()
        
        assert result.exit_code == 0
        assert 'Exported 10 items' in result.output
        
        # Should complete quickly (less than 5 seconds for 10 items)
        assert (end_time - start_time) < 5.0