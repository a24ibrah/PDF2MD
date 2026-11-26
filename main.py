#!/usr/bin/env python3
"""CLI wrapper entry point for PDF2MD."""

import sys
from pathlib import Path

# Add src to sys.path so it works directly without installation
project_root = Path(__file__).resolve().parent
src_dir = project_root / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from pdf2md.cli import main

if __name__ == "__main__":
    sys.exit(main())

