# UpLang Test Suite

This directory contains the complete test suite for UpLang, redesigned using pytest with comprehensive coverage of core functionality.

## Test Structure

- `conftest.py` - Shared pytest fixtures and configuration
- `test_models.py` - Tests for data model classes (Mod, ModComparisonResult, SyncStats)
- `test_json_utils.py` - Tests for robust JSON handling utilities
- `test_utils.py` - Tests for utility functions (filename sanitization, mod ID creation)

## Running Tests

```bash
# Run all tests
PYTHONPATH=src python -m pytest tests/ -v

# Run with coverage
PYTHONPATH=src python -m pytest tests/ --cov=uplang --cov-report=html

# Run specific test file
PYTHONPATH=src python -m pytest tests/test_models.py -v
```

## Test Coverage

The test suite covers:

- **Data Models**: Comprehensive testing of mod metadata, comparison results, and synchronization statistics
- **JSON Utilities**: Robust JSON parsing with encoding fallbacks, malformed JSON recovery, and order preservation
- **Utility Functions**: Filename sanitization, mod ID creation, and path handling
- **Error Handling**: Edge cases, invalid inputs, and graceful error recovery
- **Unicode Support**: Proper handling of international characters and emoji

## Key Features

- **Fixtures**: Reusable test data including mock JAR files and temporary directories
- **Order Preservation**: Tests verify that JSON key ordering is maintained during read/write operations
- **Error Recovery**: Comprehensive testing of fallback strategies for malformed files
- **Unicode Handling**: Full support for international characters in filenames and content
- **Real-world Scenarios**: Tests based on actual Minecraft mod file structures and common issues

All tests follow the same code style and commenting standards as the main codebase, using English comments and descriptive test names.

## Type Annotations

The test suite includes proper type annotations and handles the distinction between `Dict` and `OrderedDict` types correctly. The `json_utils` module has been updated to use `Mapping[str, Any]` for input parameters to accept both dict and OrderedDict instances, and returns `OrderedDict[str, Any]` to maintain key ordering preservation.