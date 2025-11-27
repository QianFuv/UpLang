"""
Command-line interface for UpLang.
"""

import builtins
import logging
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click

from uplang import __version__
from uplang.core import (
    CacheManager,
    LanguageComparator,
    LanguageExtractor,
    LanguageSynchronizer,
    ModScanner,
)
from uplang.exceptions import UpLangError
from uplang.models import LanguageFile, SyncResult
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


@click.group(context_settings={"auto_envvar_prefix": "UPLANG"})
@click.version_option(version=__version__, prog_name="UpLang")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (errors only)")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--log-file", type=click.Path(path_type=str), help="Log file path")
@click.pass_context
def main(
    ctx: click.Context,
    verbose: bool,
    quiet: bool,
    no_color: bool,
    log_file: str | None,
):
    """
    UpLang - Minecraft Modpack Language File Synchronizer
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color

    set_verbose_mode(verbose)
    set_quiet_mode(quiet)
    set_color_enabled(not no_color)

    if log_file:
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )


@main.command()
@click.argument(
    "mods_dir", type=click.Path(exists=True, file_okay=False, path_type=str)
)
@click.argument("resourcepack_dir", type=click.Path(file_okay=False, path_type=str))
@click.option("--dry-run", is_flag=True, help="Simulate without modifying files")
@click.option("--force", is_flag=True, help="Ignore cache, process all mods")
@click.option("--parallel", "-p", default=4, help="Number of parallel workers")
@click.option(
    "--force-english-on-change",
    is_flag=True,
    help="Sync new English when Chinese unchanged",
)
def sync(
    mods_dir: str,
    resourcepack_dir: str,
    dry_run: bool,
    force: bool,
    parallel: int,
    force_english_on_change: bool,
):
    """
    Synchronize language files from mods to resource pack.
    """
    mods_path = Path(mods_dir)
    rp_path = Path(resourcepack_dir)

    print_info(f"UpLang v{__version__} - Language File Synchronizer")
    print_info(f"Mods directory: {mods_path}")
    print_info(f"Resource pack: {rp_path}")

    if dry_run:
        print_warning("DRY RUN MODE - No files will be modified")

    try:
        scanner = ModScanner()
        print_info("\nScanning mods...")
        mods = scanner.scan_directory(mods_path)
        print_success(f"Found {len(mods)} mods")

        cache_path = rp_path / ".uplang_cache.json"
        cache = CacheManager(cache_path)

        if force:
            print_warning("Force mode enabled - ignoring cache")
            cache.clear()

        results = []
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    _sync_single_mod,
                    mod,
                    rp_path,
                    cache,
                    dry_run,
                    force,
                    force_english_on_change,
                ): mod
                for mod in mods
            }

            print_info(f"\nSynchronizing with {parallel} parallel workers...")
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    if not result.skipped:
                        if result.success:
                            print_success(str(result))
                        else:
                            print_error(str(result))
                except Exception as e:
                    mod = futures[future]
                    print_error(f"{mod.mod_id}: unexpected error - {e}")

        if not dry_run:
            cache.save()

        _print_summary(results)

    except UpLangError as e:
        print_error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@main.command()
@click.argument(
    "mods_dir", type=click.Path(exists=True, file_okay=False, path_type=str)
)
@click.argument("resourcepack_dir", type=click.Path(file_okay=False, path_type=str))
def check(mods_dir: str, resourcepack_dir: str):
    """
    Check differences without synchronizing (dry-run mode).
    """
    ctx = click.get_current_context()
    ctx.invoke(
        sync,
        mods_dir=mods_dir,
        resourcepack_dir=resourcepack_dir,
        dry_run=True,
        force=False,
        parallel=4,
    )


@main.command()
@click.argument(
    "mods_dir", type=click.Path(exists=True, file_okay=False, path_type=str)
)
def list(mods_dir: str):
    """
    List all mods and their language files.
    """
    mods_path = Path(mods_dir)

    try:
        scanner = ModScanner()
        extractor = LanguageExtractor()

        print_info(f"Scanning mods in {mods_path}...")
        mods = scanner.scan_directory(mods_path)

        for mod in mods:
            print_info(f"\n{mod.name} ({mod.mod_id}) v{mod.version}")
            print_info(f"  Type: {mod.mod_type.value}")
            print_info(f"  JAR: {mod.jar_path.name}")

            lang_files = extractor.extract_language_files(mod)
            for lang_code, lang_file in lang_files.items():
                print_info(f"  {lang_code}.json: {len(lang_file.content)} keys")

        print_success(f"\nTotal: {len(mods)} mods")

    except UpLangError as e:
        print_error(f"Error: {e}")
        sys.exit(1)


@main.command()
@click.argument("mod_jar", type=click.Path(exists=True, dir_okay=False, path_type=str))
@click.argument("output_dir", type=click.Path(file_okay=False, path_type=str))
def extract(mod_jar: str, output_dir: str):
    """
    Extract language files from a single mod JAR.
    """
    jar_path = Path(mod_jar)
    output_path = Path(output_dir)

    try:
        scanner = ModScanner()
        extractor = LanguageExtractor()

        print_info(f"Scanning {jar_path.name}...")
        mod = scanner.scan_jar(jar_path)
        print_info(f"Mod: {mod}")

        lang_files = extractor.extract_language_files(mod)

        for lang_code, lang_file in lang_files.items():
            output_file = output_path / f"{lang_code}.json"
            extractor.json_handler.dump(lang_file.content, output_file)
            key_count = len(lang_file.content)
            print_success(
                f"Extracted {lang_code}.json ({key_count} keys) -> {output_file}"
            )

        print_success(f"\nExtracted {len(lang_files)} language files")

    except UpLangError as e:
        print_error(f"Error: {e}")
        sys.exit(1)


@main.command()
@click.argument("mod_jar", type=click.Path(exists=True, dir_okay=False, path_type=str))
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
def diff(mod_jar: str, resourcepack_dir: str):
    """
    Show detailed differences for a single mod.
    """
    jar_path = Path(mod_jar)
    rp_path = Path(resourcepack_dir)

    try:
        scanner = ModScanner()
        extractor = LanguageExtractor()
        comparator = LanguageComparator()

        mod = scanner.scan_jar(jar_path)
        print_info(f"Mod: {mod}\n")

        mod_langs = extractor.extract_language_files(mod)

        if "en_us" not in mod_langs:
            print_warning("No en_us.json found in mod")
            return

        mod_en = mod_langs["en_us"]
        rp_en = extractor.load_from_resource_pack(rp_path, mod.mod_id, "en_us")

        if rp_en is None:
            print_info(f"English: {len(mod_en.content)} keys (new mod)")
        else:
            diff_result = comparator.compare(rp_en.content, mod_en.content)
            print_info(f"English: {diff_result}")

            if diff_result.added:
                print_success(f"\nAdded keys ({len(diff_result.added)}):")
                for key in sorted(diff_result.added):
                    print_verbose(f"  + {key}: {mod_en.content[key]}")

            if diff_result.modified:
                print_warning(f"\nModified keys ({len(diff_result.modified)}):")
                for key in sorted(diff_result.modified):
                    print_verbose(f"  ~ {key}:")
                    print_verbose(f"    Old: {rp_en.content[key]}")
                    print_verbose(f"    New: {mod_en.content[key]}")

            if diff_result.deleted:
                print_error(f"\nDeleted keys ({len(diff_result.deleted)}):")
                for key in sorted(diff_result.deleted):
                    print_verbose(f"  - {key}")

    except UpLangError as e:
        print_error(f"Error: {e}")
        sys.exit(1)


@main.command(name="import")
@click.argument("zip_file", type=click.Path(exists=True, dir_okay=False, path_type=str))
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
@click.option("--dry-run", is_flag=True, help="Preview changes without modifying files")
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing translations (default: only import untranslated)",
)
def import_translations(
    zip_file: str, resourcepack_dir: str, dry_run: bool, overwrite: bool
):
    """
    Import translations from a resource pack zip file.
    """
    zip_path = Path(zip_file)
    rp_path = Path(resourcepack_dir)

    print_info(f"Importing translations from {zip_path.name}")
    print_info(f"Target resource pack: {rp_path}")

    if dry_run:
        print_warning("DRY RUN MODE - No files will be modified")

    try:
        from uplang.core.importer import TranslationImporter

        importer = TranslationImporter()
        result = importer.import_from_zip(
            zip_path, rp_path, dry_run=dry_run, overwrite=overwrite
        )

        print_info(f"\nProcessed {result.total_mods} mod(s)")
        print_success(f"Keys imported: {result.keys_imported}")
        print_info(f"Keys skipped (already translated): {result.keys_skipped}")

        if result.errors:
            print_warning(f"\nErrors encountered: {len(result.errors)}")
            for error in result.errors:
                print_error(f"  {error}")

    except Exception as e:
        print_error(f"Import failed: {e}")
        sys.exit(1)


@main.command()
@click.argument(
    "mods_dir", type=click.Path(exists=True, file_okay=False, path_type=str)
)
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
@click.option(
    "--yes", "-y", is_flag=True, help="Skip confirmation and delete all orphaned mods"
)
def clean(mods_dir: str, resourcepack_dir: str, yes: bool):
    """
    Remove language files for mods that no longer exist.
    """
    rp_path = Path(resourcepack_dir)
    assets_path = rp_path / "assets"

    if not assets_path.exists():
        print_warning("No assets directory found")
        return

    print_info(f"Scanning {assets_path}...")
    rp_mod_ids = {d.name for d in assets_path.iterdir() if d.is_dir()}
    print_info(f"Found {len(rp_mod_ids)} mod directories in resource pack")

    mods_path = Path(mods_dir)
    print_info(f"\nScanning {mods_path}...")
    scanner = ModScanner()
    current_mods = scanner.scan_directory(mods_path)
    current_mod_ids = {mod.mod_id for mod in current_mods}
    print_info(f"Found {len(current_mods)} mods in mods directory")

    orphaned_mod_ids = rp_mod_ids - current_mod_ids

    if not orphaned_mod_ids:
        print_success("No orphaned mods found. Resource pack is clean!")
        return

    print_warning(f"\nFound {len(orphaned_mod_ids)} orphaned mod(s):")
    for mod_id in sorted(orphaned_mod_ids):
        mod_path = assets_path / mod_id
        lang_path = mod_path / "lang"
        if lang_path.exists():
            lang_files = builtins.list(lang_path.glob("*.json"))
            print_info(f"  - {mod_id} ({len(lang_files)} language files)")
        else:
            print_info(f"  - {mod_id}")

    if not yes:
        print_warning("\nThis will permanently delete the directories listed above.")
        confirmation = click.confirm("Do you want to continue?", default=False)
        if not confirmation:
            print_info("Cancelled.")
            return

    cache = CacheManager(rp_path / ".uplang_cache.json")
    deleted_count = 0

    for mod_id in orphaned_mod_ids:
        mod_path = assets_path / mod_id
        try:
            shutil.rmtree(mod_path)
            cache.remove_mod(mod_id)
            print_success(f"Deleted: {mod_id}")
            deleted_count += 1
        except Exception as e:
            print_error(f"Failed to delete {mod_id}: {e}")

    cache.save()
    print_success(f"\nCleaned {deleted_count} orphaned mod(s)")


@main.command()
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
def stats(resourcepack_dir: str):
    """
    Show translation statistics.
    """
    rp_path = Path(resourcepack_dir)
    assets_path = rp_path / "assets"

    if not assets_path.exists():
        print_warning("No assets directory found")
        return

    extractor = LanguageExtractor()
    total_mods = 0
    total_keys_en = 0
    total_keys_zh = 0
    total_translated = 0
    failed_files = []

    for mod_dir in assets_path.iterdir():
        if not mod_dir.is_dir():
            continue

        mod_id = mod_dir.name

        try:
            en_file = extractor.load_from_resource_pack(rp_path, mod_id, "en_us")
        except Exception as e:
            failed_files.append((mod_id, "en_us", str(e)))
            en_file = None

        try:
            zh_file = extractor.load_from_resource_pack(rp_path, mod_id, "zh_cn")
        except Exception as e:
            failed_files.append((mod_id, "zh_cn", str(e)))
            zh_file = None

        if en_file is None:
            continue

        total_mods += 1
        total_keys_en += len(en_file.content)

        if zh_file:
            total_keys_zh += len(zh_file.content)
            for key, value in zh_file.content.items():
                if key in en_file.content and value != en_file.content[key]:
                    total_translated += 1

    print_info(f"Total mods: {total_mods}")
    print_info(f"Total English keys: {total_keys_en}")
    print_info(f"Total Chinese keys: {total_keys_zh}")
    print_info(f"Translated keys: {total_translated}")

    if total_keys_en > 0:
        percentage = (total_translated / total_keys_en) * 100
        print_success(f"Translation coverage: {percentage:.1f}%")

    if failed_files:
        print_warning(f"\nFailed to parse {len(failed_files)} file(s):")
        for mod_id, lang_code, error_msg in failed_files:
            print_error(f"  - {mod_id}/{lang_code}: {error_msg.split('(')[0].strip()}")


@main.command()
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
@click.option("--dry-run", is_flag=True, help="Check without modifying files")
@click.option("--check", is_flag=True, help="Only check for issues, do not fix")
def format(resourcepack_dir: str, dry_run: bool, check: bool):
    """
    Fix JSON format and synchronize key order with English files.
    """
    rp_path = Path(resourcepack_dir)
    assets_path = rp_path / "assets"

    if not assets_path.exists():
        print_warning("No assets directory found")
        return

    if dry_run or check:
        print_warning("CHECK MODE - No files will be modified")

    extractor = LanguageExtractor()
    synchronizer = LanguageSynchronizer()

    total_mods = 0
    fixed_mods = 0
    total_reordered = 0
    total_reformatted = 0
    issues_found = []

    print_info(f"Scanning {assets_path}...")

    for mod_dir in assets_path.iterdir():
        if not mod_dir.is_dir():
            continue

        mod_id = mod_dir.name
        total_mods += 1

        try:
            en_file = extractor.load_from_resource_pack(rp_path, mod_id, "en_us")
        except Exception as e:
            issues_found.append((mod_id, "en_us", f"Failed to load: {e}"))
            continue

        if en_file is None:
            continue

        try:
            zh_file = extractor.load_from_resource_pack(rp_path, mod_id, "zh_cn")
        except Exception as e:
            issues_found.append((mod_id, "zh_cn", f"Failed to load: {e}"))
            zh_file = None

        mod_fixed = False
        import json

        from uplang.utils import calculate_dict_hash

        def needs_formatting(file_path, content):
            """
            Check if file needs formatting by comparing current content
            with formatted version.
            """
            try:
                if not file_path.exists():
                    return True
                with open(file_path, encoding="utf-8", errors="surrogatepass") as f:
                    current_text = f.read()
                formatted_text = (
                    json.dumps(content, ensure_ascii=False, indent=2) + "\n"
                )
                return current_text != formatted_text
            except Exception:
                return True

        if zh_file:
            original_order = builtins.list(zh_file.content.keys())
            reordered_content = synchronizer.reorder_by_reference(
                zh_file.content, en_file.content
            )
            new_order = builtins.list(reordered_content.keys())

            if original_order != new_order:
                print_verbose(f"  {mod_id}: Key order needs synchronization")
                total_reordered += 1

            zh_file_path = rp_path / "assets" / mod_id / "lang" / "zh_cn.json"
            if needs_formatting(zh_file_path, reordered_content):
                total_reformatted += 1
                mod_fixed = True

                if not dry_run and not check:
                    zh_file_reordered = LanguageFile(
                        mod_id=mod_id,
                        lang_code="zh_cn",
                        content=reordered_content,
                        content_hash=calculate_dict_hash(reordered_content),
                    )
                    try:
                        extractor.save_to_resource_pack(rp_path, zh_file_reordered)
                    except Exception as e:
                        issues_found.append((mod_id, "zh_cn", f"Failed to save: {e}"))

        en_file_path = rp_path / "assets" / mod_id / "lang" / "en_us.json"
        if needs_formatting(en_file_path, en_file.content):
            total_reformatted += 1
            mod_fixed = True

            if not dry_run and not check:
                try:
                    en_file_reformatted = LanguageFile(
                        mod_id=mod_id,
                        lang_code="en_us",
                        content=en_file.content,
                        content_hash=calculate_dict_hash(en_file.content),
                    )
                    extractor.save_to_resource_pack(rp_path, en_file_reformatted)
                except Exception as e:
                    issues_found.append((mod_id, "en_us", f"Failed to save: {e}"))

        if mod_fixed:
            fixed_mods += 1
            if not dry_run and not check:
                print_success(f"Fixed: {mod_id}")

    print_info("\n" + "=" * 50)
    print_info("Format Summary")
    print_info("=" * 50)
    print_info(f"Total mods scanned: {total_mods}")

    if dry_run or check:
        print_warning(f"Mods needing fixes: {fixed_mods}")
        print_info(f"  Files needing key order sync: {total_reordered}")
    else:
        print_success(f"Mods fixed: {fixed_mods}")
        print_info(f"  Files reformatted: {total_reformatted}")
        print_info(f"  Chinese files reordered: {total_reordered}")

    if issues_found:
        print_warning(f"\nIssues found ({len(issues_found)}):")
        for mod_id, lang_code, issue in issues_found:
            print_error(f"  {mod_id}/{lang_code}: {issue}")

    print_info("=" * 50)


@main.group()
def cache():
    """
    Cache management commands.
    """
    pass


@cache.command("clear")
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
def cache_clear(resourcepack_dir: str):
    """
    Clear the cache to force full synchronization.
    """
    rp_path = Path(resourcepack_dir)
    cache_path = rp_path / ".uplang_cache.json"

    if cache_path.exists():
        cache_path.unlink()
        print_success(f"Cache cleared: {cache_path}")
    else:
        print_warning("No cache file found")


@main.command()
@click.argument(
    "resourcepack_dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
)
@click.option("--host", default="127.0.0.1", help="Server host address")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option(
    "--open-browser/--no-open-browser",
    default=True,
    help="Open browser automatically",
)
def web(resourcepack_dir: str, host: str, port: int, open_browser: bool):
    """
    Launch web interface for translation management.
    """
    from uplang.web.app import start_server

    rp_path = Path(resourcepack_dir)

    print_info(f"Starting web server at http://{host}:{port}")
    print_info(f"Resource pack directory: {rp_path}")
    print_info("Press Ctrl+C to stop the server")

    if open_browser:
        import threading
        import webbrowser

        def open_browser_delayed():
            import time

            time.sleep(1.5)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    try:
        start_server(rp_path, host, port)
    except KeyboardInterrupt:
        print_info("\nServer stopped")
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        sys.exit(1)


def _sync_single_mod(mod, rp_path, cache, dry_run, force, force_english_on_change):
    """
    Synchronize a single mod's language files.
    """
    try:
        extractor = LanguageExtractor()
        synchronizer = LanguageSynchronizer()

        mod_langs = extractor.extract_language_files(mod)

        if "en_us" in mod_langs:
            mod_en = mod_langs["en_us"]
            mod_zh = mod_langs.get("zh_cn")

            if not force and not cache.is_changed(
                mod.mod_id,
                mod_en.content_hash,
                mod_zh.content_hash if mod_zh else None,
            ):
                return SyncResult(mod_id=mod.mod_id, skipped=True)

            rp_en = extractor.load_from_resource_pack(rp_path, mod.mod_id, "en_us")
            rp_zh = extractor.load_from_resource_pack(rp_path, mod.mod_id, "zh_cn")

            synced_en, diff = synchronizer.synchronize_english(mod_en, rp_en)

            zh_modified = set()
            if mod_zh and rp_zh:
                for key in diff.modified:
                    if key in mod_zh.content and key in rp_zh.content:
                        if mod_zh.content[key] != rp_zh.content[key]:
                            zh_modified.add(key)
            diff.zh_modified = zh_modified

            synced_zh = synchronizer.synchronize_chinese(
                synced_en, mod_zh, rp_en, rp_zh, diff, force_english_on_change
            )

            zh_added_keys = 0
            zh_deleted_keys = 0
            if rp_zh is not None:
                synced_keys = set(synced_zh.content.keys())
                rp_keys = set(rp_zh.content.keys())
                zh_added_keys = len(synced_keys - rp_keys)
                zh_deleted_keys = len(rp_keys - synced_keys)

            if (
                not diff.has_changes
                and rp_en is not None
                and (rp_zh is None or synced_zh.content == rp_zh.content)
            ):
                cache.update_mod(
                    mod.mod_id,
                    mod.jar_path.name,
                    mod_en.content_hash,
                    mod_zh.content_hash if mod_zh else None,
                )
                return SyncResult(mod_id=mod.mod_id, skipped=True)

            if not dry_run:
                extractor.save_to_resource_pack(rp_path, synced_en)
                extractor.save_to_resource_pack(rp_path, synced_zh)

                cache.update_mod(
                    mod.mod_id,
                    mod.jar_path.name,
                    mod_en.content_hash,
                    mod_zh.content_hash if mod_zh else None,
                )

            total_added = len(diff.added) + zh_added_keys
            total_deleted = len(diff.deleted) + zh_deleted_keys

            return SyncResult(
                mod_id=mod.mod_id,
                success=True,
                skipped=False,
                added_keys=total_added,
                modified_keys=len(diff.modified),
                deleted_keys=total_deleted,
            )

        elif "zh_cn" in mod_langs:
            mod_zh = mod_langs["zh_cn"]

            if not force and not cache.is_changed(
                mod.mod_id,
                None,
                mod_zh.content_hash,
            ):
                return SyncResult(mod_id=mod.mod_id, skipped=True)

            rp_zh = extractor.load_from_resource_pack(rp_path, mod.mod_id, "zh_cn")

            synced_zh, diff = synchronizer.synchronize_chinese_as_primary(mod_zh, rp_zh)

            if not diff.has_changes and rp_zh is not None:
                cache.update_mod(
                    mod.mod_id,
                    mod.jar_path.name,
                    None,
                    mod_zh.content_hash,
                )
                return SyncResult(mod_id=mod.mod_id, skipped=True)

            if not dry_run:
                extractor.save_to_resource_pack(rp_path, synced_zh)

                cache.update_mod(
                    mod.mod_id,
                    mod.jar_path.name,
                    None,
                    mod_zh.content_hash,
                )

            return SyncResult(
                mod_id=mod.mod_id,
                success=True,
                skipped=False,
                added_keys=len(diff.added),
                modified_keys=len(diff.modified),
                deleted_keys=len(diff.deleted),
            )

        else:
            return SyncResult(mod_id=mod.mod_id, skipped=True)

    except Exception as e:
        return SyncResult(mod_id=mod.mod_id, success=False, error=str(e))


def _print_summary(results):
    """
    Print synchronization summary.
    """
    total = len(results)
    successful = sum(1 for r in results if r.success and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    failed = sum(1 for r in results if not r.success)

    total_added = sum(r.added_keys for r in results)
    total_modified = sum(r.modified_keys for r in results)
    total_deleted = sum(r.deleted_keys for r in results)

    print_info("\n" + "=" * 50)
    print_info("Synchronization Summary")
    print_info("=" * 50)
    print_info(f"Total mods: {total}")
    print_success(f"Synchronized: {successful}")
    print_warning(f"Skipped: {skipped}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    print_info("\nTotal changes:")
    print_success(f"  Added keys: {total_added}")
    print_warning(f"  Modified keys: {total_modified}")
    print_error(f"  Deleted keys: {total_deleted}")
    print_info("=" * 50)


if __name__ == "__main__":
    main()
