import json
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    config_path = Path("config/config.json")
    if not config_path.exists():
        raise FileNotFoundError("config.json not found")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_region(region: str) -> bool:
    """Validate if region exists in config"""
    config = load_config()
    return region.lower() in config["regions"]

def get_region_config(region: str) -> Dict[str, Any]:
    """Get configuration for specific region"""
    config = load_config()
    return config["regions"].get(region.lower())

def is_admin_user(user_id: int) -> bool:
    """Check if user is admin"""
    config = load_config()
    return user_id in config["admin_users"]

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
