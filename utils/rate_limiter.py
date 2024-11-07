import time
import asyncio
from typing import Dict, Optional

class RateLimiter:
    def __init__(self, max_calls: int, time_frame: float):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.calls: Dict[str, list] = {}

    async def wait(self, key: str = "default"):
        now = time.monotonic()
        
        if key not in self.calls:
            self.calls[key] = []

        self.calls[key] = [t for t in self.calls[key] if now - t < self.time_frame]

        if len(self.calls[key]) >= self.max_calls:
            sleep_time = self.time_frame - (now - self.calls[key][0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.calls[key].append(time.monotonic())
