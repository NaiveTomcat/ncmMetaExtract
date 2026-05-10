import dataclasses
import time
import requests
import json
import os
from pathlib import Path

ENDPOINT = "https://api.paugram.com/netease/"
LYRICS_ENDPOINT = "https://music.163.com/api/song/lyric"
CACHE_DIR = Path.home() / ".cache" / "ncmMetaExtract"

@dataclasses.dataclass
class Metadata:
    id: str = ""
    cover_path: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    lyric: str = ""
    sub_lyric: str = ""
    album_pic_url: str = ""  # Store original album picture URL for downloading

    @classmethod
    def from_id(cls, id: str):
        return cls(id=id)
    
    @classmethod
    def from_cover_path(cls, cover_path: str):
        return cls(cover_path=cover_path, id=cover_path.split("/")[-1].split(".")[0].split("-")[-1])
    
    @classmethod
    def from_track_json(cls, track: dict):
        """
        Create Metadata from a track object from the playlist API.
        Track should contain fields like: id, name, artists, album
        """
        track_id = str(track.get("id", ""))
        title = track.get("name", "")
        
        # Extract artist name - handle both 'ar' and 'artists' fields
        artist = ""
        artists_list = track.get("ar") or track.get("artists", [])
        if artists_list:
            artist = artists_list[0].get("name", "")
        
        # Extract album name and picture URL from 'album' field
        album_info = track.get("album", {})
        album = album_info.get("name", "")
        album_pic_url = album_info.get("picUrl", "")
        
        return cls(
            id=track_id,
            title=title,
            artist=artist,
            album=album,
            album_pic_url=album_pic_url
        )

    def populate_from_dict(self, data: dict):
        self.title = data.get("title", "")
        self.artist = data.get("artist", "")
        self.album = data.get("album", "")
        self.lyric = data.get("lyric", "")
        self.sub_lyric = data.get("sub_lyric", "")

    def fetch_metadata(self):
        if not self.id:
            raise ValueError("ID is required to fetch metadata")
        
        # Try to load from cache first
        cache_file = CACHE_DIR / f"{self.id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.populate_from_dict(data)
                print(f"[INFO]:    Loaded metadata for ID {self.id} from cache")
                return
            except (json.JSONDecodeError, IOError):
                # If cache is corrupted, proceed to fetch from server
                pass
        
        # Fetch from remote server
        resp = requests.get(f"{ENDPOINT}?id={self.id}")
        while resp.status_code == 429:
            # Handle rate limiting by waiting and retrying
            print(f"[WARNING]: Rate limited when fetching metadata for ID {self.id}. Retrying after 5 seconds...")
            time.sleep(5)
            resp = requests.get(f"{ENDPOINT}?id={self.id}")
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch metadata for ID {self.id}: {resp.status_code}")
        data = resp.json()
        if str(data.get("id")) != str(self.id):
            raise ValueError(f"Fetched metadata ID {data.get('id')} does not match expected ID {self.id}")
        
        # Save to cache
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            # If caching fails, just continue without caching
            pass
        
        self.populate_from_dict(data)

    def fetch_lyrics(self):
        """Fetch lyrics from NetEase API using the track ID."""
        if not self.id:
            raise ValueError("ID is required to fetch lyrics")
        
        try:
            params = {
                "id": self.id,
                "lv": 1,
                "kv": 1,
                "tv": -1
            }
            resp = requests.get(LYRICS_ENDPOINT, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"[WARNING]: Failed to fetch lyrics for ID {self.id}: {resp.status_code}")
                return
            
            data = resp.json()
            if data.get("code") != 200:
                print(f"[WARNING]: Lyrics API returned error code {data.get('code')} for ID {self.id}")
                return
            
            lrc = data.get("lrc", {})
            self.lyric = lrc.get("lyric", "")
            
            # Handle translated lyrics if available
            tlyric = data.get("tlyric", {})
            self.sub_lyric = tlyric.get("lyric", "")
            
            if self.lyric:
                print(f"[INFO]:    Successfully fetched lyrics for ID {self.id}")
            else:
                print(f"[INFO]:    No lyrics found for ID {self.id}")
        except Exception as e:
            print(f"[WARNING]: Error fetching lyrics for ID {self.id}: {e}")

    def download_cover(self, dest_dir: str | None = None) -> str | None:
        """Download cover image from album_pic_url and save to cover_path."""
        if not self.album_pic_url:
            return None
        
        if not dest_dir:
            dest_dir = str(CACHE_DIR / "covers")
        
        try:
            os.makedirs(dest_dir, exist_ok=True)
            
            # Determine file extension from URL
            url_path = self.album_pic_url.split("?")[0]  # Remove query params
            if url_path.endswith(".jpg"):
                ext = ".jpg"
            elif url_path.endswith(".png"):
                ext = ".png"
            else:
                ext = ".jpg"  # Default to jpg
            
            cover_filename = f"{self.id}{ext}"
            cover_path = os.path.join(dest_dir, cover_filename)
            
            # Skip if already downloaded
            if os.path.exists(cover_path):
                self.cover_path = cover_path
                return cover_path
            
            # Download the cover
            resp = requests.get(self.album_pic_url, timeout=10)
            if resp.status_code != 200:
                print(f"[WARNING]: Failed to download cover for ID {self.id}")
                return None
            
            with open(cover_path, 'wb') as f:
                f.write(resp.content)
            
            self.cover_path = cover_path
            print(f"[INFO]:    Downloaded cover for ID {self.id} to {cover_path}")
            return cover_path
        except Exception as e:
            print(f"[WARNING]: Error downloading cover for ID {self.id}: {e}")
            return None



