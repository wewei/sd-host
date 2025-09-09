#!/usr/bin/env python3
"""
SD-Host CLI Tool entry point
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.main import app

if __name__ == "__main__":
    app()