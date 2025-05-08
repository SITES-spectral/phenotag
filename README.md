# PhenoTag

A tool for annotating phenocam images with quality indicators and regions of interest (ROIs) for the SITES Spectral ecosystem.

## Features

- Modern Streamlit-based UI with optimal layout and components
- Station and instrument selection from dropdown menus with tooltips
- Interactive data directory configuration with simplified workflow
- Memory-efficient image loading and processing
- Image annotation capabilities for quality assessment and ROI definition
- Persistent annotations stored in YAML files alongside image data
- Session state persistence via descriptive YAML configuration files
- Real-time feedback with status indicators and progress tracking

## Installation

### Requirements

- Python 3.12+
- Dependencies listed in `pyproject.toml`

### Setup

1. Clone this repository
2. Create and activate a virtual environment (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   # or using uv (recommended)
   uv pip install -e .
   ```

4. For development, install with development dependencies:
   ```bash
   pip install -e ".[dev]"
   # or using uv (recommended)
   uv pip install -e ".[dev]"
   ```

## Usage

### Direct Execution

Run the Streamlit application:

```bash
streamlit run src/phenotag/app/main.py
```

### CLI

PhenoTag can also be run via CLI:

```bash
# Display help and available commands
phenotag

# Run the standard application
phenotag run

# Run with memory-optimized version
phenotag run --memory-optimized

# Run with specific port and host
phenotag run --port 8080 --host 0.0.0.0
```

Command line options:
- `--port/-p`: Specify the port (default: 8501)
- `--host`: Specify the host (default: localhost)
- `--browser`: Open the UI in the default browser
- `--memory-optimized/-m`: Use memory-optimized version with advanced memory management

## Data Organization

PhenoTag expects data to be organized in the following structure:

```
{data_dir}/{station}/phenocams/products/{instrument}/L1/{year}/{doy}/
```

Where:
- `{data_dir}`: Base directory for data storage
- `{station}`: Station name (e.g., "abisko")
- `{instrument}`: Phenocam instrument name (e.g., "netcam01")
- `{year}`: Year in YYYY format
- `{doy}`: Day of year in DDD format

## Components

### UI (User Interface)

The UI is built using Streamlit and provides:
- Sidebar with station and instrument selection
- Configuration options for data directory
- Session management (save, reset, auto-save)
- Data editor for viewing and annotating images

### IO Tools

Handles file operations including:
- YAML configuration loading and saving
- Image path discovery and filtering
- Session configuration management

### Image Processor

Provides memory-efficient image handling:
- Lazy loading of images to reduce memory footprint
- Image resizing and formatting for display
- ROI management and analysis
- Chromatic coordinate calculations

### Memory Management (New!)

The memory-optimized version includes:
- Real-time memory usage monitoring and visualization
- Automatic image downscaling when memory is limited
- Smart caching with auto-cleanup for large datasets
- Memory usage dashboard in the UI
- Memory tracking tools for performance optimization

To use the memory-optimized version:
```bash
phenotag run --memory-optimized
```

For detailed documentation, see `docs/memory_management_example.md`.

## Session Management

PhenoTag automatically saves the session state to `~/.phenotag/sites_spectral_phenocams_session_config.yaml` when:
- Changing selected station
- Changing selected instrument
- Modifying the data directory
- Scanning for images

Sessions can be manually saved or reset using the clearly labeled buttons in the Configuration panel:
- 💾 Save Session: Manually save current session state
- 🔄 Reset Session: Clear and reset current session

When working with annotations, the UI provides additional options:
- 💾 Save Annotations: Save the current annotations and session state
- 🔄 Reset Annotations: Reset the current view of annotations

## Annotation System

PhenoTag stores image annotations in YAML files alongside the images they describe:

```
{data_dir}/{station}/phenocams/products/{instrument}/L1/{year}/{doy}/annotations.yaml
```

The annotation system:
- Automatically loads existing annotations when scanning images
- Saves annotations when the user clicks "Save Annotations"
- Stores quality flags and ROI information for each image
- Persists annotations between sessions
- Handles errors gracefully with user feedback

For detailed documentation, see `docs/annotation_system.md`.

## Development

### Project Structure

- `src/phenotag/ui/`: Main UI code
- `src/phenotag/io_tools/`: I/O utilities
- `src/phenotag/processors/`: Image processing modules
- `src/phenotag/config/`: Configuration files
- `src/phenotag/memory/`: Memory management system
- `src/phenotag/cli/`: Command-line interface
- `docs/`: Documentation
- `tests/`: Test files

### Adding New Features

When adding new features:
1. Update the relevant modules
2. Add appropriate tests
3. Update documentation
4. Ensure session state persistence if applicable