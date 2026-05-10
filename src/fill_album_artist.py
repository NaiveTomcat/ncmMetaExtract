"""Fill MP4 aART tags from filename-derived album artists.

This script scans converted .m4a files, groups them by album tag, extracts
track author names from the filename suffix after the last hyphen, and writes
the common author list back to each file's aART tag.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from mutagen.mp4 import MP4

import unicodedata


def parse_authors_from_filename(file_path: Path) -> list[str]:
    """Extract authors from the filename suffix after the last hyphen."""
    stem = file_path.stem
    if " - " not in stem:
        return []

    suffix = stem.rsplit(" - ", 1)[1].strip()
    if not suffix:
        return []

    authors = [part.strip() for part in suffix.replace("，", ",").split(",")]
    return [author for author in authors if author]


def iter_m4a_files(root_dir: Path) -> Iterable[Path]:
    for file_path in root_dir.rglob("*.m4a"):
        if file_path.is_file():
            yield file_path


def get_album_tag(file_path: Path) -> str:
    try:
        audio = MP4(str(file_path))
    except Exception:
        return ""

    album_tag = audio.tags.get("\xa9alb") if audio.tags else None
    if not album_tag:
        return ""

    return str(album_tag[0]).strip()


def common_authors(author_lists: list[list[str]]) -> list[str]:
    if not author_lists:
        return []

    common = [author for author in author_lists[0] if author]
    for authors in author_lists[1:]:
        author_set = set(authors)
        common = [author for author in common if author in author_set]
        if not common:
            break

    return common


def update_album_artists(root_dir: Path, dry_run: bool = False) -> int:
    album_map: dict[str, list[tuple[Path, list[str]]]] = defaultdict(list)

    for file_path in iter_m4a_files(root_dir):
        album = get_album_tag(file_path)
        if not album:
            print(f"[WARN]:    Skip {file_path}: missing album tag")
            continue

        authors = parse_authors_from_filename(file_path)
        if not authors:
            print(f"[WARN]:    Skip {file_path}: no authors found in filename")
            continue

        normalized_authors = [unicodedata.normalize("NFC", author) for author in authors]

        album_map[album].append((file_path, normalized_authors))

    updated_files = 0
    not_updated_files = 0
    for album, entries in album_map.items():
        album_common_authors = common_authors([authors for _, authors in entries])
        if not album_common_authors:
            print(f"[WARN]:    Album {album!r} has no common authors; skipping")
            not_updated_files += len(entries)
            continue

        album_artist = ", ".join(album_common_authors)
        print(f"[INFO]:    Album {album!r} -> aART = {album_artist}")

        for file_path, _ in entries:
            if dry_run:
                print(f"[DRY-RUN]: {file_path} -> aART = {album_artist}")
                updated_files += 1
                continue

            audio = MP4(str(file_path))
            audio["aART"] = [album_artist]
            audio.save()
            print(f"[INFO]:    Updated {file_path}")
            updated_files += 1

    print(f"[INFO]:    Updated {updated_files} files")
    print(f"[INFO]:    Skipped {not_updated_files} files")

    return updated_files + not_updated_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill MP4 aART tags with the common authors of each album"
    )
    parser.add_argument(
        "root_dir",
        nargs="?",
        default=".",
        help="Root directory to scan for converted .m4a files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned updates without writing tags",
    )
    args = parser.parse_args()

    root_dir = Path(args.root_dir).expanduser().resolve()
    if not root_dir.is_dir():
        print(f"[ERROR]:   {root_dir} is not a valid directory")
        raise SystemExit(1)

    updated_files = update_album_artists(root_dir, dry_run=args.dry_run)
    print(f"[INFO]:    Processed {updated_files} files")


if __name__ == "__main__":
    main()