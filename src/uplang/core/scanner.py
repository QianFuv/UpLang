"""
JAR file scanner for extracting mod metadata.
"""

import tomllib
from pathlib import Path
from zipfile import ZipFile

from uplang.exceptions import ModMetadataError, ModNotFoundError
from uplang.models import Mod, ModType
from uplang.utils.output import print_verbose


class ModScanner:
    """
    Scan JAR files and extract mod metadata.
    """

    def scan_directory(self, mods_dir: Path) -> list[Mod]:
        """
        Scan a directory for JAR files and extract mod information.
        """
        if not mods_dir.exists():
            raise ModNotFoundError(
                f"Mods directory not found: {mods_dir}",
                context={"path": str(mods_dir)},
            )

        jar_files = list(mods_dir.glob("*.jar"))
        print_verbose(f"Found {len(jar_files)} JAR files in {mods_dir}")

        mods = []
        for jar_path in jar_files:
            try:
                mod = self.scan_jar(jar_path)
                mods.append(mod)
                print_verbose(f"Scanned: {mod}")
            except Exception as e:
                print_verbose(f"Failed to scan {jar_path.name}: {e}")
                continue

        return mods

    def scan_jar(self, jar_path: Path) -> Mod:
        """
        Extract mod metadata from a JAR file.
        """
        if not jar_path.exists():
            raise ModNotFoundError(
                f"JAR file not found: {jar_path}", context={"path": str(jar_path)}
            )

        try:
            with ZipFile(jar_path, "r") as jar:
                mod = self._try_forge_metadata(jar, jar_path)
                if mod:
                    return mod

                mod = self._try_fabric_metadata(jar, jar_path)
                if mod:
                    return mod

                mod = self._try_neoforge_metadata(jar, jar_path)
                if mod:
                    return mod

        except Exception as e:
            raise ModMetadataError(
                f"Failed to read JAR file: {e}", context={"path": str(jar_path)}
            ) from e

        return self._create_fallback_mod(jar_path)

    def _try_forge_metadata(self, jar: ZipFile, jar_path: Path) -> Mod | None:
        """
        Try to extract Forge mod metadata.
        """
        try:
            if "META-INF/mods.toml" not in jar.namelist():
                return None

            with jar.open("META-INF/mods.toml") as f:
                toml_data = tomllib.loads(f.read().decode("utf-8"))

            if "mods" not in toml_data or not toml_data["mods"]:
                return None

            mod_info = toml_data["mods"][0]
            return Mod(
                mod_id=mod_info.get("modId", jar_path.stem),
                name=mod_info.get("displayName", mod_info.get("modId", jar_path.stem)),
                version=mod_info.get("version", "unknown"),
                jar_path=jar_path,
                mod_type=ModType.FORGE,
            )
        except Exception:
            return None

    def _try_fabric_metadata(self, jar: ZipFile, jar_path: Path) -> Mod | None:
        """
        Try to extract Fabric mod metadata.
        """
        try:
            if "fabric.mod.json" not in jar.namelist():
                return None

            with jar.open("fabric.mod.json") as f:
                import json

                json_data = json.loads(f.read().decode("utf-8"))

            return Mod(
                mod_id=json_data.get("id", jar_path.stem),
                name=json_data.get("name", json_data.get("id", jar_path.stem)),
                version=json_data.get("version", "unknown"),
                jar_path=jar_path,
                mod_type=ModType.FABRIC,
            )
        except Exception:
            return None

    def _try_neoforge_metadata(self, jar: ZipFile, jar_path: Path) -> Mod | None:
        """
        Try to extract NeoForge mod metadata.
        """
        try:
            if "META-INF/neoforge.mods.toml" not in jar.namelist():
                return None

            with jar.open("META-INF/neoforge.mods.toml") as f:
                toml_data = tomllib.loads(f.read().decode("utf-8"))

            if "mods" not in toml_data or not toml_data["mods"]:
                return None

            mod_info = toml_data["mods"][0]
            return Mod(
                mod_id=mod_info.get("modId", jar_path.stem),
                name=mod_info.get("displayName", mod_info.get("modId", jar_path.stem)),
                version=mod_info.get("version", "unknown"),
                jar_path=jar_path,
                mod_type=ModType.NEOFORGE,
            )
        except Exception:
            return None

    def _create_fallback_mod(self, jar_path: Path) -> Mod:
        """
        Create a fallback Mod object when metadata cannot be extracted.
        """
        from uplang.utils.path_utils import extract_mod_id

        mod_id = extract_mod_id(jar_path)
        print_verbose(f"Using fallback mod_id for {jar_path.name}: {mod_id}")

        return Mod(
            mod_id=mod_id,
            name=jar_path.stem,
            version="unknown",
            jar_path=jar_path,
            mod_type=ModType.UNKNOWN,
        )
