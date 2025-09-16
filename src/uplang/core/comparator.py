import json

def compare_files(old_content: bytes, new_content: bytes) -> dict:
    """Compares two language files and returns the new keys found in the new file."""
    try:
        old_data = json.loads(old_content)
        new_data = json.loads(new_content)
    except json.JSONDecodeError:
        # Handle non-json .lang files if necessary in the future
        # For now, we assume JSON
        return {}

    new_keys = {}
    for key, value in new_data.items():
        if key not in old_data:
            new_keys[key] = value
    
    return new_keys