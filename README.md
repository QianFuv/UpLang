# UpLang

**Minecraft Modpack Language File Synchronizer**

A command-line tool to streamline the process of updating language files for Minecraft Java Edition modpacks.

---

## Overview

UpLang automates the synchronization of language files between Minecraft mods and localization resource packs. It's designed specifically for modpack maintainers who need to keep their Chinese (zh_cn) translations up-to-date as mods are updated.

### Key Features

- **Automatic Detection**: Scans mod JARs and extracts language files
- **Smart Synchronization**: Identifies added, modified, and deleted translation keys
- **Format Preservation**: Maintains JSON key order and formatting (blank lines, indentation)
- **Intelligent Translation**: Prioritizes mod-provided Chinese translations, falls back to English
- **Hash-based Caching**: Only processes mods with changed language files
- **Parallel Processing**: Multi-threaded mod processing for large modpacks
- **Forge/Fabric/NeoForge Support**: Works with all major mod loaders

---

## Installation

### From PyPI (Recommended)

```bash
pip install uplang
```

### From Source

```bash
git clone https://github.com/QianFuv/UpLang.git
cd UpLang
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Basic Usage

Synchronize language files from mods to a resource pack:

```bash
uplang sync /path/to/mods /path/to/resourcepack
```

### Check Differences (Dry Run)

Preview changes without modifying files:

```bash
uplang check /path/to/mods /path/to/resourcepack
```

### List All Mods

View all mods and their language files:

```bash
uplang list /path/to/mods
```

---

## Commands

### `uplang sync`

Synchronize language files from mods to resource pack.

```bash
uplang sync <mods_dir> <resourcepack_dir> [OPTIONS]
```

**Options:**
- `--dry-run`: Simulate without modifying files
- `--force`: Ignore cache, process all mods
- `--parallel <n>`: Number of parallel workers (default: 4)

**Example:**

```bash
uplang sync ./mods ./resourcepack --parallel 8
```

---

### `uplang check`

Check differences without synchronizing (equivalent to `sync --dry-run`).

```bash
uplang check <mods_dir> <resourcepack_dir>
```

---

### `uplang list`

List all mods and their language files.

```bash
uplang list <mods_dir>
```

**Example Output:**

```
Example Mod (examplemod) v1.0.0
  Type: forge
  JAR: examplemod-1.0.0.jar
  en_us.json: 42 keys
  zh_cn.json: 38 keys
```

---

### `uplang extract`

Extract language files from a single mod JAR.

```bash
uplang extract <mod_jar> <output_dir>
```

**Example:**

```bash
uplang extract ./mods/examplemod-1.0.0.jar ./extracted
```

---

### `uplang diff`

Show detailed differences for a single mod.

```bash
uplang diff <mod_jar> <resourcepack_dir>
```

**Example Output:**

```
Mod: Example Mod (examplemod) v1.0.0

English: +5 ~3 -2

Added keys (5):
  + item.examplemod.new_item: New Item
  + block.examplemod.new_block: New Block
  ...

Modified keys (3):
  ~ item.examplemod.sword:
    Old: Iron Sword
    New: Steel Sword
  ...

Deleted keys (2):
  - item.examplemod.old_item
  ...
```

---

### `uplang stats`

Show translation statistics for the resource pack.

```bash
uplang stats <resourcepack_dir>
```

**Example Output:**

```
Total mods: 150
Total English keys: 12,543
Total Chinese keys: 12,543
Translated keys: 10,234
Translation coverage: 81.6%
```

---

### `uplang clean`

Remove language files for mods that no longer exist (interactive).

```bash
uplang clean <resourcepack_dir>
```

---

### `uplang cache clear`

Clear the cache to force full synchronization.

```bash
uplang cache clear <resourcepack_dir>
```

---

## Global Options

Available for all commands:

- `--verbose`, `-v`: Enable verbose output
- `--quiet`, `-q`: Quiet mode (errors only)
- `--no-color`: Disable colored output
- `--log-file <path>`: Write logs to file
- `--version`: Show version information
- `--help`: Show help message

**Example:**

```bash
uplang sync ./mods ./resourcepack --verbose --log-file sync.log
```

---

## Environment Variables

UpLang supports configuration via environment variables with the `UPLANG_` prefix:

### Global Options
- `UPLANG_VERBOSE=1`: Enable verbose output
- `UPLANG_QUIET=1`: Enable quiet mode
- `UPLANG_NO_COLOR=1`: Disable colored output
- `UPLANG_LOG_FILE=/path/to/log`: Set log file path

### Command-Specific Options
Environment variables can also be used for command options using the format `UPLANG_<COMMAND>_<OPTION>`:

- `UPLANG_SYNC_PARALLEL=8`: Set parallel workers for sync command
- `UPLANG_SYNC_FORCE=1`: Force sync, ignore cache
- `UPLANG_SYNC_DRY_RUN=1`: Enable dry-run mode

**Example:**

```bash
# Set verbose mode and log file via environment
export UPLANG_VERBOSE=1
export UPLANG_LOG_FILE=~/uplang.log

# Run sync with 8 parallel workers
UPLANG_SYNC_PARALLEL=8 uplang sync ./mods ./resourcepack
```

---

## How It Works

### Synchronization Logic

1. **Scan Mods**: UpLang scans all JAR files in the mods directory
2. **Extract Language Files**: Extracts `en_us.json` and `zh_cn.json` from each mod
3. **Check Cache**: Uses hash-based cache to skip unchanged mods
4. **Compare**: Identifies added, modified, and deleted keys
5. **Synchronize English**: Updates resource pack's `en_us.json` with mod's English file
6. **Synchronize Chinese**: For each key:
   - If key is new/modified: Use mod's Chinese translation if available, otherwise use English
   - If key is deleted: Remove from resource pack
7. **Preserve Format**: Maintains original key order and JSON formatting

### Cache System

UpLang uses a hash-based cache (`.uplang_cache.json`) to track mod changes:

```json
{
  "version": "0.3.0",
  "last_updated": "2025-11-02T10:30:00",
  "mods": {
    "examplemod": {
      "jar_name": "examplemod-1.0.0.jar",
      "en_us_hash": "abc123...",
      "zh_cn_hash": "def456...",
      "last_sync": "2025-11-02T10:30:00"
    }
  }
}
```

Only mods with changed language files are processed, making subsequent syncs very fast.

---

## Architecture

```
src/uplang/
├── __init__.py                # Package metadata, version
├── __main__.py                # Entry point (python -m uplang)
├── cli.py                     # CLI commands and interface
├── core/
│   ├── __init__.py
│   ├── scanner.py             # Scan JAR files in mods directory
│   ├── extractor.py           # Extract language files from JARs
│   ├── comparator.py          # Compare language files (set operations)
│   ├── synchronizer.py        # Synchronize language files
│   └── cache.py               # Hash-based change detection
├── models/
│   ├── __init__.py
│   ├── mod.py                 # Mod data class
│   ├── language_file.py       # Language file data class
│   └── sync_result.py         # Sync operation result
├── utils/
│   ├── __init__.py
│   ├── json_handler.py        # JSON read/write with format preservation
│   ├── hash_utils.py          # Hash calculation utilities
│   ├── path_utils.py          # Path and filename utilities
│   └── output.py              # Console output (colors, formatting)
└── exceptions.py              # Custom exception hierarchy
```

---

## Development

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=uplang --cov-report=html
```

### Code Quality

UpLang follows these standards:

- **Language**: English for all code (variables, functions, comments)
- **Documentation**: Docstrings only, no inline comments
- **Architecture**: Low coupling, high extensibility
- **Type Hints**: Full type annotations

---

## Examples

### Example 1: Initial Setup

```bash
# First time setup - sync all mods
uplang sync ./mods ./resourcepack --force

# Output:
# UpLang v0.3.0 - Language File Synchronizer
# Mods directory: ./mods
# Resource pack: ./resourcepack
#
# Scanning mods...
# Found 120 mods
#
# Synchronizing with 4 parallel workers...
# examplemod: +42 ~0 -0
# anothermod: +156 ~12 -3
# ...
#
# Synchronization Summary
# ==================================================
# Total mods: 120
# Synchronized: 120
# Skipped: 0
# Failed: 0
#
# Total changes:
#   Added keys: 8,432
#   Modified keys: 234
#   Deleted keys: 56
# ==================================================
```

### Example 2: Update After Mod Update

```bash
# After updating some mods
uplang sync ./mods ./resourcepack

# Output:
# ...
# Synchronizing with 4 parallel workers...
# examplemod: +5 ~3 -2
# anothermod: skipped (no changes)
# thirdmod: skipped (no changes)
# ...
#
# Synchronization Summary
# ==================================================
# Total mods: 120
# Synchronized: 1
# Skipped: 119
# Failed: 0
#
# Total changes:
#   Added keys: 5
#   Modified keys: 3
#   Deleted keys: 2
# ==================================================
```

### Example 3: Check Before Syncing

```bash
# Preview changes
uplang check ./mods ./resourcepack

# Output shows what would change without modifying files
```

---

## Troubleshooting

### Issue: "No en_us.json found in mod"

Some mods don't include language files in the JAR. This is normal and can be ignored.

### Issue: "Failed to parse JSON"

The language file may have invalid JSON syntax. UpLang will skip the file and log the error.

### Issue: Cache not working

Clear the cache and resync:

```bash
uplang cache clear ./resourcepack
uplang sync ./mods ./resourcepack
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI
- Uses [ruamel.yaml](https://yaml.readthedocs.io/) for format-preserving JSON handling
- Colorized output with [Colorama](https://github.com/tartley/colorama)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/QianFuv/UpLang/issues)
- **Email**: qianfuv@qq.com

---

**Made with ❤️ for the Minecraft modding community**
