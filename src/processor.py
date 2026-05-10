import metadata
import song

from mutagen.mp4 import MP4, MP4Cover
from utils import get_type_from_cover_path, process_lyrics

import os
import subprocess

def process_song(cover_path: str, base_dir: str):
# Create Metadata instance from cover path
    meta = metadata.Metadata.from_cover_path(cover_path)
    try:
        meta.fetch_metadata()
    except ValueError as e:
        print(f"Error fetching metadata: {e}")
        return
    print(f"Fetched metadata for ID {meta.id}:")
    print(f"Title: {meta.title}")
    print(f"Artist: {meta.artist}")
    print(f"Album: {meta.album}")

    # Create Song instance and search for file path
    song_instance = song.Song(metadata=meta)
    file_path = song_instance.search_file_path(base_dir)

    assert file_path is not None, "Failed to find song file in the specified directory"
    print(f"Found song file at: {file_path}")

    # assert file_path.endswith(".m4a"), "Expected file to have .m4a extension"
    if not file_path.lower().endswith(".m4a"):
        print(f"File {file_path} is not in m4a format, converting...")
        file_path = convert_to_m4a(file_path)
        print(f"Converted file path: {file_path}")

    process_m4a_file(file_path, meta)


def process_m4a_file(file_path: str, meta: metadata.Metadata):
    audio = MP4(file_path)

    audio["\xa9nam"] = meta.title
    audio["\xa9ART"] = meta.artist
    audio["\xa9alb"] = meta.album

    combined_lyric = process_lyrics(meta.lyric, meta.sub_lyric)
    if combined_lyric:
        audio["\xa9lyr"] = combined_lyric

    try:
        cover_type = get_type_from_cover_path(meta.cover_path)
        with open(meta.cover_path, "rb") as f:
            cover_data = f.read()
        audio["covr"] = [MP4Cover(cover_data, imageformat=cover_type)]
    except Exception as e:
        print(f"Error processing cover image: {e}")

    audio.save()


def convert_to_m4a(file_path: str):
    """
    Using ffmpeg to convert given file to m4a format.
    Just spawn a subprocess to call ffmpeg.
    """
    base, ext = os.path.splitext(file_path)
    if ext.lower() == ".m4a":
        print(f"File {file_path} is already in m4a format, skipping conversion.")
        return file_path
    
    new_file_path = f"{base}.m4a"
    command = [
        "ffmpeg",
        "-i", file_path,
        "-c:a", "alac",
        "-c:v", "copy",
        new_file_path
    ]
    print(f"Converting {file_path} to m4a format...")
    subprocess.run(command)
    return new_file_path
