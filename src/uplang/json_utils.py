"""
JSON handling utilities with robust error handling.

This module provides comprehensive JSON parsing and writing functionality
with support for multiple encodings, malformed JSON recovery, and order preservation.
"""

import json
import re
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Any, Optional, Union, Mapping
from contextlib import contextmanager


def read_json_robust(file_path: Path, logger=None) -> OrderedDict[str, Any]:
    """Read JSON file with robust encoding and format handling.

    This function implements multiple fallback strategies to handle
    various JSON encoding and formatting issues commonly found in
    Minecraft mod language files.

    Handles:
    - UTF-8 BOM removal
    - Multiple encoding strategies (UTF-8, Latin1, CP1252)
    - Surrogate character cleaning
    - Malformed JSON (trailing commas, unquoted keys, comments)
    - Order preservation using OrderedDict

    Args:
        file_path: Path to JSON file to read
        logger: Optional logger for debug messages

    Returns:
        OrderedDict containing parsed JSON data, empty OrderedDict on failure
    """
    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()

        # Handle UTF-8 BOM
        if content_bytes.startswith(b'\xef\xbb\xbf'):
            content_bytes = content_bytes[3:]
            if logger:
                logger.debug(f"Removed UTF-8 BOM from {file_path.name}")

        # Try different encoding strategies
        content_str = None
        encoding_used = None

        for encoding, error_handler in [
            ('utf-8', 'strict'),
            ('utf-8', 'replace'),
            ('utf-8-sig', 'replace'),
            ('latin1', 'replace'),
            ('cp1252', 'replace')
        ]:
            try:
                content_str = content_bytes.decode(encoding, errors=error_handler)
                encoding_used = f"{encoding} with {error_handler}"
                if encoding != 'utf-8' or error_handler != 'strict':
                    if logger:
                        logger.debug(f"Used {encoding_used} for {file_path.name}")
                break
            except UnicodeDecodeError:
                continue

        if content_str is None:
            if logger:
                logger.warning(f"Could not decode {file_path} with any encoding")
            return OrderedDict()

        # Clean up surrogate characters
        content_str = clean_surrogate_chars(content_str)

        # Try to parse JSON with multiple strategies
        parse_strategies = [
            ("direct", lambda x: json.loads(x, object_pairs_hook=OrderedDict)),
            ("fixed", lambda x: json.loads(fix_common_json_issues(x), object_pairs_hook=OrderedDict)),
            ("aggressive_fix", lambda x: json.loads(aggressive_json_fix(x), object_pairs_hook=OrderedDict)),
            ("extract_dict", lambda x: extract_dict_from_malformed_json(x))
        ]

        for strategy_name, strategy_func in parse_strategies:
            try:
                result = strategy_func(content_str)
                if isinstance(result, dict):  # Accept empty dicts too
                    if strategy_name != "direct" and logger:
                        logger.debug(f"Used {strategy_name} strategy for {file_path.name}")
                    # Ensure we always return OrderedDict
                    if isinstance(result, OrderedDict):
                        return result
                    else:
                        return OrderedDict(result)
            except json.JSONDecodeError as e:
                if strategy_name == "direct" and logger:
                    logger.debug(f"Initial JSON parse failed for {file_path.name}: {e}")
                continue
            except Exception:
                continue

        if logger:
            logger.warning(f"Could not parse JSON in {file_path} with any strategy")
        return OrderedDict()

    except OSError as e:
        if logger:
            logger.warning(f"Failed to read {file_path}: {e}")
        return OrderedDict()


def clean_surrogate_chars(text: str) -> str:
    """Remove or replace surrogate characters that can't be encoded in UTF-8.

    Args:
        text: Input text that may contain surrogate characters

    Returns:
        Cleaned text with surrogate characters removed
    """
    # Remove high and low surrogate characters
    text = re.sub(r'[\ud800-\udfff]', '', text)
    return text


def fix_common_json_issues(json_str: str) -> str:
    """Attempt to fix common JSON formatting issues.

    This function applies various fixes to handle malformed JSON
    commonly found in Minecraft mod files.

    Fixes:
    - Trailing commas before closing brackets
    - Unquoted object keys
    - Single-line and multi-line comments
    - Invalid control characters
    - Missing colons between keys and values
    - Malformed string values

    Args:
        json_str: Raw JSON string to fix

    Returns:
        Fixed JSON string
    """
    # Remove comments first
    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

    # Remove or replace invalid control characters (except allowed ones)
    # Keep only: \t (tab), \n (newline), \r (carriage return)
    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', json_str)

    # Fix missing colons between keys and values
    # Pattern: "key" "value" -> "key": "value"
    json_str = re.sub(r'("[\w\s.:-]+")(\s+)("[\w\s.:-]*")', r'\1:\3', json_str)

    # Remove trailing commas before closing brackets/braces
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # Try to quote unquoted keys (more comprehensive)
    # Handle keys that might contain dots, hyphens, etc.
    json_str = re.sub(r'(\s*)([a-zA-Z_][\w.-]*)\s*:', r'\1"\2":', json_str)

    # Fix malformed quoted keys (double quotes within quotes)
    json_str = re.sub(r'"([^"]*)"([^"]*)"(\s*:)', r'"\1\2"\3', json_str)

    # Fix incomplete string values at end of lines
    lines = json_str.split('\n')
    fixed_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.endswith((',', '}', ']', '"')) and ':' in line and not line.endswith(':'):
            # This might be an incomplete string value
            if line.count('"') % 2 == 1:  # Odd number of quotes
                line += '"'
        fixed_lines.append(line)
    json_str = '\n'.join(fixed_lines)

    return json_str


def aggressive_json_fix(json_str: str) -> str:
    """More aggressive JSON fixing for severely malformed files.

    Used as a fallback when standard fixes fail. Applies more
    intrusive transformations to attempt parsing.

    Args:
        json_str: JSON string that failed standard parsing

    Returns:
        Heavily modified JSON string
    """
    # Apply basic fixes first
    json_str = fix_common_json_issues(json_str)

    # Remove any remaining invalid characters
    json_str = re.sub(r'[^\x20-\x7E\t\n\r\u00A0-\uFFFF]', '', json_str)

    # Try to fix broken key-value pairs
    # Look for patterns like: "key" value without colon
    json_str = re.sub(r'("[\w\s.-]+")(\s+)(["\w])', r'\1: \3', json_str)

    # Fix broken strings (missing quotes)
    lines = json_str.split('\n')
    fixed_lines = []

    for line in lines:
        stripped = line.strip()
        if ':' in stripped and not stripped.startswith('"'):
            # Try to identify and fix unquoted values
            parts = stripped.split(':', 1)
            if len(parts) == 2:
                key_part = parts[0].strip()
                value_part = parts[1].strip()

                # Ensure key is quoted
                if not (key_part.startswith('"') and key_part.endswith('"')):
                    if key_part.startswith('"'):
                        key_part = key_part + '"'
                    elif key_part.endswith('"'):
                        key_part = '"' + key_part
                    else:
                        key_part = f'"{key_part}"'

                # Ensure value is quoted if it's not a number/boolean/null
                if value_part and not (
                    value_part.startswith('"') or
                    value_part.startswith('{') or
                    value_part.startswith('[') or
                    value_part.lower() in ['true', 'false', 'null'] or
                    re.match(r'^-?\d+(\.\d+)?$', value_part.rstrip(','))
                ):
                    value_part = value_part.rstrip(',')
                    if not value_part.startswith('"'):
                        value_part = f'"{value_part}"'
                    if line.strip().endswith(','):
                        value_part += ','

                fixed_line = '  ' + key_part + ': ' + value_part
                fixed_lines.append(fixed_line)
                continue

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def extract_dict_from_malformed_json(json_str: str) -> OrderedDict:
    """Last resort: extract key-value pairs from severely malformed JSON.

    When all parsing strategies fail, this function uses regex patterns
    to extract anything that looks like key-value pairs.

    Args:
        json_str: Malformed JSON string

    Returns:
        OrderedDict with extracted key-value pairs
    """
    result = OrderedDict()

    # Look for patterns that look like key-value pairs
    # Pattern: anything that looks like "key": "value" or key: value
    patterns = [
        r'"([^"]+)"\s*:\s*"([^"]*)"',  # "key": "value"
        r'"([^"]+)"\s*:\s*([^,}\n]+)',  # "key": value
        r'([a-zA-Z_][\w.-]*)\s*:\s*"([^"]*)"',  # key: "value"
        r'([a-zA-Z_][\w.-]*)\s*:\s*([^,}\n]+)',  # key: value
    ]

    for pattern in patterns:
        matches = re.findall(pattern, json_str, re.MULTILINE)
        for match in matches:
            key, value = match
            key = key.strip().strip('"')
            value = str(value).strip().strip('"').rstrip(',').strip()

            # Skip obviously invalid entries
            if key and value and len(key) < 200 and len(value) < 1000:
                # Clean the value
                value = re.sub(r'[^\x20-\x7E\t\n\r\u00A0-\uFFFF]', '', value)
                if value:  # Only add if value is not empty after cleaning
                    result[key] = value

    return result


def write_json_safe(file_path: Path, data: Mapping[str, Any], logger=None):
    """Write JSON file with proper encoding and error handling.

    Ensures proper UTF-8 encoding and removes any problematic
    surrogate characters before writing.

    Args:
        file_path: Path where to write the JSON file
        data: Mapping (dict or OrderedDict) to serialize as JSON
        logger: Optional logger for error messages

    Raises:
        OSError: If file cannot be written
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean any surrogate characters from the data
        cleaned_data = clean_data_surrogates(data)

        # Write with UTF-8 encoding, replacing any problematic characters
        # Use sort_keys=False to preserve the original key order
        json_str = json.dumps(cleaned_data, ensure_ascii=False, indent=4, sort_keys=False)

        # Remove any remaining surrogate characters from the JSON string
        json_str = clean_surrogate_chars(json_str)

        with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(json_str)

    except OSError as e:
        raise OSError(f"Failed to write {file_path}: {e}")


def clean_data_surrogates(data):
    """Recursively clean surrogate characters from data structures.

    Args:
        data: Data structure (dict, list, str, or other) to clean

    Returns:
        Cleaned data structure with surrogate characters removed
    """
    if isinstance(data, dict):
        return {clean_surrogate_chars(k) if isinstance(k, str) else k:
               clean_data_surrogates(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_surrogates(item) for item in data]
    elif isinstance(data, str):
        return clean_surrogate_chars(data)
    else:
        return data


class TempJsonProcessor:
    """Unified processor for handling JSON content via temporary files.

    This class provides utilities for processing JSON content that may
    be in bytes form or require temporary file handling.
    """

    @staticmethod
    @contextmanager
    def temp_file(content_bytes: bytes, suffix='.json'):
        """Context manager for temporary file handling.

        Args:
            content_bytes: Bytes content to write to temporary file
            suffix: File suffix for temporary file

        Yields:
            Path object for the temporary file
        """
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp_file:
                tmp_file.write(content_bytes)
                temp_path = Path(tmp_file.name)
            yield temp_path
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    @staticmethod
    def process_bytes_to_dict(content_bytes: bytes, logger=None) -> Optional[OrderedDict[str, Any]]:
        """Process bytes content to JSON dict using temporary file.

        Args:
            content_bytes: Raw bytes containing JSON data
            logger: Optional logger for debug messages

        Returns:
            Parsed OrderedDict or None if parsing fails
        """
        try:
            with TempJsonProcessor.temp_file(content_bytes) as temp_path:
                result = read_json_robust(temp_path, logger)
                return result if isinstance(result, OrderedDict) else None
        except Exception as e:
            if logger:
                logger.debug(f"Failed to process bytes to JSON dict: {e}")
            return None

    @staticmethod
    def validate_json_bytes(content_bytes: bytes, logger=None) -> bool:
        """Validate that bytes content is valid JSON.

        Args:
            content_bytes: Raw bytes to validate
            logger: Optional logger for debug messages

        Returns:
            True if content can be parsed as JSON, False otherwise
        """
        try:
            result = TempJsonProcessor.process_bytes_to_dict(content_bytes, logger)
            return isinstance(result, OrderedDict)
        except Exception:
            return False