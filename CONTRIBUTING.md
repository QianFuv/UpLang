# Contributing to UpLang

We welcome and appreciate contributions to the `UpLang` project! By contributing, you help us improve and expand the tool for everyone. Please take a moment to review this guide to make the contribution process as smooth as possible.

## Table of Contents

1.  [Code of Conduct](#code-of-conduct)
2.  [How to Contribute](#how-to-contribute)
    *   [Reporting Bugs](#reporting-bugs)
    *   [Suggesting Enhancements](#suggesting-enhancements)
    *   [Writing Code](#writing-code)
3.  [Development Setup](#development-setup)
4.  [Coding Guidelines](#coding-guidelines)
5.  [Testing](#testing)
6.  [Submitting Changes](#submitting-changes)
7.  [License](#license)

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on our [GitHub Issues page](https://github.com/QianFuv/UpLang/issues). When reporting a bug, please include:

*   A clear and concise description of the bug.
*   Steps to reproduce the behavior.
*   Expected behavior.
*   Actual behavior.
*   Screenshots or error messages (if applicable).
*   Your operating system, Python version, and `UpLang` version.

### Suggesting Enhancements

Have an idea for a new feature or an improvement to existing functionality? We'd love to hear it! Please open an issue on our [GitHub Issues page](https://github.com/QianFuv/UpLang/issues) and describe your suggestion in detail.

### Writing Code

We welcome code contributions! If you'd like to contribute code, please follow the steps outlined in the [Submitting Changes](#submitting-changes) section.

## Development Setup

To set up your development environment:

1.  **Prerequisites**: Ensure you have Python 3.11+ and `uv` installed.
    *   [Download Python](https://www.python.org/downloads/)
    *   `pip install uv`
2.  **Clone the repository**:
    ```bash
    git clone https://github.com/QianFuv/UpLang.git
    cd UpLang
    ```
3.  **Install dependencies in a virtual environment**:
    ```bash
    uv pip install -e .[test]
    ```
    This command installs the project in editable mode and includes test dependencies.

## Coding Guidelines

*   **Follow PEP 8**: Adhere to Python's official style guide.
*   **Type Hinting**: Use type hints for function arguments and return values.
*   **Clear and Concise Code**: Write readable and maintainable code.
*   **Comments**: Add comments where necessary to explain complex logic or non-obvious decisions.
*   **Docstrings**: Use docstrings for modules, classes, and functions.

## Testing

Before submitting your changes, please ensure all existing tests pass and add new tests for any new features or bug fixes.

To run the tests:

```bash
uv run pytest tests/test_integration.py
```

## Submitting Changes

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine.
3.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    ```
    or
    ```bash
    git checkout -b bugfix/your-bug-fix-name
    ```
4.  **Make your changes** and commit them with clear, concise commit messages.
5.  **Push your branch** to your forked repository.
6.  **Open a Pull Request** to the `main` branch of the original `UpLang` repository.
    *   Provide a clear title and description for your pull request.
    *   Reference any related issues.
    *   Ensure your code passes all tests.

## License

By contributing to `UpLang`, you agree that your contributions will be licensed under the MIT License.
