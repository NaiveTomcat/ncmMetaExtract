import argparse
import processor

def main():
    parser = argparse.ArgumentParser(description="Extract metadata from NCM API and attach to files")
    parser.add_argument("cover_path", help="Path to the cover image file (used to extract ID)")
    parser.add_argument("base_dir", help="Base directory to search for music files")
    args = parser.parse_args()

    processor.process_song(args.cover_path, args.base_dir)

   
if __name__ == "__main__":
    main()
