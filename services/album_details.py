import asyncio
import logging
import aiohttp
import uuid
from typing import Dict, Optional

class AppleMusicService:
    def __init__(self, api_key: str):
        self.base_url = "https://api.music.apple.com/v1"
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Music-User-Token': 'your_user_token'
        }

    async def get_album_details(self, album_id: str) -> Dict:
        """
        Fetch detailed album information from Apple Music API
        
        :param album_id: Unique identifier for the album
        :return: Comprehensive album metadata
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/catalog/us/albums/{album_id}", 
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"API Error: {response.status}")
            except Exception as e:
                logging.error(f"Album fetch error: {e}")
                raise

class AlbumDetailsFormatter:
    @staticmethod
    async def format_album_details(album_data: Dict, user_info: Dict) -> Dict:
        """
        Format album details into a readable format
        
        :param album_data: Raw album metadata
        :param user_info: User request information
        :return: Formatted album details
        """
        try:
            attributes = album_data['attributes']
            
            # Cover art preparation
            cover_url = attributes['artwork']['url'].replace(
                '{w}x{h}', '1200x1200'
            )
            
            # Duration calculation
            total_tracks = attributes.get('trackCount', 0)
            total_duration_ms = sum([
                track.get('attributes', {}).get('durationInMillis', 0) 
                for track in album_data.get('relationships', {}).get('tracks', {}).get('data', [])
            ])
            total_duration_minutes = total_duration_ms / (1000 * 60)
            
            # Detailed album information
            album_details = (
                f"🎵 Album: {attributes['name']}\n"
                f"👤 Artist: {attributes['artistName']}\n"
                f"📅 Release Date: {attributes['releaseDate']}\n"
                f"🎼 Total Tracks: {total_tracks}\n"
                f"⏱️ Total Duration: {total_duration_minutes:.2f} minutes\n"
                f"🏷️ Genre: {', '.join(attributes.get('genreNames', ['Unknown']))}\n"
                f"🔒 Explicit: {'Yes' if attributes.get('contentRating') == 'explicit' else 'No'}\n"
                f"💿 Record Label: {attributes.get('recordLabel', 'Unknown')}\n"
                f"🆔 Album ID: {album_data['id']}"
            )
            
            return {
                'text': album_details,
                'cover_url': cover_url
            }
        
        except Exception as e:
            logging.error(f"Album details formatting error: {e}")
            raise

class CoverDownloader:
    @staticmethod
    async def download_cover(url: str) -> Optional[str]:
        """
        Download album cover image
        
        :param url: Cover image URL
        :return: Path to downloaded image or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Generate unique filename
                        filename = f"temp_cover_{uuid.uuid4()}.jpg"
                        
                        with open(filename, 'wb') as f:
                            f.write(await response.read())
                        
                        return filename
        except Exception as e:
            logging.error(f"Cover download error: {e}")
        
        return None

class TelegramAlbumHandler:
    def __init__(self, bot, apple_music_service):
        self.bot = bot
        self.apple_music_service = apple_music_service

    async def handle_album_command(self, update, context):
        """
        Handle album details command
        
        :param update: Telegram update object
        :param context: Telegram context
        """
        try:
            # Extract album ID from command
            if len(context.args) < 1:
                await update.message.reply_text(
                    "Please provide an Apple Music album ID or URL"
                )
                return

            album_id = self.extract_album_id(context.args[0])
            
            # Fetch album details
            album_data = await self.apple_music_service.get_album_details(album_id)
            
            # Format album details
            details = await AlbumDetailsFormatter.format_album_details(
                album_data['data'][0], 
                update.effective_user.to_dict()
            )
            
            # Download cover
            cover_path = await CoverDownloader.download_cover(details['cover_url'])
            
            # Send album details
            if cover_path:
                await update.message.reply_photo(
                    photo=cover_path,
                    caption=details['text']
                )
            else:
                await update.message.reply_text(details['text'])
        
        except Exception as e:
            logging.error(f"Album command error: {e}")
            await update.message.reply_text(
                "Failed to fetch album details. Please try again."
            )

    def extract_album_id(self, input_text: str) -> str:
        """
        Extract album ID from various input formats
        
        :param input_text: Album URL or ID
        :return: Extracted album ID
        """
        # Handle Apple Music URLs
        if 'music.apple.com' in input_text:
            parts = input_text.split('/')
            return parts[-1].split('?')[0]
        
        # Assume direct album ID
        return input_text

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Main Initialization Function
async def main():
    # Initialize services
    apple_music_service = AppleMusicService('YOUR_APPLE_MUSIC_API_KEY')
    
    # Setup Telegram bot
    application = Application.builder().token('YOUR_TELEGRAM_BOT_TOKEN').build()
    
    # Create album handler
    album_handler = TelegramAlbumHandler(application.bot, apple_music_service)
    
    # Add command handler
    application.add_handler(CommandHandler('album', album_handler.handle_album_command))
    
    # Start the bot
    await application.run_polling(drop_pending_updates=True)

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())