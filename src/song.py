import dataclasses
import metadata
import os

@dataclasses.dataclass
class Song:
    metadata: metadata.Metadata
    file_path: str = ""

    def search_file_path(self, base_dir: str):
        """
        Search for the song file in the given base directory using the metadata.
        Assumes files are named in the format "Artist - Title.ext" or "Title - Artist.ext".
        However, since the metadata only contains one artist, but the file could\
            be named with multiple artists, the search strategy will be:

        1. Look for files that contain the title.
        2. If multiple files match, look for files that also contain the artist.
        3. If still multiple files match, flavor files with extensions like .mp3 or .flac
        """

        candidates:list[str] = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                if self.metadata.title.lower() in file.lower():
                    candidates.append(os.path.join(root, file))
        
        if not candidates:
            return None
        
        # If only one candidate, return it
        if len(candidates) == 1:
            self.file_path = candidates[0]
            return self.file_path
        
        # Filter candidates by artist
        artist_candidates = [c for c in candidates if self.metadata.artist.lower() in c.lower()]
        if len(artist_candidates) == 1:
            self.file_path = artist_candidates[0]
            return self.file_path
        
        # If still multiple candidates, look for common audio file extensions
        audio_extensions = ['m4a', 'flac']
        for ext in audio_extensions:
            ext_candidates = [c for c in artist_candidates if c.lower().endswith(ext)]
            if len(ext_candidates) == 1:
                self.file_path = ext_candidates[0]
                return self.file_path
        
        # If still multiple candidates, just take the first one (or could implement more complex logic)
        self.file_path = candidates[0]
        return self.file_path

