"""Synchronization and difference calculation mapping logic for translations."""

from __future__ import annotations

from .models import DEFAULT_TARGET_LOCALES, JarLanguageParseResult
from .utils import _is_untranslated_value


def _collect_mod_locale_translations(
    parse_results: tuple[JarLanguageParseResult, ...],
) -> dict[str, dict[str, dict[str, str]]]:
    """Collect parsed locale mappings keyed by mod id and locale.

    Args:
        parse_results: Parsing results returned from jar scanning.

    Returns:
        Nested mapping of mod id to locale to translation mapping.
    """

    mod_locale_mappings: dict[str, dict[str, dict[str, str]]] = {}
    for parse_result in parse_results:
        for language_file in parse_result.language_files:
            locale_name = language_file.locale.lower()
            if locale_name not in DEFAULT_TARGET_LOCALES:
                continue
            locale_mappings = mod_locale_mappings.setdefault(language_file.mod_id, {})
            locale_mappings[locale_name] = language_file.translations
    return mod_locale_mappings


def _calculate_en_translation_diff(
    previous_translations: dict[str, str],
    latest_translations: dict[str, str],
) -> tuple[set[str], set[str], set[str]]:
    """Calculate added, deleted, and changed key sets between two mappings.

    Args:
        previous_translations: Existing translation mapping.
        latest_translations: Latest translation mapping.

    Returns:
        Tuple containing added, deleted, and changed key sets.
    """

    previous_keys = set(previous_translations.keys())
    latest_keys = set(latest_translations.keys())

    added_keys = latest_keys - previous_keys
    deleted_keys = previous_keys - latest_keys
    changed_keys = {
        key
        for key in previous_keys & latest_keys
        if previous_translations[key] != latest_translations[key]
    }

    return added_keys, deleted_keys, changed_keys


def _sync_zh_translations_for_en_update(
    previous_en_translations: dict[str, str],
    latest_en_translations: dict[str, str],
    current_zh_translations: dict[str, str],
    latest_zh_translations: dict[str, str],
) -> tuple[dict[str, str], int]:
    """Sync zh_cn keys and untranslated values using English key diffs.

    Args:
        previous_en_translations: Existing en_us mapping in resource pack.
        latest_en_translations: Latest en_us mapping parsed from mods.
        current_zh_translations: Existing zh_cn mapping in resource pack.
        latest_zh_translations: Latest zh_cn mapping parsed from mods.

    Returns:
        Updated zh_cn mapping and number of changed entries.
    """

    merged_translations = dict(current_zh_translations)
    merged_changes = 0
    added_keys, deleted_keys, changed_keys = _calculate_en_translation_diff(
        previous_en_translations,
        latest_en_translations,
    )

    for key in deleted_keys:
        if key in merged_translations:
            del merged_translations[key]
            merged_changes += 1

    for key in changed_keys:
        fallback_value = latest_zh_translations.get(key, latest_en_translations[key])
        existing_value = merged_translations.get(key)

        if existing_value is None:
            merged_translations[key] = fallback_value
            merged_changes += 1
            continue

        previous_english = previous_en_translations.get(key)
        if _is_untranslated_value(
            existing_value,
            previous_english,
        ) and existing_value != fallback_value:
            merged_translations[key] = fallback_value
            merged_changes += 1

    for key in added_keys:
        if key in merged_translations:
            continue
        fallback_value = latest_zh_translations.get(key, latest_en_translations[key])
        merged_translations[key] = fallback_value
        merged_changes += 1

    return merged_translations, merged_changes


def _merge_imported_translations_for_mod(
    current_zh_translations: dict[str, str],
    current_en_translations: dict[str, str],
    imported_zh_translations: dict[str, str],
) -> tuple[dict[str, str], int]:
    """Merge imported zh_cn entries into one mod language mapping.

    Args:
        current_zh_translations: Current resource-pack zh_cn entries.
        current_en_translations: Current resource-pack en_us entries.
        imported_zh_translations: Imported pack zh_cn entries.

    Returns:
        Updated zh_cn mapping and number of replaced entries.
    """

    merged_translations = dict(current_zh_translations)
    replaced_entries = 0

    for key, current_value in current_zh_translations.items():
        english_reference = current_en_translations.get(key)
        if not _is_untranslated_value(current_value, english_reference):
            continue

        imported_value = imported_zh_translations.get(key)
        if imported_value is None or imported_value == current_value:
            continue

        merged_translations[key] = imported_value
        replaced_entries += 1

    return merged_translations, replaced_entries
