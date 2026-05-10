import argparse
import metadata
import song

from mutagen.mp4 import MP4, MP4Cover
from utils import get_type_from_cover_path, process_lyrics


def main():
    parser = argparse.ArgumentParser(description="Extract metadata from NCM API and attach to files")
    parser.add_argument("cover_path", help="Path to the cover image file (used to extract ID)")
    parser.add_argument("base_dir", help="Base directory to search for music files")
    args = parser.parse_args()

    # Create Metadata instance from cover path
    meta = metadata.Metadata.from_cover_path(args.cover_path)
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
    file_path = song_instance.search_file_path(args.base_dir)

    assert file_path is not None, "Failed to find song file in the specified directory"
    print(f"Found song file at: {file_path}")

    assert file_path.endswith(".m4a"), "Expected file to have .m4a extension"
    music = MP4(file_path)
    music["\xa9nam"] = meta.title
    music["\xa9ART"] = meta.artist
    music["\xa9alb"] = meta.album
    music["\xa9lyr"] = process_lyrics(meta.lyric, meta.sub_lyric)

    if music.get("covr"):
        print("File already has cover art, skipping cover attachment")
    else:
        with open(args.cover_path, "rb") as f:
            cover_data = f.read()
            cover_type = get_type_from_cover_path(args.cover_path)
            music["covr"] = [MP4Cover(cover_data, imageformat=cover_type)]

    music.save()
    print(f"Metadata attached to file: {file_path}")


if __name__ == "__main__":
    main()
