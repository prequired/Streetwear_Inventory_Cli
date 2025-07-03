"""Test configuration management"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from inv.utils.config import (
    load_config, save_config, get_config, validate_config_structure,
    validate_config_file, create_default_config, get_config_path
)


class TestConfigManagement:
    """Test configuration file management"""
    
    def test_create_default_config(self):
        """Test creating default configuration"""
        config = create_default_config()
        
        assert 'database' in config
        assert 'brand_prefixes' in config
        assert 'defaults' in config
        assert 'photos' in config
        
        assert config['database']['url'] == 'sqlite:///streetwear_inventory.db'
        assert config['brand_prefixes']['nike'] == 'NIK'
        assert config['defaults']['consignment_split'] == 70
        assert config['photos']['storage_path'] == './photos'
    
    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading configuration"""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            config = create_default_config()
            config['database']['url'] = 'sqlite:///test_database.db'
            
            # Save config
            save_config(config)
            
            # Load config
            loaded_config = load_config()
            
            assert loaded_config['database']['url'] == 'sqlite:///test_database.db'
            assert loaded_config['brand_prefixes']['nike'] == 'NIK'
        finally:
            os.chdir(original_cwd)
    
    def test_load_nonexistent_config(self, tmp_path, monkeypatch):
        """Test loading non-existent config file"""
        # Clear cache
        monkeypatch.setattr('inv.utils.config._cached_config', None)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                load_config()
        finally:
            os.chdir(original_cwd)
    
    def test_load_invalid_yaml(self, tmp_path, monkeypatch):
        """Test loading invalid YAML config"""
        # Clear cache
        monkeypatch.setattr('inv.utils.config._cached_config', None)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create invalid YAML file
            with open('config.yaml', 'w') as f:
                f.write('invalid: yaml:\n  - content:\n- malformed')
            
            with pytest.raises(ValueError, match="Invalid YAML configuration"):
                load_config()
        finally:
            os.chdir(original_cwd)
    
    def test_config_caching(self, tmp_path, monkeypatch):
        """Test configuration caching behavior"""
        # Clear cache
        monkeypatch.setattr('inv.utils.config._cached_config', None)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            config = create_default_config()
            save_config(config)
            
            # Load config twice
            config1 = load_config()
            config2 = load_config()
            
            # Should be same object (cached)
            assert config1 is config2
            
            # Force reload
            config3 = load_config(force_reload=True)
            assert config3 is not config1
        finally:
            os.chdir(original_cwd)


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration"""
        config = create_default_config()
        config['database']['url'] = 'sqlite:///test_valid.db'
        
        errors = validate_config_structure(config)
        assert len(errors) == 0
    
    def test_validate_missing_sections(self):
        """Test validation with missing sections"""
        config = {'database': {}}
        
        errors = validate_config_structure(config)
        
        assert any('Missing required section: brand_prefixes' in e for e in errors)
        assert any('Missing required section: defaults' in e for e in errors)
        assert any('Missing required section: photos' in e for e in errors)
    
    def test_validate_invalid_database_config(self):
        """Test validation with invalid database config"""
        config = create_default_config()
        config['database'] = 'not a dict'
        
        errors = validate_config_structure(config)
        assert any('database section must be a dictionary' in e for e in errors)
    
    def test_validate_missing_database_fields(self):
        """Test validation with missing database fields"""
        config = create_default_config()
        del config['database']['url']
        
        errors = validate_config_structure(config)
        assert any('Missing database field: url' in e for e in errors)
    
    def test_validate_empty_database_fields(self):
        """Test validation with empty database fields"""
        config = create_default_config()
        config['database']['url'] = ''
        
        errors = validate_config_structure(config)
        assert any('Empty database field: url' in e for e in errors)
    
    def test_validate_invalid_brand_prefixes(self):
        """Test validation with invalid brand prefixes"""
        config = create_default_config()
        config['brand_prefixes']['nike'] = 'NIKE'  # Too long
        
        errors = validate_config_structure(config)
        assert any("Brand prefix for 'nike' must be exactly 3 characters" in e for e in errors)
    
    def test_validate_invalid_consignment_split(self):
        """Test validation with invalid consignment split"""
        config = create_default_config()
        config['defaults']['consignment_split'] = 150  # Too high
        
        errors = validate_config_structure(config)
        assert any('consignment_split must be an integer between 0 and 100' in e for e in errors)
    
    def test_validate_missing_photos_path(self):
        """Test validation with missing photos storage path"""
        config = create_default_config()
        del config['photos']['storage_path']
        
        errors = validate_config_structure(config)
        assert any('Missing photos.storage_path field' in e for e in errors)
    
    def test_validate_config_file_missing(self, tmp_path):
        """Test validating non-existent config file"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            errors = validate_config_file()
            assert any('Failed to load config file' in e for e in errors)
        finally:
            os.chdir(original_cwd)