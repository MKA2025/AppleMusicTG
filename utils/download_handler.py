from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import TelegramLogger
from utils.auth import UserAuthorization
from services.download_service import DownloadService
from utils.helpers import is_valid_apple_music_url

class DownloadHandler:
    def __init__(self, config: dict, logger: TelegramLogger, auth: UserAuthorization):
        self.config = config
        self.logger = logger
        self.auth = auth
        self.download_service = DownloadService(config)

    async def handle_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download command and URLs"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        url = update.message.text

        # Check authorization
        if not await self.auth.check_user_auth(user_id):
            await update.message.reply_text(
                "⚠️ You need to join our channel to use this bot.\n"
                f"Channel: {self.config.get('auth_channel_link')}"
            )
            return

        if not is_valid_apple_music_url(url):
            await update.message.reply_text("❌ Please provide a valid Apple Music URL.")
            return

        # Log download request
        await self.logger.log_download(user_id, user_name, {"url": url})

        try:
            # Start download process
            status_message = await update.message.reply_text("🔄 Processing download...")
            
            download_result = await self.download_service.download(url)
            
            # Send file
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=open(download_result['file_path'], 'rb'),
                title=download_result['title'],
                performer=download_result['artist']
            )

            await status_message.edit_text("✅ Download completed!")
            
            # Log success
            await self.logger.send_log(
                f"Download Successful\n"
                f"User: {user_name} ({user_id})\n"
                f"Track: {download_result['title']}",
                level="SUCCESS"
            )

        except Exception as e:
            await status_message.edit_text(f"❌ Download failed: {str(e)}")
            await self.logger.log_error(e, user_id)
