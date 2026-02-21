"""Data models and core definitions for the uplang package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_TARGET_LOCALES: frozenset[str] = frozenset({"en_us", "zh_cn"})


@dataclass(frozen=True, slots=True)
class LanguagePathMatch:
    """Represents one language file path discovered inside a mod jar.

    Args:
        internal_path: The zip internal path of the language file.
        mod_id: The mod identifier extracted from the internal path.
        locale: The locale name extracted from the file name.
        absolute_offset: The zip header offset for the language file entry.

    Returns:
        None.
    """

    internal_path: str
    mod_id: str
    locale: str
    absolute_offset: int


@dataclass(frozen=True, slots=True)
class ParsedLanguageFile:
    """Represents one parsed language JSON file from a mod jar.

    Args:
        jar_path: The source jar file path.
        internal_path: The zip internal path of the language file.
        mod_id: The mod identifier extracted from the internal path.
        locale: The locale name extracted from the file name.
        absolute_offset: The zip header offset for the language file entry.
        translations: Parsed translation key-value mapping.

    Returns:
        None.
    """

    jar_path: Path
    internal_path: str
    mod_id: str
    locale: str
    absolute_offset: int
    translations: dict[str, str]


@dataclass(frozen=True, slots=True)
class LanguageParseFailure:
    """Represents a language parsing failure for one jar entry.

    Args:
        internal_path: The zip internal path that failed to parse.
        reason: A concise reason for the failure.

    Returns:
        None.
    """

    internal_path: str
    reason: str


@dataclass(frozen=True, slots=True)
class JarLanguageParseResult:
    """Contains parsed language files and failures for one mod jar.

    Args:
        jar_path: The source jar file path.
        language_files: Successfully parsed language files.
        failures: Language files that failed to read or parse.

    Returns:
        None.
    """

    jar_path: Path
    language_files: tuple[ParsedLanguageFile, ...]
    failures: tuple[LanguageParseFailure, ...]


class JarParseError(Exception):
    """Raised when a jar file cannot be opened or searched."""
