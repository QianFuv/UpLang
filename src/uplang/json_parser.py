"""Tolerant JSON parser with compatibility handling."""

from __future__ import annotations

import json
import re
from typing import Any, cast

import orjson

FALLBACK_JSON_ENCODINGS: tuple[str, ...] = (
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "utf-32",
    "utf-32-le",
    "utf-32-be",
    "gb18030",
    "cp1252",
)


def _remove_json_comments(text: str) -> str:
    """Remove JSON-like comments from text while preserving strings.

    Args:
        text: Source text that may contain comments.

    Returns:
        Text without comment segments.
    """

    result: list[str] = []
    in_string = False
    escaped = False
    only_whitespace_since_newline = True
    index = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            if char in "\r\n":
                only_whitespace_since_newline = True
            index += 1
            continue

        if char == '"':
            in_string = True
            only_whitespace_since_newline = False
            result.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue

        if char == "#" and only_whitespace_since_newline:
            index += 1
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue

        result.append(char)
        if char in "\r\n":
            only_whitespace_since_newline = True
        elif char in " \t":
            pass
        else:
            only_whitespace_since_newline = False
        index += 1

    return "".join(result)


def _wrap_json_object_if_needed(text: str) -> str:
    """Wrap key-value only content in object braces when possible.

    Args:
        text: Source text that may miss outer braces.

    Returns:
        Normalized text with object braces when applicable.
    """

    stripped = text.strip()
    if stripped == "":
        return text
    if stripped.startswith("{") or stripped.startswith("["):
        return text
    if not re.search(r'"[^"]*"\s*:', stripped):
        return text
    return "{\n" + stripped + "\n}"


def _strip_trailing_commas(text: str) -> str:
    """Strip trailing commas before object or array endings.

    Args:
        text: Source text that may contain trailing commas.

    Returns:
        Text without trailing commas before closing delimiters.
    """

    return re.sub(r",\s*([}\]])", r"\1", text)


def _extract_first_json_root(text: str) -> str:
    """Extract the first complete root JSON value from text.

    Args:
        text: Source text that may include trailing garbage.

    Returns:
        The first complete root JSON value or the original stripped text.
    """

    stripped = text.strip()
    if stripped == "":
        return stripped
    opener = stripped[0]
    if opener not in "[{":
        return stripped
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(stripped):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == opener:
            depth += 1
            continue
        if char == closer:
            depth -= 1
            if depth == 0:
                return stripped[: index + 1]

    return stripped


def _close_unbalanced_braces(text: str) -> str:
    """Close unbalanced object or array delimiters.

    Args:
        text: Source text that may end with missing closers.

    Returns:
        Text with appended closing delimiters when detectable.
    """

    open_curly = 0
    close_curly = 0
    open_square = 0
    close_square = 0
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            open_curly += 1
        elif char == "}":
            close_curly += 1
        elif char == "[":
            open_square += 1
        elif char == "]":
            close_square += 1

    missing_curly = max(0, open_curly - close_curly)
    missing_square = max(0, open_square - close_square)
    if missing_curly == 0 and missing_square == 0:
        return text
    return text + ("]" * missing_square) + ("}" * missing_curly)


def _convert_json_value(raw_value: Any) -> str:
    """Convert JSON object value to string.

    Args:
        raw_value: Value from tolerant JSON parsing.

    Returns:
        String representation of the value.
    """

    if isinstance(raw_value, str):
        return raw_value
    if isinstance(raw_value, bool):
        return "true" if raw_value else "false"
    if raw_value is None:
        return "null"
    return str(raw_value)


def _coerce_translation_map(raw_mapping: dict[str, Any]) -> dict[str, str]:
    """Coerce parsed mapping values into string values.

    Args:
        raw_mapping: Parsed JSON object.

    Returns:
        Translation mapping with string keys and values.
    """

    return {
        key: _convert_json_value(value)
        for key, value in raw_mapping.items()
    }


def _tolerant_json_decode(content: bytes) -> dict[str, str]:
    """Decode JSON content with compatibility normalization.

    Args:
        content: Raw language file bytes.

    Returns:
        Parsed translation mapping.

    Raises:
        ValueError: If no tolerant strategy can parse the content.
    """

    decode_candidates: list[str] = ["utf-8", *FALLBACK_JSON_ENCODINGS, "latin-1"]
    seen_encodings: set[str] = set()

    for encoding in decode_candidates:
        if encoding in seen_encodings:
            continue
        seen_encodings.add(encoding)
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            continue

        normalized = text.lstrip("\ufeff")
        normalized = normalized.replace("\x00", "")
        normalized = _remove_json_comments(normalized)
        normalized = _wrap_json_object_if_needed(normalized)
        normalized = _strip_trailing_commas(normalized)
        normalized = _extract_first_json_root(normalized)
        normalized = _close_unbalanced_braces(normalized)

        if normalized.strip() == "":
            return {}

        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError:
            continue

        if not isinstance(parsed, dict):
            continue
        coerced = _coerce_translation_map(parsed)
        if len(coerced) == 0 and len(parsed) > 0:
            continue
        return coerced

    raise ValueError("Unable to parse language JSON with compatibility modes")


def parse_language_json(content: bytes) -> dict[str, str]:
    """Parse one language JSON payload with compatibility handling.

    Args:
        content: Raw JSON bytes from a language file.

    Returns:
        Parsed translation key-value mapping.

    Raises:
        ValueError: If decoding fails after compatibility strategies.
    """

    try:
        parsed = orjson.loads(content)
    except orjson.JSONDecodeError:
        return _tolerant_json_decode(content)

    if not isinstance(parsed, dict):
        return _tolerant_json_decode(content)

    if all(
        isinstance(key, str) and isinstance(value, str) for key, value in parsed.items()
    ):
        return cast(dict[str, str], parsed)

    return _tolerant_json_decode(content)
