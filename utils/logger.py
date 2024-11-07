import logging
from telegram import Bot
from typing import Optional
from pathlib import Path

class TelegramLogger:
    def __init__(self, bot: Bot, log_channel_id: Optional[int] = None):
        self.bot = bot
        self.log_channel_id = log_channel_id
        self.logger = logging.getLogger(__name__)

        # Configure file logging
        log_file = Path("logs/bot.log")
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)

    async def send_log(self, message: str, level: str = "INFO"):
        """Send log message to Telegram channel"""
        if not self.log_channel_id:
            return

        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "DOWNLOAD": "⬇️"
        }
        
        try:
            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=f"{emoji_map.get(level, 'ℹ️')} {level}\n\n{message}",
                disable_notification=level == "INFO"
            )
        except Exception as e:
            self.logger.error(f"Failed to send log: {e}")

    async def log_download(self, user_id: int, user_name: str, track_info: dict):
        """Log download information"""
        log_message = (
            f"Download Started\n"
            f"User: {user_name} ({user_id})\n"
            f"Track: {track_info.get('name', 'Unknown')}\n"
            f"Artist: {track_info.get('artist', 'Unknown')}"
        )
        await self.send_log(log_message, "DOWNLOAD")
        self.logger.info(f"Download started by user {user_id}: {track_info.get('name')}")

    async def log_error(self, error: Exception, user_id: Optional[int] = None):
        """Log error information"""
        error_msg = (
            f"Error Occurred\n"
            f"Type: {type(error).__name__}\n"
            f"Message: {str(error)}"
        )
        if user_id:
            error_msg += f"\nUser ID: {user_id}"
            
        await self.send_log(error_msg, "ERROR")
        self.logger.error(f"Error for user {user_id}: {str(error)}")
