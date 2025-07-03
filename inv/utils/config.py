"""Configuration management for YAML config files"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


CONFIG_FILE = "config.yaml"
_cached_config: Optional[Dict[str, Any]] = None


def get_config_path() -> Path:
    """Get the path to the config file"""
    return Path.cwd() / CONFIG_FILE


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    global _cached_config
    
    if _cached_config is not None and not force_reload:
        return _cached_config
    
    config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            _cached_config = yaml.safe_load(f)
        return _cached_config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to YAML file"""
    global _cached_config
    
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        _cached_config = config
    except Exception as e:
        raise Exception(f"Failed to save configuration: {e}")


def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    return load_config()


def get_current_config() -> Dict[str, Any]:
    """Get current cached configuration without reloading"""
    if _cached_config is None:
        return load_config()
    return _cached_config


def validate_config_structure(config: Dict[str, Any]) -> List[str]:
    """Validate configuration structure and return any errors"""
    errors = []
    
    # Check required sections
    required_sections = ['database', 'brand_prefixes', 'defaults', 'photos']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate database section
    if 'database' in config:
        db_config = config['database']
        if not isinstance(db_config, dict):
            errors.append("database section must be a dictionary")
        else:
            required_db_fields = ['url']
            for field in required_db_fields:
                if field not in db_config:
                    errors.append(f"Missing database field: {field}")
                elif not db_config[field]:
                    errors.append(f"Empty database field: {field}")
    
    # Validate brand_prefixes section
    if 'brand_prefixes' in config:
        brand_prefixes = config['brand_prefixes']
        if not isinstance(brand_prefixes, dict):
            errors.append("brand_prefixes section must be a dictionary")
        else:
            for brand, prefix in brand_prefixes.items():
                if not isinstance(prefix, str) or len(prefix) != 3:
                    errors.append(f"Brand prefix for '{brand}' must be exactly 3 characters")
    
    # Validate defaults section
    if 'defaults' in config:
        defaults = config['defaults']
        if not isinstance(defaults, dict):
            errors.append("defaults section must be a dictionary")
        else:
            if 'consignment_split' in defaults:
                split = defaults['consignment_split']
                if not isinstance(split, int) or split < 0 or split > 100:
                    errors.append("consignment_split must be an integer between 0 and 100")
    
    # Validate photos section
    if 'photos' in config:
        photos = config['photos']
        if not isinstance(photos, dict):
            errors.append("photos section must be a dictionary")
        else:
            if 'storage_path' not in photos:
                errors.append("Missing photos.storage_path field")
    
    return errors


def validate_config_file() -> List[str]:
    """Validate the current config file"""
    try:
        config = load_config(force_reload=True)
        return validate_config_structure(config)
    except Exception as e:
        return [f"Failed to load config file: {e}"]


def create_default_config() -> Dict[str, Any]:
    """Create default configuration structure"""
    return {
        'database': {
            'url': 'sqlite:///streetwear_inventory.db'
        },
        'brand_prefixes': {
            'nike': 'NIK',
            'adidas': 'ADI',
            'supreme': 'SUP'
        },
        'defaults': {
            'location': '',
            'consignment_split': 70
        },
        'photos': {
            'storage_path': './photos'
        }
    }