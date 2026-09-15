import json
import os
import uuid
from typing import List, Dict, Any

import sys
base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(base_dir, "data")
os.makedirs(DATA_DIR, exist_ok=True)
PRESETS_FILE = os.path.join(DATA_DIR, "presets.json")

def load_presets() -> List[Dict[str, Any]]:
    if not os.path.exists(PRESETS_FILE):
        return []
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading presets: {e}")
        return []

def save_presets(presets: List[Dict[str, Any]]):
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4)
    except Exception as e:
        print(f"Error saving presets: {e}")

def add_preset(preset_data: Dict[str, Any]):
    presets = load_presets()
    # Add unique ID if not present
    if "id" not in preset_data:
        preset_data["id"] = str(uuid.uuid4())
    presets.append(preset_data)
    save_presets(presets)

def update_preset(preset_id: str, updated_data: Dict[str, Any]):
    presets = load_presets()
    for i, p in enumerate(presets):
        if p.get("id") == preset_id:
            presets[i] = updated_data
            break
    save_presets(presets)

def delete_preset(preset_id: str):
    presets = load_presets()
    presets = [p for p in presets if p.get("id") != preset_id]
    save_presets(presets)

def export_preset(preset_data: Dict[str, Any], filepath: str):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, indent=4)
    except Exception as e:
        print(f"Error exporting preset: {e}")
        raise e

def import_preset(filepath: str) -> Dict[str, Any]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Regenerate ID to avoid collisions
            data["id"] = str(uuid.uuid4())
            return data
    except Exception as e:
        print(f"Error importing preset: {e}")
        raise e
