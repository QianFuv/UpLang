"""Tests for Minecraft mod language file parsing utilities."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from zipfile import ZipFile

from click.testing import CliRunner

from uplang.cli import main
from uplang.lang_parser import (
    DEFAULT_TARGET_LOCALES,
    JarParseError,
    discover_jar_language_paths,
    parse_language_json,
    parse_mod_jar_languages,
    parse_mods_directory,
)


def test_discover_language_paths_for_known_jar() -> None:
    """Verify language paths and metadata can be discovered from a known jar.

    Args:
        None.

    Returns:
        None.
    """

    jar_path = Path("tests_local/mods/[forge]ctov-3.4.14.jar")
    matches = discover_jar_language_paths(jar_path)
    assert len(matches) == 5
    assert matches[0].mod_id == "ctov"
    assert matches[0].internal_path.startswith("assets/ctov/lang/")
    assert all(match.absolute_offset >= 0 for match in matches)


def test_discover_jar_language_paths_validates_invalid_archive() -> None:
    """Verify invalid archive input raises JarParseError for discovery.

    Args:
        None.

    Returns:
        None.
    """

    try:
        discover_jar_language_paths(Path("pyproject.toml"))
    except JarParseError:
        pass
    else:
        raise AssertionError("Expected JarParseError for invalid archive input")


def test_cli_extracts_en_us_and_zh_cn_to_resourcepack(tmp_path: Path) -> None:
    """Verify CLI extracts language files to assets/<mod_id>/lang paths.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    mods_dir = tmp_path / "mods"
    resourcepack_dir = tmp_path / "resourcepack"
    assets_dir = resourcepack_dir / "assets"
    mods_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    source_jar = Path("tests_local/mods/[forge]ctov-3.4.14.jar")
    shutil.copy2(source_jar, mods_dir / source_jar.name)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["init", str(mods_dir), str(assets_dir), "--workers", "2"],
    )

    assert result.exit_code == 0
    assert "written_files=2" in result.output

    en_us_path = assets_dir / "ctov" / "lang" / "en_us.json"
    zh_cn_path = assets_dir / "ctov" / "lang" / "zh_cn.json"
    fr_fr_path = assets_dir / "ctov" / "lang" / "fr_fr.json"

    assert en_us_path.exists()
    assert zh_cn_path.exists()
    assert not fr_fr_path.exists()


def test_import_cli_replaces_untranslated_values_from_import_pack(
    tmp_path: Path,
) -> None:
    """Verify import command replaces untranslated zh_cn values from import pack.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    assets_dir = tmp_path / "pack" / "assets"
    import_assets_dir = tmp_path / "import_pack" / "assets"
    mod_lang_dir = assets_dir / "examplemod" / "lang"
    import_mod_lang_dir = import_assets_dir / "examplemod" / "lang"
    mod_lang_dir.mkdir(parents=True, exist_ok=True)
    import_mod_lang_dir.mkdir(parents=True, exist_ok=True)

    current_en = {
        "key.same": "Hello",
        "key.untranslated": "Welcome",
        "key.translated": "Goodbye",
        "key.missing_in_import": "Nope",
    }
    current_zh = {
        "key.same": "Hello",
        "key.untranslated": "Welcome",
        "key.translated": "再见",
        "key.missing_in_import": "Nope",
    }
    imported_zh = {
        "key.same": "你好",
        "key.untranslated": "欢迎",
        "key.translated": "导入再见",
    }

    from uplang.cli import _encode_translations

    (mod_lang_dir / "en_us.json").write_bytes(_encode_translations(current_en))
    (mod_lang_dir / "zh_cn.json").write_bytes(_encode_translations(current_zh))
    (import_mod_lang_dir / "zh_cn.json").write_bytes(_encode_translations(imported_zh))

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["import", str(assets_dir), str(import_assets_dir)],
    )

    assert result.exit_code == 0
    assert "scanned_mods=1" in result.output
    assert "updated_mods=1" in result.output
    assert "replaced_entries=2" in result.output

    merged = parse_language_json((mod_lang_dir / "zh_cn.json").read_bytes())
    assert merged["key.same"] == "你好"
    assert merged["key.untranslated"] == "欢迎"
    assert merged["key.translated"] == "再见"
    assert merged["key.missing_in_import"] == "Nope"


def test_import_cli_skips_when_import_zh_file_missing(tmp_path: Path) -> None:
    """Verify import command skips mods without imported zh_cn file.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    assets_dir = tmp_path / "pack" / "assets"
    import_assets_dir = tmp_path / "import_pack" / "assets"
    mod_lang_dir = assets_dir / "examplemod" / "lang"
    mod_lang_dir.mkdir(parents=True, exist_ok=True)
    import_assets_dir.mkdir(parents=True, exist_ok=True)

    from uplang.cli import _encode_translations

    (mod_lang_dir / "en_us.json").write_bytes(_encode_translations({"k": "Hello"}))
    (mod_lang_dir / "zh_cn.json").write_bytes(_encode_translations({"k": "Hello"}))

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["import", str(assets_dir), str(import_assets_dir)],
    )

    assert result.exit_code == 0
    assert "scanned_mods=1" in result.output
    assert "updated_mods=0" in result.output
    assert "replaced_entries=0" in result.output


def test_import_cli_replaces_using_zip_import_source(tmp_path: Path) -> None:
    """Verify import command can read zh_cn translations from zip import source.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    assets_dir = tmp_path / "pack" / "assets"
    mod_lang_dir = assets_dir / "examplemod" / "lang"
    mod_lang_dir.mkdir(parents=True, exist_ok=True)
    import_zip_path = tmp_path / "import_pack.zip"

    from uplang.cli import _encode_translations

    (mod_lang_dir / "en_us.json").write_bytes(_encode_translations({"k": "Hello"}))
    (mod_lang_dir / "zh_cn.json").write_bytes(_encode_translations({"k": "Hello"}))

    zip_zh = _encode_translations({"k": "你好"})
    with ZipFile(import_zip_path, "w") as archive:
        archive.writestr("assets/examplemod/lang/zh_cn.json", zip_zh)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["import", str(assets_dir), str(import_zip_path)],
    )

    assert result.exit_code == 0
    assert "scanned_mods=1" in result.output
    assert "updated_mods=1" in result.output
    assert "replaced_entries=1" in result.output

    merged = parse_language_json((mod_lang_dir / "zh_cn.json").read_bytes())
    assert merged["k"] == "你好"


def test_update_cli_syncs_en_and_zh_based_on_en_diff(tmp_path: Path) -> None:
    """Verify update command syncs add/delete/change from en_us into both locales.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    mods_dir = tmp_path / "mods"
    assets_dir = tmp_path / "pack" / "assets"
    mods_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "demomod" / "lang").mkdir(parents=True, exist_ok=True)

    previous_en = {
        "key.same": "Same",
        "key.delete": "DeleteMe",
        "key.change": "OldValue",
        "key.change_translated": "OldTranslatedSource",
    }
    previous_zh = {
        "key.same": "已翻译保持",
        "key.delete": "会删除",
        "key.change": "OldValue",
        "key.change_translated": "原本中文",
    }

    latest_en = {
        "key.same": "Same",
        "key.change": "NewValue",
        "key.change_translated": "NewTranslatedSource",
        "key.add": "AddValue",
    }
    latest_zh = {
        "key.same": "最新已翻译",
        "key.change": "新中文值",
        "key.change_translated": "最新中文值",
        "key.add": "新增中文值",
    }

    from uplang.cli import _encode_translations

    en_path = assets_dir / "demomod" / "lang" / "en_us.json"
    zh_path = assets_dir / "demomod" / "lang" / "zh_cn.json"
    en_path.write_bytes(_encode_translations(previous_en))
    zh_path.write_bytes(_encode_translations(previous_zh))

    jar_path = mods_dir / "demomod-1.0.0.jar"
    with ZipFile(jar_path, "w") as archive:
        archive.writestr(
            "assets/demomod/lang/en_us.json",
            _encode_translations(latest_en),
        )
        archive.writestr(
            "assets/demomod/lang/zh_cn.json",
            _encode_translations(latest_zh),
        )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["update", str(mods_dir), str(assets_dir), "--workers", "2"],
    )

    assert result.exit_code == 0
    assert "scanned_mods=1" in result.output
    assert "updated_mods=1" in result.output
    assert "added_keys=1" in result.output
    assert "deleted_keys=1" in result.output
    assert "changed_keys=2" in result.output

    merged_en = parse_language_json(en_path.read_bytes())
    assert merged_en == latest_en

    merged_zh = parse_language_json(zh_path.read_bytes())
    assert "key.delete" not in merged_zh
    assert merged_zh["key.same"] == "已翻译保持"
    assert merged_zh["key.change"] == "新中文值"
    assert merged_zh["key.change_translated"] == "原本中文"
    assert merged_zh["key.add"] == "新增中文值"


def test_update_cli_skips_when_no_en_diff(tmp_path: Path) -> None:
    """Verify update command does not rewrite files when en_us has no changes.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    mods_dir = tmp_path / "mods"
    assets_dir = tmp_path / "pack" / "assets"
    mods_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "demomod" / "lang").mkdir(parents=True, exist_ok=True)

    from uplang.cli import _encode_translations

    en_values = {"key.same": "Same"}
    zh_values = {"key.same": "已翻译"}

    en_path = assets_dir / "demomod" / "lang" / "en_us.json"
    zh_path = assets_dir / "demomod" / "lang" / "zh_cn.json"
    en_path.write_bytes(_encode_translations(en_values))
    zh_path.write_bytes(_encode_translations(zh_values))

    jar_path = mods_dir / "demomod-1.0.1.jar"
    with ZipFile(jar_path, "w") as archive:
        archive.writestr(
            "assets/demomod/lang/en_us.json",
            _encode_translations(en_values),
        )
        archive.writestr(
            "assets/demomod/lang/zh_cn.json",
            _encode_translations({"key.same": "最新已翻译"}),
        )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["update", str(mods_dir), str(assets_dir)],
    )

    assert result.exit_code == 0
    assert "scanned_mods=1" in result.output
    assert "updated_mods=0" in result.output
    assert "added_keys=0" in result.output
    assert "deleted_keys=0" in result.output
    assert "changed_keys=0" in result.output

    merged_en = parse_language_json(en_path.read_bytes())
    merged_zh = parse_language_json(zh_path.read_bytes())
    assert merged_en == en_values
    assert merged_zh == zh_values


def test_cli_preserves_surrogates_as_escaped_unicode() -> None:
    """Verify CLI serializer preserves surrogate code points as unicode escapes.

    Args:
        None.

    Returns:
        None.
    """

    from uplang.cli import _encode_translations

    payload = _encode_translations({"bad\ud810key": "value\ud810"})
    output = payload.decode("utf-8")
    assert "\\uD810" in output
    assert "\ufffd" not in output


def test_cli_escapes_private_use_code_points() -> None:
    """Verify serializer keeps private-use code points as unicode escapes.

    Args:
        None.

    Returns:
        None.
    """

    from uplang.cli import _encode_translations

    payload = _encode_translations({"minecraft": "§7Minecraft §f\ue588"})
    output = payload.decode("utf-8")
    assert "\\uE588" in output
    assert chr(0xE588) not in output


def test_cli_preserves_surrogate_split_sequence_text() -> None:
    """Verify serializer preserves split surrogate sequence as escaped text.

    Args:
        None.

    Returns:
        None.
    """

    from uplang.cli import _encode_translations

    key = "item.traveloptics.forlorn_harbinger.tooltip.darkness"
    payload = _encode_translations({key: "\ud810E\udd87黑暗能量: %s"})
    output = payload.decode("utf-8")
    assert "\\uD810E\\uDD87" in output
    assert "\ufffd" not in output


def test_parse_languages_for_known_jar_default_locales() -> None:
    """Verify default locale filter only parses en_us and zh_cn.

    Args:
        None.

    Returns:
        None.
    """

    jar_path = Path("tests_local/mods/[forge]ctov-3.4.14.jar")
    result = parse_mod_jar_languages(jar_path)
    assert len(result.language_files) == 2
    assert len(result.failures) == 0
    parsed_locales = {item.locale for item in result.language_files}
    assert parsed_locales == {"en_us", "zh_cn"}


def test_parse_languages_for_known_jar_all_locales() -> None:
    """Verify all locales can be parsed when locale filter is disabled.

    Args:
        None.

    Returns:
        None.
    """

    jar_path = Path("tests_local/mods/[forge]ctov-3.4.14.jar")
    result = parse_mod_jar_languages(jar_path, target_locales=None)
    assert len(result.language_files) == 5
    assert len(result.failures) == 0


def test_parse_jar_without_language_files() -> None:
    """Verify jars without language files return empty successful result.

    Args:
        None.

    Returns:
        None.
    """

    jar_path = Path("tests_local/mods/0Pack2Reload-Forge-1.20.1-1.0.1.jar")
    result = parse_mod_jar_languages(jar_path)
    assert len(result.language_files) == 0
    assert len(result.failures) == 0


def test_parse_non_utf8_language_file() -> None:
    """Verify non-UTF-8 language files are parsed using fallback encodings.

    Args:
        None.

    Returns:
        None.
    """

    jar_path = Path("tests_local/mods/autumnity-1.20.1-5.0.2.jar")
    result = parse_mod_jar_languages(jar_path, target_locales=None)
    cz_cs = [
        item
        for item in result.language_files
        if item.internal_path.endswith("cz_cs.json")
    ]
    assert len(cz_cs) == 1
    assert len(cz_cs[0].translations) > 0


def test_parse_compatibility_variants() -> None:
    """Verify common malformed JSON patterns are handled compatibly.

    Args:
        None.

    Returns:
        None.
    """

    samples: list[bytes] = [
        b'\xef\xbb\xbf{"a":"b"}',
        b'{\n// comment\n"a":"b"\n}',
        b'"a":"b"',
        b'{"a":"b",}',
        b'{"a":"b"}\n}',
        b'{"a":1,"b":true,"c":null}',
    ]
    for payload in samples:
        parsed = parse_language_json(payload)
        assert len(parsed) > 0


def test_parse_all_local_mods_directory_default_locales_parallel() -> None:
    """Verify all local jars can be parsed with default locales and threads.

    Args:
        None.

    Returns:
        None.
    """

    mods_dir = Path("tests_local/mods")
    start_time = time.perf_counter()
    results = parse_mods_directory(mods_dir, max_workers=8)
    elapsed = time.perf_counter() - start_time

    expected_jar_count = len(list(mods_dir.glob("*.jar")))
    assert len(results) == expected_jar_count
    assert all(result.jar_path.suffix.lower() == ".jar" for result in results)
    assert {"en_us", "zh_cn"} == DEFAULT_TARGET_LOCALES

    total_language_files = sum(len(result.language_files) for result in results)
    total_failures = sum(len(result.failures) for result in results)
    assert total_language_files > 0
    assert total_failures >= 0
    assert elapsed < 300


def test_parse_mods_directory_materializes_locale_iterable(tmp_path: Path) -> None:
    """Verify locale iterables are stable across parallel workers.

    Args:
        tmp_path: Temporary directory fixture path.

    Returns:
        None.
    """

    source_jars = [
        Path("tests_local/mods/[forge]ctov-3.4.14.jar"),
        Path("tests_local/mods/accessories-neoforge-1.0.0-beta.48+1.20.1.jar"),
    ]
    for source_jar in source_jars:
        shutil.copy2(source_jar, tmp_path / source_jar.name)

    tuple_result = parse_mods_directory(
        tmp_path,
        target_locales=("en_us", "zh_cn"),
        max_workers=4,
    )
    generator_result = parse_mods_directory(
        tmp_path,
        target_locales=(locale for locale in ("en_us", "zh_cn")),
        max_workers=4,
    )

    tuple_total = sum(len(item.language_files) for item in tuple_result)
    generator_total = sum(len(item.language_files) for item in generator_result)
    assert generator_total == tuple_total


def test_parse_mod_jar_languages_validates_invalid_archive() -> None:
    """Verify invalid jar archives raise JarParseError even with no matches.

    Args:
        None.

    Returns:
        None.
    """

    try:
        parse_mod_jar_languages(Path("pyproject.toml"))
    except JarParseError:
        pass
    else:
        raise AssertionError("Expected JarParseError for invalid archive input")
