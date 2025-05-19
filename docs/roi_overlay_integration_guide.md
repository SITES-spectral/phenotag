# ROI Overlay Integration Guide

This guide explains how to integrate PhenoTag's ROI (Region of Interest) overlay functionality into external applications, including how to load and save annotation files.

## Table of Contents

- [Overview](#overview)
- [ROI Overlay System](#roi-overlay-system)
- [Annotation File Format](#annotation-file-format)
- [Integration Example](#integration-example)
- [Working with Annotation Files](#working-with-annotation-files)
- [Best Practices](#best-practices)
- [Common Issues and Solutions](#common-issues-and-solutions)

## Overview

PhenoTag provides functionality for defining, displaying, and annotating Regions of Interest (ROIs) on phenocam images. This functionality can be leveraged by external applications through direct integration with PhenoTag's components or by implementing compatible interfaces.

## ROI Overlay System

The ROI overlay system consists of:

1. **ROI Definition**: Polygons defined by coordinates that represent areas of interest in an image
2. **Overlay Rendering**: Functions to draw ROIs onto images with proper colors and labels
3. **Serialization/Deserialization**: Utilities to convert between in-memory and YAML storage formats
4. **Annotation Management**: Tools for tracking annotation status and progress

### Core Components

The key components for ROI handling are:

- `roi_utils.py`: Provides critical functions for ROI serialization and overlay
- `ImageProcessor`: Implements ROI analysis and visualization functionality
- `annotation_status_manager.py`: Manages annotation status and completion tracking
- `load_annotations.py`: Handles loading annotations from YAML files

## Annotation File Format

### ROI Definition YAML

ROIs are defined in YAML files with the following structure:

```yaml
rois:
  ROI_01:
    points: [[100, 1800], [2700, 1550], [2500, 2700], [100, 2700]]
    color: [0, 255, 0]  # BGR format
    thickness: 7
  ROI_02:
    points: [[100, 930], [3700, 1050], [3700, 1150], [100, 1300]]
    color: [0, 0, 255]
    thickness: 7
```

### Annotation Files

Annotations are stored in YAML files with this structure:

```yaml
# Metadata
created: "2025-05-14T12:34:56.789012"
last_modified: "2025-05-14T13:45:12.345678"
day_of_year: "001"
year: "2023"
station: "abisko"
instrument: "PC01"
annotation_time_minutes: 45.8

# Tracking data
expected_image_count: 12
annotated_image_count: 8
completion_percentage: 66.67

# Individual file status
file_status:
  'image1.jpg': "completed"
  'image2.jpg': "in_progress"

# Annotations
annotations:
  'image1.jpg':
    - roi_name: "ROI_00"
      discard: false
      snow_presence: false
      flags: []
    
    - roi_name: "ROI_01"
      discard: false
      snow_presence: true
      flags: ["sunny", "clouds"]
```

### File Paths

Annotations follow this directory structure:

```
{base_dir}/{normalized_station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/
```

With specific files:
- `annotations_{day}.yaml`: Day-level annotation file
- `{image_basename}_annotations.yaml`: Per-image annotation files (deprecated)
- `day_status_{day}.yaml`: Day status tracking file
- `L1_annotation_status_{station}_{instrument}.yaml`: Overall annotation status file

## Integration Example

Here's how to integrate PhenoTag's ROI overlay functionality into your own application:

```python
import os
import yaml
import cv2
from phenotag.ui.components.roi_utils import overlay_polygons, deserialize_polygons
from phenotag.io_tools.load_annotations import get_day_annotations_path
from phenotag.processors.image_processor import ImageProcessor

def display_image_with_rois(image_path, station_name, instrument_id, year, day_of_year, base_dir=None):
    """
    Display an image with ROIs overlaid from PhenoTag annotations.
    
    Parameters:
        image_path (str): Path to the image to display
        station_name (str): The name of the station
        instrument_id (str): The ID of the instrument
        year (str): The year (e.g., "2023")
        day_of_year (str): The day of year (e.g., "001")
        base_dir (str, optional): Base directory for annotations
    
    Returns:
        numpy.ndarray: The image with ROIs overlaid
    """
    # 1. Get the annotations file path
    day = day_of_year.zfill(3)  # Ensure day is padded with zeros
    
    if base_dir is None:
        base_dir = os.environ.get("PHENOTAG_DATA_DIR", "/data/sites")
    
    ann_path = get_day_annotations_path(base_dir, station_name, instrument_id, year, day)
    
    # 2. Load annotations if they exist
    if os.path.exists(ann_path):
        with open(ann_path, 'r') as f:
            annotations_data = yaml.safe_load(f)
    else:
        print(f"No annotations found at: {ann_path}")
        return cv2.imread(image_path)
    
    # 3. Find the ROI definitions
    # First look for ROIs in the same directory
    roi_path = os.path.join(os.path.dirname(ann_path), "rois.yaml")
    
    # Look up one level if not found
    if not os.path.exists(roi_path):
        roi_path = os.path.join(os.path.dirname(os.path.dirname(ann_path)), "rois.yaml")
    
    # Look up another level if still not found
    if not os.path.exists(roi_path):
        roi_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ann_path))), "rois.yaml")
    
    if os.path.exists(roi_path):
        with open(roi_path, 'r') as f:
            roi_data = yaml.safe_load(f)
            rois = roi_data.get('rois', {})
            roi_dict = deserialize_polygons(rois)
    else:
        print(f"No ROI definitions found near: {ann_path}")
        return cv2.imread(image_path)
    
    # 4. Overlay ROIs on the image
    # Option 1: Using ImageProcessor (recommended for additional features)
    processor = ImageProcessor(image_path)
    processor.overlay_polygons_from_dict(roi_dict, enable_overlay=True)
    image_with_rois = processor.get_image(with_overlays=True)
    
    # Option 2: Using the simpler overlay_polygons function
    # image_with_rois = overlay_polygons(image_path, roi_dict, show_names=True)
    
    return image_with_rois
```

## Working with Annotation Files

### Loading Annotations

To load annotation data programmatically:

```python
import os
import yaml
from phenotag.io_tools.load_annotations import get_day_annotations_path

def load_annotations(station_name, instrument_id, year, day_of_year, base_dir=None):
    """
    Load PhenoTag annotations for a specific day.
    
    Parameters:
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day_of_year (str): Day of year (padded to 3 digits)
        base_dir (str, optional): Base directory
        
    Returns:
        dict: The loaded annotations or empty dict if not found
    """
    # Ensure day is padded with zeros
    day = day_of_year.zfill(3)
    
    if base_dir is None:
        base_dir = os.environ.get("PHENOTAG_DATA_DIR", "/data/sites")
    
    # Get the path to the annotations file
    ann_path = get_day_annotations_path(base_dir, station_name, instrument_id, year, day)
    
    # Load annotations if they exist
    if os.path.exists(ann_path):
        try:
            with open(ann_path, 'r') as f:
                annotations_data = yaml.safe_load(f)
                return annotations_data
        except Exception as e:
            print(f"Error loading annotations: {str(e)}")
            return {}
    else:
        print(f"No annotations found at: {ann_path}")
        return {}
```

### Saving Annotations

To save annotation data programmatically:

```python
import os
import yaml
import datetime
from phenotag.io_tools.load_annotations import get_day_annotations_path

def save_annotations(annotations_data, station_name, instrument_id, year, day_of_year, base_dir=None):
    """
    Save PhenoTag annotations for a specific day.
    
    Parameters:
        annotations_data (dict): The annotations to save
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day_of_year (str): Day of year (padded to 3 digits)
        base_dir (str, optional): Base directory
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    # Ensure day is padded with zeros
    day = day_of_year.zfill(3)
    
    if base_dir is None:
        base_dir = os.environ.get("PHENOTAG_DATA_DIR", "/data/sites")
    
    # Get the path to the annotations file
    ann_path = get_day_annotations_path(base_dir, station_name, instrument_id, year, day)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(ann_path), exist_ok=True)
    
    # Update metadata
    if 'created' not in annotations_data:
        annotations_data['created'] = datetime.datetime.now().isoformat()
    
    annotations_data['last_modified'] = datetime.datetime.now().isoformat()
    annotations_data['day_of_year'] = day
    annotations_data['year'] = year
    annotations_data['station'] = station_name
    annotations_data['instrument'] = instrument_id
    
    # Calculate completion statistics
    all_files = annotations_data.get('annotations', {}).keys()
    expected_image_count = len(all_files)
    
    completed_files = 0
    file_status = {}
    
    for filename, annotations in annotations_data.get('annotations', {}).items():
        # Check if file has complete annotations
        is_complete = False
        if annotations:
            is_complete = any(
                ann.get('discard', False) or 
                ann.get('snow_presence', False) or 
                ann.get('flags', []) or
                ann.get('not_needed', False)
                for ann in annotations
            )
        
        file_status[filename] = "completed" if is_complete else "in_progress"
        if is_complete:
            completed_files += 1
    
    annotations_data['expected_image_count'] = expected_image_count
    annotations_data['annotated_image_count'] = completed_files
    
    if expected_image_count > 0:
        annotations_data['completion_percentage'] = round(
            (completed_files / expected_image_count) * 100, 2
        )
    else:
        annotations_data['completion_percentage'] = 0
    
    annotations_data['file_status'] = file_status
    
    # Save to file
    try:
        with open(ann_path, 'w') as f:
            yaml.dump(annotations_data, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving annotations: {str(e)}")
        return False
```

## Best Practices

1. **Path Construction**: Always use the provided utilities for path construction to ensure compatibility with PhenoTag's expected structure.

2. **Error Handling**: Implement robust error handling when loading/saving annotation files to prevent data loss.

3. **Validation**: Verify annotation data format before processing to avoid runtime errors.

4. **Memory Management**: Process large batches of annotations in chunks to avoid excessive memory usage.

5. **Station Name Normalization**: Use the same station name normalization logic as PhenoTag for consistent path generation.

6. **ROI Format Compatibility**: Ensure ROI definitions follow the expected format with points, color, and thickness properties.

7. **Metadata Preservation**: When saving annotations, preserve all metadata fields to maintain compatibility.

## Common Issues and Solutions

1. **Issue**: ROIs not appearing on images
   **Solution**: Check if ROI coordinates are within image bounds; PhenoTag clips out-of-bounds points

2. **Issue**: Cannot find annotation files
   **Solution**: Verify the path construction using the `get_day_annotations_path` function

3. **Issue**: ROI colors display incorrectly
   **Solution**: Remember that ROI colors in YAML are in BGR format, but most image libraries use RGB

4. **Issue**: Annotation file format incompatibility
   **Solution**: Use the deserialization functions provided by PhenoTag to handle format conversion

5. **Issue**: Missing directories when saving
   **Solution**: Always create necessary directories with `os.makedirs(..., exist_ok=True)` before saving

## Example Prompt

To use this functionality in your own package:

```python
from phenotag.processors.image_processor import ImageProcessor
from phenotag.ui.components.roi_utils import deserialize_polygons, overlay_polygons
from phenotag.io_tools.load_annotations import get_day_annotations_path

# 1. Import necessary modules for ROI handling and annotation management
# 2. Use get_day_annotations_path to find annotation files
# 3. Use deserialize_polygons to convert ROI definitions from YAML format
# 4. Use ImageProcessor or overlay_polygons to display ROIs on images
# 5. Save annotation changes using structured YAML format
```

By following these guidelines, you can seamlessly integrate PhenoTag's ROI and annotation functionality into your own applications while maintaining compatibility with existing data structures.