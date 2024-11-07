import time
from typing import Optional, Callable
from dataclasses import dataclass

@dataclass
class ProgressInfo:
    current: int
    total: int
    speed: float  # bytes per second
    eta: int      # seconds
    message: str

class ProgressTracker:
    def __init__(self, callback: Callable[[ProgressInfo], None], interval: int = 1):
        self.callback = callback
        self.interval = interval
        self.start_time = time.time()
        self.last_update = 0
        self.last_current = 0
        
    def update(self, current: int, total: int, message: Optional[str] = None):
        now = time.time()
        if now - self.last_update >= self.interval:
            # Calculate speed
            time_diff = now - self.last_update
            size_diff = current - self.last_current
            speed = size_diff / time_diff if time_diff > 0 else 0
            
            # Calculate ETA
            remaining_size = total - current
            eta = int(remaining_size / speed) if speed > 0 else 0
            
            # Create progress info
            progress = ProgressInfo(
                current=current,
                total=total,
                speed=speed,
                eta=eta,
                message=message or "Downloading..."
            )
            
            # Call callback
            self.callback(progress)
            
            # Update last values
            self.last_update = now
            self.last_current = current
