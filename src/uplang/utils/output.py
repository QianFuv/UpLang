"""
Console output utilities.
"""

import sys
from typing import Any

from colorama import just_fix_windows_console, Fore, Style

just_fix_windows_console()


_color_enabled = True
_quiet_mode = False
_verbose_mode = False


def set_color_enabled(enabled: bool) -> None:
    """
    Enable or disable colored output.
    """
    global _color_enabled
    _color_enabled = enabled


def set_quiet_mode(quiet: bool) -> None:
    """
    Enable or disable quiet mode.
    """
    global _quiet_mode
    _quiet_mode = quiet


def set_verbose_mode(verbose: bool) -> None:
    """
    Enable or disable verbose mode.
    """
    global _verbose_mode
    _verbose_mode = verbose


def _colorize(text: str, color: str) -> str:
    """
    Apply color to text if colors are enabled.
    """
    if not _color_enabled:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def print_info(message: str, **kwargs: Any) -> None:
    """
    Print an info message.
    """
    if _quiet_mode:
        return
    print(_colorize(message, Fore.CYAN), **kwargs)


def print_success(message: str, **kwargs: Any) -> None:
    """
    Print a success message.
    """
    if _quiet_mode:
        return
    print(_colorize(message, Fore.GREEN), **kwargs)


def print_warning(message: str, **kwargs: Any) -> None:
    """
    Print a warning message.
    """
    if _quiet_mode:
        return
    print(_colorize(message, Fore.YELLOW), **kwargs)


def print_error(message: str, **kwargs: Any) -> None:
    """
    Print an error message.
    """
    print(_colorize(message, Fore.RED), file=sys.stderr, **kwargs)


def print_verbose(message: str, **kwargs: Any) -> None:
    """
    Print a verbose message (only if verbose mode is enabled).
    """
    if _quiet_mode or not _verbose_mode:
        return
    print(_colorize(f"  {message}", Fore.WHITE + Style.DIM), **kwargs)
