import json
import os

def add_new_keys(zh_cn_path: str, changes: dict):
    """Merges new translation keys into the zh_cn.json file."""
    if not changes:
        return

    try:
        if os.path.exists(zh_cn_path):
            with open(zh_cn_path, 'r', encoding='utf-8') as f:
                zh_data = json.load(f)
        else:
            zh_data = {}

        # Add new keys
        for key, value in changes.items():
            if key not in zh_data:
                zh_data[key] = value

        with open(zh_cn_path, 'w', encoding='utf-8') as f:
            json.dump(zh_data, f, ensure_ascii=False, indent=4)
            
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error adding new keys to {zh_cn_path}: {e}")

def synchronize_language_file(zh_cn_path: str, en_us_path: str):
    """
    Synchronizes a zh_cn.json file with an en_us.json file.
    - Adds keys from en_us.json that are missing in zh_cn.json.
    - Removes keys from zh_cn.json that are missing in en_us.json.
    """
    try:
        if not os.path.exists(en_us_path):
            print(f"Warning: English language file not found at {en_us_path}. Skipping synchronization for {zh_cn_path}.")
            return

        with open(en_us_path, 'r', encoding='utf-8') as f:
            en_data = json.load(f)

        zh_data = {} # Initialize as empty dictionary
        if os.path.exists(zh_cn_path):
            try:
                with open(zh_cn_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict): # Ensure it's a dictionary
                        zh_data = loaded_data
                    else:
                        print(f"Warning: {zh_cn_path} contains non-dictionary JSON. Initializing as empty for synchronization.")
            except json.JSONDecodeError:
                print(f"Warning: {zh_cn_path} contains invalid JSON. Initializing as empty for synchronization.")
        
        # Identify keys to add
        keys_to_add = {key: value for key, value in en_data.items() if key not in zh_data}
        # Identify keys to remove
        keys_to_remove = {key for key in zh_data if key not in en_data}

        # Apply additions
        for key, value in keys_to_add.items():
            zh_data[key] = value

        # Apply deletions
        for key in keys_to_remove:
            del zh_data[key]

        if keys_to_add or keys_to_remove:
            with open(zh_cn_path, 'w', encoding='utf-8') as f:
                json.dump(zh_data, f, ensure_ascii=False, indent=4)
            print(f"  - Synchronized {zh_cn_path}: Added {len(keys_to_add)} keys, Removed {len(keys_to_remove)} keys.")
        else:
            print(f"  - No synchronization needed for {zh_cn_path}.")

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error synchronizing language file {zh_cn_path}: {e}")