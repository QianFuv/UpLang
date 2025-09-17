import zipfile
import os
from typing import Optional, Tuple

from uplang.models import Mod

def extract_lang_file(mod: Mod, lang_code: str = "en_us") -> Optional[Tuple[str, bytes]]:
    """Extracts a specified language file from a mod's .jar file."""
    try:
        with zipfile.ZipFile(mod.file_path, 'r') as jar_file:
            # Common language file paths
            possible_paths = [
                f"assets/{mod.mod_id}/lang/{lang_code}.json",
                f"assets/{mod.mod_id}/lang/{lang_code}.lang"
            ]
            
            for path in possible_paths:
                if path in jar_file.namelist():
                    with jar_file.open(path) as lang_file:
                        return (path, lang_file.read())
    except Exception as e:
        print(f"Error extracting language file from {mod.file_path}: {e}")
    
    return None