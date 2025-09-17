"""
Utility functions for UpLang
"""

import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for all operating systems

    Removes or replaces characters that are invalid in filenames on Windows, macOS, or Linux
    """
    # Characters that are invalid in Windows filenames, plus some problematic ones
    invalid_chars = r'[<>:"/\\|?*+]'

    # Replace invalid characters with underscores
    sanitized = re.sub(invalid_chars, '_', filename)

    # Replace multiple consecutive underscores with single underscore
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing periods and spaces (Windows doesn't like these)
    sanitized = sanitized.strip('. ')

    # Ensure the filename isn't empty
    if not sanitized:
        sanitized = "unknown"

    # Truncate if too long (255 is the typical filesystem limit)
    if len(sanitized) > 200:  # Leave some room for extensions
        sanitized = sanitized[:200]

    return sanitized


def create_safe_mod_id(jar_name: str) -> str:
    """Create a safe mod ID from a JAR filename"""
    # Remove the .jar extension
    base_name = Path(jar_name).stem

    # Sanitize the filename
    safe_name = sanitize_filename(base_name)

    return f"unrecognized_{safe_name}"