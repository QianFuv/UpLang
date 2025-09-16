import os
import zipfile
import tomllib
import json
import hashlib
from typing import List

from uplang.models import Mod

def _calculate_hash(file_path: str) -> str:
    """Calculates the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def scan_mods(mods_dir: str) -> List[Mod]:
    """Scans a directory for mod .jar files and extracts their metadata."""
    mods: List[Mod] = []
    
    if not os.path.isdir(mods_dir):
        print(f"Error: Mods directory not found at '{mods_dir}'")
        return mods

    for item in os.scandir(mods_dir):
        if item.name == ".connector":
            continue

        if item.is_file() and item.name.endswith(".jar"):
            try:
                with zipfile.ZipFile(item.path, 'r') as jar_file:
                    mod_info_found = False
                    # Check for Forge mods
                    if 'META-INF/mods.toml' in jar_file.namelist():
                        with jar_file.open('META-INF/mods.toml') as toml_file:
                            toml_data = tomllib.load(toml_file)
                            if toml_data.get('mods') and len(toml_data['mods']) > 0:
                                mod_info = toml_data['mods'][0]
                                mod = Mod(
                                    mod_id=mod_info.get('modId', 'unknown'),
                                    version=mod_info.get('version', 'unknown'),
                                    file_path=item.path,
                                    file_hash=_calculate_hash(item.path)
                                )
                                mods.append(mod)
                                mod_info_found = True
                    
                    # Check for Fabric mods if not a Forge mod
                    if not mod_info_found and 'fabric.mod.json' in jar_file.namelist():
                        with jar_file.open('fabric.mod.json') as json_file:
                            mod_info = json.load(json_file)
                            mod = Mod(
                                mod_id=mod_info.get('id', 'unknown'),
                                version=mod_info.get('version', 'unknown'),
                                file_path=item.path,
                                file_hash=_calculate_hash(item.path)
                            )
                            mods.append(mod)
                            mod_info_found = True

                    # Fallback to file hashing and path scanning
                    if not mod_info_found:
                        for file_in_jar in jar_file.namelist():
                            if file_in_jar.startswith('assets/') and '/lang/' in file_in_jar and file_in_jar.endswith('.json'):
                                parts = file_in_jar.split('/')
                                if len(parts) > 2 and parts[0] == 'assets':
                                    mod_id = parts[1]
                                    file_hash = _calculate_hash(item.path)
                                    mod = Mod(
                                        mod_id=mod_id,
                                        version=file_hash,
                                        file_path=item.path,
                                        file_hash=file_hash
                                    )
                                    mods.append(mod)
                                    break  # Found mod_id, no need to check other files

            except Exception as e:
                print(f"Could not process {item.name}: {e}")
                
    return mods
