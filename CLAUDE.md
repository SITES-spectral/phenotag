# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PhenoTag is a Python application for phenological annotation, built with Streamlit. It's part of the SITES Spectral ecosystem, focusing on phenotype analysis and annotation tools.

## Commands

### Installation

```bash
# Install the package in development mode
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

### Running the Application

```bash
# Run the application through the CLI
python -m phenotag.cli.main run

# Or use the installed script
phenotag run
```

Command line options:
- `--port/-p`: Specify the port (default: 8501)
- `--host`: Specify the host (default: localhost)
- `--browser`: Open the UI in the default browser

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=phenotag

# Run a specific test file
pytest tests/test_io_tools.py

# Run a specific test
pytest tests/test_io_tools.py::test_function_name
```

## Project Architecture

PhenoTag follows a modular architecture:

1. **UI Module** (`src/phenotag/ui/`): 
   - Contains the Streamlit interface components
   - Entry point is `main.py` which sets up the Streamlit application

2. **CLI Module** (`src/phenotag/cli/`):
   - Provides command-line interface for launching the application
   - Handles command-line arguments and bootstraps the UI

3. **Configuration** (`src/phenotag/config/`):
   - Manages application settings from YAML files
   - `flags.yaml`: Quality flags for marking phenocam images
   - `stations.yaml`: Configuration for observation stations

4. **IO Tools** (`src/phenotag/io_tools/`):
   - Utilities for file input/output operations
   - Includes YAML handling for configuration loading

5. **Reports** (`src/phenotag/reports/`):
   - Report generation functionality

## Important Configuration

The application uses Streamlit as its web framework, configured in `pyproject.toml`:

```toml
[tool.streamlit]
entry_point = "phenotag.ui.main:main"
```

CLI entry point is defined as:

```toml
[project.scripts]
phenotag = "phenotag.cli.main:main"
```

Python 3.12+ is required as specified in the project configuration.

## Memory Hints

- Always use mcp `context7 resolve-library-id` for streamlit, duckdb, polars and marimo.
- Prefer to use simple, clean, single tasked functions with clear separation of concerns.
- Avoid backward compatibility when in development mode. We are in development mode.
- Prefer `uv pip` over `pip`

## Additional Guidance

- Always check the external_api_docs/ before any answer

## Documentation Guidance

- Before given an answer that involves streamlit, duckdb, polars, opencv or marimo read the offline documentation in `/home/jobelund/lu2024-12-46/SITES/Spectral/apps/phenotag/docs/external_api_docs` to provide a better and up to date answer.