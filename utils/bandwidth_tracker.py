import asyncio
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class BandwidthRecord:
    timestamp: float = field(default_factory=time.time)
    bytes_transferred: int = 0
    duration: float = 0.0

class BandwidthTracker:
    def __init__(
        self, 
        window_size: int = 60,  # Default window size in seconds
        max_records: int = 100
    ):
        self.window_size = window_size
        self.max_records = max_records
        self.user_bandwidth_records: Dict[int, List[BandwidthRecord]] = {}
        self.global_bandwidth_records: List[BandwidthRecord] = []

    def _prune_old_records(self, records: List[BandwidthRecord], current_time: float):
        """Remove records older than the specified window size."""
        cutoff_time = current_time - self.window_size
        return [record for record in records if record.timestamp >= cutoff_time]

    def record_bandwidth(
        self, 
        user_id: Optional[int] = None, 
        bytes_transferred: int = 0, 
        duration: float = 0.0
    ):
        """
        Record bandwidth usage for a specific user or globally.
        
        :param user_id: Optional user ID to track individual bandwidth
        :param bytes_transferred: Number of bytes transferred
        :param duration: Time taken for transfer
        """
        current_time = time.time()
        record = BandwidthRecord(
            timestamp=current_time,
            bytes_transferred=bytes_transferred,
            duration=duration
        )

        # Record global bandwidth
        self.global_bandwidth_records.append(record)
        self.global_bandwidth_records = self._prune_old_records(
            self.global_bandwidth_records, 
            current_time
        )

        # Record user-specific bandwidth if user_id is provided
        if user_id is not None:
            if user_id not in self.user_bandwidth_records:
                self.user_bandwidth_records[user_id] = []
            
            self.user_bandwidth_records[user_id].append(record)
            self.user_bandwidth_records[user_id] = self._prune_old_records(
                self.user_bandwidth_records[user_id], 
                current_time
            )

            # Limit number of records
            if len(self.user_bandwidth_records[user_id]) > self.max_records:
                self.user_bandwidth_records[user_id] = self.user_bandwidth_records[user_id][-self.max_records:]

    def calculate_bandwidth(
        self, 
        user_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate bandwidth usage for a specific user or globally.
        
        :param user_id: Optional user ID to calculate individual bandwidth
        :return: Dictionary with bandwidth statistics
        """
        current_time = time.time()
        
        # Select the appropriate records
        records = (
            self.user_bandwidth_records.get(user_id, []) 
            if user_id is not None 
            else self.global_bandwidth_records
        )

        # Prune old records
        records = self._prune_old_records(records, current_time)

        if not records:
            return {
                'total_bytes': 0,
                'transfer_rate': 0.0,
                'average_speed': 0.0
            }

        # Calculate total bytes and duration
        total_bytes = sum(record.bytes_transferred for record in records)
        total_duration = current_time - records[0].timestamp

        # Calculate transfer rate (bytes per second)
        transfer_rate = total_bytes / (total_duration or 1)

        # Calculate average speed
        average_speed = total_bytes / (sum(record.duration for record in records) or 1)

        return {
            'total_bytes': total_bytes,
            'transfer_rate': transfer_rate,
            'average_speed': average_speed
        }

    def get_top_bandwidth_users(self, top_n: int = 5) -> List[Dict]:
        """
        Get top users by bandwidth usage.
        
        :param top_n: Number of top users to return
        :return: List of users sorted by bandwidth usage
        """
        user_bandwidth = []
        
        for user_id, records in self.user_bandwidth_records.items():
            bandwidth_stats = self.calculate_bandwidth(user_id)
            user_bandwidth.append({
                'user_id': user_id,
                'total_bytes': bandwidth_stats['total_bytes'],
                'transfer_rate': bandwidth_stats['transfer_rate']
            })
        
        # Sort users by total bytes transferred in descending order
        return sorted(
            user_bandwidth, 
            key=lambda x: x['total_bytes'], 
            reverse=True
        )[:top_n]

    def reset_bandwidth_tracking(self, user_id: Optional[int] = None):
        """
        Reset bandwidth tracking for a specific user or globally.
        
        :param user_id: Optional user ID to reset individual tracking
        """
        if user_id is None:
            # Reset global tracking
            self.global_bandwidth_records = []
        else:
            # Reset user-specific tracking
            if user_id in self.user_bandwidth_records:
                del self.user_bandwidth_records[user_id]

    async def monitor_bandwidth(self, interval: int = 5):
        """
        Async method to continuously monitor and log bandwidth usage.
        
        :param interval: Interval between bandwidth checks in seconds
        """
        try:
            while True:
                # Log global bandwidth
                global_stats = self.calculate_bandwidth()
                logger.info(f"Global Bandwidth Usage: {global_stats}")

                # Log top bandwidth users
                top_users = self.get_top_bandwidth_users()
                logger.info(f"Top Bandwidth Users: {top_users}")

                # Wait for specified interval
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Bandwidth monitoring stopped.")

# Example Usage
async def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create BandwidthTracker instance
    bandwidth_tracker = BandwidthTracker(
        window_size=60,  # 1-minute window
        max_records=100
    )

    # Simulate bandwidth usage
    def simulate_download(user_id: int, bytes_transferred: int):
        bandwidth_tracker.record_bandwidth(
            user_id=user_id,
            bytes_transferred=bytes_transferred,
            duration=1.0
        )

    # Simulate downloads for different users
    simulate_download(1, 1024 * 1024)  # 1 MB for user 1
    simulate_download(2, 2 * 1024 * 1024)  # 2 MB for user 2
    simulate_download(3, 500 * 1024)  # 500 KB for user 3

    # Calculate and display bandwidth
    print("User 1 Bandwidth:", bandwidth_tracker.calculate_bandwidth(user_id=1))
    print("Global Bandwidth:", bandwidth_tracker.calculate_bandwidth())
    print("Top Bandwidth Users:", bandwidth_tracker.get_top_bandwidth_users())

    # Optional: Start continuous bandwidth monitoring
    monitor_task = asyncio.create_task(bandwidth_tracker.monitor_bandwidth())

    # Run for a short time
    await asyncio.sleep(10)

    # Cancel monitoring
    monitor_task.cancel()

# Run the example
if __name__ == "__main__":
    asyncio.run(main())