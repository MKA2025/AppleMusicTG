from telegram import Update
from telegram.ext import ContextTypes
from services.apple_music_service import AppleMusicService
from services.download_service import DownloadService
from utils.helpers import is_valid_apple_music_url, extract_track_id

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /download command and Apple Music URLs"""
    url = update.message.text

    if not is_valid_apple_music_url(url):
        await update.message.reply_text("Please provide a valid Apple Music URL.")
        return

    track_id = extract_track_id(url)
    
    apple_music_service = AppleMusicService()
    download_service = DownloadService()

    try:
        track_info = await apple_music_service.get_track_info(track_id)
        download_url = await apple_music_service.get_download_url(track_id)
        
        await update.message.reply_text(f"Starting download: {track_info['name']} by {track_info['artist']}")
        
        file_path = await download_service.download_track(download_url, track_info)
        
        await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=open(file_path, 'rb'),
            title=track_info['name'],
            performer=track_info['artist']
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
