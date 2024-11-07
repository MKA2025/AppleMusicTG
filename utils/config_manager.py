import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
