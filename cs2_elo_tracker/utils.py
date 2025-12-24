import json
import unicodedata
from typing import Dict
from pathlib import Path

# Default data directory
DATA_DIR = Path(__file__).parent.parent / "data"

def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(exist_ok=True)

def get_display_width(text: str) -> int:
    """Calculate display width accounting for wide CJK characters"""
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width

def pad_string(text: str, target_width: int) -> str:
    """Pad string to target display width"""
    current_width = get_display_width(text)
    if current_width >= target_width:
        return text
    return text + ' ' * (target_width - current_width)

def load_json(filepath: Path, default=None):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def save_json(filepath: Path, data):
    """Save data to JSON file"""
    ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_jsonl(filepath: Path) -> list:
    """Load JSONL file"""
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
    except FileNotFoundError:
        pass
    return results

def save_jsonl(filepath: Path, data: list):
    """Save data to JSONL file"""
    ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def load_aliases(filepath: Path = None) -> Dict[str, str]:
    """Load player aliases"""
    if filepath is None:
        filepath = DATA_DIR / "player_aliases.json"
    return load_json(filepath, {})

def normalize_name(name: str, aliases: Dict[str, str]) -> str:
    """Normalize player name using aliases"""
    return aliases.get(name, name)