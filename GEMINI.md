# Gemini Project Context: uplang

## Project Overview

`uplang` is a command-line tool designed to streamline the process of updating language files for Minecraft Java Edition modpacks. It helps localization teams by automatically detecting changes in mods (new, updated, or deleted) and synchronizing new translation keys into the resource pack. It also ensures consistency between English (`en_us.json`) and Chinese (`zh_cn.json`) language files, adding missing keys and removing obsolete ones.

The project is built in Python 3.11 and uses `uv` for dependency management. It supports both Forge and Fabric mods.

## File Structure

```
UpLang/
├── src/
│   └── uplang/           # Main application source code
│       ├── __init__.py
│       ├── cli.py          # Command-line interface setup (argparse)
│       ├── models.py       # Data models for mods
│       └── core/           # Core logic modules
│           ├── comparator.py   # Compares language files
│           ├── extractor.py    # Extracts language files from JARs
│           ├── scanner.py      # Scans mod directories
│           ├── state.py        # Manages project state (mod info)
│           └── synchronizer.py # Synchronizes language file content
├── tests/
│   ├── run_tests.py      # Automated test runner (now test_integration.py)
│   ├── create_test_data.py # Script to generate dummy mods
│   └── test_integration.py # Automated integration tests using pytest
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # General project information
├── GEMINI.md             # Context for Gemini
├── CONTRIBUTING.md       # Contribution guidelines
└── uv.lock               # uv lock file for dependencies
```

## Commands

The tool provides two main commands:

### `uplang init <mods_dir> <resource_pack_dir>`

Run this command once for a new project or when setting up a new resource pack. It performs an initial scan of the mods directory, creates the required `assets/<mod_id>/lang` structure in your resource pack, and extracts the base `en_us.json` file for each mod. If a `zh_cn.json` exists in the mod JAR, it's copied; otherwise, `en_us.json` is copied to `zh_cn.json`. Finally, it performs a completion/synchronization operation on the `zh_cn.json` using the `en_us.json` as the reference.

### `uplang check <mods_dir> <resource_pack_dir>`

Run this command whenever you update your mods. It compares the current state of the mods folder against the last known state, reports any new, updated, or deleted mods, and automatically merges any new translation keys into the appropriate `zh_cn.json` files. It also performs a comprehensive synchronization of all `zh_cn.json` files in the resource pack with their corresponding `en_us.json` files (adds keys present in English but missing in Chinese, removes keys present in Chinese but missing in English).

## Testing

The project includes a full suite of automated integration tests.

To run the tests, execute the following command from the project root:

```bash
uv run pytest tests/test_integration.py
```

This command will create dummy mods, run both the `init` and `check` commands, and verify that the outcomes are correct, including language file synchronization.