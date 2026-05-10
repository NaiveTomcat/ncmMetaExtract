import argparse
import processor
import time
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Extract metadata from NCM API and attach to files")
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")
    
    # Single mode - process a single cover file
    single_parser = subparsers.add_parser("single", help="Process a single cover file")
    single_parser.add_argument("cover_path", help="Path to the cover image file (used to extract ID)")
    single_parser.add_argument("base_dir", help="Base directory to search for music files")
    single_parser.add_argument("--dest", help="Destination directory for output files (optional)")
    
    # Batch mode - process all cover files in a directory
    batch_parser = subparsers.add_parser("batch", help="Process all cover files in a directory")
    batch_parser.add_argument("cover_dir", help="Directory containing cover image files")
    batch_parser.add_argument("base_dir", help="Base directory to search for music files")
    batch_parser.add_argument("--dest", help="Destination directory for output files (optional)")
    batch_parser.add_argument("--delete-orphaned-covers", action="store_true", help="Delete cover files if corresponding music file is not found")
    
    args = parser.parse_args()
    
    if args.mode == "single":
        processor.process_song(args.cover_path, args.base_dir, dest=args.dest)
    elif args.mode == "batch":
        process_batch(args.cover_dir, args.base_dir, args.dest, delete_orphaned=args.delete_orphaned_covers)
    else:
        parser.print_help()


def process_batch(cover_dir_str: str, base_dir: str, dest: str | None = None, delete_orphaned: bool = False):
    """Process all cover files in a directory."""
    cover_dir = Path(cover_dir_str)
    if not cover_dir.is_dir():
        print(f"[ERROR]:   {cover_dir} is not a valid directory")
        return
    
    # Common cover image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    cover_files = [f for f in cover_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    if not cover_files:
        print(f"[ERROR]:   No cover files found in {cover_dir}")
        return
    
    print(f"[INFO]:    Found {len(cover_files)} cover files to process")
    
    for i, cover_file in enumerate(cover_files, 1):
        print(f"[INFO]:    [{i}/{len(cover_files)}] Processing {cover_file.name}...")
        try:
            processor.process_song(str(cover_file), base_dir, dest=dest, delete_orphaned=delete_orphaned)
        except Exception as e:
            print(f"[ERROR]:   Error processing {cover_file.name}: {e}")
            time.sleep(1)  # Brief pause before continuing to the next file
            continue

   
if __name__ == "__main__":
    main()
