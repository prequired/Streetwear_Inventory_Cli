"""Database initialization utilities for CLI commands"""

import functools
import click
from ..database.connection import db
from .config import get_config


def with_database(func):
    """Decorator to ensure database is initialized before command execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Initialize database connection
            config = get_config()
            db.initialize(config)
            
            # Call the original function
            return func(*args, **kwargs)
            
        except FileNotFoundError:
            click.echo("❌ Configuration file not found. Run 'inv setup' first.")
            return
        except Exception as e:
            click.echo(f"❌ Database initialization error: {e}")
            return
    
    return wrapper