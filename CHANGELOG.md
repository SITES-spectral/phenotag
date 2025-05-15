# Changelog

All notable changes to the PhenoTag project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Centralized annotation status tracking system:**
  - Status saved in L1 parent folder with consistent naming pattern: `L1_annotation_status_{station}_{instrument}.yaml`
  - Calendar view shows progress icons based on centralized status tracking
  - Improved annotation status caching for better performance
  - Automatic status updates when annotations are saved
- **Enhanced annotation time tracking:**
  - Accumulation of annotation time across multiple sessions
  - Preservation of previous annotation time when updating files
  - Improved time tracking to avoid double-counting
  - Better display of total annotation time in the UI

### Fixed
- Fixed an undefined `annotation_time_minutes` error in the annotation saving function
- Added missing `yaml` import to fix annotation loading error
- Fixed `station_name` reference error when saving to L1 parent directory
- **Fixed critical issue with annotation auto-saving overwriting data:**
  - Implemented robust normalized comparison to avoid false change detection
  - Enhanced the annotation loading logic to properly update widget values
  - Added explicit widget state management to ensure flags appear correctly in UI
  - Prevented auto-saving when annotations are just loaded (vs. actually changed)
  - Added detailed debug logging to track annotation changes
  - Fixed type inconsistencies in flag comparisons
- **Enhanced "Copy ROI_00 Settings to All ROIs" behavior:**
  - Changed from persistent linkage to a one-time copy operation
  - Added checkboxes to select which settings to copy (flags, discard, snow presence)
  - Allows individual customization of ROIs after copying common settings
  - More descriptive success message showing which settings were copied

### Added
- New UI guide documentation (`docs/ui_guide.md`)
- Persistent annotation system that saves annotations to YAML files
- **Enhanced "Apply ROI_00 Settings to All ROIs" button functionality:**
  - Improved consistency by applying all settings (discard, snow presence, and flags)
  - Added detailed visual indicators showing which ROIs are affected
  - Enhanced error handling with clear user feedback
  - Added comprehensive logging for easier debugging
  - Improved UI notifications when settings are applied from ROI_00
  - Added expandable list of affected ROIs in the ROI_00 tab
- New `save_annotations` and `load_annotations` functions in io_tools
- Documentation of the annotation storage system (`docs/annotation_system.md`)
- Comprehensive stations.yaml schema documentation (`docs/stations_yaml_schema.md`)
- Enhanced debugging output for image counting in calendar view
- Specific debugging for day 90 (March 31st) which had format mismatch issues
- Added toggle for showing ROI overlays on images in the image viewer
- Added "Load Instrument ROIs" button to use instrument-specific ROIs from stations.yaml configuration
- Support for displaying multiple instrument-specific ROIs with proper coloring and naming
- Advanced ROI lookup using normalized station names from configuration
- Improved ROI information display showing details of loaded ROIs
- Added instrument ROI discovery across all stations for moved instruments
- Enhanced debugging for ROI loading with detailed step-by-step progress output
- Added robust error handling for ROI application issues with fallback to default ROIs
- Added format conversion between YAML-friendly ROI format and OpenCV-compatible format
- Implemented a custom ROI overlay function as fallback for handling format issues
- Fixed polygon point format conversion to ensure compatibility with OpenCV drawing functions
- Improved ROI format conversion with enhanced compatibility between YAML and OpenCV formats
- Added enhanced error handling with proper format validation for ROI display
- Implemented better color handling in ROI display with improved text visibility
- Fixed inconsistencies between stations.yaml ROI format and ImageProcessor requirements
- Added support for both tuple and list format handling in ROI overlay
- Added ROI transparency/alpha support with improved rendering
- Created a robust format conversion utility for ROI representation
- Added "Load Full Station Configuration" button to view complete station data from stations.yaml
- New station configuration viewer with tabs for formatted and raw JSON views
- Interactive structured display of stations, platforms, instruments, and available ROIs
- **Redesigned ROI annotations UI with tabbed interface:**
  - Individual tab for each ROI for focused annotation
  - Summary tab showing overview of all annotated ROIs
  - Statistics on annotation status with metrics
  - Flag distribution visualization
  - Improved organization and workflow
- **Enhanced annotation auto-save system with:**
  - Automatic saves every 60 seconds when changes are detected
  - User-configurable auto-save option with toggle
  - "Save immediately on changes" option for real-time persistence
  - Visual countdown timer for next auto-save
  - Contextual save button that changes label based on save status
  - Visual indicators showing saved/unsaved state with timestamps
  - Automatic saving when navigating between days, instruments, or stations
  - Forced saves on all context changes (switching tabs, days, stations, instruments)
  - Comprehensive save enforcement during critical operations
- **Annotation timer system for tracking work metrics:**
  - Automatic tracking of time spent on annotations for each day
  - Inactivity detection that pauses timer after 3 minutes without interaction
  - Persistent time tracking that accumulates across sessions
  - Display of elapsed annotation time in the UI
  - Storage of annotation time as metadata in YAML files
  - Integration with navigation and auto-save systems
  - Automatic pausing when switching contexts (days, instruments, stations)

### Changed
- Further improved directory scanner to handle all day-of-year formats (padded, unpadded, and integer)
- Enhanced calendar component to be more resilient to different day-of-year formats
- Added detailed debugging output for calendar image counting
- Improved image counting algorithm to support all path format variations
- Enhanced day format handling with triple-format checking (padded, unpadded, and integer)
- **Completely refactored the UI into modular components:**
  - Split monolithic main.py into clean, reusable components
  - Created component-based architecture with clear separation of concerns
  - Moved ROI utilities to a dedicated module to avoid circular imports
  - Integrated memory management directly into the main UI
  - Moved calendar view to sidebar for better organization
  - Improved annotation panel with status indicators and auto-save
  - Enhanced layout with better use of containers and columns
  - Simplified UI by removing tab interface - focused on current image annotation only

### Fixed
- Fixed critical issue with calendar not showing correct image counts for certain days
- Resolved inconsistencies between the calendar view and dataframe display
- Enhanced robustness for day-of-year format handling to prevent missing images
- Fixed specific issue with day 090 (March 31st) not showing proper image counts in calendar
- **Fixed annotation persistence issues:**
  - Resolved issue with annotations not loading when returning to a previously annotated day
  - Fixed inconsistent behavior when switching between instruments and stations
  - Added robust state tracking for annotation loading
  - Improved error handling during annotation loading and saving
  - Added save-before-navigation to prevent data loss
  - Enhanced debugging for annotation operations
  - Fixed session state conflict with auto-save widgets when switching between tabs
  - Implemented tab-specific session state keys to prevent widget conflicts

## [0.2.0] - 2025-05-12

### Added
- Memory-efficient directory scanning for phenocam images
- Lazy loading for image data to reduce memory usage
- Calendar view for date-based image navigation
- Support for scanning by month
- Consistent handling of day-of-year directories with and without leading zeros
- Debug logging to help troubleshoot month filtering issues
- Added auto-discovery of directories for better user experience
- Automatic scanning for days when opening the calendar view

### Fixed
- Month filtering now correctly handles days with or without leading zeros
- Directory paths now try both with and without leading zeros for better compatibility
- Calendar now correctly shows images for the selected month
- Improved UI feedback when switching between stations and instruments
- Fixed scanning behavior to only load directories as needed
- Made interface more resilient to different directory naming conventions
- Added proper filtering of days by month in the calendar view
- Fixed PyArrow conversion issue when displaying files in the dataframe
- Fixed image count discrepancy in the calendar view
- Fixed calendar not showing images due to day of year format mismatches (leading zeros)

### Changed
- Path handling in directory scanner to support different directory formats
- Improved path construction to try multiple path formats
- Added diagnostic logging to monitor day filtering operations
- Enhanced UI to display only timestamps instead of full filenames
- Added guidance for when no L1 data is found
- Switched to a more memory-efficient approach for directory scanning
- Improved "Scan for Images" to preserve existing data
- Added a single "Refresh Data" button that safely refreshes years, months, and days
- Made scanning operations non-destructive to prevent data loss
- Improved data handling when changing months or years in the calendar
- Added progress indicators throughout the application for better user feedback

## [0.1.1] - 2025-05-10

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