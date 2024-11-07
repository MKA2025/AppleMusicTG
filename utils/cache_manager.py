import json
import time
from pathlib import Path
from typing import Any, Optional

class CacheManager:
    def __init__(self, cache_dir: Path, max_age: int = 3600):
        self.cache_dir = cache_dir
        self.max_age = max_age
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"
        
    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
            
        try:
            data = json.loads(cache_path.read_text())
            if time.time() - data["timestamp"] > self.max_age:
                cache_path.unlink()
                return None
            return data["value"]
        except (json.JSONDecodeError, KeyError):
            cache_path.unlink()
            return None
            
    def set(self, key: str, value: Any):
        cache_path = self._get_cache_path(key)
        data = {
            "timestamp": time.time(),
            "value": value
        }
        cache_path.write_text(json.dumps(data))
        
    def clear(self):
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
