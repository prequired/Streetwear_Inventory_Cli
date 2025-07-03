"""Data validation utilities"""

import re
from typing import List, Optional
from decimal import Decimal, InvalidOperation


# Valid sizes for different categories
VALID_SHOE_SIZES = [
    # Men's whole sizes
    "4", "4.5", "5", "5.5", "6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", 
    "10", "10.5", "11", "11.5", "12", "12.5", "13", "13.5", "14", "14.5", "15", "16", "17", "18",
    # Extended sizes
    "3", "3.5", "19", "20"
]

VALID_CLOTHING_SIZES = [
    "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL",
    # Numeric sizes
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "38", "40", "42", "44", "46", "48", "50"
]

VALID_CONDITIONS = ["DS", "VNDS", "Used"]
VALID_BOX_STATUS = ["box", "tag", "both", "neither"]
VALID_ITEM_STATUS = ["available", "sold", "held", "deleted"]
VALID_OWNERSHIP_TYPES = ["owned", "consignment"]


def normalize_size(size_input: str) -> str:
    """Normalize size input to standard format"""
    if not size_input:
        raise ValueError("Size cannot be empty")
    
    size = str(size_input).strip().upper()
    
    # Handle fraction formats
    size = size.replace("½", ".5")
    size = size.replace(" 1/2", ".5")
    size = size.replace("1/2", ".5")
    
    # Remove extra spaces
    size = re.sub(r'\s+', '', size)
    
    return size


def validate_size(size: str, category: str = "shoe") -> bool:
    """Validate if size is in valid list"""
    normalized_size = normalize_size(size)
    
    if category.lower() in ["shoe", "shoes", "sneaker", "sneakers"]:
        return normalized_size in VALID_SHOE_SIZES
    elif category.lower() in ["clothing", "apparel", "shirt", "pants", "jacket"]:
        return normalized_size in VALID_CLOTHING_SIZES
    else:
        # Default to shoe sizes or allow both
        return normalized_size in VALID_SHOE_SIZES or normalized_size in VALID_CLOTHING_SIZES


def validate_condition(condition: str) -> bool:
    """Validate item condition"""
    return condition in VALID_CONDITIONS


def validate_box_status(box_status: str) -> bool:
    """Validate box status"""
    return box_status in VALID_BOX_STATUS


def validate_item_status(status: str) -> bool:
    """Validate item status"""
    return status in VALID_ITEM_STATUS


def validate_ownership_type(ownership_type: str) -> bool:
    """Validate ownership type"""
    return ownership_type in VALID_OWNERSHIP_TYPES


def validate_price(price_input: str) -> Decimal:
    """Validate and convert price to Decimal"""
    if not price_input:
        raise ValueError("Price cannot be empty")
    
    try:
        price = Decimal(str(price_input).strip().replace('$', '').replace(',', ''))
        if price < 0:
            raise ValueError("Price cannot be negative")
        if price > 999999.99:
            raise ValueError("Price too large")
        return price
    except InvalidOperation:
        raise ValueError(f"Invalid price format: {price_input}")


def validate_percentage(percentage: int) -> bool:
    """Validate percentage value"""
    return isinstance(percentage, int) and 0 <= percentage <= 100


def validate_phone(phone: str) -> str:
    """Validate and normalize phone number"""
    if not phone:
        raise ValueError("Phone number cannot be empty")
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid US phone number
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        raise ValueError("Invalid phone number format")


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return True  # Email is optional
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_sku_format(sku: str) -> bool:
    """Validate SKU format (3 letters + 3 digits)"""
    pattern = r'^[A-Z]{3}\d{3}$'
    return bool(re.match(pattern, sku))


def validate_brand_name(brand: str) -> str:
    """Validate and normalize brand name"""
    if not brand:
        raise ValueError("Brand name cannot be empty")
    
    brand = brand.strip()
    if len(brand) > 100:
        raise ValueError("Brand name too long (max 100 characters)")
    
    return brand


def validate_model_name(model: str) -> str:
    """Validate and normalize model name"""
    if not model:
        raise ValueError("Model name cannot be empty")
    
    model = model.strip()
    if len(model) > 200:
        raise ValueError("Model name too long (max 200 characters)")
    
    return model


def validate_color_name(color: str) -> str:
    """Validate and normalize color name"""
    if not color:
        raise ValueError("Color name cannot be empty")
    
    color = color.strip()
    if len(color) > 100:
        raise ValueError("Color name too long (max 100 characters)")
    
    return color


def get_validation_errors(data: dict) -> List[str]:
    """Get all validation errors for item data"""
    errors = []
    
    try:
        validate_brand_name(data.get('brand', ''))
    except ValueError as e:
        errors.append(f"Brand: {e}")
    
    try:
        validate_model_name(data.get('model', ''))
    except ValueError as e:
        errors.append(f"Model: {e}")
    
    try:
        validate_color_name(data.get('color', ''))
    except ValueError as e:
        errors.append(f"Color: {e}")
    
    if not validate_size(data.get('size', ''), data.get('category', 'shoe')):
        errors.append(f"Invalid size: {data.get('size', '')}")
    
    if not validate_condition(data.get('condition', '')):
        errors.append(f"Invalid condition: {data.get('condition', '')}")
    
    if not validate_box_status(data.get('box_status', '')):
        errors.append(f"Invalid box status: {data.get('box_status', '')}")
    
    try:
        validate_price(data.get('current_price', ''))
    except ValueError as e:
        errors.append(f"Current price: {e}")
    
    try:
        validate_price(data.get('purchase_price', ''))
    except ValueError as e:
        errors.append(f"Purchase price: {e}")
    
    return errors