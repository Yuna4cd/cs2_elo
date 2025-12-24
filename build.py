#!/usr/bin/env python3
"""
Build script to create executable using PyInstaller

Install PyInstaller first:
    pip install pyinstaller

Then run:
    python build.py
"""

import subprocess
import sys
import shutil
from pathlib import Path

def build():
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'CS2_ELO_Tracker',
        '--onefile',
        '--windowed',  # No console window
        '--add-data', 'cs2_elo_tracker:cs2_elo_tracker',
        'run.py'
    ]
    
    # Add icon if exists
    icon_path = Path('icon.ico')
    if icon_path.exists():
        cmd.extend(['--icon', str(icon_path)])
    
    print("Building executable...")
    subprocess.run(cmd)
    
    # Create data folder next to exe
    dist_data = Path('dist/data')
    dist_data.mkdir(exist_ok=True)
    
    # Copy default config files if they exist
    data_files = [
        'player_aliases.json',
        'initial_elos.json'
    ]
    
    for filename in data_files:
        src = Path('data') / filename
        if src.exists():
            shutil.copy(src, dist_data / filename)
            print(f"Copied {filename}")
    
    print("\nBuild complete!")
    print(f"Executable: dist/CS2_ELO_Tracker{'exe' if sys.platform == 'win32' else ''}")
    print("Make sure the 'data' folder is in the same directory as the executable.")

if __name__ == '__main__':
    build()