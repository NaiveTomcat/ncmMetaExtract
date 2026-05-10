import metadata
import song

from mutagen.mp4 import MP4, MP4Cover
from utils import get_type_from_cover_path, get_image_format_from_bytes, process_lyrics

import os
import subprocess
import shutil
import json
import time
from pathlib import Path

def process_song(cover_path: str, base_dir: str, dest: str | None = None, delete_orphaned: bool = False):
# Create Metadata instance from cover path
    meta = metadata.Metadata.from_cover_path(cover_path)
    try:
        meta.fetch_metadata()
    except ValueError as e:
        print(f"[ERROR]:   Error fetching metadata: {e}")
        return
    # print(f"Fetched metadata for ID {meta.id}:")
    # print(f"Title: {meta.title}")
    # print(f"Artist: {meta.artist}")
    # print(f"Album: {meta.album}")

    # Create Song instance and search for file path
    song_instance = song.Song(metadata=meta)
    file_path = song_instance.search_file_path(base_dir)

    if file_path is None:
        if delete_orphaned:
            try:
                os.remove(cover_path)
                print(f"[INFO]:    Deleted orphaned cover file: {cover_path}")
            except Exception as e:
                print(f"[ERROR]:   Failed to delete orphaned cover file {cover_path}: {e}")
        else:
            print(f"[ERROR]:   Failed to find song file in the specified directory")
        return
    
    print(f"[INFO]:    Found song file at: {file_path}")

    # assert file_path.endswith(".m4a"), "Expected file to have .m4a extension"
    if not file_path.lower().endswith(".m4a"):
        print(f"[INFO]:    File {file_path} is not in m4a format, converting...")
        file_path = convert_to_m4a(file_path, dest_dir=dest)
        print(f"[INFO]:    Converted file path: {file_path}")

    process_m4a_file(file_path, meta, dest=dest)


# def process_m4a_file(file_path: str, meta: metadata.Metadata, dest: str | None = None):
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

    # Set "aART" (album artist) to "Various Artists" 
    # since we don't have specific album artist information 
    # and this can help with organization in Apple Music 
    # when multiple artists are involved in an album.
    audio["aART"] = "Various Artists"

    combined_lyric = process_lyrics(meta.lyric, meta.sub_lyric)
    if combined_lyric:
        audio["\xa9lyr"] = combined_lyric

    try:
        cover_type = get_type_from_cover_path(meta.cover_path)
        with open(meta.cover_path, "rb") as f:
            cover_data = f.read()
        audio["covr"] = [MP4Cover(cover_data, imageformat=cover_type)]
    except Exception as e:
        print(f"[ERROR]:   Error processing cover image: {e}")

    audio.save()
    print(f"[INFO]:    Saved to: {output_path}")


def convert_to_m4a(file_path: str, dest_dir: str|None = None) -> str:
    """
    Using ffmpeg to convert given file to m4a format.
    Just spawn a subprocess to call ffmpeg.
    """
    base, ext = os.path.splitext(file_path)
    if ext.lower() == ".m4a":
        print(f"[INFO]:    File {file_path} is already in m4a format, skipping conversion.")
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
    if os.path.exists(new_file_path):
        print(f"[INFO]:    Converted file {new_file_path} already exists, skipping conversion.")
        return new_file_path
    command = [
        "ffmpeg",
        "-i", file_path,
        "-c:a", codec,
        "-c:v", "copy",
        new_file_path,
        "-y"
    ]
    print(f"[INFO]:    Converting {file_path} to m4a format...")
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return new_file_path


def process_track_list(track_list_path: str, base_dir: str, dest: str | None = None):
    """
    Process all tracks from a NetEase Cloud Music playlist JSON file.
    
    Args:
        track_list_path: Path to the track_list.json file
        base_dir: Base directory to search for music files
        dest: Destination directory for output files
    """
    # Load the track list JSON
    try:
        with open(track_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR]:   Failed to load track list: {e}")
        return
    
    # Extract tracks from the result object
    result = data.get("result", {})
    tracks = result.get("tracks", [])
    
    if not tracks:
        print(f"[ERROR]:   No tracks found in {track_list_path}")
        return
    
    print(f"[INFO]:    Found {len(tracks)} tracks to process")
    
    for i, track in enumerate(tracks, 1):
        if not track:  # Skip empty track objects
            continue
            
        try:
            print(f"[INFO]:    [{i}/{len(tracks)}] Processing track ID {track.get('id')}...")
            process_track_from_json(track, base_dir, dest=dest)
            time.sleep(0.5)  # Brief pause to avoid rate limiting
        except Exception as e:
            print(f"[ERROR]:   Error processing track {track.get('id')}: {e}")
            continue


def process_track_from_json(track: dict, base_dir: str, dest: str | None = None):
    """
    Process a single track from the playlist JSON.
    
    Args:
        track: Track object from the playlist API
        base_dir: Base directory to search for music files
        dest: Destination directory for output files
    """
    # Create Metadata from track JSON
    meta = metadata.Metadata.from_track_json(track)
    
    # Create Song instance and search for file path
    song_instance = song.Song(metadata=meta)
    file_path = song_instance.search_file_path(base_dir)
    
    if file_path is None:
        print(f"[WARNING]: Failed to find song file for: {meta.title} - {meta.artist}")
        return
    
    print(f"[INFO]:    Found song file at: {file_path}")
    
    # Download cover if not already present
    if not meta.cover_path or not os.path.exists(meta.cover_path):
        cover_path = meta.download_cover(dest_dir=str(metadata.CACHE_DIR / "covers"))
        if not cover_path:
            print(f"[WARNING]: Failed to download cover for: {meta.title}")
            # Continue even if cover download fails
    
    # Fetch lyrics from API
    print(f"[INFO]:    Fetching lyrics for: {meta.title}")
    meta.fetch_lyrics()
    
    # Convert to m4a if necessary
    if not file_path.lower().endswith(".m4a"):
        print(f"[INFO]:    File {file_path} is not in m4a format, converting...")
        file_path = convert_to_m4a(file_path, dest_dir=dest)
        print(f"[INFO]:    Converted file path: {file_path}")
    
    # Process the m4a file
    process_m4a_file(file_path, meta, dest=dest, use_downloaded_cover=True)


def process_m4a_file(file_path: str, meta: metadata.Metadata, dest: str | None = None, use_downloaded_cover: bool = False):
    """
    Process and write metadata to m4a file.
    
    Args:
        file_path: Path to the m4a file
        meta: Metadata object containing track information
        dest: Destination directory for output files
        use_downloaded_cover: If True, use downloaded cover from album_pic_url
    """
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

    # Set "aART" (album artist) to "Various Artists" 
    # since we don't have specific album artist information 
    # and this can help with organization in Apple Music 
    # when multiple artists are involved in an album.
    audio["aART"] = "Various Artists"

    combined_lyric = process_lyrics(meta.lyric, meta.sub_lyric)
    if combined_lyric:
        audio["\xa9lyr"] = combined_lyric

    # Handle cover image
    cover_data = None
    image_format = None
    
    if use_downloaded_cover and meta.cover_path and os.path.exists(meta.cover_path):
        # Use the downloaded cover
        try:
            image_format = get_type_from_cover_path(meta.cover_path)
            with open(meta.cover_path, "rb") as f:
                cover_data = f.read()
        except Exception as e:
            print(f"[WARNING]: Error reading downloaded cover: {e}")
    elif meta.cover_path and os.path.exists(meta.cover_path):
        # Use the original cover path
        try:
            image_format = get_type_from_cover_path(meta.cover_path)
            with open(meta.cover_path, "rb") as f:
                cover_data = f.read()
        except Exception as e:
            print(f"[ERROR]:   Error processing cover image: {e}")
    
    if cover_data and image_format:
        audio["covr"] = [MP4Cover(cover_data, imageformat=image_format)]

    audio.save()
    print(f"[INFO]:    Saved to: {output_path}")
