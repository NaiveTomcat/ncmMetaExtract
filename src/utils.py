import re
from mutagen.mp4 import AtomDataType, MP4Cover

def get_type_from_cover_path(cover_path: str) -> AtomDataType:
    """
    Get the file type by magic number from the cover path.
    """
    with open(cover_path, "rb") as f:
        header = f.read(12)  # Read the first 12 bytes to check for magic numbers
        if header.startswith(b"\xFF\xD8\xFF"):  # JPEG magic number
            return MP4Cover.FORMAT_JPEG
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG magic number
            return MP4Cover.FORMAT_PNG
        else:
            raise ValueError(f"Unsupported cover image format for file: {cover_path}")

def process_lyrics(lyric: str, sub_lyric: str) -> str:
    """
    Combine the main lyric and sub lyric line by line to create a combined lyric string.
    And also strip out the timestamps from the lyrics, since Apple Music does not\
        support synced lyrics from local files.
    
    Handles cases where main lyrics and sub lyrics may not have line-for-line correspondence.
    Matches lyrics based on timestamps instead.
    """
    
    def is_valid_timestamp_line(line: str) -> bool:
        """Check if a line has a valid timestamp format [mm:ss.xx]"""
        match = re.match(r'^\[\d{2}:\d{2}\.\d{2}\]', line)
        return match is not None
    
    def extract_timestamp_and_text(line: str) -> tuple[str, str] | None:
        """Extract timestamp and text from a line. Returns (timestamp, text) or None if invalid."""
        if not is_valid_timestamp_line(line):
            return None
        ts, text = line.split("]", 1)
        return (ts, text)
    
    if sub_lyric == "":
        # Filter lines with valid timestamps and strip them
        return "\n".join([
            line.split("]", 1)[-1] 
            for line in lyric.splitlines() 
            if is_valid_timestamp_line(line)
        ])
    
    lyric_lines = lyric.splitlines()
    sub_lyric_lines = sub_lyric.splitlines()
    
    # Extract timestamp-text pairs, filtering out invalid lines
    main_lyrics_dict = {}
    for line in lyric_lines:
        data = extract_timestamp_and_text(line)
        if data:
            ts, text = data
            if ts not in main_lyrics_dict:
                main_lyrics_dict[ts] = []
            main_lyrics_dict[ts].append(text)
    
    sub_lyrics_dict = {}
    for line in sub_lyric_lines:
        data = extract_timestamp_and_text(line)
        if data:
            ts, text = data
            if ts not in sub_lyrics_dict:
                sub_lyrics_dict[ts] = []
            sub_lyrics_dict[ts].append(text)
    
    # Get all unique timestamps, sorted
    all_timestamps = sorted(set(main_lyrics_dict.keys()) | set(sub_lyrics_dict.keys()))
    
    combined_lines = []
    for ts in all_timestamps:
        main_texts = main_lyrics_dict.get(ts, [])
        sub_texts = sub_lyrics_dict.get(ts, [])
        
        # Combine texts from both lyrics
        if main_texts and sub_texts:
            # Both have content at this timestamp
            combined_lines.extend(main_texts)
            combined_lines.extend(sub_texts)
        elif main_texts:
            # Only main lyrics have content
            combined_lines.extend(main_texts)
        else:
            # Only sub lyrics have content
            combined_lines.extend(sub_texts)
        # Add a blank line after each line of lyrics
        combined_lines.append("")
    
    return "\n".join(combined_lines)

