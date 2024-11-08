import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DownloadTracker:
    def __init__(self):
        self.downloads: Dict[int, DownloadStatus] = {}

    def start_download(self, user_id: int, total_size: int):
        """Start tracking a download for a user."""
        if user_id in self.downloads:
            logger.warning(f"User  {user_id} already has an active download.")
            return

        self.downloads[user_id] = DownloadStatus(total_size)
        logger.info(f"Download started for user {user_id}. Total size: {total_size} bytes.")

    def update_progress(self, user_id: int, bytes_downloaded: int):
        """Update the progress of a user's download."""
        if user_id not in self.downloads:
            logger.warning(f"User  {user_id} does not have an active download.")
            return

        download_status = self.downloads[user_id]
        download_status.bytes_downloaded += bytes_downloaded
        download_status.last_update_time = time.time()
        logger.info(f"User  {user_id}: Download progress updated. Bytes downloaded: {download_status.bytes_downloaded}/{download_status.total_size}.")

        if download_status.is_complete():
            self.complete_download(user_id)

    def complete_download(self, user_id: int):
        """Mark a user's download as complete."""
        if user_id not in self.downloads:
            logger.warning(f"User  {user_id} does not have an active download.")
            return

        download_status = self.downloads.pop(user_id)
        logger.info(f"Download completed for user {user_id}. Total size: {download_status.total_size} bytes.")

    def get_status(self, user_id: int) -> Optional[Dict[str, int]]:
        """Get the current download status for a user."""
        if user_id not in self.downloads:
            logger.warning(f"User  {user_id} does not have an active download.")
            return None
        
        download_status = self.downloads[user_id]
        return {
            'total_size': download_status.total_size,
            'bytes_downloaded': download_status.bytes_downloaded,
            'progress': download_status.get_progress(),
            'last_update_time': download_status.last_update_time
        }

@dataclass
class DownloadStatus:
    total_size: int
    bytes_downloaded: int = 0
    last_update_time: float = field(default_factory=time.time)

    def get_progress(self) -> float:
        """Calculate the download progress percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.bytes_downloaded / self.total_size) * 100

    def is_complete(self) -> bool:
        """Check if the download is complete."""
        return self.bytes_downloaded >= self.total_size

# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tracker = DownloadTracker()
    user_id = 1
    total_size = 1000  # Total size in bytes

    # Start download
    tracker.start_download(user_id, total_size)

    # Simulate download progress
    for _ in range(5):
        time.sleep(1)  # Simulate time delay
        tracker.update_progress(user_id, 200)  # Update with 200 bytes downloaded

    # Check status
    status = tracker.get_status(user_id)
    print(status)

    # Complete download
    tracker.complete_download(user_id)