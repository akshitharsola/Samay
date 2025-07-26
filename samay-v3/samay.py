#!/usr/bin/env python3
"""
Samay v3 - Main Entry Point
===========================
Clean entry point for the Samay multi-agent session manager
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

# Import and run the main manager
from orchestrator.manager import main

if __name__ == "__main__":
    main()