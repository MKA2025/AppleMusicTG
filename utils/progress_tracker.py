import time
from typing import Callable, Optional

class ProgressTracker:
    def __init__(self, update_callback: Callable = None):
        self.progress_chars = ['⬜️', '⬛️']
        self.start_time = time.time()
        self.last_update_time = 0
        self.update_callback = update_callback
        self.last_bytes = 0
        
    def create_progress_bar(self, current: int, total: int, width: int = 10) -> str:
        """Create a progress bar string"""
        progress = min(current / total if total > 0 else 0, 1.0)
        filled = int(width * progress)
        bar = self.progress_chars[1] * filled + self.progress_chars[0] * (width - filled)
        percentage = progress * 100
        speed = self.calculate_speed(current)
        
        return (
            f"[{bar}] {percentage:.1f}%\n"
            f"📥 {self.format_size(current)}/{self.format_size(total)}\n"
            f"⚡️ {self.format_size(speed)}/s"
        )
        
    def calculate_speed(self, current_bytes: int) -> float:
        """Calculate download speed"""
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        if time_diff >= 1:
            speed = (current_bytes - self.last_bytes) / time_diff
            self.last_bytes = current_bytes
            self.last_update_time = current_time
            return speed
        return 0
        
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}GB"

    async def update_progress(self, current: int, total: int):
        """Update progress and call callback if provided"""
        if self.update_callback:
            progress_text = self.create_progress_bar(current, total)
            await self.update_callback(progress_text)
