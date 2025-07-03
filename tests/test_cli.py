"""Test CLI commands"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner

from inv.cli import cli, setup, test_connection
from inv.utils.config import create_default_config


class TestCLICommands:
    """Test CLI command functionality"""
    
    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Streetwear Inventory Management CLI' in result.output
        assert 'setup' in result.output
        assert 'test-connection' in result.output
    
    def test_setup_command_help(self):
        """Test setup command help"""
        runner = CliRunner()
        result = runner.invoke(setup, ['--help'])
        
        assert result.exit_code == 0
        assert 'Interactive setup wizard' in result.output
    
    def test_test_connection_help(self):
        """Test test-connection command help"""
        runner = CliRunner()
        result = runner.invoke(test_connection, ['--help'])
        
        assert result.exit_code == 0
        assert 'Test database connection' in result.output
    
    def test_test_connection_no_config(self, monkeypatch):
        """Test test-connection without config file"""
        # Clear config cache
        monkeypatch.setattr('inv.utils.config._cached_config', None)
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            os.chdir(tmp_dir)
            
            try:
                result = runner.invoke(test_connection)
                assert result.exit_code == 1
                assert 'Configuration file not found' in result.output
            finally:
                os.chdir(original_cwd)