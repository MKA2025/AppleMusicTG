import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

def load_config(config_path: str = "config/config.json") -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        validate_config(config)
        return config
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError:
        raise ConfigError(f"Invalid JSON in configuration file: {config_path}")

def validate_config(config: Dict):
    """Validate configuration structure"""
    required_keys = ['bot_token', 'admin_users', 'regions', 'download_settings']
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required configuration key: {key}")

def validate_region(region: str, config: Dict) -> bool:
    """Check if region is valid"""
    return region.lower() in config['regions']

def get_region_config(region: str, config: Dict) -> Dict:
    """Get region specific configuration"""
    return config['regions'].get(region.lower(), {})

def is_admin_user(user_id: int, config: Dict) -> bool:
    """Check if user is an admin"""
    return user_id in config['admin_users']

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def get_download_path(config: Dict) -> Path:
    """Get and create download directory"""
    path = Path(config['download_settings']['output_path'])
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_temp_path(config: Dict) -> Path:
    """Get and create temporary directory"""
    path = Path(config['download_settings']['temp_path'])
    path.mkdir(parents=True, exist_ok=True)
    return path

def clean_filename(filename: str) -> str:
    """Clean filename from invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS format"""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

def get_current_time() -> str:
    """Get current time in formatted string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
