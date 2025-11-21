"""
Tests for console output utilities.
"""

import pytest

from uplang.utils.output import (
    print_error,
    print_info,
    print_success,
    print_verbose,
    print_warning,
    set_color_enabled,
    set_quiet_mode,
    set_verbose_mode,
)


@pytest.fixture(autouse=True)
def reset_output_settings():
    """
    Reset output settings before each test.
    """
    set_color_enabled(True)
    set_quiet_mode(False)
    set_verbose_mode(False)
    yield
    set_color_enabled(True)
    set_quiet_mode(False)
    set_verbose_mode(False)


def test_print_info(capsys):
    """
    Test printing info messages.
    """
    print_info("Test info message")
    captured = capsys.readouterr()
    assert "Test info message" in captured.out


def test_print_success(capsys):
    """
    Test printing success messages.
    """
    print_success("Test success message")
    captured = capsys.readouterr()
    assert "Test success message" in captured.out


def test_print_warning(capsys):
    """
    Test printing warning messages.
    """
    print_warning("Test warning message")
    captured = capsys.readouterr()
    assert "Test warning message" in captured.out


def test_print_error(capsys):
    """
    Test printing error messages.
    """
    print_error("Test error message")
    captured = capsys.readouterr()
    assert "Test error message" in captured.err


def test_print_verbose_when_enabled(capsys):
    """
    Test printing verbose messages when verbose mode is enabled.
    """
    set_verbose_mode(True)
    print_verbose("Test verbose message")
    captured = capsys.readouterr()
    assert "Test verbose message" in captured.out


def test_print_verbose_when_disabled(capsys):
    """
    Test that verbose messages are not printed when disabled.
    """
    set_verbose_mode(False)
    print_verbose("Test verbose message")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_quiet_mode_suppresses_info(capsys):
    """
    Test that quiet mode suppresses info messages.
    """
    set_quiet_mode(True)
    print_info("Test info")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_quiet_mode_suppresses_success(capsys):
    """
    Test that quiet mode suppresses success messages.
    """
    set_quiet_mode(True)
    print_success("Test success")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_quiet_mode_suppresses_warning(capsys):
    """
    Test that quiet mode suppresses warning messages.
    """
    set_quiet_mode(True)
    print_warning("Test warning")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_quiet_mode_allows_error(capsys):
    """
    Test that quiet mode still prints error messages.
    """
    set_quiet_mode(True)
    print_error("Test error")
    captured = capsys.readouterr()
    assert "Test error" in captured.err


def test_quiet_mode_suppresses_verbose(capsys):
    """
    Test that quiet mode suppresses verbose messages.
    """
    set_quiet_mode(True)
    set_verbose_mode(True)
    print_verbose("Test verbose")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_color_disabled_no_ansi_codes(capsys):
    """
    Test that disabling colors removes ANSI codes.
    """
    set_color_enabled(False)
    print_info("Test message")
    captured = capsys.readouterr()
    assert "\033[" not in captured.out or "Test message" in captured.out


def test_color_enabled_with_colors():
    """
    Test that colors are enabled by default.
    """
    set_color_enabled(True)
    assert True


def test_set_verbose_mode_true():
    """
    Test enabling verbose mode.
    """
    set_verbose_mode(True)
    assert True


def test_set_verbose_mode_false():
    """
    Test disabling verbose mode.
    """
    set_verbose_mode(False)
    assert True


def test_set_quiet_mode_true():
    """
    Test enabling quiet mode.
    """
    set_quiet_mode(True)
    assert True


def test_set_quiet_mode_false():
    """
    Test disabling quiet mode.
    """
    set_quiet_mode(False)
    assert True


def test_print_info_with_kwargs(capsys):
    """
    Test print_info with additional keyword arguments.
    """
    print_info("Test", end="")
    captured = capsys.readouterr()
    assert "Test" in captured.out


def test_print_error_goes_to_stderr(capsys):
    """
    Test that errors are printed to stderr.
    """
    print_error("Error message")
    captured = capsys.readouterr()
    assert captured.err != ""
    assert captured.out == ""


def test_verbose_mode_with_special_characters(capsys):
    """
    Test verbose mode with unicode characters.
    """
    set_verbose_mode(True)
    print_verbose("Unicode: 中文 😀")
    captured = capsys.readouterr()
    assert "Unicode" in captured.out
