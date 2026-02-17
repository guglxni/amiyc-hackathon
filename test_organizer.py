"""Test suite for File Organizer skill.

Tests follow Python best practices:
- Fail fast validation
- Specific exceptions
- No mutable defaults
- Clean test structure
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from organizer import FileInfo, FileOrganizer, OrganizeResult


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_file_info_creation(self, tmp_path: Path) -> None:
        """Test FileInfo is created with correct attributes."""
        test_file = tmp_path / "test.py"
        test_file.touch()

        info = FileInfo(
            source_path=test_file,
            category="Code",
            created_date=datetime(2024, 1, 15),
        )

        assert info.source_path == test_file
        assert info.category == "Code"
        assert isinstance(info.created_date, datetime)

    def test_suggested_name_generation(self, tmp_path: Path) -> None:
        """Test suggested name is generated for generic filenames."""
        test_file = tmp_path / "IMG_1234.png"
        test_file.touch()

        info = FileInfo(
            source_path=test_file,
            category="Images",
            created_date=datetime(2024, 1, 15, 10, 30, 0),
        )

        assert "Images_20240115_103000.png" == info.suggested_name

    def test_suggested_name_preserved(self, tmp_path: Path) -> None:
        """Test meaningful names are preserved."""
        test_file = tmp_path / "my_project.py"
        test_file.touch()

        info = FileInfo(
            source_path=test_file,
            category="Code",
            created_date=datetime(2024, 1, 15),
        )

        assert info.suggested_name == "my_project.py"


class TestFileOrganizer:
    """Tests for FileOrganizer class."""

    def test_organizer_validates_source(self) -> None:
        """Test organizer validates source folder exists."""
        with pytest.raises(ValueError, match="does not exist"):
            FileOrganizer("/nonexistent/path")

    def test_organizer_validates_is_directory(self, tmp_path: Path) -> None:
        """Test organizer validates source is directory."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError, match="not a directory"):
            FileOrganizer(test_file)

    def test_get_category_images(self, tmp_path: Path) -> None:
        """Test category detection for images."""
        organizer = FileOrganizer(tmp_path)

        assert organizer._get_category(Path("test.png")) == "Images"
        assert organizer._get_category(Path("test.jpg")) == "Images"
        assert organizer._get_category(Path("test.JPEG")) == "Images"

    def test_get_category_code(self, tmp_path: Path) -> None:
        """Test category detection for code files."""
        organizer = FileOrganizer(tmp_path)

        assert organizer._get_category(Path("test.py")) == "Code"
        assert organizer._get_category(Path("test.js")) == "Code"
        assert organizer._get_category(Path("test.ts")) == "Code"

    def test_get_category_misc(self, tmp_path: Path) -> None:
        """Test unknown extensions go to Misc."""
        organizer = FileOrganizer(tmp_path)

        assert organizer._get_category(Path("test.xyz")) == "Misc"
        assert organizer._get_category(Path("test.unknown")) == "Misc"

    def test_scan_files_skips_hidden(self, tmp_path: Path) -> None:
        """Test hidden files are skipped."""
        # Create files
        (tmp_path / ".hidden").touch()
        (tmp_path / "visible.txt").touch()

        organizer = FileOrganizer(tmp_path)
        files = organizer.scan_files()

        assert len(files) == 1
        assert all(".hidden" not in str(f.source_path) for f in files)

    def test_scan_files_skips_category_folders(self, tmp_path: Path) -> None:
        """Test files in category folders are skipped."""
        # Create category folder with file
        (tmp_path / "Images").mkdir()
        (tmp_path / "Images" / "existing.png").touch()

        # Create file in root
        (tmp_path / "new.png").touch()

        organizer = FileOrganizer(tmp_path)
        files = organizer.scan_files()

        assert len(files) == 1
        assert files[0].source_path.name == "new.png"


class TestOrganizeResult:
    """Tests for OrganizeResult dataclass."""

    def test_empty_result(self) -> None:
        """Test empty result has zero counts."""
        result = OrganizeResult()

        assert result.success_count == 0
        assert result.error_count == 0
        assert result.skipped_count == 0
        assert result.all_succeeded is True

    def test_result_with_success(self) -> None:
        """Test result with successful operations."""
        result = OrganizeResult()
        result.organized.append(None)  # type: ignore

        assert result.success_count == 1
        assert result.all_succeeded is True

    def test_result_with_errors(self) -> None:
        """Test result with failures."""
        result = OrganizeResult()
        result.errors.append((Path("test"), "error"))

        assert result.error_count == 1
        assert result.all_succeeded is False


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_organize_workflow(self, tmp_path: Path) -> None:
        """Test complete organization workflow."""
        # Create test files
        (tmp_path / "photo.png").touch()
        (tmp_path / "script.py").touch()
        (tmp_path / "doc.pdf").touch()

        organizer = FileOrganizer(tmp_path, dry_run=True)
        files = organizer.scan_files()

        assert len(files) == 3

        result = organizer.organize(files)
        assert result.success_count == 3

    def test_dry_run_does_not_move(self, tmp_path: Path) -> None:
        """Test dry run does not actually move files."""
        # Create test file
        test_file = tmp_path / "photo.png"
        test_file.touch()

        organizer = FileOrganizer(tmp_path, dry_run=True)
        files = organizer.scan_files()
        organizer.organize(files)

        # File should still be in original location
        assert test_file.exists()

    def test_generate_report(self, tmp_path: Path) -> None:
        """Test report generation."""
        (tmp_path / "photo.png").touch()
        (tmp_path / "script.py").touch()

        organizer = FileOrganizer(tmp_path, dry_run=True)
        files = organizer.scan_files()
        organizer.organize(files)

        report = organizer.generate_report()

        assert report["mode"] == "DRY RUN"
        assert report["files_organized"] == 2
        assert "Images" in report["by_category"]
        assert "Code" in report["by_category"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
