# UpLang

`UpLang` is a command-line tool designed to streamline the process of updating language files for Minecraft Java Edition modpacks. It assists localization teams by automatically detecting changes in mods (new, updated, or deleted) and synchronizing new translation keys into the resource pack. It also ensures consistency between English and Chinese language files, adding missing keys and removing obsolete ones.

## Features

*   **Mod Scanning**: Automatically detects new, updated, and deleted mods in your modpack directory.
*   **Initial Setup (`uplang init`)**:
    *   Scans mods and extracts `en_us.json` for each.
    *   If a mod JAR contains `zh_cn.json`, it's copied; otherwise, `en_us.json` is copied to `zh_cn.json`.
    *   Performs initial synchronization of `zh_cn.json` with `en_us.json` (adds missing keys, removes extra keys).
    *   Creates the necessary `assets/<mod_id>/lang` structure in your resource pack.
    *   Saves the mod state for future comparisons.
*   **Update Checking (`uplang check`)**:
    *   Compares the current mod state against the last known state.
    *   Reports new, updated, and deleted mods.
    *   Automatically merges new translation keys into `zh_cn.json` files for updated mods.
    *   **Comprehensive Language Synchronization**: Ensures all `zh_cn.json` files in the resource pack are synchronized with their corresponding `en_us.json` files (adds keys present in English but missing in Chinese, removes keys present in Chinese but missing in English).
*   **Cross-platform Compatibility**: Designed to work on Windows, macOS, and Linux.

## Installation

`UpLang` is built with Python 3.11 and uses `uv` for dependency management.

1.  **Ensure Python 3.11+ is installed.**
2.  **Install `uv`**:
    ```bash
    pip install uv
    ```
3.  **Clone the repository**:
    ```bash
    git clone https://github.com/QianFuv/UpLang.git
    cd UpLang
    ```
4.  **Install dependencies with `uv`**:
    ```bash
    uv pip install -e .
    ```

## Usage

### `uplang init <mods_dir> <resource_pack_dir>`

Run this command once for a new project or when setting up a new resource pack.

*   `<mods_dir>`: The absolute or relative path to your Minecraft modpack's mods directory (e.g., `C:\Users\YourUser\AppData\Roaming\.minecraft\mods`).
*   `<resource_pack_dir>`: The absolute or relative path to your resource pack's root directory where `assets` folder will be created (e.g., `C:\Users\YourUser\Desktop\MyResourcePack`).

**Example:**
```bash
uplang init "C:\Users\YourUser\AppData\Roaming\.minecraft\mods" "C:\Users\YourUser\Desktop\MyResourcePack"
```

### `uplang check <mods_dir> <resource_pack_dir>`

Run this command whenever you update your mods. It will detect changes and synchronize language files.

*   `<mods_dir>`: The absolute or relative path to your Minecraft modpack's mods directory.
*   `<resource_pack_dir>`: The absolute or relative path to your resource pack's root directory.

**Example:**
```bash
uplang check "C:\Users\YourUser\AppData\Roaming\.minecraft\mods" "C:\Users\YourUser\Desktop\MyResourcePack"
```

## Testing

The project includes a full suite of automated integration tests.

To run the tests, execute the following command from the project root:

```bash
uv run pytest tests/test_integration.py
```

This command will set up dummy mods, run both the `init` and `check` commands, and verify that the outcomes are correct, including language file synchronization.

## Contributing

We welcome contributions to `UpLang`! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
