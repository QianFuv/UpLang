"""
UpLang CLI interface.

This module provides the command-line interface for UpLang,
a tool to synchronize language files for Minecraft modpacks.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from uplang.config import ProjectConfig, AppConfig
from uplang.commands import InitCommand, CheckCommand
from uplang.exceptions import UpLangError


app = typer.Typer(
    name="uplang",
    help="A tool to synchronize language files for Minecraft modpacks",
    rich_markup_mode="rich"
)

console = Console()


def version_callback(value: bool):
    """Display version information and exit."""
    if value:
        from uplang.version import get_cached_version
        console.print(f"UpLang version {get_cached_version()}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        help="Show version and exit"
    )
):
    """UpLang - Minecraft modpack language file synchronizer."""
    pass


@app.command()
def init(
    mods_dir: Path = typer.Argument(
        ...,
        help="Directory containing mod JAR files",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    resource_pack_dir: Path = typer.Argument(
        ...,
        help="Resource pack directory to create/update",
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level", "-l",
        help="Logging level"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Suppress console output"
    ),
    no_color: bool = typer.Option(
        False, "--no-color",
        help="Disable colored output"
    )
):
    """Initialize or synchronize resource pack with mods directory.

    This command scans the mods directory for JAR files, extracts language files,
    and creates/updates the resource pack structure with synchronized translations.
    """
    try:
        config = AppConfig(
            log_level=log_level,
            quiet_mode=quiet,
            no_color=no_color
        )

        project_config = ProjectConfig.from_paths(
            str(mods_dir),
            str(resource_pack_dir),
            config
        )

        if not quiet:
            console.print(Panel(
                "UpLang Initialization",
                subtitle="Setting up resource pack with mod language files",
                style="bold blue"
            ))

        command = InitCommand(project_config)
        result = command.execute()

        if result.success:
            if not quiet:
                console.print("[green]✓[/green] Initialization completed successfully")
            sys.exit(0)
        else:
            if not quiet:
                console.print(f"[red]✗[/red] Initialization failed: {result.message}")
            sys.exit(1)

    except UpLangError as e:
        if not quiet:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        if not quiet:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        if not quiet:
            console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


@app.command()
def check(
    mods_dir: Path = typer.Argument(
        ...,
        help="Directory containing mod JAR files",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    resource_pack_dir: Path = typer.Argument(
        ...,
        help="Resource pack directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level", "-l",
        help="Logging level"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Suppress console output"
    ),
    no_color: bool = typer.Option(
        False, "--no-color",
        help="Disable colored output"
    )
):
    """Check for mod updates and synchronize language files.

    This command compares the current state with the previous scan,
    identifies changes, and updates language files accordingly.
    """
    try:
        config = AppConfig(
            log_level=log_level,
            quiet_mode=quiet,
            no_color=no_color
        )

        project_config = ProjectConfig.from_paths(
            str(mods_dir),
            str(resource_pack_dir),
            config
        )

        if not quiet:
            console.print(Panel(
                "UpLang Check",
                subtitle="Checking for mod updates and synchronizing files",
                style="bold blue"
            ))

        command = CheckCommand(project_config)
        result = command.execute()

        if result.success:
            if not quiet:
                console.print("[green]✓[/green] Check completed successfully")
            sys.exit(0)
        else:
            if not quiet:
                console.print(f"[red]✗[/red] Check failed: {result.message}")
            sys.exit(1)

    except UpLangError as e:
        if not quiet:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        if not quiet:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        if not quiet:
            console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()