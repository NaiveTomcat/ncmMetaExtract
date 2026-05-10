import metadata
import song

from mutagen.mp4 import MP4, MP4Cover
from utils import get_type_from_cover_path, process_lyrics

import os
import subprocess
import shutil

def process_song(cover_path: str, base_dir: str, dest: str | None = None):
# Create Metadata instance from cover path
    meta = metadata.Metadata.from_cover_path(cover_path)
    try:
        meta.fetch_metadata()
    except ValueError as e:
        print(f"Error fetching metadata: {e}")
        return
    # print(f"Fetched metadata for ID {meta.id}:")
    # print(f"Title: {meta.title}")
    # print(f"Artist: {meta.artist}")
    # print(f"Album: {meta.album}")

    # Create Song instance and search for file path
    song_instance = song.Song(metadata=meta)
    file_path = song_instance.search_file_path(base_dir)

    assert file_path is not None, "Failed to find song file in the specified directory"
    print(f"[INFO]: Found song file at: {file_path}")

    # assert file_path.endswith(".m4a"), "Expected file to have .m4a extension"
    if not file_path.lower().endswith(".m4a"):
        print(f"[INFO]: File {file_path} is not in m4a format, converting...")
        file_path = convert_to_m4a(file_path, dest_dir=dest)
        print(f"[INFO]: Converted file path: {file_path}")

    process_m4a_file(file_path, meta, dest=dest)


def process_m4a_file(file_path: str, meta: metadata.Metadata, dest: str | None = None):
    # Handle destination directory
    if dest is not None:
        os.makedirs(dest, exist_ok=True)
        dest_path = os.path.join(dest, os.path.basename(file_path))
        if file_path != dest_path:
            shutil.copy2(file_path, dest_path)
        output_path = dest_path
    else:
        output_path = file_path
    
    audio = MP4(output_path)

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
        print(f"[ERROR]: Error processing cover image: {e}")

    audio.save()
    print(f"[INFO]: Saved to: {output_path}")


def convert_to_m4a(file_path: str, dest_dir: str|None = None) -> str:
    """
    Using ffmpeg to convert given file to m4a format.
    Just spawn a subprocess to call ffmpeg.
    """
    base, ext = os.path.splitext(file_path)
    if ext.lower() == ".m4a":
        print(f"[INFO]: File {file_path} is already in m4a format, skipping conversion.")
        return file_path
    
    if ext.lower() == ".ncm":
        # [TODO]: Implement ncm decryption logic here.
        raise NotImplementedError("NCM decryption is not implemented yet. Please convert the file to a supported format (e.g., FLAC or MP3) before running the tool.")

    codec = "alac"  # Default to ALAC for lossless conversion
    if ext.lower() == ".flac":
        # Use ALAC codec for lossless conversion to m4a
        codec = "alac"
    if ext.lower() == ".mp3":
        # Use AAC codec for lossy conversion to m4a
        codec = "aac"
    new_file_path = f"{base}.m4a" if dest_dir is None else os.path.join(dest_dir, os.path.basename(f"{base}.m4a"))
    command = [
        "ffmpeg",
        "-i", file_path,
        "-c:a", codec,
        "-c:v", "copy",
        new_file_path,
        "-y"
    ]
    print(f"[INFO]: Converting {file_path} to m4a format...")
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return new_file_path
