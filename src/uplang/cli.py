"""Command-line interface for mod language extraction and translation import."""

from __future__ import annotations

from pathlib import Path

import click

from .importer import _load_imported_zh_mappings
from .io import _build_target_path, _encode_translations, _load_translation_file
from .lang_parser import parse_mods_directory
from .models import DEFAULT_TARGET_LOCALES, JarParseError
from .sync import (
    _calculate_en_translation_diff,
    _collect_mod_locale_translations,
    _merge_imported_translations_for_mod,
    _sync_zh_translations_for_en_update,
)

_EN_LOCALE = "en_us"
_ZH_LOCALE = "zh_cn"


@click.group(help="Utilities for MC language extraction and import.")
def main() -> None:
    """Root command group for uplang.

    Args:
        None.

    Returns:
        None.
    """


@main.command(name="init", help="Extract en_us and zh_cn language files from jars.")
@click.argument(
    "mods_dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
)
@click.argument(
    "assets_dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
)
@click.option(
    "--workers",
    type=click.IntRange(min=1),
    default=None,
    help="Optional parser worker count.",
)
def init_command(mods_dir: Path, assets_dir: Path, workers: int | None) -> None:
    """Extract language files from mod jars into one resource-pack assets dir.

    Args:
        mods_dir: Directory containing mod jar files.
        assets_dir: Assets directory in the resource pack.
        workers: Optional worker count for parallel parsing.

    Returns:
        None.
    """

    try:
        parse_results = parse_mods_directory(
            mods_dir,
            target_locales=DEFAULT_TARGET_LOCALES,
            max_workers=workers,
        )
    except JarParseError as exc:
        raise click.ClickException(str(exc)) from exc

    written_files = 0
    failed_files = 0

    for parse_result in parse_results:
        failed_files += len(parse_result.failures)
        for language_file in parse_result.language_files:
            destination = _build_target_path(
                assets_dir,
                language_file.mod_id,
                language_file.locale,
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(_encode_translations(language_file.translations))
            written_files += 1

    click.echo(f"written_files={written_files}")
    click.echo(f"failed_files={failed_files}")


@main.command(
    name="update",
    help="Sync detected en_us key updates into resource-pack en_us and zh_cn.",
)
@click.argument(
    "mods_dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
)
@click.argument(
    "assets_dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
)
@click.option(
    "--workers",
    type=click.IntRange(min=1),
    default=None,
    help="Optional parser worker count.",
)
def update_command(mods_dir: Path, assets_dir: Path, workers: int | None) -> None:
    """Update resource-pack translations based on detected en_us diffs.

    Args:
        mods_dir: Directory containing mod jar files.
        assets_dir: Assets directory in the resource pack.
        workers: Optional worker count for parallel parsing.

    Returns:
        None.
    """

    try:
        parse_results = parse_mods_directory(
            mods_dir,
            target_locales=DEFAULT_TARGET_LOCALES,
            max_workers=workers,
        )
    except JarParseError as exc:
        raise click.ClickException(str(exc)) from exc

    failed_files = sum(len(parse_result.failures) for parse_result in parse_results)
    mod_locale_mappings = _collect_mod_locale_translations(parse_results)

    scanned_mods = 0
    updated_mods = 0
    added_keys_total = 0
    deleted_keys_total = 0
    changed_keys_total = 0
    zh_changes_total = 0

    for mod_id in sorted(mod_locale_mappings.keys()):
        locale_mappings = mod_locale_mappings[mod_id]
        latest_en_translations = locale_mappings.get(_EN_LOCALE)
        if latest_en_translations is None:
            continue

        scanned_mods += 1
        en_path = _build_target_path(assets_dir, mod_id, _EN_LOCALE)
        zh_path = _build_target_path(assets_dir, mod_id, _ZH_LOCALE)

        previous_en_translations = (
            _load_translation_file(en_path) if en_path.exists() else {}
        )
        current_zh_translations = (
            _load_translation_file(zh_path) if zh_path.exists() else {}
        )

        added_keys, deleted_keys, changed_keys = _calculate_en_translation_diff(
            previous_en_translations,
            latest_en_translations,
        )
        if len(added_keys) == 0 and len(deleted_keys) == 0 and len(changed_keys) == 0:
            continue

        updated_mods += 1
        added_keys_total += len(added_keys)
        deleted_keys_total += len(deleted_keys)
        changed_keys_total += len(changed_keys)

        en_path.parent.mkdir(parents=True, exist_ok=True)
        zh_path.parent.mkdir(parents=True, exist_ok=True)
        en_path.write_bytes(_encode_translations(latest_en_translations))

        latest_zh_translations = locale_mappings.get(_ZH_LOCALE, {})
        synced_zh_translations, zh_changes = _sync_zh_translations_for_en_update(
            previous_en_translations,
            latest_en_translations,
            current_zh_translations,
            latest_zh_translations,
        )
        zh_changes_total += zh_changes
        zh_path.write_bytes(_encode_translations(synced_zh_translations))

    click.echo(f"scanned_mods={scanned_mods}")
    click.echo(f"updated_mods={updated_mods}")
    click.echo(f"added_keys={added_keys_total}")
    click.echo(f"deleted_keys={deleted_keys_total}")
    click.echo(f"changed_keys={changed_keys_total}")
    click.echo(f"zh_changes={zh_changes_total}")
    click.echo(f"failed_files={failed_files}")


@main.command(
    name="import",
    help="Import zh_cn translations from an assets directory or zip file.",
)
@click.argument(
    "assets_dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
)
@click.argument(
    "import_source",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=True,
        path_type=Path,
    ),
)
def import_command(assets_dir: Path, import_source: Path) -> None:
    """Import available zh_cn translations into the current resource pack.

    Args:
        assets_dir: Current resource-pack assets directory.
        import_source: Imported assets directory or zip file path.

    Returns:
        None.
    """

    scanned_mods = 0
    updated_mods = 0
    replaced_entries = 0

    target_language_files = sorted(
        assets_dir.glob("*/lang/zh_cn.json"),
        key=lambda path: path.as_posix().lower(),
    )
    target_mod_ids = {path.parent.parent.name for path in target_language_files}
    imported_mappings = _load_imported_zh_mappings(import_source, target_mod_ids)

    for target_zh_path in target_language_files:
        mod_id = target_zh_path.parent.parent.name
        scanned_mods += 1

        imported_zh_translations = imported_mappings.get(mod_id)
        if imported_zh_translations is None:
            continue

        current_en_path = assets_dir / mod_id / "lang" / "en_us.json"
        current_zh_translations = _load_translation_file(target_zh_path)
        current_en_translations = (
            _load_translation_file(current_en_path) if current_en_path.exists() else {}
        )

        merged_translations, replaced_count = _merge_imported_translations_for_mod(
            current_zh_translations,
            current_en_translations,
            imported_zh_translations,
        )
        if replaced_count == 0:
            continue

        target_zh_path.write_bytes(_encode_translations(merged_translations))
        updated_mods += 1
        replaced_entries += replaced_count

    click.echo(f"scanned_mods={scanned_mods}")
    click.echo(f"updated_mods={updated_mods}")
    click.echo(f"replaced_entries={replaced_entries}")


if __name__ == "__main__":
    main()
