from telegram import Update
from telegram.ext import ContextTypes
from utils.download_manager import DownloadManager

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command"""
    user_id = update.effective_user.id
    download_status = DownloadManager.get_status(user_id)
    
    if download_status:
        await update.message.reply_text(
            f"Current download status:\n"
            f"Progress: {download_status.progress:.2f}%\n"
            f"Status: {download_status.status}\n"
            f"Message: {download_status.message}"
        )
    else:
        await update.message.reply_text("You don't have any active downloads.")
