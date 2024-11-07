import logging
from telegram import Bot
from typing import Optional

class TelegramLogger:
    def __init__(self, bot: Bot, log_channel_id: Optional[int] = None):
        self.bot = bot
        self.log_channel_id = log_channel_id
        self.logger = logging.getLogger(__name__)

    async def send_log(self, message: str, level: str = "INFO"):
        """Send log message to Telegram channel"""
        if not self.log_channel_id:
            return

        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅"
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
        await self.send_log(
            f"Download Started\n"
            f"User: {user_name} ({user_id})\n"
            f"Track: {track_info.get('name')}\n"
            f"Artist: {track_info.get('artist')}"
        )

    async def log_error(self, error: Exception, user_id: Optional[int] = None):
        """Log error information"""
        error_msg = (
            f"Error Occurred\n"
            f"Type: {type(error).__name__}\n"
            f"Message: {str(error)}"
        )
        if user_id:
            error_msg += f"\nUser ID: {user_id}"
            
        await self.send_log(error_msg, level="ERROR")
