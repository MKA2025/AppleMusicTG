import sqlite3
from datetime import datetime
from typing import Dict, List

class UserStats:
    def __init__(self, db_path: str = "data/user_stats.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    track_id TEXT,
                    track_name TEXT,
                    download_date DATETIME,
                    success BOOLEAN,
                    file_size INTEGER,
                    duration INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_seen DATETIME,
                    last_active DATETIME
                )
            """)
    
    async def log_download(self, user_id: int, track_info: Dict, success: bool):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO downloads 
                (user_id, track_id, track_name, download_date, success, file_size, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                track_info.get('id'),
                track_info.get('name'),
                datetime.now(),
                success,
                track_info.get('size'),
                track_info.get('duration')
            ))
    
    async def get_user_stats(self, user_id: int) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total successful downloads
            total = cursor.execute("""
                SELECT COUNT(*) FROM downloads 
                WHERE user_id = ? AND success = 1
            """, (user_id,)).fetchone()[0]
            
            # Get total downloaded size
            total_size = cursor.execute("""
                SELECT SUM(file_size) FROM downloads
                WHERE user_id = ? AND success = 1
            """, (user_id,)).fetchone()[0] or 0
            
            # Get recent downloads
            recent = cursor.execute("""
                SELECT track_name, download_date 
                FROM downloads
                WHERE user_id = ? AND success = 1
                ORDER BY download_date DESC LIMIT 5
            """, (user_id,)).fetchall()
            
            return {
                'total_downloads': total,
                'total_size': total_size,
                'recent_downloads': recent
            }
