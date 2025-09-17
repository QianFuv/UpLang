"""
Mod scanning functionality
"""

import hashlib
import json
import tomllib
import zipfile
from pathlib import Path
from typing import List, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from uplang.exceptions import ModScanError
from uplang.logger import UpLangLogger
from uplang.models import Mod, ModType
from uplang.utils import create_safe_mod_id


class ModScanner:

    def __init__(self, logger: UpLangLogger):
        self.logger = logger

    def scan_directory(self, mods_dir: Path) -> List[Mod]:
        """Scan a directory for mod JAR files and extract metadata"""
        if not mods_dir.exists() or not mods_dir.is_dir():
            raise ModScanError(f"Mods directory not found: {mods_dir}")

        jar_files = list(mods_dir.glob("*.jar"))
        jar_files = [f for f in jar_files if f.name != ".connector"]

        if not jar_files:
            self.logger.warning(f"No JAR files found in {mods_dir}")
            return []

        mods = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.logger.console,
            disable=self.logger._quiet_mode
        ) as progress:
            task = progress.add_task("Scanning mods...", total=len(jar_files))

            for jar_file in jar_files:
                try:
                    mod = self._scan_jar_file(jar_file)
                    if mod:
                        mods.append(mod)
                except Exception as e:
                    self.logger.warning(f"Failed to process {jar_file.name}: {e}")

                progress.advance(task)

        self.logger.info(f"Scanned {len(mods)} mods from {len(jar_files)} JAR files")
        return mods

    def _scan_jar_file(self, jar_path: Path) -> Optional[Mod]:
        """Scan a single JAR file for mod metadata"""
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar_file:
                mod = self._extract_forge_metadata(jar_file, jar_path)
                if not mod:
                    mod = self._extract_fabric_metadata(jar_file, jar_path)
                if not mod:
                    mod = self._extract_fallback_metadata(jar_file, jar_path)
                if not mod:
                    mod = self._create_unrecognized_mod(jar_path)

                return mod

        except (zipfile.BadZipFile, OSError) as e:
            raise ModScanError(f"Cannot read JAR file {jar_path}: {e}")

    def _extract_forge_metadata(self, jar_file: zipfile.ZipFile, jar_path: Path) -> Optional[Mod]:
        """Extract metadata from Forge mod"""
        if 'META-INF/mods.toml' not in jar_file.namelist():
            return None

        try:
            with jar_file.open('META-INF/mods.toml') as toml_file:
                content = self._decode_content(toml_file.read())
                toml_data = tomllib.loads(content)

                if not toml_data.get('mods') or len(toml_data['mods']) == 0:
                    return None

                mod_info = toml_data['mods'][0]
                return Mod(
                    mod_id=mod_info.get('modId', 'unknown'),
                    version=mod_info.get('version', 'unknown'),
                    file_path=jar_path,
                    mod_type=ModType.FORGE,
                    file_hash=self._calculate_hash(jar_path)
                )

        except (tomllib.TOMLDecodeError, KeyError, IndexError):
            return None

    def _extract_fabric_metadata(self, jar_file: zipfile.ZipFile, jar_path: Path) -> Optional[Mod]:
        """Extract metadata from Fabric mod"""
        if 'fabric.mod.json' not in jar_file.namelist():
            return None

        try:
            with jar_file.open('fabric.mod.json') as json_file:
                content = self._decode_content(json_file.read())
                mod_info = json.loads(content)

                return Mod(
                    mod_id=mod_info.get('id', 'unknown'),
                    version=mod_info.get('version', 'unknown'),
                    file_path=jar_path,
                    mod_type=ModType.FABRIC,
                    file_hash=self._calculate_hash(jar_path)
                )

        except (json.JSONDecodeError, KeyError):
            return None

    def _extract_fallback_metadata(self, jar_file: zipfile.ZipFile, jar_path: Path) -> Optional[Mod]:
        """Extract metadata by scanning for language files"""
        for file_path in jar_file.namelist():
            if file_path.startswith('assets/') and '/lang/' in file_path and file_path.endswith('.json'):
                parts = file_path.split('/')
                if len(parts) > 2 and parts[0] == 'assets':
                    mod_id = parts[1]
                    file_hash = self._calculate_hash(jar_path)
                    return Mod(
                        mod_id=mod_id,
                        version=file_hash[:8],
                        file_path=jar_path,
                        mod_type=ModType.UNKNOWN,
                        file_hash=file_hash
                    )
        return None

    def _create_unrecognized_mod(self, jar_path: Path) -> Mod:
        """Create a mod entry for unrecognized JAR files"""
        safe_mod_id = create_safe_mod_id(jar_path.name)
        return Mod(
            mod_id=safe_mod_id,
            version="unknown",
            file_path=jar_path,
            mod_type=ModType.UNKNOWN,
            file_hash=self._calculate_hash(jar_path)
        )

    @staticmethod
    def _calculate_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _decode_content(content_bytes: bytes) -> str:
        """Decode bytes content with fallback encoding"""
        try:
            return content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return content_bytes.decode('utf-8', errors='surrogateescape')