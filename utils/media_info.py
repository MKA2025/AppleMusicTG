from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class MediaInfo:
    title: str
    artist: str
    album: Optional[str] = None
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    disc_number: Optional[int] = None
    total_discs: Optional[int] = None
    genre: Optional[str] = None
    release_date: Optional[str] = None
    duration: Optional[int] = None
    artwork_url: Optional[str] =
