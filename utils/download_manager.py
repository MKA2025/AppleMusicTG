import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DownloadStatus:
    status: str
    progress: float
    message: str
    file_path: Optional[Path] = None
    error: Optional[str] = None

class DownloadManager:
    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_status: Dict[int, DownloadStatus] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def start_download(self, user_id: int, download_coroutine):
        """Start a new download task"""
        if user_id in self.active_downloads:
            raise DownloadError("User already has an active download")
            
        async with self._semaphore:
            self.download_status[user_id] = DownloadStatus(
                status="starting",
                progress=0.0,
                message="Initializing download..."
            )
            
            task = asyncio.create_task(download_coroutine)
            self.active_downloads[user_id] = task
            
            try:
                await task
            except asyncio.CancelledError:
                self.download_status[user_id] = DownloadStatus(
                    status="cancelled",
                    progress=0.0,
                    message="Download cancelled"
                )
                raise
            except Exception as e:
                self.download_status[user_id] = DownloadStatus(
                    status="error",
                    progress=0.0,
                    message="Download failed",
                    error=str(e)
                )
                raise
            finally:
                self.active_downloads.pop(user_id, None)

    def cancel_download(self, user_id: int):
        """Cancel an active download"""
        if user_id in self.active_downloads:
            self.active_downloads[user_id].cancel()
            return True
        return False

    def get_status(self, user_id: int) -> Optional[DownloadStatus]:
        """Get current download status"""
        return self.download_status.get(user_id)

    def update_status(self, user_id: int, status: DownloadStatus):
        """Update download status"""
        self.download_status[user_id] = status
