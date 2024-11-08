# services/download_service.py
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import os

class DownloadProgress:
    def __init__(self, track_id: str, total_size: int):
        self.track_id = track_id
        self.total_size = total_size
        self.downloaded_size = 0
        self.start_time = time.time()
        self.status = "pending"
        self.attempts = 0
        self.error = None

class DownloadService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.download_dir = Path(config.get('download_path', './downloads'))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)
        
        # Progress tracking
        self.download_progresses: Dict[str, DownloadProgress] = {}

    async def download_track(
        self, 
        track_info: Dict[str, Any], 
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download track with advanced progress tracking and retry mechanism
        """
        track_id = track_info['id']
        
        # Initialize progress tracking
        progress = DownloadProgress(
            track_id, 
            track_info.get('file_size', 0)
        )
        self.download_progresses[track_id] = progress

        try:
            return await self._download_with_retry(
                track_info, 
                progress, 
                on_progress
            )
        except Exception as e:
            self._handle_final_download_failure(progress, e)
            raise

    async def _download_with_retry(
        self, 
        track_info: Dict[str, Any], 
        progress: DownloadProgress,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download with retry mechanism and progress tracking
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                progress.attempts = attempt
                progress.status = "downloading"
                
                result = await self._download_file(
                    track_info, 
                    progress, 
                    on_progress
                )
                
                progress.status = "completed"
                return result
            
            except Exception as e:
                self.logger.warning(
                    f"Download attempt {attempt} failed: {e}"
                )
                
                progress.error = str(e)
                progress.status = "failed"
                
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
        
        raise Exception("Max retries exceeded")

    async def _download_file(
        self, 
        track_info: Dict[str, Any], 
        progress: DownloadProgress,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Actual file download with progress tracking
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(track_info['download_url']) as response:
                response.raise_for_status()
                
                filename = self._generate_filename(track_info)
                file_path = self.download_dir / filename
                
                total_size = int(response.headers.get('content-length', 0))
                progress.total_size = total_size
                
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 10):
                        f.write(chunk)
                        
                        progress.downloaded_size += len(chunk)
                        
                        if on_progress:
                            await on_progress(
                                progress.track_id, 
                                progress.downloaded_size, 
                                total_size
                            )
                
                download_time = time.time() - progress.start_time
                download_speed = (
                    progress.downloaded_size / download_time 
                    if download_time > 0 else 0
                )
                
                return {
                    'file_path': str(file_path),
                    'filename': filename,
                    'track_id': progress.track_id,
                    'download_time': download_time,
                    'file_size': progress.downloaded_size,
                    'download_speed': download_speed
                }

    def _generate_filename(self, track_info: Dict[str, Any]) -> str:
        """
        Generate unique and safe filename
        """
        artist = self._sanitize_filename(track_info.get('artist', 'Unknown'))
        title = self._sanitize_filename(track_info.get('title', 'Unknown Track'))
        
        timestamp = int(time.time())
        return f"{artist} - {title}_{timestamp}.mp3"

    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove invalid characters from filename
        """
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()

    def _handle_final_download_failure(
        self, 
        progress: DownloadProgress, 
        error: Exception
    ):
        """
        Handle final download failure after all retries
        """
        progress.status = "failed"
        progress.error = str(error)
        
        self.logger.critical(
            f"Download failed for track {progress.track_id}: {error}"
        )

    def get_download_progress(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve download progress for a specific track
        """
        progress = self.download_progresses.get(track_id)
        if progress:
            return {
                'track_id': track_id,
                'status': progress.status,
                'downloaded_size': progress.downloaded_size,
                'total_size': progress.total_size,
                'progress_percentage': (
                    (progress.downloaded_size / progress.total_size * 100) 
                    if progress.total_size > 0 else 0
                ),
                'attempts': progress.attempts,
                'error': progress.error
            }
        return None

    async def bulk_download(
        self, 
        tracks: List[Dict[str, Any]], 
        on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Download multiple tracks concurrently
        """
        download_tasks = [
            self.download_track(track, on_progress) 
            for track in tracks
        ]
        
        return await asyncio.gather(*download_tasks, return_exceptions=True)

# Callback function example
async def progress_callback(track_id: str, downloaded: int, total: int):
    progress_percentage = (downloaded / total * 100) if total > 0 else 0
    print(f"Track {track_id} Progress: {progress_percentage:.2f}%")

# Usage example
async def main():
    config = {
        'download_path': './downloads',
        'max_retries': 3,
        'retry_delay': 5
    }

    download_service = DownloadService(config)

    tracks = [
        {
            'id': 'track1',
            'title': 'Song 1',
            'artist': 'Artist 1',
            'download_url': 'https://example.com/track1.mp3'
        },
        {
            'id': 'track2',
            'title': 'Song 2',
            'artist': 'Artist 2', 
            'download_url': 'https://example.com/track2.mp3'
        }
    ]

    try:
        # Bulk download with progress tracking
        results = await download_service.bulk_download(
            tracks, 
            on_progress=progress_callback
        )

        for result in results:
            if isinstance(result, dict):
                print(f"Successfully downloaded: {result['filename']}")
            else:
                print(f"Download failed: {result}")

    except Exception as e:
        print(f"Bulk download error: {e}")

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())