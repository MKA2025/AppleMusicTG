import asyncio
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from pathlib import Path
import time

@dataclass
class DownloadItem:
    user_id: int
    track_info: Dict[str, Any]
    status: str = 'pending'
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    file_path: Optional[Path] = None
    error: Optional[str] = None
    retries: int = 0

@dataclass
class DownloadStatus:
    status: str
    progress: float
    message: str
    file_path: Optional[Path] = None
    error: Optional[str] = None

class DownloadManager:
    def __init__(self, max_concurrent: int = 2, max_retries: int = 3):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_status: Dict[int, DownloadStatus] = {}
        self.download_queue: List[DownloadItem] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.download_history: List[DownloadItem] = []

    async def add_download(self, user_id: int, download_info: Dict[str, Any]) -> int:
        """Add download to queue and return position"""
        download_item = DownloadItem(
            user_id=user_id, 
            track_info=download_info
        )
        self.download_queue.append(download_item)
        return len(self.download_queue)

    async def start_download_queue(self):
        """Process download queue"""
        while self.download_queue:
            if len(self.active_downloads) < self.max_concurrent:
                download_item = self.download_queue.pop(0)
                asyncio.create_task(self._process_download(download_item))
            await asyncio.sleep(1)

    async def _process_download(self, download_item: DownloadItem):
        """Process individual download with retry mechanism"""
        try:
            download_item.start_time = time.time()
            download_item.status = 'downloading'

            # Actual download logic would be implemented here
            # For example:
            # file_path = await self._download_track(download_item.track_info)
            # download_item.file_path = file_path

            download_item.end_time = time.time()
            download_item.status = 'completed'
            self.download_history.append(download_item)

        except Exception as e:
            download_item.retries += 1
            download_item.error = str(e)

            if download_item.retries <= self.max_retries:
                # Retry download
                self.download_queue.append(download_item)
            else:
                download_item.status = 'failed'
                self.download_history.append(download_item)

    def get_download_stats(self, user_id: int = None):
        """Get download statistics"""
        if user_id:
            return [item for item in self.download_history if item.user_id == user_id]
        return self.download_history

    def clear_download_history(self, user_id: int = None):
        """Clear download history"""
        if user_id:
            self.download_history = [
                item for item in self.download_history if item.user_id != user_id
            ]
        else:
            self.download_history.clear()

    # Existing methods can remain the same
    async def start_download(self, user_id: int, download_coroutine):
        # Existing implementation
        pass

    def cancel_download(self, user_id: int):
        # Existing implementation
        pass

    def get_status(self, user_id: int) -> Optional[DownloadStatus]:
        # Existing implementation
        pass

    def update_status(self, user_id: int, status: DownloadStatus):
        # Existing implementation
        pass