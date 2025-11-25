---
![SITES Spectral Thematic Center](https://h24-original.s3.amazonaws.com/231546/28893673-EQhe9.png "SITES Spectral Thematic Center")

# Swedish Infrastructure for Ecosystem Science (SITES) - Spectral | Thematic Center (SSTC)

["SITES spectral"](https://www.fieldsites.se/en-GB/sites-thematic-programs/sites-spectral-32634403)

# PhenoTag Documentation

Welcome to the PhenoTag documentation. This guide is organized into sections to help you quickly find the information you need.

## 📚 Documentation Sections

### [User Guide](./user-guide/)
Start here if you're new to PhenoTag or want to learn how to use the application effectively.

- [**Quick Start Guide**](./user-guide/quickstart.md) - Get running in under 2 minutes
- [**Getting Started for Beginners**](./user-guide/phenotag_for_beginners.md) - Complete introduction with visual guides
- [**User Interface Guide**](./user-guide/ui_guide.md) - Comprehensive UI component reference
- [**Annotation Workflow**](./user-guide/popup_annotation_workflow.md) - Step-by-step annotation process

### [Developer Guide](./developer-guide/)
Technical documentation for developers extending or integrating PhenoTag.

- [**Integration Guide**](./developer-guide/phenotag_integration_guide.md) - Using PhenoTag in your applications
- [**Core Integration**](./developer-guide/phenotag_core_integration.md) - Core API integration
- [**ROI Overlay Integration**](./developer-guide/roi_overlay_integration_guide.md) - Working with ROI overlays
- [**Memory Management**](./developer-guide/memory_management_example.md) - Optimizing memory usage
- [**I/O Tools**](./developer-guide/io_tools.md) - File operations and data handling

### [Configuration](./configuration/)
Reference documentation for configuration files and schemas.

- [**Stations Configuration**](./configuration/stations_yaml_schema.md) - Camera station setup
- [**Annotation Schema**](./configuration/annotation_files_schema.md) - Annotation file format
- [**Station Normalization**](./configuration/station_name_normalization.md) - Naming conventions
- [**Filename Formats**](./configuration/filename_formats.md) - File naming standards

### [Algorithms](./algorithms/)
Documentation for the algorithms used in PhenoTag.

- [**Default ROI Algorithm**](./algorithms/default_roi_algorithm.md) - Automatic ROI detection
- [**ROI Examples**](./algorithms/default_roi_examples.md) - Practical ROI usage examples
- [**OpenCV ROI Processing**](./algorithms/opencv-roi-docs.md) - OpenCV-based ROI operations

### [API Reference](./api-reference/)
System architecture and API documentation.

- [**Annotation System**](./api-reference/annotation_system.md) - Annotation storage and management
- [**Loading and Saving**](./api-reference/annotation_loading_saving.md) - Data persistence operations

### [External API Docs](./external_api_docs/)
Documentation for third-party libraries used in PhenoTag.

- [**Streamlit**](./external_api_docs/streamlit/) - Web UI framework
- [**DuckDB**](./external_api_docs/duckdb/) - Analytics database
- [**Polars**](./external_api_docs/polars/) - Fast DataFrame library
- [**Marimo**](./external_api_docs/marimo/) - Reactive notebooks
- [**OpenCV**](./external_api_docs/opencv/) - Computer vision library

### [Tutorials](./tutorials/)
Step-by-step tutorials and practical examples.

*(Coming soon)*

### [Legacy Documentation](./legacy/)
Older documentation kept for reference.

- Contains previous PR descriptions and deprecated documentation
- Not actively maintained

## 🚀 Quick Start

1. **New Users**: Start with the [Quick Start Guide](./user-guide/quickstart.md) or [Beginners Guide](./user-guide/phenotag_for_beginners.md)
2. **Developers**: Check the [Integration Guide](./developer-guide/phenotag_integration_guide.md)
3. **Configuration**: See [Stations Configuration](./configuration/stations_yaml_schema.md)

## 📖 Additional Resources

- **Main README**: See the [project README](../README.md) for installation and basic usage
- **CLAUDE.md**: Development instructions for AI-assisted coding at [CLAUDE.md](../CLAUDE.md)
- **Source Code**: Browse the [source code](../src/phenotag/) for implementation details

## Maintainers

* José M. Beltrán-Abaunza, PhD | Lund University, Department of Physical Geography and Ecosystem Science | SITES spectral Research Engineer

## Contributors

* José M. Beltrán-Abaunza, PhD | Lund University, Department of Physical Geography and Ecosystem Science | SITES spectral Research Engineer
* Lars Eklundh, Professor | Lund University, Department of Physical Geography and Ecosystem Science | SITES spectral Coordinator

* Kexin Guo | Lund University, Department of Physical Gepgraphy and Ecosystem Science | Bachelor program 2022-2025 | Supported UX and code alpha testing, data analysis and codebase debuging. Thesis to be linked here.


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
```

*Replace [version] with the specific version number you used.*