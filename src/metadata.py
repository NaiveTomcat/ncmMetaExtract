import dataclasses
import time
import requests
import json
import os
from pathlib import Path

ENDPOINT = "https://api.paugram.com/netease/"
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

    @classmethod
    def from_id(cls, id: str):
        return cls(id=id)
    
    @classmethod
    def from_cover_path(cls, cover_path: str):
        return cls(cover_path=cover_path, id=cover_path.split("/")[-1].split(".")[0].split("-")[-1])

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
                print(f"[INFO]: Loaded metadata for ID {self.id} from cache")
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


