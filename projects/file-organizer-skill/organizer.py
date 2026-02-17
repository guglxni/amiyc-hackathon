"""Auto-Organize Developer Workspace Skill

Automatically categorizes and organizes files in a developer workspace
based on file type and creation date.

Categories:
- Images: .png, .jpg, .jpeg, .gif, .svg, .webp
- Documents: .pdf, .docx, .txt, .md, .epub
- Code: .py, .js, .ts, .jsx, .tsx, .html, .css, .json, .yaml, .yml
- Archives: .zip, .tar, .gz, .rar, .7z
- Data: .csv, .xlsx, .parquet, .json
- Executables: .dmg, .pkg, .exe, .app
- Misc: Everything else
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable


@dataclass
class FileInfo:
    """Information about a file to be organized."""

    source_path: Path
    category: str
    created_date: datetime
    suggested_name: str = ""
    target_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.suggested_name:
            self.suggested_name = self._generate_suggested_name()

    def _generate_suggested_name(self) -> str:
        """Generate a descriptive name based on content or date."""
        timestamp = self.created_date.strftime("%Y%m%d_%H%M%S")
        original_name = self.source_path.stem
        extension = self.source_path.suffix

        # If name is generic (like IMG_1234, screenshot), add date
        generic_prefixes = ("img_", "image_", "screenshot", "screen shot", "untitled")
        if any(original_name.lower().startswith(p) for p in generic_prefixes):
            return f"{self.category}_{timestamp}{extension}"

        return self.source_path.name


@dataclass
class OrganizeResult:
    """Result of organization operation."""

    organized: list[FileInfo] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.organized)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def all_succeeded(self) -> bool:
        return len(self.errors) == 0


class FileOrganizer:
    """Organizes files by category and date."""

    CATEGORIES: dict[str, tuple[str, ...]] = {
        "Images": (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"),
        "Documents": (".pdf", ".docx", ".doc", ".txt", ".md", ".epub", ".rtf"),
        "Code": (
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".xml",
            ".sh",
            ".zsh",
            ".bash",
        ),
        "Archives": (".zip", ".tar", ".gz", ".tgz", ".bz2", ".rar", ".7z"),
        "Data": (".csv", ".xlsx", ".xls", ".parquet", ".db", ".sqlite"),
        "Executables": (".dmg", ".pkg", ".exe", ".msi", ".app", ".deb", ".rpm"),
        "Videos": (".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"),
        "Audio": (".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"),
    }

    def __init__(
        self,
        source_folder: Path,
        dry_run: bool = True,
        organize_by_date: bool = True,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> None:
        self.source_folder = Path(source_folder).expanduser().resolve()
        self.dry_run = dry_run
        self.organize_by_date = organize_by_date
        self.progress_callback = progress_callback
        self.result = OrganizeResult()

        if not self.source_folder.exists():
            raise ValueError(f"Source folder does not exist: {source_folder}")
        if not self.source_folder.is_dir():
            raise ValueError(f"Source path is not a directory: {source_folder}")

    def _get_category(self, file_path: Path) -> str:
        """Determine file category based on extension."""
        extension = file_path.suffix.lower()

        for category, extensions in self.CATEGORIES.items():
            if extension in extensions:
                return category

        return "Misc"

    def _get_creation_date(self, file_path: Path) -> datetime:
        """Get file creation date, falling back to modification date."""
        stat = file_path.stat()

        # Try creation time first (macOS), fall back to modification time
        try:
            timestamp = stat.st_birthtime
        except AttributeError:
            timestamp = stat.st_mtime

        return datetime.fromtimestamp(timestamp)

    def _generate_target_path(self, file_info: FileInfo) -> Path:
        """Generate target path for organized file."""
        if self.organize_by_date:
            date_folder = file_info.created_date.strftime("%Y-%m")
            target = (
                self.source_folder
                / file_info.category
                / date_folder
                / file_info.suggested_name
            )
        else:
            target = self.source_folder / file_info.category / file_info.suggested_name

        # Handle duplicates
        counter = 1
        original_target = target
        while target.exists() and target != file_info.source_path:
            stem = original_target.stem
            suffix = original_target.suffix
            target = original_target.with_name(f"{stem}_{counter}{suffix}")
            counter += 1

        return target

    def _report_progress(self, current: int, total: int, status: str) -> None:
        """Report progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(current, total, status)

    def scan_files(self) -> list[FileInfo]:
        """Scan source folder and categorize all files."""
        files: list[FileInfo] = []

        # Get all files (excluding hidden files and our category folders)
        category_names = set(self.CATEGORIES.keys()) | {"Misc"}
        all_paths = [
            p
            for p in self.source_folder.rglob("*")
            if p.is_file()
            and not p.name.startswith(".")
            and not any(cat in p.parts for cat in category_names)
        ]

        total = len(all_paths)
        for idx, file_path in enumerate(all_paths):
            self._report_progress(idx, total, f"Scanning: {file_path.name}")

            category = self._get_category(file_path)
            created_date = self._get_creation_date(file_path)

            file_info = FileInfo(
                source_path=file_path,
                category=category,
                created_date=created_date,
            )
            file_info.target_path = self._generate_target_path(file_info)

            # Skip if already in correct location
            if file_info.target_path == file_path:
                self.result.skipped.append(file_path)
            else:
                files.append(file_info)

        return files

    def organize(self, files: list[FileInfo]) -> OrganizeResult:
        """Organize files into categorized folders."""
        total = len(files)

        for idx, file_info in enumerate(files):
            self._report_progress(idx, total, f"Organizing: {file_info.source_path.name}")

            if self.dry_run:
                self.result.organized.append(file_info)
                continue

            try:
                # Create target directory
                if file_info.target_path:
                    file_info.target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Move file
                    shutil.move(str(file_info.source_path), str(file_info.target_path))
                    self.result.organized.append(file_info)

            except (OSError, shutil.Error) as e:
                self.result.errors.append((file_info.source_path, str(e)))

        self._report_progress(total, total, "Complete")
        return self.result

    def generate_report(self) -> dict:
        """Generate organization report."""
        by_category: dict[str, int] = {}
        for file_info in self.result.organized:
            by_category[file_info.category] = by_category.get(file_info.category, 0) + 1

        return {
            "mode": "DRY RUN" if self.dry_run else "LIVE",
            "source_folder": str(self.source_folder),
            "total_files_scanned": len(self.result.organized)
            + len(self.result.skipped)
            + len(self.result.errors),
            "files_organized": self.result.success_count,
            "files_skipped": self.result.skipped_count,
            "errors": self.result.error_count,
            "by_category": by_category,
            "organized_files": [
                {
                    "original": str(f.source_path.relative_to(self.source_folder)),
                    "new": str(f.target_path.relative_to(self.source_folder))
                    if f.target_path
                    else None,
                    "category": f.category,
                }
                for f in self.result.organized
            ],
        }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-organize developer workspace files"
    )
    parser.add_argument(
        "source_folder",
        help="Path to folder to organize",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry-run)",
    )
    parser.add_argument(
        "--no-date-folders",
        action="store_true",
        help="Don't create date-based subfolders",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show progress",
    )

    args = parser.parse_args()

    try:
        def progress(current: int, total: int, status: str) -> None:
            if args.verbose:
                print(f"[{current}/{total}] {status}")

        organizer = FileOrganizer(
            source_folder=args.source_folder,
            dry_run=not args.apply,
            organize_by_date=not args.no_date_folders,
            progress_callback=progress,
        )

        print(f"📁 Scanning: {organizer.source_folder}")
        if not args.apply:
            print("🧪 DRY RUN MODE - No files will be moved\n")

        files = organizer.scan_files()
        print(f"Found {len(files)} files to organize")

        if files:
            result = organizer.organize(files)
            report = organizer.generate_report()

            if args.json:
                print(json.dumps(report, indent=2, default=str))
            else:
                print(f"\n{'=' * 50}")
                print(f"📊 Organization Report")
                print(f"{'=' * 50}")
                print(f"Mode: {report['mode']}")
                print(f"Files organized: {report['files_organized']}")
                print(f"Files skipped (already organized): {report['files_skipped']}")
                print(f"Errors: {report['errors']}")
                print(f"\nBy category:")
                for cat, count in sorted(report["by_category"].items()):
                    print(f"  {cat}: {count}")

                if not args.apply and report['files_organized'] > 0:
                    print(f"\n⚡ Run with --apply to execute these changes")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
