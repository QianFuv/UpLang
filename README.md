# UpLang

[![PyPI](https://img.shields.io/pypi/v/UpLang)](https://badge.fury.io/py/uplang)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FQianFuv%2FUpLang%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/QianFuv/UpLang)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/uplang?color=light-green)](https://pypi.org/project/uplang/)

**UpLang** is a powerful command-line tool designed to streamline localization workflows for Minecraft Java Edition modpacks. It automates the complex process of managing translation files across multiple mods, ensuring perfect synchronization between English and Chinese language files while preserving translation integrity and key ordering.

> ⚠️ **Development Notice**: UpLang is currently in active development and rapid iteration. While stable for production use, new features and improvements are being added frequently. Please check the [releases](https://github.com/QianFuv/UpLang/releases) page for the latest updates and consider updating regularly to benefit from new features and bug fixes.

## 🌐 Languages

**English** | [简体中文](README_zh.md)

## 🚀 Key Features

- **🔍 Intelligent Mod Detection**: Automatically scans and tracks new, updated, and deleted mods
- **🔄 Smart Synchronization**: Maintains translation order while adding missing keys and removing obsolete ones
- **🛡️ Robust Error Handling**: Advanced JSON parsing with multiple fallback strategies for malformed files
- **📊 Progress Tracking**: Rich console interface with real-time progress indicators
- **🌐 Cross-Platform**: Works seamlessly on Windows, macOS, and Linux
- **⚡ Incremental Updates**: Efficient delta processing for large modpacks
- **🎯 Order Preservation**: Maintains original key ordering in language files
- **📚 Professional Documentation**: Comprehensive docstrings and code comments
- **🔧 Dependency Injection**: Clean architecture with testable components

## 📋 System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Minecraft**: Java Edition (Forge/Fabric mods)

## 🛠️ Installation

### Option 1: From PyPI (Recommended)

The easiest way to install UpLang is directly from PyPI:

```bash
# Install UpLang
pip install uplang

# Verify installation
uplang --help
```

### Option 2: Development Installation

For contributing or development purposes:

```bash
# Clone the repository
git clone https://github.com/QianFuv/UpLang.git
cd UpLang

# Using uv (recommended for development)
pip install uv
uv sync
uv pip install -e .

# Or using pip directly
pip install -e .
```

## 📖 Usage

### Initial Setup

For new projects or when setting up a new resource pack:

```bash
uplang init <mods_directory> <resource_pack_directory>
```

**Example:**
```bash
uplang init "~/.minecraft/mods" "./MyResourcePack"
```

**What it does:**
- 🔍 Scans all JAR files in the mods directory
- 📂 Creates the necessary `assets/<mod_id>/lang/` structure
- 📄 Extracts `en_us.json` from each mod
- 🔄 Copies or creates `zh_cn.json` files
- ⚙️ Performs initial synchronization
- 💾 Saves project state for future comparisons

### Updating Translations

When you add, update, or remove mods:

```bash
uplang check <mods_directory> <resource_pack_directory>
```

**Example:**
```bash
uplang check "~/.minecraft/mods" "./MyResourcePack"
```

**What it does:**
- 📊 Compares current state with previous scan
- 🆕 Identifies new, updated, and deleted mods
- 🔄 Merges new translation keys into existing files
- 🧹 Removes obsolete keys
- ✅ Synchronizes all language files
- 💾 Updates project state

## 📁 Output Structure

After running UpLang, your resource pack will have this structure:

```
MyResourcePack/
├── assets/
│   ├── mod_one/
│   │   └── lang/
│   │       ├── en_us.json
│   │       └── zh_cn.json
│   ├── mod_two/
│   │   └── lang/
│   │       ├── en_us.json
│   │       └── zh_cn.json
│   └── ...
├── pack.mcmeta (if it exists)
├── .uplang_state.json (project state)
└── uplang_*.log (operation logs)
```

## 🧪 Testing

Run the comprehensive test suite to verify everything works correctly:

```bash
# Run all tests
PYTHONPATH=src python -m pytest tests/ -v

# Run with coverage report
PYTHONPATH=src python -m pytest tests/ --cov=uplang --cov-report=html

# Run specific test modules
PYTHONPATH=src python -m pytest tests/test_json_utils.py -v    # JSON processing tests
PYTHONPATH=src python -m pytest tests/test_models.py -v        # Data model tests
PYTHONPATH=src python -m pytest tests/test_utils.py -v         # Utility function tests

# If using development installation with uv
uv run pytest tests/ -v
```

The test suite includes:
- **Data Model Testing**: Comprehensive validation of mod objects, comparison results, and sync statistics
- **JSON Processing**: Robust parsing with encoding fallbacks, malformed JSON recovery, and order preservation
- **Utility Functions**: Filename sanitization, mod ID creation, and path handling
- **Error Handling**: Edge cases, invalid inputs, and graceful recovery strategies
- **Unicode Support**: International characters, emoji, and encoding edge cases
- **Order Preservation**: Ensures JSON key ordering is maintained during operations

### Current Test Coverage

- ✅ **Data Models**: Mod metadata, comparison results, synchronization statistics
- ✅ **JSON Processing**: Multi-encoding support, malformed JSON recovery, OrderedDict preservation
- ✅ **Utility Functions**: Safe filename handling, mod ID generation, string operations
- ✅ **Error Handling**: Exception hierarchy and context preservation
- ✅ **Unicode Handling**: International character support and encoding fallbacks

## 🔧 Advanced Features

### Robust JSON Processing

UpLang handles real-world edge cases:
- **Multiple encodings**: UTF-8, UTF-8-sig, Latin1, CP1252
- **Malformed JSON**: Trailing commas, unquoted keys, comments
- **Encoding issues**: UTF-8 BOM, surrogate characters
- **Recovery strategies**: Multiple parsing fallbacks

### Translation Preservation

- **Existing translations** are always preserved during synchronization
- **Key ordering** follows the English language file structure
- **Incremental updates** only process changed files for efficiency
- **Atomic operations** ensure data integrity

### Code Quality Standards

- **Comprehensive Documentation**: All modules, classes, and methods include detailed docstrings
- **Type Safety**: Complete type annotations throughout the codebase
- **Error Handling**: Hierarchical exception system with context information
- **Clean Architecture**: Dependency injection and separation of concerns
- **Professional Standards**: Industry-grade code organization and documentation

### Logging and Monitoring

- **Detailed logs** saved to timestamped files
- **Progress indicators** for long-running operations
- **Error reporting** with context and suggested solutions
- **State tracking** for debugging and auditing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- 🐛 Reporting bugs
- 💡 Suggesting features
- 🔧 Setting up development environment
- 📝 Code style guidelines
- ✅ Testing requirements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful console output
- Uses [uv](https://github.com/astral-sh/uv) for fast dependency management
- Inspired by the Minecraft modding community's localization needs

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/QianFuv/UpLang/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/QianFuv/UpLang/discussions)
- 📧 **Contact**: [Project Maintainer](https://github.com/QianFuv)

---

<div align="center">
  <strong>Made with ❤️ for the Minecraft modding community</strong>
</div>