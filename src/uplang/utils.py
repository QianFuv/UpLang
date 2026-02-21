"""Utility functions for string and translation sanitization."""

from __future__ import annotations

import re

_SURROGATE_TOKEN_PATTERN = re.compile(r"__UPLANG_SURR_([0-9A-F]{4})__")
_CJK_CHARACTER_PATTERN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
_ASCII_LETTER_PATTERN = re.compile(r"[A-Za-z]")


def _sanitize_utf8_string(value: str) -> str:
    """Replace surrogate code points with reversible token placeholders.

    Args:
        value: Source string that may contain surrogate code points.

    Returns:
        UTF-8 safe string without surrogate code points.
    """

    chunks: list[str] = []
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            chunks.append(f"__UPLANG_SURR_{codepoint:04X}__")
        else:
            chunks.append(character)
    return "".join(chunks)


def _sanitize_translations(translations: dict[str, str]) -> dict[str, str]:
    """Sanitize translation keys and values for UTF-8 output.

    Args:
        translations: Original translation mapping.

    Returns:
        Translation mapping without surrogate code points.
    """

    return {
        _sanitize_utf8_string(key): _sanitize_utf8_string(value)
        for key, value in translations.items()
    }


def _is_private_use_codepoint(codepoint: int) -> bool:
    """Check whether codepoint is in Unicode private-use ranges.

    Args:
        codepoint: Unicode codepoint integer value.

    Returns:
        True when codepoint is private-use, otherwise False.
    """

    return (
        0xE000 <= codepoint <= 0xF8FF
        or 0xF0000 <= codepoint <= 0xFFFFD
        or 0x100000 <= codepoint <= 0x10FFFD
    )


def _escape_codepoint_as_json_unicode(codepoint: int) -> str:
    """Escape one codepoint using JSON-compatible unicode escapes.

    Args:
        codepoint: Unicode codepoint integer value.

    Returns:
        JSON unicode escape sequence for the codepoint.
    """

    if codepoint <= 0xFFFF:
        return f"\\u{codepoint:04X}"
    normalized = codepoint - 0x10000
    high = 0xD800 + (normalized >> 10)
    low = 0xDC00 + (normalized & 0x3FF)
    return f"\\u{high:04X}\\u{low:04X}"


def _escape_private_use_characters(text: str) -> str:
    """Escape private-use characters as unicode escape sequences.

    Args:
        text: UTF-8 JSON text.

    Returns:
        JSON text where private-use characters are represented as escapes.
    """

    chunks: list[str] = []
    for character in text:
        codepoint = ord(character)
        if _is_private_use_codepoint(codepoint):
            chunks.append(_escape_codepoint_as_json_unicode(codepoint))
        else:
            chunks.append(character)
    return "".join(chunks)


def _restore_surrogate_escape_tokens(text: str) -> str:
    """Restore surrogate token placeholders into unicode escape sequences.

    Args:
        text: UTF-8 JSON text with surrogate token placeholders.

    Returns:
        JSON text with surrogate escapes.
    """

    return _SURROGATE_TOKEN_PATTERN.sub(r"\\u\1", text)


def _contains_cjk_character(text: str) -> bool:
    """Check whether text contains CJK ideograph characters.

    Args:
        text: Input text to inspect.

    Returns:
        True when at least one CJK ideograph is present.
    """

    return _CJK_CHARACTER_PATTERN.search(text) is not None


def _is_untranslated_value(value: str, english_reference: str | None) -> bool:
    """Determine whether one zh_cn value is likely still untranslated.

    Args:
        value: Value from the current zh_cn translation file.
        english_reference: Optional value from the matching en_us key.

    Returns:
        True when value appears to be untranslated English text.
    """

    normalized_value = value.strip()
    if normalized_value == "":
        return False

    if english_reference is not None and normalized_value == english_reference.strip():
        return True

    if _contains_cjk_character(normalized_value):
        return False

    return _ASCII_LETTER_PATTERN.search(normalized_value) is not None
