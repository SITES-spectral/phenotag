---
![SITES Spectral Thematic Center](https://h24-original.s3.amazonaws.com/231546/28893673-EQhe9.png "SITES Spectral Thematic Center")

# Swedish Infrastructure for Ecosystem Science (SITES) - Spectral | Thematic Center (SSTC)

["SITES spectral"](https://www.fieldsites.se/en-GB/sites-thematic-programs/sites-spectral-32634403)

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

# Image utilities - get default ROI for a JPEG image
phenotag images default-roi path/to/image.jpg

# Get default ROI in JSON format with custom parameters
phenotag images default-roi path/to/image.jpg --format json --roi-name "Custom_ROI" --color "255,0,0"
```

#### Run Command Options:
- `--port/-p`: Specify the port (default: 8501)
- `--host`: Specify the host (default: localhost)
- `--browser`: Open the UI in the default browser
- `--memory-optimized/-m`: Use memory-optimized version with advanced memory management

#### Image Utilities

The `images default-roi` command generates default ROI coordinates for JPEG images using the same intelligent sky detection algorithm as the main application:

```bash
# Basic usage - outputs YAML format compatible with stations.yaml
phenotag images default-roi image.jpg

# Output in JSON format
phenotag images default-roi image.jpg --format json

# Customize ROI parameters
phenotag images default-roi image.jpg --roi-name "ROI_02" --color "255,0,0" --thickness 5
```

**Options:**
- `--format/-f`: Output format - 'yaml' (default) or 'json'
- `--roi-name`: Name for the ROI (default: 'ROI_00')
- `--color`: RGB color as comma-separated values (default: '0,255,0' for green)
- `--thickness`: Line thickness for the ROI (default: 7)

The default ROI algorithm intelligently detects and excludes sky areas when possible, or falls back to the full image frame. This ensures optimal region selection for phenological analysis.

For detailed information about the algorithm, see `docs/default_roi_algorithm.md`.
For practical examples and workflow integration, see `docs/default_roi_examples.md`.

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
{data_dir}/{station}/phenocams/products/{instrument}/L1/{year}/{doy}/annotations_{doy}.yaml
```

The annotation system features:
- Intelligent auto-save with 60-second interval for annotations
- User-toggleable auto-save with visual countdown display
- Automatic saving when changing days, instruments, or stations
- Visual indicators of save status and unsaved changes
- Time-stamped save history with clear success/failure feedback
- Automatic loading of existing annotations when navigating to a day
- Persistence of annotations across sessions
- Clear status indicators showing the annotation state
- **Annotation timer that tracks time spent on each day:**
  - Automatically tracks active annotation time with 3-minute inactivity detection
  - Displays elapsed time in the annotation panel
  - Persists timing data in annotation files for reporting and analytics
  - Accumulates annotation time across multiple sessions

For detailed documentation, see `docs/api-reference/annotation_system.md`.

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

### Key Documentation

- `docs/`: Main documentation index
- `docs/user-guide/`: User guides and tutorials
- `docs/developer-guide/`: Developer documentation and integration guides
- `docs/configuration/`: Configuration file schemas and documentation
- `docs/algorithms/`: Algorithm documentation (ROI detection, etc.)
- `docs/api-reference/`: API and system documentation
- `docs/external_api_docs/`: Third-party library documentation

### Adding New Features

When adding new features:
1. Update the relevant modules
2. Add appropriate tests
3. Update documentation
4. Ensure session state persistence if applicable

## Maintainers

* José M. Beltrán-Abaunza, PhD | Lund University, Department of Physical Geography and Ecosystem Science | SITES spectral Research Engineer

## Contributors

* José M. Beltrán-Abaunza, PhD | Lund University, Department of Physical Geography and Ecosystem Science | SITES spectral Research Engineer
* Lars Eklundh, Professor | Lund University, Department of Physical Geography and Ecosystem Science | SITES spectral Coordinator
* Kexin Guo | Lund University, Department of Physical Gepgraphy and Ecosystem Science | Bachelor program 2022-2025 | Supported UX and code alpha testing, annotations, data analysis, and codebase debugging. Thesis to be linked here.

## Development Support

This package was developed with support from [Claude](https://claude.ai/code) (Anthropic's Claude 3.5 Sonnet model), which assisted with code refactoring, documentation organization, and architectural improvements.

## Citation

If you use this package in your research, please cite it as follows:

**Chicago Style (Author-Date):**

Beltrán-Abaunza, José M., and Lars Eklundh. *PhenoTag: A Python Package for Phenological Image Annotation*. Version [version]. Lund: SITES Spectral Thematic Center, Lund University, 2025. https://github.com/sites-spectral/phenotag.

**Chicago Style (Notes-Bibliography):**

Beltrán-Abaunza, José M., and Lars Eklundh. *PhenoTag: A Python Package for Phenological Image Annotation*. Version [version]. Lund: SITES Spectral Thematic Center, Lund University, 2025. https://github.com/sites-spectral/phenotag.

**BibTeX:**
```bibtex
@software{beltran_abaunza_phenotag_2025,
  author = {Beltrán-Abaunza, José M. and Eklundh, Lars},
  title = {PhenoTag: A Python Package for Phenological Image Annotation},
  year = {2025},
  publisher = {SITES Spectral Thematic Center, Lund University},
  address = {Lund, Sweden},
  url = {https://github.com/sites-spectral/phenotag},
  note = {Version [version]}
}
```

*Replace [version] with the specific version number you used.*
