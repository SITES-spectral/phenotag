# PhenoTag Annotation Files Schema

This document describes how the PhenoTag system manages individual annotation files for each day of phenological data, including the file structure, schema, and management processes.

## File Structure

PhenoTag manages two types of annotation files:

### 1. Daily Annotation Files

These files contain the detailed annotations for each image on a specific day:

```
{base_dir}/{normalized_station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/annotations_{day_of_year}.yaml
```

Example:
```
/home/jobelund/lu2024-12-46/SITES/Spectral/data/lonnstorp/phenocams/products/LON_AGR_PL01_PHE01/L1/2023/123/annotations_123.yaml
```

### 2. Annotation Status Files

These files track the overall annotation status for each day across an instrument:

```
{base_dir}/{normalized_station_name}/phenocams/products/{instrument_id}/L1/L1_annotation_status_{normalized_station_name}_{instrument_id}.yaml
```

Example:
```
/home/jobelund/lu2024-12-46/SITES/Spectral/data/lonnstorp/phenocams/products/LON_AGR_PL01_PHE01/L1/L1_annotation_status_lonnstorp_LON_AGR_PL01_PHE01.yaml
```

## Schema Details

### Daily Annotation File Schema

```yaml
# Annotation file for a specific day
created: "2025-05-14T12:34:56.789012"  # Creation timestamp (ISO format)
day_of_year: "001"                     # Day number (padded with zeros)
station: "abisko"                      # Station name (normalized)
instrument: "ANS_FOR_BL01_PHE01"       # Instrument ID
annotation_time_minutes: 45.8          # Time spent annotating

# Each image is stored as a key with its annotations
annotations:
  '/path/to/file1.jpg':                # Full path to image file
    quality:                           # File-level quality data
      discard_file: false              # Whether to discard the entire file
      snow_presence: false             # Snow presence indicator
    rois:                              # Region of Interest annotations
      ROI_00:                          # ROI_00 is the full image
        discard_roi: false             # Whether to discard this ROI
        snow_presence: false           # Snow presence in this ROI
        annotated_flags: []            # Quality flags for this ROI
      ROI_01:                          # Custom ROI
        discard_roi: false
        snow_presence: true
        annotated_flags: ["sunny", "snow_covered"]
      # Additional ROIs as defined in stations.yaml
```

### Annotation Status File Schema

```yaml
# Status file tracking annotation progress
metadata:
  station: "abisko"                    # Station name (normalized)
  instrument_id: "ANS_FOR_BL01_PHE01"  # Instrument ID
  created: "2025-05-14T10:00:00.000000" # Creation timestamp
  last_updated: "2025-05-14T15:30:00.000000" # Last update timestamp

# Annotation status by year and day
annotations:
  "2023":                              # Year
    "001":                             # Day of year (padded with zeros)
      status: "completed"              # Status: "not_annotated", "in_progress", or "completed"
      last_updated: "2025-05-14T11:22:33.000000"
    "002":
      status: "in_progress"
      last_updated: "2025-05-14T14:20:10.000000"
    # Additional days...
  "2024":
    # Similar structure for other years
```

## File Management

### Creating and Saving Annotations

Annotations are created and saved through these primary functions:

1. `save_all_annotations()` in `src/phenotag/ui/components/annotation.py`
   - Main function that orchestrates saving annotations
   - Supports force saving and auto-saving functionality
   - Creates any necessary directories

2. `save_annotations()` in `src/phenotag/io_tools/__init__.py`
   - Lower-level function that writes the annotation data to YAML files

3. `save_status_to_l1_parent()` in `src/phenotag/ui/components/annotation_status_manager.py`
   - Updates the centralized status file when annotation status changes

### Loading Annotations

Annotations are loaded through these functions:

1. `load_day_annotations()` in `src/phenotag/ui/components/annotation.py`
   - Handles loading annotations for a specific day
   - Converts them to the internal format used by the UI

2. `load_annotations()` in `src/phenotag/io_tools/load_annotations.py`
   - Low-level function to read annotation files from disk

3. `check_day_annotation_status()` in `src/phenotag/ui/components/annotation_status.py`
   - Checks the status of annotations for a given day

## Annotation Process

1. When a user selects a day in the calendar, the system attempts to load existing annotations for that day.

2. If annotations don't exist, default values are created for each image using `get_default_quality_data()` and `get_default_roi_data()`.

3. As the user makes annotations in the UI, the changes are stored in the Streamlit session state.

4. Annotations are saved:
   - Automatically every 60 seconds (configurable)
   - When explicitly requested by the user
   - When switching to a different day, instrument, or station
   - When exiting the application

5. Annotation status is updated in the status file to track progress.

## Validation

The system performs several validations:

1. Ensures all required fields are present
2. Converts annotations from older formats to the current format if necessary
3. Validates field types (e.g., ensures flags are stored as lists)
4. Handles error cases gracefully with appropriate logging
5. Checks for path validity before saving

## Important Notes

- All annotations are station-specific and instrument-specific
- ROIs are defined in the `stations.yaml` configuration file
- Quality flags are defined in the `flags.yaml` configuration file
- Station names are normalized for filesystem operations
- The system tracks time spent on annotations for each day
- Annotation data can be exported and analyzed later