"""File I/O operations for reading and writing language translations."""

from __future__ import annotations

from pathlib import Path

import click
import orjson

from .json_parser import parse_language_json
from .utils import (
    _escape_private_use_characters,
    _restore_surrogate_escape_tokens,
    _sanitize_translations,
)


def _build_target_path(assets_dir: Path, mod_id: str, locale: str) -> Path:
    """Build the destination language file path.

    Args:
        assets_dir: Assets directory in the target resource pack.
        mod_id: Mod identifier used under the assets directory.
        locale: Locale name for the output language file.

    Returns:
        Full destination path for the output language JSON file.
    """

    return assets_dir / mod_id / "lang" / f"{locale}.json"


def _encode_translations(translations: dict[str, str]) -> bytes:
    """Encode translations to JSON bytes.

    Args:
        translations: Translation mapping to encode.

    Returns:
        UTF-8 encoded JSON bytes.
    """

    sanitized = _sanitize_translations(translations)
    encoded = orjson.dumps(sanitized, option=orjson.OPT_INDENT_2)
    escaped = _escape_private_use_characters(encoded.decode("utf-8"))
    escaped = _restore_surrogate_escape_tokens(escaped)
    return escaped.encode("utf-8")


def _load_translation_file(language_file_path: Path) -> dict[str, str]:
    """Load one language JSON file as a translation mapping.

    Args:
        language_file_path: Language JSON file path.

    Returns:
        Parsed translation mapping.

    Raises:
        click.ClickException: If file loading or parsing fails.
    """

    try:
        content = language_file_path.read_bytes()
    except OSError as exc:
        raise click.ClickException(
            f"Failed to read language file: {language_file_path}"
        ) from exc

    try:
        return parse_language_json(content)
    except ValueError as exc:
        raise click.ClickException(
            f"Failed to parse language file: {language_file_path}: {exc}"
        ) from exc
