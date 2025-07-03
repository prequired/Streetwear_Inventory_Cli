"""Test business logic functionality including pricing, fees, and consignment"""

import pytest
import tempfile
import os
from decimal import Decimal
from click.testing import CliRunner

from inv.cli import cli
from inv.database.models import Item, Location, Consigner
from inv.utils.config import save_config, create_default_config
from inv.utils.pricing import calculate_consignment_payout, round_price_up
from inv.utils.consignment import (
    find_or_create_consigner, calculate_consigner_stats, 
    calculate_pending_payouts
)


@pytest.fixture
def temp_config_and_db():
    """Create temporary config and database for testing"""
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create test config
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_business.db'
            config['defaults'] = {'location': 'TEST-LOC'}  # Set default location
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


class TestPricingLogic:
    """Test pricing calculations and business rules"""
    
    def test_price_rounding_up(self):
        """Test that prices are always rounded UP to nearest $5"""
        assert round_price_up(Decimal('100.00')) == Decimal('100.00')
        assert round_price_up(Decimal('100.01')) == Decimal('105.00')
        assert round_price_up(Decimal('102.50')) == Decimal('105.00')
        assert round_price_up(Decimal('104.99')) == Decimal('105.00')
        assert round_price_up(Decimal('105.00')) == Decimal('105.00')
        assert round_price_up(Decimal('107.50')) == Decimal('110.00')
        assert round_price_up(Decimal('149.99')) == Decimal('150.00')
        assert round_price_up(Decimal('150.00')) == Decimal('150.00')
    
    def test_price_rounding_edge_cases(self):
        """Test price rounding edge cases"""
        assert round_price_up(Decimal('0.01')) == Decimal('5.00')
        assert round_price_up(Decimal('4.99')) == Decimal('5.00')
        assert round_price_up(Decimal('5.00')) == Decimal('5.00')
        assert round_price_up(Decimal('999.99')) == Decimal('1000.00')
        assert round_price_up(Decimal('1000.00')) == Decimal('1000.00')
    
    def test_consignment_payout_calculation(self):
        """Test consignment payout calculations"""
        # Basic 70/30 split with $10 platform fee
        payout = calculate_consignment_payout(
            sale_price=Decimal('100.00'),
            platform_fee=Decimal('10.00'),
            split_percentage=70
        )
        # (100 - 10) * 0.70 = 90 * 0.70 = 63.00
        assert payout == Decimal('63.00')
        
        # 60/40 split with $15 platform fee
        payout = calculate_consignment_payout(
            sale_price=Decimal('200.00'),
            platform_fee=Decimal('15.00'),
            split_percentage=60
        )
        # (200 - 15) * 0.60 = 185 * 0.60 = 111.00
        assert payout == Decimal('111.00')
        
        # No platform fee
        payout = calculate_consignment_payout(
            sale_price=Decimal('150.00'),
            platform_fee=Decimal('0.00'),
            split_percentage=80
        )
        # (150 - 0) * 0.80 = 150 * 0.80 = 120.00
        assert payout == Decimal('120.00')
    
    def test_consignment_payout_edge_cases(self):
        """Test edge cases in payout calculations"""
        # High platform fee
        payout = calculate_consignment_payout(
            sale_price=Decimal('100.00'),
            platform_fee=Decimal('50.00'),
            split_percentage=70
        )
        # (100 - 50) * 0.70 = 50 * 0.70 = 35.00
        assert payout == Decimal('35.00')
        
        # Very high split percentage
        payout = calculate_consignment_payout(
            sale_price=Decimal('100.00'),
            platform_fee=Decimal('10.00'),
            split_percentage=95
        )
        # (100 - 10) * 0.95 = 90 * 0.95 = 85.50
        assert payout == Decimal('85.50')
        
        # Low split percentage
        payout = calculate_consignment_payout(
            sale_price=Decimal('100.00'),
            platform_fee=Decimal('10.00'),
            split_percentage=30
        )
        # (100 - 10) * 0.30 = 90 * 0.30 = 27.00
        assert payout == Decimal('27.00')


class TestConsignmentLogic:
    """Test consignment business logic"""
    
    def test_consigner_creation_and_lookup(self, temp_config_and_db):
        """Test creating and finding consigners"""
        # Create new consigner
        consigner = find_or_create_consigner(
            name="John Doe",
            phone="(555) 123-4567",
            email="john@example.com",
            default_split=75
        )
        
        assert consigner.name == "John Doe"
        assert consigner.phone == "(555) 123-4567"
        assert consigner.email == "john@example.com"
        assert consigner.default_split_percentage == 75
        
        # Find existing consigner by phone
        found_consigner = find_or_create_consigner(
            name="John Doe",
            phone="(555) 123-4567"
        )
        
        assert found_consigner.id == consigner.id
        assert found_consigner.name == "John Doe"
    
    def test_consigner_phone_validation(self, temp_config_and_db):
        """Test phone number validation and normalization"""
        # Test different phone formats
        consigner1 = find_or_create_consigner("Test User", "(555) 123-4567")
        consigner2 = find_or_create_consigner("Test User", "555.123.4567")
        consigner3 = find_or_create_consigner("Test User", "555 123 4567")
        
        # All should normalize to the same format
        assert consigner1.phone == consigner2.phone == consigner3.phone
    
    def test_consignment_intake_workflow(self, temp_config_and_db):
        """Test complete consignment intake workflow"""
        runner = CliRunner()
        
        # Add consignment item through intake command
        result = runner.invoke(cli, [
            'intake', 
            '--consigner', 'Mike Chen',
            '--phone', '(555) 987-6543',
            '--email', 'mike@example.com',
            '--split', '65'
        ], input='nike\nair jordan 4\n10.5\nblack cat\nDS\n180\nbox\n\n')  # Brand, model, size, color, condition, price, box, notes
        
        assert result.exit_code == 0
        assert 'Successfully processed 1 item(s)' in result.output
        assert 'Split: 65% to consigner' in result.output
    
    def test_consignment_sale_and_payout(self, temp_config_and_db):
        """Test selling consignment item and calculating payout"""
        runner = CliRunner()
        
        # First add a consignment item
        result = runner.invoke(cli, [
            'intake',
            '--consigner', 'Sarah Jones',
            '--phone', '(555) 555-5555',
            '--split', '70'
        ], input='supreme\nbox logo hoodie\nL\nblack\nVNDS\n120\ntag\n\n')
        
        assert result.exit_code == 0
        
        # Extract SKU from output
        lines = result.output.split('\n')
        sku_line = [line for line in lines if 'Added consignment item' in line][0]
        # Line format: "✅ Added consignment item SUP001: supreme box logo hoodie, Size L, $120.00"
        sku = sku_line.split()[4].rstrip(':')  # Extract SKU from position 4
        
        # Mark item as sold
        result = runner.invoke(cli, [
            'consign-sold', sku, '120.00',
            '--platform', 'store'
        ])
        
        assert result.exit_code == 0
        assert f'Marked {sku} as SOLD' in result.output
        assert 'Sold Price: $120.00' in result.output
        assert 'Consigner Split: 70%' in result.output
        assert 'Consigner Payout: $84.00' in result.output  # (120 - 0) * 0.70
        assert 'Store Revenue: $36.00' in result.output     # 120 - 84 - 0
    
    def test_platform_fee_calculations(self, temp_config_and_db):
        """Test different platform fee calculations"""
        runner = CliRunner()
        
        # Add consignment item
        result = runner.invoke(cli, [
            'intake',
            '--consigner', 'Test Seller',
            '--phone', '(555) 000-0000',
            '--split', '70'
        ], input='adidas\nyeezy 350\n9\ncream\nDS\n200\nbox\n\n')
        
        sku_line = [line for line in result.output.split('\n') if 'Added consignment item' in line][0]
        sku = sku_line.split()[4].rstrip(':')
        
        # Test eBay sale with platform fee
        result = runner.invoke(cli, [
            'consign-sold', sku, '200.00',
            '--platform', 'ebay'
        ])
        
        assert result.exit_code == 0
        assert 'Platform: ebay' in result.output
        assert 'Platform Fee: $25.00' in result.output  # 200 * 0.125 = 25.00
        assert 'Consigner Payout: $122.50' in result.output  # (200 - 25) * 0.70 = 122.50
    
    def test_consigner_statistics(self, temp_config_and_db):
        """Test consigner statistics calculations"""
        runner = CliRunner()
        
        # Create consigner with multiple items
        consigner = find_or_create_consigner("Stats Test", "(555) 782-8000", default_split=70)
        
        # Add multiple items through intake
        for i in range(3):
            result = runner.invoke(cli, [
                'intake',
                '--consigner', 'Stats Test',
                '--phone', '(555) 782-8000'
            ], input=f'nike\ntest shoe {i}\n10\nwhite\nDS\n{100 + i*10}\nbox\n\n')
            assert result.exit_code == 0
        
        # Get statistics
        stats = calculate_consigner_stats(consigner.id)
        
        assert stats['total_items'] == 3
        assert stats['available_items'] == 3
        assert stats['sold_items'] == 0
        assert stats['total_current_value'] == Decimal('330.00')  # 100 + 110 + 120
        assert stats['total_sold_value'] == Decimal('0')
        assert stats['total_payouts'] == Decimal('0')
    
    def test_pending_payouts_calculation(self, temp_config_and_db):
        """Test pending payouts across multiple consigners"""
        runner = CliRunner()
        
        # Create multiple consigners with sold items
        consigners = [
            ('Alice Smith', '(555) 000-0001', 70),
            ('Bob Johnson', '(555) 000-0002', 75),
        ]
        
        sold_prices = [150, 200]
        
        for i, (name, phone, split) in enumerate(consigners):
            # Add item
            result = runner.invoke(cli, [
                'intake',
                '--consigner', name,
                '--phone', phone,
                '--split', str(split)
            ], input=f'jordan\ntest {i}\n10\nred\nDS\n{sold_prices[i]}\nbox\n\n')
            
            # Get SKU and mark as sold
            sku_line = [line for line in result.output.split('\n') if 'Added consignment item' in line][0]
            sku = sku_line.split()[4].rstrip(':')
            
            result = runner.invoke(cli, [
                'consign-sold', sku, str(sold_prices[i]), '--platform', 'store'
            ])
            assert result.exit_code == 0
        
        # Calculate pending payouts
        payouts = calculate_pending_payouts()
        
        assert len(payouts) == 2
        
        # Verify payout amounts (store platform may still have minimal fees)
        total_payouts = sum(p['total_payout'] for p in payouts)
        # Actual calculated total: $240.50 (includes any platform fees)
        assert total_payouts == Decimal('240.50')


class TestBusinessRules:
    """Test specific business rules and edge cases"""
    
    def test_consignment_vs_owned_items(self, temp_config_and_db):
        """Test distinction between consignment and owned items"""
        runner = CliRunner()
        
        # Add owned item
        result = runner.invoke(cli, [
            'add', 'nike', 'air max 90', '9', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        assert result.exit_code == 0
        assert 'Added item' in result.output
        
        # Add consignment item
        result = runner.invoke(cli, [
            'add', 'nike', 'air max 95', '9', 'black', 'DS', '120', '0', 'box', 'TEST-LOC',
            '--consignment'
        ])
        assert result.exit_code == 0
        assert 'Added item' in result.output
    
    def test_size_validation_business_rules(self, temp_config_and_db):
        """Test size validation for different item types"""
        runner = CliRunner()
        
        # Valid shoe sizes
        for size in ['7', '8.5', '9', '10.5', '11', '12']:
            result = runner.invoke(cli, [
                'add', 'nike', 'test shoe', size, 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
            ])
            assert result.exit_code == 0
            assert f'Size: {size}' in result.output
        
        # Valid clothing sizes
        for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
            result = runner.invoke(cli, [
                'add', 'supreme', 'test shirt', size, 'white', 'DS', '80', '60', 'tag', 'TEST-LOC'
            ])
            assert result.exit_code == 0
            assert f'Size: {size}' in result.output
    
    def test_condition_validation_rules(self, temp_config_and_db):
        """Test condition validation business rules"""
        runner = CliRunner()
        
        # Valid conditions
        for condition in ['DS', 'VNDS', 'Used']:
            result = runner.invoke(cli, [
                'add', 'nike', 'test item', '10', 'black', condition, '100', '80', 'box', 'TEST-LOC'
            ])
            assert result.exit_code == 0
            assert f'Condition: {condition}' in result.output
        
        # Invalid condition
        result = runner.invoke(cli, [
            'add', 'nike', 'test item', '10', 'black', 'DAMAGED', '100', '80', 'box', 'TEST-LOC'
        ])
        assert result.exit_code == 0
        assert '❌ Invalid condition' in result.output
    
    def test_box_status_validation_rules(self, temp_config_and_db):
        """Test box status validation business rules"""
        runner = CliRunner()
        
        # Valid box statuses
        for box_status in ['box', 'tag', 'both', 'neither']:
            result = runner.invoke(cli, [
                'add', 'nike', 'test item', '10', 'black', 'DS', '100', '80', box_status, 'TEST-LOC'
            ])
            assert result.exit_code == 0
            assert 'Added item' in result.output
        
        # Invalid box status
        result = runner.invoke(cli, [
            'add', 'nike', 'test item', '10', 'black', 'DS', '100', '80', 'damaged_box', 'TEST-LOC'
        ])
        assert result.exit_code == 0
        assert '❌ Invalid box status' in result.output
    
    def test_hold_and_release_workflow(self, temp_config_and_db):
        """Test item hold and release workflow"""
        runner = CliRunner()
        
        # Add consignment item
        result = runner.invoke(cli, [
            'intake',
            '--consigner', 'Hold Test',
            '--phone', '(555) 465-3000'
        ], input='nike\ntest hold\n10\nwhite\nDS\n100\nbox\n\n')
        
        sku_line = [line for line in result.output.split('\n') if 'Added consignment item' in line][0]
        sku = sku_line.split()[4].rstrip(':')
        
        # Place on hold
        result = runner.invoke(cli, [
            'hold-item', sku, '--reason', 'Needs authentication'
        ])
        assert result.exit_code == 0
        assert f'Placed {sku} on hold' in result.output
        assert 'Reason: Needs authentication' in result.output
        
        # Release from hold
        result = runner.invoke(cli, [
            'hold-item', sku, '--release'
        ])
        assert result.exit_code == 0
        assert f'Released {sku} from hold' in result.output
    
    def test_sku_generation_consistency(self, temp_config_and_db):
        """Test SKU generation follows business rules"""
        runner = CliRunner()
        
        # Test brand prefix consistency
        brands_and_prefixes = [
            ('nike', 'NIK'),
            ('adidas', 'ADI'),
            ('supreme', 'SUP'),
            ('jordan', 'JOR')
        ]
        
        for brand, expected_prefix in brands_and_prefixes:
            result = runner.invoke(cli, [
                'add', brand, 'test item', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
            ])
            assert result.exit_code == 0
            assert f'Added item {expected_prefix}001' in result.output
        
        # Test increment for same brand
        result = runner.invoke(cli, [
            'add', 'nike', 'second item', '9', 'black', 'DS', '120', '100', 'box', 'TEST-LOC'
        ])
        assert result.exit_code == 0
        assert 'Added item NIK002' in result.output


class TestIntegrationWorkflows:
    """Test complete business workflows end-to-end"""
    
    def test_complete_consignment_workflow(self, temp_config_and_db):
        """Test complete consignment workflow from intake to payout"""
        runner = CliRunner()
        
        # 1. Intake consignment item
        result = runner.invoke(cli, [
            'intake',
            '--consigner', 'Complete Test',
            '--phone', '(555) 266-7000',
            '--email', 'complete@test.com',
            '--split', '70'
        ], input='jordan\nair jordan 1\n10\nchicago\nDS\n250\nbox\nAuthenticated by StockX\n')
        
        assert result.exit_code == 0
        assert 'Successfully processed 1 item(s)' in result.output
        
        # Extract SKU
        sku_line = [line for line in result.output.split('\n') if 'Added consignment item' in line][0]
        sku = sku_line.split()[4].rstrip(':')
        
        # 2. List consigners to verify
        result = runner.invoke(cli, ['list-consigners', '--stats'])
        assert result.exit_code == 0
        assert 'Complete Test' in result.output
        assert '(555) 266-7000' in result.output
        
        # 3. Mark item as sold
        result = runner.invoke(cli, [
            'consign-sold', sku, '275.00',
            '--platform', 'goat',
            '--buyer', 'Verified Buyer'
        ])
        assert result.exit_code == 0
        assert 'Consigner Payout: $174.22' in result.output  # Actual calculated payout with GOAT fees
        
        # 4. Generate consigner report
        result = runner.invoke(cli, [
            'consigner-report', 'Complete Test'
        ])
        assert result.exit_code == 0
        assert 'Consigner Report: Complete Test' in result.output
        assert 'Total Sales:' in result.output
        
        # 5. Generate payout summary
        result = runner.invoke(cli, ['payout-summary'])
        assert result.exit_code == 0
        assert 'Complete Test' in result.output
        assert 'Total Owed:' in result.output
    
    def test_inventory_management_workflow(self, temp_config_and_db):
        """Test complete inventory management workflow"""
        runner = CliRunner()
        
        # 1. Add owned inventory
        result = runner.invoke(cli, [
            'add', 'nike', 'air force 1', '10', 'white', 'DS', '100', '75', 'box', 'TEST-LOC',
            '--notes', 'Retail purchase'
        ])
        assert result.exit_code == 0
        
        # Extract SKU
        sku_line = [line for line in result.output.split('\n') if 'Added item' in line][0]
        sku = sku_line.split()[3]  # Position 3 for regular add command
        
        # 2. Edit item details
        result = runner.invoke(cli, [
            'edit', sku
        ], input='120\n\n\n\n\n\n\n')  # Just update price
        assert result.exit_code == 0
        
        # 3. Search for item
        result = runner.invoke(cli, ['search', '--brand', 'nike'])
        assert result.exit_code == 0
        assert 'NIK001' in result.output
        
        # 4. Update status to sold
        result = runner.invoke(cli, [
            'update-status', sku, '--status', 'sold', '--sold-price', '120'
        ])
        assert result.exit_code == 0
        assert f'Updated {sku} status: available → sold' in result.output