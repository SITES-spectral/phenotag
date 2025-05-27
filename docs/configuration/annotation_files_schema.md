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
# Metadata
created: "2025-05-14T12:34:56.789012"     # Timestamp when the annotation file was first created (ISO format)
last_modified: "2025-05-14T13:45:12.345678" # Timestamp of the last modification
day_of_year: "001"                        # Day of year (DOY) as a string with leading zeros
year: "2023"                              # Year as a string
station: "abisko"                         # Station name
instrument: "PC01"                        # Instrument identifier
annotation_time_minutes: 45.8             # Accumulated time spent on annotations for this day

# Tracking data
expected_image_count: 12                  # Total number of images for this day
annotated_image_count: 8                  # Number of images that have annotations
completion_percentage: 66.67              # Percentage of images annotated (rounded to 2 decimal places)

# Individual file status
file_status:
  'image1.jpg': "completed"               # Each image has a status: 'completed' or 'in_progress'
  'image2.jpg': "in_progress"
  'image3.jpg': "completed"
  # ... more files

# Annotations
annotations:
  'image1.jpg':                           # Key is the image filename
    - roi_name: "ROI_00"                  # Default ROI (full image)
      discard: false                      # Whether to discard this ROI
      snow_presence: false                # Whether snow is present in this ROI
      flags: []                           # Quality flags (empty list means no flags)
    
    - roi_name: "ROI_01"                  # Custom ROI
      discard: false
      snow_presence: true
      flags: ["sunny", "clouds"]          # Multiple flags can be applied
    
    # More ROIs for this image...
  
  'image2.jpg':
    # Similar structure for other images
    # ...
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

## File Status Values

Each image in the `file_status` section can have one of these values:

- `completed`: All ROIs for the image have been properly annotated
- `in_progress`: Some ROIs for the image still need annotation

## Determining Completion Status

An image is considered fully annotated if:

1. It has annotations for all expected ROIs (ROI_00 plus any custom ROIs)
2. Each ROI has at least one of the following set:
   - `discard` is set to `true`
   - `snow_presence` is set to `true`
   - There is at least one quality flag in the `flags` list
   - The special flag `not_needed` is present in the `flags` list

Day completion percentage is calculated as:
```
(annotated_image_count / expected_image_count) * 100
```

## Important Implementation Notes

### "No Annotation Needed" Field

The `not_needed` field is implemented as a separate boolean property:

```yaml
annotations:
  'image1.jpg':
    - roi_name: "ROI_00"
      discard: false
      snow_presence: false
      flags: []           # Empty list - no actual quality flags
      not_needed: true    # Separate field indicating no annotation needed
```

> **⚠️ IMPORTANT**: This is implemented as a dedicated boolean field rather than a flag in the flags list.
> This design:
> 1. Keeps the flags list exclusively for actual quality indicators
> 2. Makes flag counting more accurate (flags.length only counts actual quality flags)
> 3. Provides clearer separation of concerns in the data model
> 4. Supports backward compatibility with older annotation files
>
> When loading older files that used "not_needed" as a flag, it's automatically migrated to the new field structure.

## File Management

### Creating and Saving Annotations

Annotations are created and saved through these primary functions:

1. `save_all_annotations()` in `src/phenotag/ui/components/annotation.py`
   - Main function that orchestrates saving annotations
   - Supports force saving and auto-saving functionality
   - Creates any necessary directories
   - Updates completion statistics and file status

2. `save_status_to_l1_parent()` in `src/phenotag/ui/components/annotation_status_manager.py`
   - Updates the centralized status file when annotation status changes

### Loading Annotations

Annotations are loaded through these functions:

1. `load_day_annotations()` in `src/phenotag/ui/components/annotation.py`
   - Handles loading annotations for a specific day
   - Converts them to the internal format used by the UI
   - Displays completion statistics when loading annotations

2. `display_annotation_completion_status()` in `src/phenotag/ui/components/annotation.py`
   - Shows progress bar and metrics for annotation completion
   - Displays individual file status in a table

## Legacy Format Support

PhenoTag supports loading older annotation files that may not have all the fields described above. When such files are loaded:

1. Basic fields like `annotations` will be processed
2. Missing fields like `expected_image_count` will be calculated when the file is saved
3. The next save operation will update the file to the current schema