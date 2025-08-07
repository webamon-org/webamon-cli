"""Configuration management for Webamon CLI."""

import os
import json
from typing import Optional
from pathlib import Path


class Config:
    """Configuration class for storing API settings."""
    
    def __init__(self, 
                 api_key: Optional[str] = None):
        """Initialize configuration."""
        self.api_key = api_key or os.getenv('WEBAMON_API_KEY')
        
        # Automatically select API URL based on API key presence
        if self.api_key:
            self.api_url = 'https://pro.webamon.com'
        else:
            self.api_url = 'https://search.webamon.com'
    
    @classmethod
    def load(cls, config_file: Optional[str] = None) -> 'Config':
        """Load configuration from file or environment."""
        if config_file:
            config_path = Path(config_file)
        else:
            # Default config locations
            config_path = Path.home() / '.webamon' / 'config.json'
            if not config_path.exists():
                config_path = Path.cwd() / '.webamon.json'
        
        config_data = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                # If config file is corrupted, continue with defaults
                pass
        
        return cls(
            api_key=config_data.get('api_key')
        )
    
    def save(self, config_file: Optional[str] = None) -> None:
        """Save configuration to file."""
        if config_file:
            config_path = Path(config_file)
        else:
            config_dir = Path.home() / '.webamon'
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / 'config.json'
        
        config_data = {
            'api_key': self.api_key
        }
        
        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.api_url and self.api_key)