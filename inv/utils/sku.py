"""SKU generation utilities with brand prefix logic"""

import re
from typing import Dict, Optional
from sqlalchemy.orm import Session

from ..database.connection import get_db_session
from ..database.models import Item
from .config import get_config


def get_brand_prefix(brand: str) -> str:
    """Get 3-letter prefix for brand, with collision handling"""
    config = get_config()
    brand_prefixes = config.get('brand_prefixes', {})
    
    # Normalize brand name
    brand_lower = brand.lower().strip()
    
    # Check if brand already has a prefix
    if brand_lower in brand_prefixes:
        return brand_prefixes[brand_lower].upper()
    
    # Generate new prefix from brand name
    base_prefix = generate_prefix_from_name(brand)
    
    # Check for collisions and find available prefix
    available_prefix = find_available_prefix(base_prefix, brand_prefixes)
    
    return available_prefix


def generate_prefix_from_name(brand: str) -> str:
    """Generate 3-letter prefix from brand name"""
    brand = brand.upper().strip()
    
    # Remove non-alphabetic characters
    clean_brand = re.sub(r'[^A-Z]', '', brand)
    
    if len(clean_brand) >= 3:
        # Take first 3 letters
        return clean_brand[:3]
    elif len(clean_brand) >= 1:
        # Pad with repeated letters
        prefix = clean_brand
        while len(prefix) < 3:
            prefix += clean_brand[-1]
        return prefix
    else:
        # Fallback for brands with no letters
        return "UNK"


def find_available_prefix(base_prefix: str, existing_prefixes: Dict[str, str]) -> str:
    """Find available prefix using phonetic variants"""
    # List of existing prefix values (not keys)
    used_prefixes = set(prefix.upper() for prefix in existing_prefixes.values())
    
    if base_prefix not in used_prefixes:
        return base_prefix
    
    # Generate phonetic variants
    variants = generate_phonetic_variants(base_prefix)
    
    for variant in variants:
        if variant not in used_prefixes:
            return variant
    
    # If all phonetic variants are taken, use numeric suffix
    counter = 1
    while f"{base_prefix}{counter:02d}" in used_prefixes:
        counter += 1
    
    return f"{base_prefix[:2]}{counter:01d}"


def generate_phonetic_variants(prefix: str) -> list:
    """Generate phonetic variants for collision resolution"""
    if len(prefix) != 3:
        return []
    
    variants = []
    
    # Common phonetic substitutions
    substitutions = {
        'A': ['E', 'I', 'O', 'U'],
        'E': ['A', 'I', 'O', 'U'], 
        'I': ['A', 'E', 'O', 'U'],
        'O': ['A', 'E', 'I', 'U'],
        'U': ['A', 'E', 'I', 'O'],
        'B': ['P', 'V'],
        'C': ['K', 'S'],
        'D': ['T'],
        'F': ['V', 'P'],
        'G': ['K', 'J'],
        'J': ['G', 'Y'],
        'K': ['C', 'G'],
        'P': ['B', 'F'],
        'S': ['C', 'Z'],
        'T': ['D'],
        'V': ['B', 'F'],
        'Y': ['J'],
        'Z': ['S']
    }
    
    # Generate variants by substituting each position
    for pos in range(3):
        original_char = prefix[pos]
        if original_char in substitutions:
            for replacement in substitutions[original_char]:
                variant = prefix[:pos] + replacement + prefix[pos+1:]
                variants.append(variant)
    
    return variants


def get_next_sku_number(prefix: str) -> int:
    """Get the next available SKU number for a given prefix"""
    with get_db_session() as session:
        # Find highest existing number for this prefix
        pattern = f"{prefix}%"
        
        items = session.query(Item).filter(
            Item.sku.like(pattern)
        ).all()
        
        max_number = 0
        sku_pattern = re.compile(rf'^{re.escape(prefix)}(\d{{3}})(?:-\d+)?$')
        
        for item in items:
            match = sku_pattern.match(item.sku)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        
        return max_number + 1


def generate_sku(brand: str, variant_id: int = 1) -> str:
    """Generate complete SKU for an item"""
    prefix = get_brand_prefix(brand)
    number = get_next_sku_number(prefix)
    
    base_sku = f"{prefix}{number:03d}"
    
    if variant_id == 1:
        return base_sku
    else:
        return f"{base_sku}-{variant_id}"


def validate_sku_format(sku: str) -> bool:
    """Validate SKU format (3 letters + 3 digits, optional variant)"""
    pattern = r'^[A-Z]{3}\d{3}(?:-\d+)?$'
    return bool(re.match(pattern, sku))


def extract_base_sku(sku: str) -> str:
    """Extract base SKU from variant SKU (NIK001-2 → NIK001)"""
    return sku.split('-')[0]


def extract_variant_id(sku: str) -> int:
    """Extract variant ID from SKU (NIK001-2 → 2, NIK001 → 1)"""
    if '-' in sku:
        return int(sku.split('-')[1])
    return 1


def check_sku_exists(sku: str) -> bool:
    """Check if SKU already exists in database"""
    with get_db_session() as session:
        return session.query(Item).filter(Item.sku == sku).first() is not None


def find_existing_variants(brand: str, model: str, color: str) -> list:
    """Find existing variants of an item (same brand/model/color)"""
    with get_db_session() as session:
        items = session.query(Item).filter(
            Item.brand.ilike(f"%{brand}%"),
            Item.model.ilike(f"%{model}%"),
            Item.color.ilike(f"%{color}%")
        ).all()
        
        return items


def get_next_variant_id(base_sku: str) -> int:
    """Get next variant ID for a base SKU"""
    with get_db_session() as session:
        pattern = f"{base_sku}%"
        
        items = session.query(Item).filter(
            Item.sku.like(pattern)
        ).all()
        
        max_variant = 0
        variant_pattern = re.compile(rf'^{re.escape(base_sku)}(?:-(\d+))?$')
        
        for item in items:
            match = variant_pattern.match(item.sku)
            if match:
                variant_str = match.group(1)
                variant_id = int(variant_str) if variant_str else 1
                max_variant = max(max_variant, variant_id)
        
        return max_variant + 1