# Contributing to UpLang

Thank you for your interest in contributing to **UpLang**! We welcome all types of contributions from the community. This guide will help you get started and ensure your contributions are accepted smoothly.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your improvements**
5. **Test thoroughly**
6. **Submit a pull request**

## 🤝 Code of Conduct

This project follows a simple code of conduct:

- **Be respectful** and constructive in all interactions
- **Welcome newcomers** and help them get started
- **Focus on the code**, not the person
- **Assume good intentions** from all contributors

By participating, you agree to maintain a welcoming environment for everyone.

## 🛠️ How to Contribute

### 🐛 Reporting Bugs

Found a bug? We'd love to hear about it! Please [open an issue](https://github.com/QianFuv/UpLang/issues/new) and include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, UpLang version)
- **Log files** if available (check resource pack directory for `uplang_*.log`)
- **Sample files** if the issue involves specific mods or language files

**Example bug report:**
```
**Bug:** Synchronization fails with error when processing mod X

**Steps to reproduce:**
1. Run `uplang init mods/ resource_pack/`
2. Add mod_x.jar to mods directory
3. Run `uplang check mods/ resource_pack/`

**Expected:** New mod should be processed successfully
**Actual:** Error message "Invalid JSON format" appears

**Environment:**
- OS: Windows 11
- Python: 3.11.2
- UpLang: 1.0.0

**Additional context:**
Log file shows encoding issues with mod's en_us.json file.
```

### 💡 Suggesting Features

Have an idea for improvement? We'd love to hear it! Please [open an issue](https://github.com/QianFuv/UpLang/issues/new) with:

- **Clear description** of the proposed feature
- **Use case** or problem it solves
- **Proposed implementation** (if you have ideas)
- **Examples** of how it would work

### 🔧 Contributing Code

We welcome code contributions! Here are some areas where help is especially appreciated:

- **Bug fixes** for open issues
- **Performance improvements** for large modpacks
- **Support for additional languages** beyond Chinese
- **Enhanced error handling** for edge cases
- **Documentation improvements**
- **Test coverage expansion**

## 🛠️ Development Setup

### Prerequisites

- **Python 3.11+** installed
- **Git** for version control
- **uv** for dependency management (recommended)

### For Users (PyPI Installation)

If you just want to use UpLang:

```bash
# Install from PyPI
pip install uplang

# Verify installation
uplang --help
```

### For Contributors (Development Setup)

If you want to contribute to UpLang:

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/UpLang.git
cd UpLang

# 3. Install uv (if not already installed)
pip install uv

# 4. Install dependencies
uv sync

# 5. Install in editable mode
uv pip install -e .

# 6. Verify installation
uplang --help
# or
python -m uplang.cli --help
```

### Alternative Development Setup (using pip)

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/UpLang.git
cd UpLang

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with test dependencies
pip install -e .[test]
```

## 📝 Coding Standards

### Python Style

- **Follow PEP 8** for code formatting
- **Use type hints** for all function parameters and returns
- **Write descriptive docstrings** for modules, classes, and functions
- **Keep functions focused** - one responsibility per function
- **Use meaningful variable names** - prefer clarity over brevity

### Code Organization

```python
# Good: Clear imports and type hints
from pathlib import Path
from typing import Dict, List, Optional
from collections import OrderedDict

def synchronize_language_files(
    zh_cn_path: Path,
    en_us_path: Path,
    logger: Optional[Logger] = None
) -> Dict[str, int]:
    """
    Synchronize Chinese language file with English reference.

    Args:
        zh_cn_path: Path to Chinese language file
        en_us_path: Path to English language file
        logger: Optional logger instance

    Returns:
        Dictionary with sync statistics
    """
    # Implementation here
```

### Error Handling

- **Use specific exceptions** rather than generic `Exception`
- **Provide helpful error messages** with context
- **Log errors appropriately** for debugging
- **Fail gracefully** when possible

```python
# Good: Specific error handling
try:
    data = read_json_robust(file_path, logger)
except FileNotFoundError:
    logger.warning(f"Language file not found: {file_path}")
    return {}
except JSONDecodeError as e:
    logger.error(f"Invalid JSON in {file_path}: {e}")
    return {}
```

### Documentation

- **Document all public functions** with docstrings
- **Include type information** in docstrings
- **Provide usage examples** for complex functions
- **Update README** if adding new features

## 🧪 Testing Guidelines

### Running Tests

```bash
# If using development setup
uv run pytest tests/test_integration.py -v

# If using pip installation
python -m pytest tests/test_integration.py -v

# Run with coverage (development)
uv run pytest tests/test_integration.py --cov=uplang

# Run specific test
uv run pytest tests/test_integration.py::test_language_file_synchronization -v
```

### Writing Tests

- **Add tests for new features** and bug fixes
- **Use descriptive test names** that explain what's being tested
- **Include edge cases** and error conditions
- **Mock external dependencies** when appropriate

```python
def test_synchronization_preserves_existing_translations():
    """Test that synchronization keeps existing Chinese translations."""
    # Setup test data
    en_data = OrderedDict([("key1", "English 1"), ("key2", "English 2")])
    zh_data = OrderedDict([("key1", "中文 1")])

    # Run synchronization
    result = synchronize_files(zh_data, en_data)

    # Verify results
    assert result["key1"] == "中文 1"  # Preserved
    assert result["key2"] == "English 2"  # Added
```

### Test Data

- **Use the existing test framework** in `tests/create_test_data.py`
- **Create realistic test scenarios** with actual mod structures
- **Clean up test files** after each test run

## 📤 Submitting Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-fabric-support` for new features
- `bugfix/fix-unicode-handling` for bug fixes
- `docs/update-readme` for documentation changes

### Commit Messages

Write clear commit messages:
```
feat: add support for Fabric mod metadata parsing

- Parse fabric.mod.json files in addition to mods.toml
- Add Fabric-specific mod ID extraction logic
- Update tests to cover both Forge and Fabric scenarios

Fixes #123
```

### Pull Request Process

1. **Create a pull request** from your feature branch to `main`
2. **Fill out the PR template** with details about your changes
3. **Ensure all tests pass** and add new tests if needed
4. **Request review** from maintainers
5. **Address feedback** promptly and push updates
6. **Merge** will be handled by maintainers after approval

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No breaking changes (or clearly documented)

## 🆘 Getting Help

Need help? Here are your options:

- **Check existing issues** for similar problems
- **Ask in GitHub Discussions** for general questions
- **Join our community** (links in README)
- **Tag maintainers** in issues if urgent

### Good Questions

- "How should I implement X feature to fit with the existing architecture?"
- "I'm seeing Y error when testing Z scenario, any suggestions?"
- "What's the best way to handle edge case A?"

## 🏷️ Release Process

For maintainers and regular contributors:

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Create release tag** following semantic versioning
4. **Update documentation** if needed

## 🎉 Recognition

All contributors will be:
- **Listed in the repository** contributors section
- **Credited in release notes** for their contributions
- **Welcomed as community members** with maintainer consideration for regular contributors

## 📄 License

By contributing to UpLang, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to UpLang! Your efforts help make Minecraft modpack localization easier for everyone. 🎮✨