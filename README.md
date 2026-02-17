# 🗂️ Auto-Organize Developer Workspace

> An Accomplish.ai automation skill that transforms messy Downloads and project folders into organized, date-stamped archives.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What It Does

Takes a mess like this:

```
Downloads/
├── IMG_2947.png
├── screenshot_2024-01-15.png
├── invoice.pdf
├── project_backup.zip
├── temp.py
├── notes.txt
└── script.js
```

And organizes it into this:

```
Downloads/
├── Images/
│   └── 2024-01/
│       ├── IMG_2947.png → Images_20240115_143022.png
│       └── screenshot_2024-01-15.png
├── Documents/
│   └── 2024-01/
│       └── invoice.pdf
├── Code/
│   └── 2024-01/
│       ├── temp.py
│       └── script.js
├── Archives/
│   └── 2024-01/
│       └── project_backup.zip
└── notes.txt → (in Misc/2024-01/)
```

---

## 🚀 Quick Start

```bash
# Clone or copy the skill
cd file-organizer-skill

# Preview what would happen (safe, no changes made)
python organizer.py ~/Downloads

# Actually organize files
python organizer.py ~/Downloads --apply

# Get JSON report for scripting
python organizer.py ~/Downloads --json --apply
```

---

## 📋 Features

| Feature | Description |
|---------|-------------|
| **Smart Categorization** | Automatically sorts files into 9 categories (Images, Code, Documents, etc.) |
| **Date-Based Folders** | Creates year-month subfolders for easy chronological browsing |
| **Content-Aware Renaming** | Renames generic filenames (IMG_1234, screenshot) with timestamps |
| **Dry-Run Mode** | Preview all changes before applying (default) |
| **Duplicate Handling** | Auto-renames conflicts with `_1`, `_2` suffixes |
| **Progress Reporting** | Real-time feedback on large operations |
| **JSON Output** | Machine-readable output for automation pipelines |
| **Safe by Design** | Never overwrites, skips already-organized files |

---

## 🗂️ Categories

| Category | Extensions |
|----------|------------|
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp` |
| Documents | `.pdf`, `.docx`, `.txt`, `.md`, `.epub` |
| Code | `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.yaml`, etc. |
| Archives | `.zip`, `.tar`, `.gz`, `.rar`, `.7z` |
| Data | `.csv`, `.xlsx`, `.parquet`, `.db` |
| Executables | `.dmg`, `.pkg`, `.exe`, `.app` |
| Videos | `.mp4`, `.mov`, `.avi`, `.mkv` |
| Audio | `.mp3`, `.wav`, `.aac`, `.flac` |
| Misc | Everything else |

---

## 🛠️ Installation

### Requirements
- Python 3.8+
- pathlib (stdlib)

### Optional (for tests)
```bash
pip install pytest
```

---

## 📖 Usage

### Basic Usage

```bash
# Dry run (default) - see what would happen
python organizer.py ~/Downloads

# Actually organize
python organizer.py ~/Downloads --apply

# Skip date folders (flat structure)
python organizer.py ~/Downloads --apply --no-date-folders

# Verbose progress
python organizer.py ~/Downloads --apply --verbose

# JSON output for automation
python organizer.py ~/Downloads --apply --json
```

### As a Module

```python
from organizer import FileOrganizer

organizer = FileOrganizer(
    source_folder="~/Downloads",
    dry_run=False,  # Actually move files
    organize_by_date=True,
)

files = organizer.scan_files()
result = organizer.organize(files)
report = organizer.generate_report()

print(f"Organized {result.success_count} files")
```

### With Progress Callback

```python
def on_progress(current: int, total: int, status: str) -> None:
    print(f"[{current}/{total}] {status}")

organizer = FileOrganizer(
    "~/Downloads",
    progress_callback=on_progress,
)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest test_organizer.py -v

# Run specific test class
pytest test_organizer.py::TestFileOrganizer -v

# Run with coverage
pytest test_organizer.py --cov=organizer --cov-report=term-missing
```

---

## 🎬 Demo Script

```bash
#!/bin/bash
# demo.sh - Quick demo for hackathon judges

echo "=== Auto-Organize Workspace Demo ==="
echo ""

# Create dummy workspace
DEMO_DIR=$(mktemp -d)
echo "Created demo workspace: $DEMO_DIR"

# Add sample files
touch "$DEMO_DIR/IMG_1234.png"
touch "$DEMO_DIR/screenshot-2024.png"
touch "$DEMO_DIR/script.py"
touch "$DEMO_DIR/README.md"
touch "$DEMO_DIR/data.csv"
touch "$DEMO_DIR/archive.zip"

echo ""
echo "Before organization:"
ls -la "$DEMO_DIR"

echo ""
echo "Running organizer (dry-run)..."
python organizer.py "$DEMO_DIR"

echo ""
echo "Applying organization..."
python organizer.py "$DEMO_DIR" --apply --verbose

echo ""
echo "After organization:"
find "$DEMO_DIR" -type f

# Cleanup
rm -rf "$DEMO_DIR"
echo ""
echo "✅ Demo complete!"
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│  FileOrganizer  │
├─────────────────┤
│ - source_folder │
│ - dry_run       │
│ - organize_by   │
├─────────────────┤
│ + scan_files()  │
│ + organize()    │
│ + generate_     │
│   _report()     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌──────────┐
│FileInfo│  │Organize  │
│       │  │Result    │
└───────┘  └──────────┘
```

---

## 📝 License

MIT License - feel free to use in your own Accomplish skills!

---

## 🙏 Acknowledgments

Built for the **"Automate Me If You Can"** Hackathon by WeMakeDevs × Accomplish.ai

- Multi-agent workflow using Cline CLI + Kimi Code CLI
- Clean code principles from Python best practices skills
- Error handling patterns for robust automation

---

> **Time saved**: This skill transforms a 30-minute manual cleanup into a 5-second automation. That's **99.7% faster**! 🚀
