# PhenoTag Integration Guide: Working with Annotations and ROIs

This document provides a comprehensive guide on integrating PhenoTag's annotation and ROI functionality into your own applications. It explains how to load annotation files, display images with overlaid ROIs, and manage the connections between annotations and image regions.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Loading Annotation Files](#loading-annotation-files)
- [Displaying Images with ROIs](#displaying-images-with-rois)
- [Working with Annotations](#working-with-annotations)
- [Complete Integration Example](#complete-integration-example)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

PhenoTag provides powerful tools for phenological annotation, including:

1. **YAML-based annotation storage** for tracking image quality, snow presence, and other flags
2. **Region of Interest (ROI) handling** for defining and visualizing specific areas within images
3. **Utilities for annotation management** to track progress and maintain metadata

This guide shows how to use these components in your own applications.

## Installation

First, install PhenoTag as a dependency in your project:

```bash
# Install from PyPI (once published)
pip install phenotag

# Or install from GitHub
pip install git+https://github.com/username/phenotag.git@v0.1.1

# Or install from local path during development
pip install -e /path/to/phenotag
```

## Loading Annotation Files

PhenoTag stores annotations in YAML files with a specific directory structure. Here's how to load them:

```python
from phenotag.io_tools.load_annotations import load_annotations

def get_image_annotations(base_dir, station_name, instrument_id, year, day, image_filename=None):
    """
    Load annotations for a specific day or image.
    
    Parameters:
        base_dir (str): Base directory for data storage
        station_name (str): Name of the station
        instrument_id (str): ID of the instrument
        year (str): Year (e.g., "2023")
        day (str): Day of year (e.g., "001") 
        image_filename (str, optional): If provided, return annotations only for this image
        
    Returns:
        dict: Annotations data
    """
    # Load all annotations for the specified day
    annotations = load_annotations(base_dir, station_name, instrument_id, year, day)
    
    # If a specific image is requested, filter the annotations
    if image_filename and 'annotations' in annotations:
        if image_filename in annotations['annotations']:
            return {'annotations': {image_filename: annotations['annotations'][image_filename]}}
        else:
            print(f"No annotations found for image: {image_filename}")
            return {'annotations': {}}
    
    return annotations
```

### Annotation File Structure

PhenoTag uses the following directory structure for annotations:

```
{base_dir}/{normalized_station_name}/phenocams/products/{instrument_id}/L1/{year}/{day}/
```

The annotation files include:
- `day_status_{day}.yaml`: Day-level status information
- `{image_basename}_annotations.yaml`: Per-image annotation files
- Legacy format: `annotations_{day}.yaml`: Day-level annotations

## Displaying Images with ROIs

PhenoTag provides utilities to overlay ROIs on images. Here's how to use them:

```python
import cv2
import yaml
from pathlib import Path
from phenotag.ui.components.roi_utils import deserialize_polygons, overlay_polygons

def display_image_with_rois(image_path, rois_yaml_path=None):
    """
    Display an image with ROIs overlaid.
    
    Parameters:
        image_path (str): Path to the image
        rois_yaml_path (str, optional): Path to ROI definitions YAML file.
            If not provided, will look for a rois.yaml file in the same directory.
            
    Returns:
        numpy.ndarray: Image with ROIs overlaid
    """
    # 1. Get ROI definitions
    if rois_yaml_path is None:
        # Look for rois.yaml in the same directory as the image
        img_dir = Path(image_path).parent
        rois_yaml_path = img_dir / "rois.yaml"
        
        # If not found, try looking up in parent directories
        if not rois_yaml_path.exists():
            rois_yaml_path = img_dir.parent / "rois.yaml"
        if not rois_yaml_path.exists():
            rois_yaml_path = img_dir.parent.parent / "rois.yaml"
    
    # 2. Load ROI definitions
    if Path(rois_yaml_path).exists():
        with open(rois_yaml_path, 'r') as f:
            roi_data = yaml.safe_load(f)
            yaml_rois = roi_data.get('rois', {})
            
            # Convert from YAML format to internal format
            rois = deserialize_polygons(yaml_rois)
    else:
        print(f"No ROI definitions found at: {rois_yaml_path}")
        # Return the original image without ROIs
        return cv2.imread(image_path)
    
    # 3. Overlay ROIs on the image
    return overlay_polygons(image_path, rois, show_names=True)
```

### ROI YAML Format

ROIs are defined in YAML files with this structure:

```yaml
rois:
  ROI_01:
    points: [[100, 200], [300, 200], [300, 400], [100, 400]]
    color: [0, 255, 0]  # Green in BGR format
    thickness: 2
  ROI_02:
    points: [[500, 600], [700, 600], [700, 800], [500, 800]]
    color: [0, 0, 255]  # Red in BGR format
    thickness: 2
```

## Working with Annotations

Annotations link quality assessments to specific ROIs within images. Here's how to work with them:

```python
def get_roi_annotations(annotations_data, image_filename, roi_name="ROI_00"):
    """
    Get annotations for a specific ROI in an image.
    
    Parameters:
        annotations_data (dict): Annotations data from load_annotations()
        image_filename (str): The filename of the image
        roi_name (str): The name of the ROI (default: "ROI_00" for full image)
        
    Returns:
        dict: Annotation data for the ROI, or None if not found
    """
    # Get annotations for this image
    if 'annotations' not in annotations_data:
        return None
        
    image_annotations = annotations_data['annotations'].get(image_filename, [])
    
    # Find the annotation for this ROI
    for roi_annotation in image_annotations:
        if roi_annotation.get('roi_name') == roi_name:
            return roi_annotation
            
    return None

def create_new_annotation(roi_name="ROI_00"):
    """
    Create a new annotation object with default values.
    
    Parameters:
        roi_name (str): The name of the ROI
        
    Returns:
        dict: Default annotation data
    """
    return {
        "roi_name": roi_name,
        "discard": False,
        "snow_presence": False,
        "flags": []
    }

def save_image_annotation(base_dir, station_name, instrument_id, year, day, 
                          image_filename, annotations, annotation_time_minutes=0):
    """
    Save annotations for a specific image.
    
    Parameters:
        base_dir (str): Base directory
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year
        image_filename (str): Image filename
        annotations (list): List of ROI annotations
        annotation_time_minutes (float): Time spent annotating
        
    Returns:
        bool: Success status
    """
    import datetime
    import os
    import yaml
    from pathlib import Path
    
    # Get the normalized station name
    from phenotag.ui.components.annotation_status_manager import get_normalized_station_name
    normalized_name = get_normalized_station_name(station_name)
    
    # Build the path to the directory
    day_path = Path(base_dir) / normalized_name / 'phenocams' / 'products' / instrument_id / 'L1' / str(year) / str(day)
    os.makedirs(day_path, exist_ok=True)
    
    # Path to the per-image annotation file
    base_name = os.path.splitext(image_filename)[0]
    img_annotation_file = day_path / f"{base_name}_annotations.yaml"
    
    # Create annotation data
    annotation_data = {
        "created": datetime.datetime.now().isoformat(),
        "last_modified": datetime.datetime.now().isoformat(),
        "day_of_year": day,
        "year": year,
        "station": station_name,
        "instrument": instrument_id,
        "filename": image_filename,
        "annotation_time_minutes": annotation_time_minutes,
        "annotations": annotations
    }
    
    # Save to YAML file
    try:
        with open(img_annotation_file, 'w') as f:
            yaml.dump(annotation_data, f, default_flow_style=False)
        
        # Also update the day status file
        update_day_status(day_path, day)
        return True
    except Exception as e:
        print(f"Error saving annotation: {e}")
        return False

def update_day_status(day_path, day):
    """
    Update the day status file with current annotation progress.
    
    Parameters:
        day_path (Path): Path to the day directory
        day (str): Day of year
    """
    import datetime
    import os
    import yaml
    from pathlib import Path
    
    # Get all annotation files in the directory
    annotation_files = list(day_path.glob("*_annotations.yaml"))
    annotation_files = [f for f in annotation_files if not f.name.startswith("day_status_")]
    
    # Count image files
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
        image_files.extend(day_path.glob(f"*{ext}"))
    
    # Calculate completion statistics
    expected_count = len(image_files)
    annotated_count = len(annotation_files)
    completion_percentage = (annotated_count / expected_count * 100) if expected_count > 0 else 0
    
    # Build the file status mapping
    file_status = {}
    image_annotations = []
    
    for annotation_file in annotation_files:
        try:
            with open(annotation_file, 'r') as f:
                data = yaml.safe_load(f)
                
            if 'filename' in data:
                image_filename = data['filename']
                image_annotations.append(image_filename)
                
                # Check if annotations exist for all ROIs
                annotations = data.get('annotations', [])
                all_annotated = True
                for roi in annotations:
                    has_annotations = (
                        roi.get('discard', False) or
                        roi.get('snow_presence', False) or
                        len(roi.get('flags', [])) > 0 or
                        roi.get('not_needed', False)
                    )
                    if not has_annotations:
                        all_annotated = False
                        break
                
                # Set status based on annotation completeness
                file_status[image_filename] = "completed" if all_annotated else "in_progress"
        except Exception as e:
            print(f"Error processing annotation file {annotation_file}: {e}")
    
    # Create the status data
    status_data = {
        "created": datetime.datetime.now().isoformat(),
        "last_modified": datetime.datetime.now().isoformat(),
        "day_of_year": day,
        "year": os.path.basename(day_path.parent),
        "station": os.path.basename(day_path.parent.parent.parent.parent.parent),
        "instrument": os.path.basename(day_path.parent.parent.parent),
        "expected_image_count": expected_count,
        "annotated_image_count": annotated_count,
        "completion_percentage": round(completion_percentage, 2),
        "file_status": file_status,
        "image_annotations": image_annotations
    }
    
    # Save the status file
    status_file_path = day_path / f"day_status_{day}.yaml"
    try:
        with open(status_file_path, 'w') as f:
            yaml.dump(status_data, f, default_flow_style=False)
    except Exception as e:
        print(f"Error updating day status file: {e}")
```

## Complete Integration Example

Here's a complete example showing how to use PhenoTag's annotation and ROI functionality in your application:

```python
import cv2
import numpy as np
import yaml
from pathlib import Path
import matplotlib.pyplot as plt
from phenotag.io_tools.load_annotations import load_annotations
from phenotag.ui.components.roi_utils import deserialize_polygons, overlay_polygons

def phenotag_workflow(base_dir, station_name, instrument_id, year, day, image_filename):
    """
    Complete workflow for loading an image, its ROIs, and annotations.
    
    Parameters:
        base_dir (str): Base directory
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year (e.g., "2023")
        day (str): Day of year (e.g., "001")
        image_filename (str): Image filename
        
    Returns:
        tuple: (image with ROIs, annotation data)
    """
    # Get normalized station name
    from phenotag.ui.components.annotation_status_manager import get_normalized_station_name
    normalized_name = get_normalized_station_name(station_name)
    
    # Construct paths
    day_path = Path(base_dir) / normalized_name / 'phenocams' / 'products' / instrument_id / 'L1' / str(year) / str(day)
    image_path = day_path / image_filename
    
    # Check if image exists
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return None, None
    
    # Load annotations
    annotations_data = load_annotations(base_dir, station_name, instrument_id, year, day)
    image_annotations = {}
    
    if 'annotations' in annotations_data and image_filename in annotations_data['annotations']:
        image_annotations = annotations_data['annotations'][image_filename]
    
    # Look for ROI definitions
    roi_candidates = [
        day_path / "rois.yaml",                # Same directory
        day_path.parent / "rois.yaml",         # Year level
        day_path.parent.parent / "rois.yaml",  # L1 level
        day_path.parent.parent.parent / "rois.yaml"  # Instrument level
    ]
    
    rois = {}
    for roi_path in roi_candidates:
        if roi_path.exists():
            with open(roi_path, 'r') as f:
                roi_data = yaml.safe_load(f)
                yaml_rois = roi_data.get('rois', {})
                rois = deserialize_polygons(yaml_rois)
                print(f"Loaded ROIs from: {roi_path}")
                break
    
    if not rois:
        print("No ROI definitions found.")
    
    # Overlay ROIs on the image
    image_with_rois = overlay_polygons(str(image_path), rois, show_names=True)
    
    return image_with_rois, image_annotations

def display_results(image_with_rois, annotations):
    """
    Display the image with ROIs and annotation information.
    
    Parameters:
        image_with_rois (numpy.ndarray): Image with ROIs overlaid
        annotations (list): List of annotation objects for each ROI
    """
    plt.figure(figsize=(12, 10))
    
    # Display the image with ROIs
    plt.subplot(1, 2, 1)
    plt.imshow(image_with_rois)
    plt.title("Image with ROIs")
    plt.axis('off')
    
    # Display the annotation information
    plt.subplot(1, 2, 2)
    
    if not annotations:
        plt.text(0.5, 0.5, "No annotations available", 
                 horizontalalignment='center', verticalalignment='center',
                 transform=plt.gca().transAxes, fontsize=14)
    else:
        info_text = "Annotation Summary:\n\n"
        
        for ann in annotations:
            roi_name = ann.get('roi_name', 'Unknown')
            discard = "Yes" if ann.get('discard', False) else "No"
            snow = "Yes" if ann.get('snow_presence', False) else "No"
            flags = ", ".join(ann.get('flags', [])) or "None"
            
            info_text += f"ROI: {roi_name}\n"
            info_text += f"  Discard: {discard}\n"
            info_text += f"  Snow presence: {snow}\n"
            info_text += f"  Flags: {flags}\n\n"
        
        plt.text(0.05, 0.95, info_text, 
                 horizontalalignment='left', verticalalignment='top',
                 transform=plt.gca().transAxes, fontsize=12)
    
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    base_dir = "/data/sites"
    station_name = "abisko"
    instrument_id = "PC01"
    year = "2023"
    day = "001"
    image_filename = "abisko_PC01_2023_001_1200.jpg"
    
    # Run the workflow
    image_with_rois, annotations = phenotag_workflow(
        base_dir, station_name, instrument_id, year, day, image_filename
    )
    
    # Display results
    if image_with_rois is not None:
        display_results(image_with_rois, annotations)
```

## Best Practices

1. **Path Handling**: Always use PhenoTag's path construction utilities to ensure compatibility with its directory structure.

2. **Error Handling**: Implement robust error handling when loading and processing annotation files, as they may be created by multiple users or systems.

3. **Station Name Normalization**: Always use PhenoTag's station name normalization function to ensure consistent directory paths.

4. **ROI Validation**: Validate ROI definitions before rendering to ensure they have valid points, colors, and thicknesses.

5. **Data Integrity**: When saving annotations, include all required metadata fields to maintain compatibility with PhenoTag.

6. **Image Boundaries**: Check that ROI coordinates are within image boundaries or use the clipping functionality provided by PhenoTag.

## Troubleshooting

1. **Issue**: ROIs not appearing on images
   **Solution**: Check if ROI coordinates are within image bounds; PhenoTag clips out-of-bounds points

2. **Issue**: Cannot find annotation files
   **Solution**: Verify the path construction using the station name normalization function

3. **Issue**: ROI colors display incorrectly
   **Solution**: Remember that ROI colors in YAML are in BGR format (OpenCV standard)

4. **Issue**: Annotation file format incompatibility
   **Solution**: Use the deserialization functions provided by PhenoTag to handle format conversion

5. **Issue**: Missing directories when saving
   **Solution**: Always create necessary directories with `os.makedirs(..., exist_ok=True)` before saving