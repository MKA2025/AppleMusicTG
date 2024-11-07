from dataclasses import dataclass
from typing import Optional, List
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
    artwork_url: Optional[str] = None
    lyrics: Optional[str] = None
    isrc: Optional[str] = None
    copyright: Optional[str] = None
    composer: Optional[str] = None
    compilation: bool = False
    explicit: bool = False
    
    def to_tags(self) -> dict:
        """Convert to tags dictionary for mutagen"""
        tags = {
            "title": self.title,
            "artist": self.artist
        }
        
        if self.album:
            tags["album"] = self.album
        if self.track_number:
            tags["tracknumber"] = str(self.track_number)
        if self.total_tracks:
            tags["tracktotal"] = str(self.total_tracks)
        if self.disc_number:
            tags["discnumber"] = str(self.disc_number)
        if self.total_discs:
            tags["disctotal"] = str(self.total_discs)
        if self.genre:
            tags["genre"] = self.genre
        if self.release_date:
            tags["date"] = self.release_date
        if self.composer:
            tags["composer"] = self.composer
        if self.copyright:
            tags["copyright"] = self.copyright
        if self.lyrics:
            tags["lyrics"] = self.lyrics
            
        return tags

@dataclass
class PlaylistInfo:
    title: str
    description: Optional[str] = None
    creator: Optional[str] = None
    tracks: List[MediaInfo] = None
    artwork_url: Optional[str] = None
    total_duration: Optional[int] = None
    
    def __post_init__(self):
        if self.tracks is None:
            self.tracks = []
        if self.total_duration is None and self.tracks:
            self.total_duration = sum(
                track.duration for track in self.tracks 
                if track.duration is not None
            )
