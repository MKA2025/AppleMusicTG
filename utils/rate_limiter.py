import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class RateLimit:
    max_requests: int
    time_window: int  # seconds
    requests: list[float] = None
    
    
