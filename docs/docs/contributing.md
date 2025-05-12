# Contributing to MinimalAgent

We're thrilled that you're interested in contributing to MinimalAgent! This document provides guidelines and instructions for contributing to the project.

## Setting Up Development Environment

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/yourusername/minimalagent.git
   cd minimalagent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

We use pytest for testing. Run the tests with:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=src/minimalagent tests/
```

## Code Style

We follow PEP 8 style guidelines. We use Black for code formatting and isort for import sorting:

```bash
black src tests
isort src tests
```

## Pull Request Process

1. **Create a branch for your feature**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**:
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Ensure tests pass**:
   ```bash
   pytest
   ```

4. **Submit a pull request**:
   - Provide a clear description of the changes
   - Reference any issues that the PR addresses
   - Make sure CI checks pass

## Documentation

Documentation is crucial - please update docs when adding or changing features:

- Update docstrings for any modified functions/classes
- Update README.md if appropriate
- Update CHANGELOG.md with your changes
- For significant changes, add/update the appropriate documentation pages

To preview documentation changes:

```bash
mkdocs serve
```

Then visit http://localhost:8000 in your browser.

## Reporting Issues

When reporting issues, please include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- System information (Python version, OS, etc.)
- If possible, a minimal code example demonstrating the issue

## Feature Requests

We welcome feature requests! When submitting:

- Describe the feature in detail
- Explain why it would be valuable
- Provide examples of how it would be used
- Indicate if you're willing to help implement it

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.