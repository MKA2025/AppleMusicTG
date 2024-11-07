import asyncio
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MediaAnalysisError(Exception):
    pass

class MediaAnalyzer:
    def __init__(self, ffprobe_path: str = "ffprobe"):
        self.ffprobe_path = ffprobe_path
        
    async def analyze_media(self, file_path: str) -> Dict:
        """Analyze media file and return detailed information"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise MediaAnalysisError(f"Analysis failed: {stderr.decode()}")
                
            return json.loads(stdout.decode())
        except Exception as e:
            logger.error(f"Media analysis error: {str(e)}")
            raise MediaAnalysisError(str(e))
            
    def get_audio_info(self, media_info: Dict) -> Dict:
        """Extract audio-specific information"""
        try:
            audio_streams = [
                s for s in media_info['streams'] 
                if s['codec_type'] == 'audio'
            ]
            if not audio_streams:
                return {}
                
            stream = audio_streams[0]
            return {
                'codec': stream['codec_name'],
                'bitrate': stream.get('bit_rate'),
                'sample_rate': stream.get('sample_rate'),
                'channels': stream.get('channels'),
                'duration': stream.get('duration')
            }
        except KeyError:
            return {}
