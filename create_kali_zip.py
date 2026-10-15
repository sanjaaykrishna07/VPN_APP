#!/usr/bin/env python3
"""
QuantumSafeVPN — Kali Linux Package Creator
============================================
Creates a clean, ready-to-deploy ZIP archive for Kali Linux.
Excludes virtual environments, cache files, and local build artifacts.
"""

import os
import sys
import zipfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(PROJECT_ROOT)
OUTPUT_ZIP = os.path.join(PARENT_DIR, "QuantumSafeVPN_Kali.zip")

EXCLUDE_DIRS = {
    "venv", ".venv", "env", "__pycache__", ".git", ".idea", ".gradle",
    "build", ".pytest_cache", ".user_uploaded", ".tempmediaStorage"
}

EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".log", ".tmp"
}


def create_clean_zip():
    print("=" * 65)
    print("   QuantumSafeVPN — Packaging Project for Kali Linux")
    print("=" * 65)
    print(f"Source Folder : {PROJECT_ROOT}")
    print(f"Output Target : {OUTPUT_ZIP}")
    print("=" * 65)

    if os.path.exists(OUTPUT_ZIP):
        try:
            os.remove(OUTPUT_ZIP)
        except Exception:
            pass

    file_count = 0
    total_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTENSIONS or file.endswith(".zip"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)

                # Store inside a root folder named QuantumSafeVPN/
                archive_name = os.path.join("QuantumSafeVPN", rel_path)
                zipf.write(full_path, archive_name)

                file_count += 1
                total_bytes += os.path.getsize(full_path)
                print(f"  [+] Added: {rel_path}")

    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)

    print()
    print("=" * 65)
    print("   ✓ PACKAGING COMPLETE!")
    print("=" * 65)
    print(f"Packaged Files : {file_count} files ({total_bytes / 1024:.1f} KB uncompressed)")
    print(f"ZIP File Size  : {zip_size_mb:.2f} MB")
    print(f"Location       : {OUTPUT_ZIP}")
    print("=" * 65)
    print()
    print("You can now transfer 'QuantumSafeVPN_Kali.zip' to your Kali machine!")


if __name__ == "__main__":
    create_clean_zip()
