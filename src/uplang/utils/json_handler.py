"""
JSON file handler with format preservation.
"""

import json
import re
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from uplang.exceptions import JSONParseError, LanguageFileError


def _escape_pua_in_json_string(json_str: str) -> str:
    """
    Replace PUA, surrogate, and noncharacters with escape sequences.
    Preserves other Unicode characters (Chinese, §, etc.) as UTF-8 bytes.

    Escapes:
    - Private Use Area (BMP): U+E000-U+F8FF
    - Surrogates: U+D800-U+DFFF
    - Noncharacters: U+FDD0-U+FDEF
    - Plane-ending noncharacters: U+FFFE, U+FFFF

    Uses uppercase hex to match JAR format.
    """
    result = []
    for char in json_str:
        code = ord(char)
        if (
            0xE000 <= code <= 0xF8FF
            or 0xD800 <= code <= 0xDFFF
            or 0xFDD0 <= code <= 0xFDEF
            or code in (0xFFFE, 0xFFFF)
        ):
            result.append(f"\\u{code:04X}")
        else:
            result.append(char)
    return "".join(result)


class JSONHandler:
    """
    Handle JSON files while preserving formatting and key order.
    """

    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.map_indent = 2
        self.yaml.sequence_indent = 2
        self.yaml.default_flow_style = False
        self.yaml.allow_duplicate_keys = True

    def _clean_control_chars(self, text: str) -> str:
        """
        Remove control characters that YAML parser cannot handle.
        Filters out C0 (0x00-0x1F) and C1 (0x80-0x9F) control characters.
        Preserves surrogate pairs for emoji support.
        """
        result = []
        for char in text:
            code = ord(char)
            if (
                code in (ord("\n"), ord("\r"), ord("\t"))
                or 0xD800 <= code <= 0xDFFF
                or (0x20 <= code < 0x7F)
                or code >= 0xA0
            ):
                result.append(char)
            else:
                result.append(" ")
        return "".join(result)

    def _find_comment_position(self, line: str) -> int:
        """
        Find the position of // comment start, ignoring // inside quoted strings.
        Returns -1 if no comment found.
        """
        in_string = False
        escape_next = False

        for i in range(len(line) - 1):
            if escape_next:
                escape_next = False
                continue

            char = line[i]

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if not in_string and line[i:i+2] == '//':
                return i

        return -1

    def _strip_comments(self, text: str) -> str:
        """
        Remove single-line and multi-line comments from JSON text.
        """
        text = text.replace("\t", " ")
        text = text.lstrip()
        text = self._clean_control_chars(text)

        lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            comment_pos = self._find_comment_position(line)
            if comment_pos > 0:
                before_comment = line[:comment_pos].rstrip()
                if before_comment and not before_comment.endswith(","):
                    if lines and lines[-1].rstrip().endswith(":"):
                        line = before_comment
                    else:
                        continue
                else:
                    line = before_comment
            lines.append(line)

        result = "\n".join(lines)
        result = re.sub(r"/\*.*?\*/", "", result, flags=re.DOTALL)
        return result

    def load(self, file_path: Path) -> dict[str, Any]:
        """
        Load JSON file preserving order and format.
        """
        if not file_path.exists():
            raise LanguageFileError(
                f"File not found: {file_path}", context={"path": str(file_path)}
            )

        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        last_error = None

        for encoding in encodings:
            try:
                errors = (
                    "surrogatepass" if encoding in ("utf-8", "utf-8-sig") else "strict"
                )
                with open(file_path, encoding=encoding, errors=errors) as f:
                    text = f.read()
                    text = self._strip_comments(text)

                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        data = self.yaml.load(text)

                    if data is None:
                        return {}
                    if not isinstance(data, dict):
                        raise JSONParseError(
                            f"Expected dict, got {type(data).__name__}",
                            context={"path": str(file_path)},
                        )
                    return data
            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                continue
            except Exception as e:
                raise JSONParseError(
                    f"Failed to parse JSON: {e}",
                    context={"path": str(file_path), "encoding": encoding},
                ) from e

        raise JSONParseError(
            f"Failed to read file with any encoding: {last_error}",
            context={"path": str(file_path), "encodings": encodings},
        ) from last_error

    def load_from_bytes(self, content: bytes) -> dict[str, Any]:
        """
        Load JSON from bytes preserving order and format.
        """
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        last_error = None

        for encoding in encodings:
            try:
                errors = (
                    "surrogatepass" if encoding in ("utf-8", "utf-8-sig") else "strict"
                )
                text = content.decode(encoding, errors=errors)
                text = self._strip_comments(text)

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = self.yaml.load(text)

                if data is None:
                    return {}
                if not isinstance(data, dict):
                    raise JSONParseError(
                        f"Expected dict, got {type(data).__name__}",
                        context={"encoding": encoding},
                    )
                return data
            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                continue
            except Exception as e:
                raise JSONParseError(
                    f"Failed to parse JSON: {e}", context={"encoding": encoding}
                ) from e

        raise JSONParseError(
            f"Failed to decode bytes with any encoding: {last_error}",
            context={"encodings": encodings},
        ) from last_error

    def dump(self, data: dict[str, Any], file_path: Path) -> None:
        """
        Save JSON file preserving order and format.
        Uses ensure_ascii=False to keep Unicode (Chinese, §) as UTF-8,
        but escapes PUA characters to match JAR format.
        Uses system default line endings for Git compatibility.
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            json_str = _escape_pua_in_json_string(json_str)
            with open(
                file_path, "w", encoding="utf-8", errors="surrogatepass"
            ) as f:
                f.write(json_str)
                f.write("\n")
        except Exception as e:
            raise LanguageFileError(
                f"Failed to write JSON file: {e}", context={"path": str(file_path)}
            ) from e
