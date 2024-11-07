import os
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

class FileManager:
    def __init__(self, config: dict):
        self.config = config
        self.output_path = Path(config['download_settings']['output_path'])
        self.temp_path = Path(config['download_settings']['temp_path'])
        self.auto_delete = config['download_settings'].get('auto_delete', False)
        self.delete_delay = config['download_settings'].get('delete_delay', 300)
        
        # Create necessary directories
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

    async def schedule_delete(self, file_path: Path):
        """Schedule file deletion after configured delay"""
        if self.auto_delete:
            try:
                await asyncio.sleep(self.delete_delay)
                self.delete_file(file_path)
            except Exception as e:
                print(f"Error in scheduled deletion of {file_path}: {e}")

    def delete_file(self, file_path: Path):
        """Delete a single file"""
        try:
            if file_path.exists():
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

    def cleanup_temp(self):
        """Clean up temporary directory"""
        try:
            if self.temp_path.exists():
                shutil.rmtree(self.temp_path)
                self.temp_path.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Error cleaning temp directory: {e}")

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except Exception:
            return 0

    def get_free_space(self) -> int:
        """Get free space in bytes"""
        return shutil.disk_usage(self.output_path).free

    def is_safe_path(self, path: Path) -> bool:
        """Check if path is safe (within output directory)"""
        try:
            return path.resolve().is_relative_to(self.output_path)
        except Exception:
            return False
