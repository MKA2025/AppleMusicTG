import aiohttp
from config import Config

class AppleMusicService:
    def __init__(self):
        self.api_base_url = "https://api.music.apple.com/v1"
        self.developer_token = Config.APPLE_MUSIC_TOKEN

    async def get_track_info(self, track_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.developer_token}"}
            url = f"{self.api_base_url}/catalog/us/songs/{track_id}"
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                track = data['data'][0]['attributes']
                
                return {
                    'id': track_id,
                    'name': track['name'],
                    'artist': track['artistName'],
                    'album': track['albumName
