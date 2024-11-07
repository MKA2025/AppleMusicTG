import shutil
from pathlib import Path
from typing import Optional
from PIL import Image
import os

class FileManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def save_artwork(self, artwork_data: bytes, path: Path, size: Optional[int] = None) -> Path:
        """Save artwork with optional resizing"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if size:
            # Resize image
            img = Image.open(artwork_data)
            img.thumbnail((size, size))
            img.save(path)
        else:
            # Save original
            path.write_bytes(artwork_data)
            
        return path
        
    def create_m3u_playlist(self, playlist_path: Path, track_paths: list[Path]):
        """Create M3U playlist file"""
        playlist_path.parent.mkdir(parents=True, exist_ok=True)
        with playlist_path.open('w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for track_path in track_paths:
                rel_path = os.path.relpath(track_path, playlist_path.parent)
                f.write(f'{rel_path}\n')
                
    def cleanup_temp_files(self, temp_dir: Path):
        """Clean up temporary files and directories"""
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            
    def get_free_space(self) -> int:
        """Get free space in bytes"""
        return shutil.disk_usage(self.base_dir).free
