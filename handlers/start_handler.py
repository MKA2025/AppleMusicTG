from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n\n"
        "Welcome to the Apple Music Downloader Bot. "
        "Use /download to start downloading music, "
        "/settings to configure bot settings, "
        "and /status to check your current download status."
    )
