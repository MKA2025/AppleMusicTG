import asyncio
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DownloadQueue:
    def __init__(self, max_concurrent: int = 3):
        self.queue = asyncio.Queue()
        self.current_downloads: Dict[int, Dict] = {}
        self.max_concurrent = max_concurrent
        
    async def add_to_queue(self, user_id: int, download_info: dict) -> int:
        """Add download to queue and return position"""
        queue_item = {
            'user_id': user_id,
            'info': download_info,
            'timestamp': time.time()
        }
        await self.queue.put(queue_item)
        return self.queue.qsize()
        
    async def start_processing(self):
        """Start processing the download queue"""
        while True:
            try:
                if len(self.current_downloads) < self.max_concurrent:
                    download = await self.queue.get()
                    asyncio.create_task(self.process_download(download))
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(5)

    async def process_download(self, download_info: dict):
        """Process a single download"""
        user_id = download_info['user_id']
        try:
            self.current_downloads[user_id] = download_info
            # Actual download logic would be implemented here
            await asyncio.sleep(1)  # Placeholder for actual download
        finally:
            if user_id in self.current_downloads:
                del self.current_downloads[user_id]
            self.queue.task_done()

    def get_queue_position(self, user_id: int) -> Optional[int]:
        """Get position in queue for user"""
        for i, item in enumerate(self.queue._queue):
            if item['user_id'] == user_id:
                return i + 1
        return None

    def is_user_downloading(self, user_id: int) -> bool:
        """Check if user has active download"""
        return user_id in self.current_downloads
