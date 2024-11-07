from telegram import Update
from telegram.ext import ContextTypes
from utils.download_manager import DownloadManager

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /cancel command"""
    user_id = update.effective_user.id
    
    if DownloadManager.cancel_download(user_id):
        await update.message.reply_text("Your current download has been cancelled.")
    else:
        await update.message.reply_text("You don't have any active downloads to cancel.")
