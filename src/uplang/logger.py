"""
Enhanced logging system for UpLang.

This module provides a rich console and file logging system with
color support, progress tracking, and structured output formatting.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.panel import Panel
from rich.table import Table


class UpLangLogger:
    """Enhanced logger with Rich console support and file logging."""

    def __init__(self, name: str = "uplang"):
        """Initialize logger with given name."""
        self.name = name
        self.console = Console()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self._log_file_path: Optional[Path] = None
        self._quiet_mode = False

    def setup(self,
              resource_pack_dir: Path,
              log_level: str = "info",
              quiet: bool = False,
              no_color: bool = False) -> Path:
        """Setup logging with console and file handlers.

        Args:
            resource_pack_dir: Directory for log files
            log_level: Logging level (debug, info, warning, error)
            quiet: Suppress console output if True
            no_color: Disable colored output if True

        Returns:
            Path to the created log file
        """

        self._quiet_mode = quiet

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        log_dir = Path(resource_pack_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._log_file_path = log_dir / f"uplang_{timestamp}.log"

        if not quiet:
            console_handler = RichHandler(
                console=Console(force_terminal=not no_color),
                show_time=False,
                show_path=False,
                markup=True
            )
            console_handler.setLevel(getattr(logging, log_level.upper()))
            self.logger.addHandler(console_handler)

        file_handler = logging.FileHandler(self._log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        return self._log_file_path

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message with yellow color."""
        self.logger.warning(f"[yellow]{message}[/yellow]")

    def error(self, message: str):
        """Log error message with red color."""
        self.logger.error(f"[red]{message}[/red]")

    def success(self, message: str):
        """Log success message with green color."""
        self.logger.info(f"[green]{message}[/green]")

    def section(self, title: str):
        """Display a section header in a panel."""
        if not self._quiet_mode:
            panel = Panel(title, style="bold blue")
            self.console.print(panel)

    def subsection(self, title: str):
        """Display a subsection header with arrow prefix."""
        if not self._quiet_mode:
            text = Text(f"▶ {title}", style="bold")
            self.console.print(text)

    def table(self, title: str, headers: list, rows: list):
        """Display data in a formatted table.

        Args:
            title: Table title
            headers: List of column headers
            rows: List of row data (each row is a list)
        """
        if not self._quiet_mode:
            table = Table(title=title)
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            self.console.print(table)

    def get_log_file(self) -> Optional[Path]:
        """Get path to the current log file."""
        return self._log_file_path


_logger_instance: Optional[UpLangLogger] = None


def get_logger() -> UpLangLogger:
    """Get or create global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = UpLangLogger()
    return _logger_instance