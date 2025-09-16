import json
import os
import sys
import platform
from datetime import datetime
from typing import List, Dict, Any

from uplang.models import Mod

# Get uplang version from pyproject.toml (or hardcode if not easily accessible)
# For simplicity, let's hardcode it for now, or read from a config if available.
# Assuming uplang version is 0.1.0 as per GEMINI.md
UPLANG_VERSION = "0.1.0"

def save_state(mods_list: List[Mod], file_path: str, mods_dir: str, resource_pack_dir: str):
    """Saves the list of mods and other state information to a JSON file."""
    try:
        state_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "uplang_version": UPLANG_VERSION,
                "os": platform.system(),
                "python_version": platform.python_version()
            },
            "project_info": {
                "mods_directory": mods_dir,
                "resource_pack_directory": resource_pack_dir,
                "mod_count": len(mods_list)
            },
            "mods": [mod.__dict__ for mod in mods_list]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=4)
    except IOError as e:
        print(f"Error saving state file to {file_path}: {e}")

def load_state(file_path: str) -> Dict[str, Any]:
    """Loads state information from a JSON file."""
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            
            mods_dict = {}
            if "mods" in state_data and isinstance(state_data["mods"], list):
                for mod_data in state_data["mods"]:
                    if "mod_id" in mod_data:
                        mods_dict[mod_data["mod_id"]] = Mod(**mod_data)
            
            # Return a dictionary that includes all loaded state data,
            # with 'mods_map' for backward compatibility with cli.py's current usage.
            state_data["mods_map"] = mods_dict
            return state_data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing state file {file_path}: {e}")
        return {}
