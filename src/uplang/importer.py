"""Logic for importing zh_cn translations from assets directories or zip files."""

from __future__ import annotations

import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import click

from .io import _load_translation_file
from .json_parser import parse_language_json

_ZH_LOCALE = "zh_cn"
_ZIP_IMPORT_ZH_PATH_REGEX = re.compile(
    r"^(?:.+/)?assets/(?P<mod_id>[A-Za-z0-9_.-]+)/lang/"
    rf"{_ZH_LOCALE}\.json$",
    flags=re.IGNORECASE,
)


def _load_imported_zh_from_directory(
    import_assets_dir: Path,
    target_mod_ids: set[str],
) -> dict[str, dict[str, str]]:
    """Load imported zh_cn translations for target mods from an assets directory.

    Args:
        import_assets_dir: Imported resource-pack assets directory.
        target_mod_ids: Mod ids that should be looked up.

    Returns:
        Mapping from mod id to imported zh_cn translation mapping.
    """

    imported_mappings: dict[str, dict[str, str]] = {}
    for mod_id in target_mod_ids:
        imported_zh_path = import_assets_dir / mod_id / "lang" / "zh_cn.json"
        if not imported_zh_path.exists():
            continue
        imported_mappings[mod_id] = _load_translation_file(imported_zh_path)
    return imported_mappings


def _load_imported_zh_from_zip(
    import_zip_path: Path,
    target_mod_ids: set[str],
) -> dict[str, dict[str, str]]:
    """Load imported zh_cn translations for target mods from a zip archive.

    Args:
        import_zip_path: Zip file containing imported translation assets.
        target_mod_ids: Mod ids that should be looked up.

    Returns:
        Mapping from mod id to imported zh_cn translation mapping.

    Raises:
        click.ClickException: If the zip file cannot be read or parsed.
    """

    candidate_paths: dict[str, str] = {}

    try:
        with ZipFile(import_zip_path, "r") as archive:
            for zip_info in archive.infolist():
                normalized_path = zip_info.filename.replace("\\", "/")
                matched = _ZIP_IMPORT_ZH_PATH_REGEX.fullmatch(normalized_path)
                if matched is None:
                    continue

                mod_id = matched.group("mod_id")
                if mod_id not in target_mod_ids:
                    continue

                existing_path = candidate_paths.get(mod_id)
                if existing_path is None:
                    candidate_paths[mod_id] = normalized_path
                    continue

                if len(normalized_path) < len(existing_path):
                    candidate_paths[mod_id] = normalized_path
                    continue

                if len(normalized_path) == len(existing_path):
                    candidate_paths[mod_id] = min(existing_path, normalized_path)

            imported_mappings: dict[str, dict[str, str]] = {}
            for mod_id, internal_path in candidate_paths.items():
                try:
                    content = archive.read(internal_path)
                except KeyError as exc:
                    raise click.ClickException(
                        "Missing language file in zip: "
                        f"{import_zip_path}!{internal_path}"
                    ) from exc

                try:
                    imported_mappings[mod_id] = parse_language_json(content)
                except ValueError as exc:
                    raise click.ClickException(
                        "Failed to parse language file in zip: "
                        f"{import_zip_path}!{internal_path}: {exc}"
                    ) from exc
    except (BadZipFile, OSError) as exc:
        raise click.ClickException(
            f"Failed to open import zip: {import_zip_path}"
        ) from exc

    return imported_mappings


def _load_imported_zh_mappings(
    import_source: Path,
    target_mod_ids: set[str],
) -> dict[str, dict[str, str]]:
    """Load imported zh_cn mappings from either a directory or zip file.

    Args:
        import_source: Imported assets directory or zip file path.
        target_mod_ids: Mod ids that should be looked up.

    Returns:
        Mapping from mod id to imported zh_cn translation mapping.

    Raises:
        click.ClickException: If import source type is unsupported.
    """

    if import_source.is_dir():
        return _load_imported_zh_from_directory(import_source, target_mod_ids)

    if import_source.is_file() and import_source.suffix.lower() == ".zip":
        return _load_imported_zh_from_zip(import_source, target_mod_ids)

    raise click.ClickException(
        f"Import source must be an assets directory or zip file: {import_source}"
    )
