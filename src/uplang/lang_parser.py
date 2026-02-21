"""Utilities for discovering and parsing Minecraft mod language files."""

from __future__ import annotations

import re
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from pathlib import Path
from zipfile import BadZipFile, ZipFile, ZipInfo

from .json_parser import parse_language_json
from .models import (
    DEFAULT_TARGET_LOCALES,
    JarLanguageParseResult,
    JarParseError,
    LanguageParseFailure,
    LanguagePathMatch,
    ParsedLanguageFile,
)

LANG_PATH_REGEX = re.compile(
    r"^assets/(?P<mod_id>[A-Za-z0-9_.-]+)/lang/(?P<locale>[^/]+)\.json$"
)


def _normalize_locale_filter(
    target_locales: Iterable[str] | None,
) -> frozenset[str] | None:
    """Normalize locale filter values.

    Args:
        target_locales: Optional iterable of locale names.

    Returns:
        None when no filter is required, otherwise a lower-case set.
    """

    if target_locales is None:
        return None
    lowered = {locale.lower() for locale in target_locales}
    if len(lowered) == 0:
        return frozenset()
    return frozenset(lowered)


def _discover_language_paths_from_infos(
    zip_infos: Iterable[ZipInfo],
) -> tuple[LanguagePathMatch, ...]:
    """Discover language files from zip entry metadata.

    Args:
        zip_infos: Zip entry metadata iterable.

    Returns:
        A sorted tuple of unique language path matches.
    """

    deduplicated: dict[str, LanguagePathMatch] = {}
    for zip_info in zip_infos:
        normalized_path = zip_info.filename.replace("\\", "/")
        parsed = LANG_PATH_REGEX.fullmatch(normalized_path)
        if parsed is None:
            continue
        existing = deduplicated.get(normalized_path)
        offset = zip_info.header_offset
        if existing is None or offset < existing.absolute_offset:
            deduplicated[normalized_path] = LanguagePathMatch(
                internal_path=normalized_path,
                mod_id=parsed.group("mod_id"),
                locale=parsed.group("locale"),
                absolute_offset=offset,
            )
    return tuple(sorted(deduplicated.values(), key=lambda item: item.internal_path))


def discover_jar_language_paths(jar_path: Path) -> tuple[LanguagePathMatch, ...]:
    """Find language JSON file paths inside one mod jar.

    Args:
        jar_path: Path to the mod jar file.

    Returns:
        A sorted tuple of unique language path matches.

    Raises:
        JarParseError: If the jar cannot be read as a valid archive.
    """

    try:
        with ZipFile(jar_path, "r") as archive:
            return _discover_language_paths_from_infos(archive.infolist())
    except (BadZipFile, OSError) as exc:
        raise JarParseError(f"Failed to open jar: {jar_path}") from exc


def parse_mod_jar_languages(
    jar_path: Path,
    target_locales: Iterable[str] | None = DEFAULT_TARGET_LOCALES,
) -> JarLanguageParseResult:
    """Parse discovered language files for one mod jar.

    Args:
        jar_path: Path to one mod jar file.
        target_locales: Optional locale names to include.
            None means include all locales.

    Returns:
        Parsing result containing successful language files and failures.

    Raises:
        JarParseError: If the jar archive cannot be opened.
    """

    locale_filter = _normalize_locale_filter(target_locales)
    parsed_files: list[ParsedLanguageFile] = []
    failures: list[LanguageParseFailure] = []

    try:
        with ZipFile(jar_path, "r") as archive:
            path_matches = _discover_language_paths_from_infos(archive.infolist())
            if locale_filter is not None:
                path_matches = tuple(
                    item
                    for item in path_matches
                    if item.locale.lower() in locale_filter
                )
            if len(path_matches) == 0:
                return JarLanguageParseResult(
                    jar_path=jar_path,
                    language_files=(),
                    failures=(),
                )

            for match in path_matches:
                try:
                    content = archive.read(match.internal_path)
                except KeyError:
                    continue
                try:
                    translations = parse_language_json(content)
                except ValueError as exc:
                    failures.append(
                        LanguageParseFailure(
                            internal_path=match.internal_path,
                            reason=f"Invalid language JSON: {exc}",
                        )
                    )
                    continue
                parsed_files.append(
                    ParsedLanguageFile(
                        jar_path=jar_path,
                        internal_path=match.internal_path,
                        mod_id=match.mod_id,
                        locale=match.locale,
                        absolute_offset=match.absolute_offset,
                        translations=translations,
                    )
                )
    except (BadZipFile, OSError) as exc:
        raise JarParseError(f"Failed to open jar: {jar_path}") from exc

    return JarLanguageParseResult(
        jar_path=jar_path,
        language_files=tuple(parsed_files),
        failures=tuple(failures),
    )


def parse_mods_directory(
    mods_dir: Path,
    target_locales: Iterable[str] | None = DEFAULT_TARGET_LOCALES,
    max_workers: int | None = None,
) -> tuple[JarLanguageParseResult, ...]:
    """Parse language files for all jar mods in a directory.

    Args:
        mods_dir: Directory containing mod jar files.
        target_locales: Optional locale names to include.
            None means include all locales.
        max_workers: Optional thread count for parallel jar parsing.

    Returns:
        A tuple of per-jar parsing results sorted by file name.
    """

    jar_paths = sorted(mods_dir.glob("*.jar"), key=lambda path: path.name.lower())
    if len(jar_paths) == 0:
        return ()

    materialized_target_locales: tuple[str, ...] | None
    if target_locales is None:
        materialized_target_locales = None
    else:
        materialized_target_locales = tuple(target_locales)

    normalized_workers = max_workers
    if normalized_workers is not None and normalized_workers < 1:
        normalized_workers = 1

    if len(jar_paths) == 1:
        return (
            parse_mod_jar_languages(
                jar_paths[0],
                target_locales=materialized_target_locales,
            ),
        )

    with ThreadPoolExecutor(max_workers=normalized_workers) as executor:
        results = list(
            executor.map(
                parse_mod_jar_languages,
                jar_paths,
                repeat(materialized_target_locales, len(jar_paths)),
            )
        )
    return tuple(results)
