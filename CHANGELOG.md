# Changelog

All notable changes to the PhenoTag project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New UI guide documentation (`docs/ui_guide.md`)
- Persistent annotation system that saves annotations to YAML files
- New `save_annotations` and `load_annotations` functions in io_tools
- Documentation of the annotation storage system (`docs/annotation_system.md`)

### Changed
- Renamed session configuration file to `sites_spectral_phenocams_session_config.yaml` for better descriptiveness
- Updated README.md with more comprehensive setup instructions and feature descriptions
- Enhanced installation instructions to include virtual environment setup
- Enhanced `find_phenocam_images` to check for existing annotation files
- Updated UI's Save Annotations button to properly save annotations to disk
- Annotations now stored at `{base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/annotations.yaml`
- Improved UI: moved scan button out of expander for better visibility
- Added automatic scanning on session load with saved configuration
- Enhanced progress feedback during scanning with status updates
- Replaced sidebar status display with toast notifications for better UX
- Added contextual error and info messages for invalid configurations
- Started UI refactoring with a new three-container layout (top, center, bottom) 
- Implemented a 1:5:1 column ratio in the center container for better content organization
- Removed all titles and subtitles from the main canvas for a cleaner interface
- Added year selector to the sidebar for easier navigation through yearly data
- Improved organization of UI controls with logical grouping in the sidebar

## [0.1.0] - 2025-05-08

### Added
- Modernized Streamlit UI with improved layout and components
- Page configuration with title, icon, and layout settings
- Status elements for better process visualization
- Enhanced sidebar with title, caption, and visual organization
- Tooltips for all major UI elements
- Metrics display for data summary statistics
- Better error messaging and status updates
- Dividers for improved visual separation
- Reset button for annotations

### Changed
- Replaced relative imports with absolute imports for better compatibility
- Fixed image display issues in data editor
- Enhanced data editor with hide_index and improved column configuration
- Updated configuration panel with better visual organization
- Improved button styling with icons and container width settings
- Enhanced image scanner workflow with better status feedback
- Better station and instrument selection interface
- More consistent UI styling throughout

### Fixed
- Image display issues in the data editor by implementing a split-layout approach
- Import errors caused by relative imports
- Deprecated parameter warnings by updating to current Streamlit API
- Annotations are now properly persisted between sessions
- Added better error messages and user feedback for annotation operations

## [0.0.1] - 2025-05-01

### Added
- Initial release
- Basic Streamlit UI
- Station and instrument selection
- Data directory configuration
- Image scanning functionality
- Year and day selection
- Image display and annotation
- Session state persistence
- Memory optimization option

[Unreleased]: https://github.com/username/phenotag/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/username/phenotag/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/username/phenotag/releases/tag/v0.0.1