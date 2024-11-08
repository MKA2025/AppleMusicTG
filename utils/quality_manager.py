import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

class AudioQuality(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"
    DOLBY_ATMOS = "dolby_atmos"

class VideoQuality(enum.Enum):
    SD = "480p"
    HD = "720p"
    FULL_HD = "1080p"
    QHD = "1440p"
    UHD = "2160p"

@dataclass
class QualityProfile:
    name: str
    audio_bitrate: int
    audio_sample_rate: int
    audio_channels: int
    video_resolution: Optional[str] = None
    video_codec: Optional[str] = None
    description: str = ""

class QualityManager:
    DEFAULT_AUDIO_PROFILES = {
        AudioQuality.LOW: QualityProfile(
            name="Low Quality",
            audio_bitrate=128,
            audio_sample_rate=44100,
            audio_channels=2,
            description="Compressed audio, suitable for limited storage"
        ),
        AudioQuality.MEDIUM: QualityProfile(
            name="Medium Quality",
            audio_bitrate=256,
            audio_sample_rate=44100,
            audio_channels=2,
            description="Balanced audio quality"
        ),
        AudioQuality.HIGH: QualityProfile(
            name="High Quality",
            audio_bitrate=320,
            audio_sample_rate=48000,
            audio_channels=2,
            description="High-quality audio for most listeners"
        ),
        AudioQuality.LOSSLESS: QualityProfile(
            name="Lossless",
            audio_bitrate=1411,
            audio_sample_rate=96000,
            audio_channels=2,
            description="Uncompressed, studio-quality audio"
        ),
        AudioQuality.DOLBY_ATMOS: QualityProfile(
            name="Dolby Atmos",
            audio_bitrate=2048,
            audio_sample_rate=96000,
            audio_channels=8,
            description="Immersive spatial audio experience"
        )
    }

    DEFAULT_VIDEO_PROFILES = {
        VideoQuality.SD: QualityProfile(
            name="Standard Definition",
            audio_bitrate=128,
            audio_sample_rate=44100,
            audio_channels=2,
            video_resolution="480p",
            video_codec="H.264",
            description="Low bandwidth, smaller file size"
        ),
        VideoQuality.HD: QualityProfile(
            name="High Definition",
            audio_bitrate=256,
            audio_sample_rate=48000,
            audio_channels=2,
            video_resolution="720p",
            video_codec="H.264",
            description="Good quality for most devices"
        ),
        VideoQuality.FULL_HD: QualityProfile(
            name="Full HD",
            audio_bitrate=320,
            audio_sample_rate=48000,
            audio_channels=2,
            video_resolution="1080p",
            video_codec="H.264",
            description="High-quality video for most screens"
        ),
        VideoQuality.QHD: QualityProfile(
            name="Quad HD",
            audio_bitrate=448,
            audio_sample_rate=48000,
            audio_channels=2,
            video_resolution="1440p",
            video_codec="H.265",
            description="High-end video quality"
        ),
        VideoQuality.UHD: QualityProfile(
            name="Ultra HD",
            audio_bitrate=512,
            audio_sample_rate=96000,
            audio_channels=2,
            video_resolution="2160p",
            video_codec="H.265",
            description="Top-tier video quality"
        )
    }

    def __init__(
        self, 
        default_audio_quality: AudioQuality = AudioQuality.HIGH,
        default_video_quality: VideoQuality = VideoQuality.HD
    ):
        self.custom_audio_profiles: Dict[str, QualityProfile] = {}
        self.custom_video_profiles: Dict[str, QualityProfile] = {}
        self.default_audio_quality = default_audio_quality
        self.default_video_quality = default_video_quality

    def add_custom_audio_profile(
        self, 
        name: str, 
        bitrate: int, 
        sample_rate: int, 
        channels: int,
        description: str = ""
    ) -> QualityProfile:
        """Add a custom audio quality profile"""
        profile = QualityProfile(
            name=name,
            audio_bitrate=bitrate,
            audio_sample_rate=sample_rate,
            audio_channels=channels,
            description=description
        )
        self.custom_audio_profiles[name] = profile
        return profile

    def add_custom_video_profile(
        self, 
        name: str, 
        resolution: str, 
        codec: str,
        audio_bitrate: int,
        audio_sample_rate: int,
        audio_channels: int,
        description: str = ""
    ) -> QualityProfile:
        """Add a custom video quality profile"""
        profile = QualityProfile(
            name=name,
            video_resolution=resolution,
            video_codec=codec,
            audio_bitrate=audio_bitrate,
            audio_sample_rate=audio_sample_rate,
            audio_channels=audio_channels,
            description=description
        )
        self.custom_video_profiles[name] = profile
        return profile

    def get_audio_profile(
        self, 
        quality: Union[AudioQuality, str] = None
    ) -> QualityProfile:
        """
        Get audio quality profile
        Supports enum, predefined quality names, and custom profiles
        """
        if quality is None:
            quality = self.default_audio_quality

        # Handle string or enum input
        if isinstance(quality, str):
            # Check custom profiles first
            if quality in self.custom_audio_profiles:
                return self.custom_audio_profiles[quality]
            
            # Convert to enum if possible
            try:
                quality = AudioQuality(quality.lower())
            except ValueError:
                # Fallback to default
                quality = self.default_audio_quality

        # Return predefined profile
        return self.DEFAULT_AUDIO_PROFILES.get(
            quality, 
            self.DEFAULT_AUDIO_PROFILES[self.default_audio_quality]
        )

    def get_video_profile(
        self, 
        quality: Union[VideoQuality, str] = None
    ) -> QualityProfile:
        """
        Get video quality profile
        Supports enum, predefined quality names, and custom profiles
        """
        if quality is None:
            quality = self.default_video_quality

        # Handle string or enum input
        if isinstance(quality, str):
            # Check custom profiles first
            if quality in self.custom_video_profiles:
                return self.custom_video_profiles[quality]
            
            # Convert to enum if possible
            try:
                quality = VideoQuality(quality.lower())
            except ValueError:
                # Fallback to default
                quality = self.default_video_quality

        # Return predefined profile
        return self.DEFAULT_VIDEO_PROFILES.get(
            quality, 
            self.DEFAULT_VIDEO_PROFILES[self.default_video_quality]
        )

    def recommend_quality(
        self, 
        available_qualities: List[Union[AudioQuality, VideoQuality]],
        preferred_quality: Union[AudioQuality, VideoQuality] = None
    ) -> Union[AudioQuality, VideoQuality]:
        """
        Recommend the best available quality
        Falls back to available options if preferred is not present
        """
        if preferred_quality is None:
            preferred_quality = (
                self.default_audio_quality 
                if isinstance(preferred_quality, AudioQuality) else self.default_video_quality
            )

        for quality in available_qualities:
            if quality == preferred_quality:
                return quality

        return available_qualities[0] if available_qualities else None

