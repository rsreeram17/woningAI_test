"""Configuration management for the API testing framework."""

import os
import yaml
from typing import Dict, Any, List
from dotenv import load_dotenv

class Config:
    """Central configuration management."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize configuration from file and environment variables."""
        load_dotenv()  # Load .env file

        self.config_file = config_file
        self._config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Replace environment variables
            config['apis']['bag']['api_key'] = os.getenv('BAG_API_KEY')
            config['apis']['dso']['api_key'] = os.getenv('DSO_API_KEY')

            # Set environment-specific URLs
            environment = os.getenv('ENVIRONMENT', 'production')
            if environment == 'production':
                config['apis']['dso']['base_url'] = config['apis']['dso']['production_url']
            else:
                config['apis']['dso']['base_url'] = config['apis']['dso']['preproduction_url']

            return config

        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")

    def _validate_config(self):
        """Validate configuration has required values."""
        required_keys = [
            'apis.bag.api_key',
            'apis.dso.api_key',
            'test_addresses',
            'renovation_scenarios'
        ]

        for key in required_keys:
            if not self._get_nested_value(key):
                raise ValueError(f"Missing required configuration: {key}")

        # Check if we have test addresses
        if not self.get_test_addresses():
            raise ValueError("No test addresses configured")

        # Check if we have renovation scenarios
        if not self.get_renovation_scenarios():
            raise ValueError("No renovation scenarios configured")

    def _get_nested_value(self, key_path: str) -> Any:
        """Get nested configuration value using dot notation."""
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def get_bag_config(self) -> Dict[str, Any]:
        """Get BAG API configuration."""
        return self._config['apis']['bag']

    def get_dso_config(self) -> Dict[str, Any]:
        """Get DSO API configuration."""
        return self._config['apis']['dso']

    def get_test_addresses(self) -> List[Dict[str, Any]]:
        """Get list of test addresses."""
        return self._config['test_addresses']

    def get_renovation_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of renovation scenarios."""
        return self._config['renovation_scenarios']

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get('logging', {})

    def get_testing_config(self) -> Dict[str, Any]:
        """Get testing configuration."""
        return self._config.get('testing', {})

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    def get_log_level(self) -> str:
        """Get logging level."""
        return os.getenv('LOG_LEVEL', 'INFO')

def load_config() -> Config:
    """Load and return configuration instance."""
    return Config()

# Global configuration instance
config = load_config()