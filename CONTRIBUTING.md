# Contributing to MinimalAgent

We appreciate your interest in contributing to MinimalAgent! This document outlines the process for contributing to the project and provides guidelines to make the process smoother.

## Getting Started

### Setting up the Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/minimalagent.git
   cd minimalagent
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Guidelines

### Code Style

We use [Black](https://github.com/psf/black) for code formatting and [isort](https://github.com/PyCQA/isort) for import sorting. To ensure your code follows our style guidelines:

```bash
# Format with Black
python -m black .

# Sort imports
python -m isort .
```

### Docstrings

All public modules, classes, functions, and methods should have Google-style docstrings. Example:

```python
def function_name(param1: str, param2: int = 0) -> dict:
    """Short description of function.

    Longer description with more details if needed.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of what the function returns
    """
    pass
```

### Testing

We use [pytest](https://docs.pytest.org/) for testing. Please write tests for any new functionality. Tests should be placed in the `tests/` directory.

To run the tests:

```bash
python -m pytest
```

To run tests with coverage report:

```bash
python -m pytest --cov=minimalagent --cov-report=term-missing
```

## Pull Request Process

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, ensuring you follow the code style and add tests.

3. Run the tests to make sure everything passes:
   ```bash
   python -m pytest
   ```

4. Update documentation if necessary.

5. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request against the `main` branch of the original repository.

7. In the pull request description, explain your changes and reference any related issues.

## Release Process

The release process is handled by maintainers using the following steps:

1. Update version in `src/minimalagent/__init__.py`
2. Update the `CHANGELOG.md` file
3. Create a new GitHub release
4. Build and publish to PyPI

## AWS Credentials for Development

Since this package interacts with AWS services, you'll need AWS credentials with appropriate permissions for development and testing. See the README for AWS credential setup instructions.

## License

By contributing to MinimalAgent, you agree that your contributions will be licensed under the project's MIT License.