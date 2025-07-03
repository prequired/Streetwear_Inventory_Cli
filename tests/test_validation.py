"""Test data validation utilities"""

import pytest
from decimal import Decimal

from inv.utils.validation import (
    normalize_size, validate_size, validate_condition, validate_box_status,
    validate_item_status, validate_ownership_type, validate_price,
    validate_percentage, validate_phone, validate_email, validate_sku_format,
    validate_brand_name, validate_model_name, validate_color_name,
    get_validation_errors
)


class TestSizeValidation:
    """Test size normalization and validation"""
    
    def test_normalize_size_basic(self):
        """Test basic size normalization"""
        assert normalize_size("10") == "10"
        assert normalize_size("10.5") == "10.5"
        assert normalize_size("  10  ") == "10"
    
    def test_normalize_size_fractions(self):
        """Test fraction normalization"""
        assert normalize_size("10½") == "10.5"
        assert normalize_size("10 1/2") == "10.5"
        assert normalize_size("10.5") == "10.5"
    
    def test_normalize_size_clothing(self):
        """Test clothing size normalization"""
        assert normalize_size("xl") == "XL"
        assert normalize_size("  m  ") == "M"
    
    def test_normalize_size_empty(self):
        """Test empty size handling"""
        with pytest.raises(ValueError, match="Size cannot be empty"):
            normalize_size("")
    
    def test_validate_shoe_sizes(self):
        """Test shoe size validation"""
        assert validate_size("10", "shoe") is True
        assert validate_size("10.5", "shoe") is True
        assert validate_size("15", "shoe") is True
        assert validate_size("25", "shoe") is False
    
    def test_validate_clothing_sizes(self):
        """Test clothing size validation"""
        assert validate_size("M", "clothing") is True
        assert validate_size("XL", "clothing") is True
        assert validate_size("32", "clothing") is True
        assert validate_size("10.5", "clothing") is False


class TestBasicValidation:
    """Test basic validation functions"""
    
    def test_validate_condition(self):
        """Test condition validation"""
        assert validate_condition("DS") is True
        assert validate_condition("VNDS") is True
        assert validate_condition("Used") is True
        assert validate_condition("New") is False
    
    def test_validate_box_status(self):
        """Test box status validation"""
        assert validate_box_status("box") is True
        assert validate_box_status("tag") is True
        assert validate_box_status("both") is True
        assert validate_box_status("neither") is True
        assert validate_box_status("none") is False
    
    def test_validate_item_status(self):
        """Test item status validation"""
        assert validate_item_status("available") is True
        assert validate_item_status("sold") is True
        assert validate_item_status("held") is True
        assert validate_item_status("deleted") is True
        assert validate_item_status("pending") is False
    
    def test_validate_ownership_type(self):
        """Test ownership type validation"""
        assert validate_ownership_type("owned") is True
        assert validate_ownership_type("consignment") is True
        assert validate_ownership_type("rental") is False


class TestPriceValidation:
    """Test price validation"""
    
    def test_validate_price_valid(self):
        """Test valid price inputs"""
        assert validate_price("100") == Decimal("100")
        assert validate_price("100.50") == Decimal("100.50")
        assert validate_price("$100.50") == Decimal("100.50")
        assert validate_price("1,000.50") == Decimal("1000.50")
    
    def test_validate_price_empty(self):
        """Test empty price input"""
        with pytest.raises(ValueError, match="Price cannot be empty"):
            validate_price("")
    
    def test_validate_price_negative(self):
        """Test negative price"""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            validate_price("-100")
    
    def test_validate_price_too_large(self):
        """Test price too large"""
        with pytest.raises(ValueError, match="Price too large"):
            validate_price("1000000")
    
    def test_validate_price_invalid_format(self):
        """Test invalid price format"""
        with pytest.raises(ValueError, match="Invalid price format"):
            validate_price("abc")


class TestPercentageValidation:
    """Test percentage validation"""
    
    def test_validate_percentage_valid(self):
        """Test valid percentages"""
        assert validate_percentage(0) is True
        assert validate_percentage(50) is True
        assert validate_percentage(100) is True
    
    def test_validate_percentage_invalid(self):
        """Test invalid percentages"""
        assert validate_percentage(-1) is False
        assert validate_percentage(101) is False
        assert validate_percentage("50") is False


class TestPhoneValidation:
    """Test phone number validation"""
    
    def test_validate_phone_valid(self):
        """Test valid phone numbers"""
        assert validate_phone("5551234567") == "(555) 123-4567"
        assert validate_phone("15551234567") == "(555) 123-4567"
        assert validate_phone("(555) 123-4567") == "(555) 123-4567"
        assert validate_phone("555-123-4567") == "(555) 123-4567"
    
    def test_validate_phone_empty(self):
        """Test empty phone number"""
        with pytest.raises(ValueError, match="Phone number cannot be empty"):
            validate_phone("")
    
    def test_validate_phone_invalid(self):
        """Test invalid phone numbers"""
        with pytest.raises(ValueError, match="Invalid phone number format"):
            validate_phone("123")
        
        with pytest.raises(ValueError, match="Invalid phone number format"):
            validate_phone("12345678901234")


class TestEmailValidation:
    """Test email validation"""
    
    def test_validate_email_valid(self):
        """Test valid email addresses"""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
        assert validate_email("") is True  # Empty is valid (optional)
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses"""
        assert validate_email("invalid-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False


class TestSkuValidation:
    """Test SKU format validation"""
    
    def test_validate_sku_format_valid(self):
        """Test valid SKU formats"""
        assert validate_sku_format("NIK001") is True
        assert validate_sku_format("ADI999") is True
        assert validate_sku_format("SUP123") is True
    
    def test_validate_sku_format_invalid(self):
        """Test invalid SKU formats"""
        assert validate_sku_format("NIK01") is False  # Too short
        assert validate_sku_format("NIKE001") is False  # Too long
        assert validate_sku_format("N1K001") is False  # Number in letters
        assert validate_sku_format("NIKOO1") is False  # Letter in numbers


class TestStringValidation:
    """Test string field validation"""
    
    def test_validate_brand_name(self):
        """Test brand name validation"""
        assert validate_brand_name("Nike") == "Nike"
        assert validate_brand_name("  Adidas  ") == "Adidas"
        
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            validate_brand_name("")
        
        with pytest.raises(ValueError, match="Brand name too long"):
            validate_brand_name("A" * 101)
    
    def test_validate_model_name(self):
        """Test model name validation"""
        assert validate_model_name("Air Jordan 1") == "Air Jordan 1"
        assert validate_model_name("  Stan Smith  ") == "Stan Smith"
        
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            validate_model_name("")
        
        with pytest.raises(ValueError, match="Model name too long"):
            validate_model_name("A" * 201)
    
    def test_validate_color_name(self):
        """Test color name validation"""
        assert validate_color_name("Black") == "Black"
        assert validate_color_name("  Red/White  ") == "Red/White"
        
        with pytest.raises(ValueError, match="Color name cannot be empty"):
            validate_color_name("")
        
        with pytest.raises(ValueError, match="Color name too long"):
            validate_color_name("A" * 101)


class TestValidationErrors:
    """Test complete validation error collection"""
    
    def test_get_validation_errors_valid_data(self):
        """Test validation with valid data"""
        data = {
            'brand': 'TestBrand',
            'model': 'Test Model',
            'color': 'Black',
            'size': '10',
            'condition': 'DS',
            'box_status': 'box',
            'current_price': '250.00',
            'purchase_price': '200.00'
        }
        
        errors = get_validation_errors(data)
        assert len(errors) == 0
    
    def test_get_validation_errors_invalid_data(self):
        """Test validation with invalid data"""
        data = {
            'brand': '',  # Invalid
            'model': 'A' * 201,  # Too long
            'color': 'Black',
            'size': '25',  # Invalid shoe size
            'condition': 'New',  # Invalid
            'box_status': 'none',  # Invalid
            'current_price': 'abc',  # Invalid
            'purchase_price': '-100'  # Invalid
        }
        
        errors = get_validation_errors(data)
        assert len(errors) > 0
        assert any('Brand:' in e for e in errors)
        assert any('Model:' in e for e in errors)
        assert any('Invalid size:' in e for e in errors)
        assert any('Invalid condition:' in e for e in errors)
        assert any('Invalid box status:' in e for e in errors)
        assert any('Current price:' in e for e in errors)
        assert any('Purchase price:' in e for e in errors)