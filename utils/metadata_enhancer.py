import logging
from typing import Dict, Any, List, Optional
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

logger = logging.getLogger(__name__)

class MetadataEnhancer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata: Dict[str, Any] = {}
        self.load_metadata()

    def load_metadata(self):
        """Load metadata from the media file."""
        try:
            audio_file = File(self.file_path, easy=True)
            if audio_file is not None:
                self.metadata = {key: audio_file[key] for key in audio_file.keys()}
                logger.info(f"Loaded metadata for {self.file_path}: {self.metadata}")
            else:
                logger.warning(f"No metadata found for {self.file_path}")
        except ID3NoHeaderError:
            logger.error(f"No ID3 header found in {self.file_path}.")
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")

    def enhance_metadata(self, additional_info: Dict[str, Any]):
        """Enhance existing metadata with additional information."""
        for key, value in additional_info.items():
            self.metadata[key] = value
            logger.info(f"Enhanced metadata for {self.file_path}: {key} = {value}")

    def save_metadata(self):
        """Save the enhanced metadata back to the media file."""
        try:
            audio_file = File(self.file_path, easy=True)
            if audio_file is not None:
                for key, value in self.metadata.items():
                    audio_file[key] = value
                audio_file.save()
                logger.info(f"Saved metadata for {self.file_path}")
            else:
                logger.warning(f"No metadata to save for {self.file_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        """Get the current metadata."""
        return self.metadata

    def display_metadata(self):
        """Display the current metadata in a readable format."""
        logger.info(f"Current metadata for {self.file_path}:")
        for key, value in self.metadata.items():
            logger.info(f"{key}: {value}")

# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Path to your media file
    media_file_path = "path/to/your/media/file.mp3"

    # Create an instance of MetadataEnhancer
    enhancer = MetadataEnhancer(media_file_path)

    # Display current metadata
    enhancer.display_metadata()

    # Enhance metadata with additional information
    additional_info = {
        "artist": "New Artist",
        "album": "New Album",
        "genre": "Pop",
        "year": 2023
    }
    enhancer.enhance_metadata(additional_info)

    # Save the enhanced metadata
    enhancer.save_metadata()

    # Display updated metadata
    enhancer.display_metadata()