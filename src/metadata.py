import dataclasses
import requests
import json

ENDPOINT = "https://api.paugram.com/netease/"

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
        
        resp = requests.get(f"{ENDPOINT}?id={self.id}")
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch metadata for ID {self.id}: {resp.status_code}")
        data = resp.json()
        if data.get("id") != self.id:
            raise ValueError(f"Fetched metadata ID {data.get('id')} does not match expected ID {self.id}")
        self.populate_from_dict(data)


