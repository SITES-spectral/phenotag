# PhenoTag Core Functionality: Using Annotations and ROIs Without Streamlit

This document explains how to utilize PhenoTag's core annotation and ROI functionality independently from its Streamlit UI. This guide is for developers who want to integrate phenological annotation capabilities into their own applications using different UI frameworks.

## Table of Contents

- [Overview](#overview)
- [Core Components](#core-components)
- [Working with Annotation Files](#working-with-annotation-files)
- [Working with ROIs](#working-with-rois)
- [Integration Examples](#integration-examples)
- [Best Practices](#best-practices)

## Overview

PhenoTag's core functionality can be separated into two main components:

1. **Annotation System**: Handles loading, saving, and managing YAML-based annotation files
2. **ROI System**: Manages region of interest definitions and overlay visualization

This guide shows how to use these components independently of Streamlit or any other UI framework.

## Core Components

### Annotation File Format

PhenoTag uses YAML files for annotation storage with the following structure:

```yaml
# Metadata
created: "2025-05-14T12:34:56.789012"
last_modified: "2025-05-14T13:45:12.345678"
day_of_year: "001"
year: "2023"
station: "abisko"
instrument: "PC01"
annotation_time_minutes: 45.8

# Image annotations
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

### ROI Definition Format

ROIs are defined in separate YAML files:

```yaml
rois:
  ROI_01:
    points: [[100, 200], [300, 200], [300, 400], [100, 400]]
    color: [0, 255, 0]  # BGR format (Green)
    thickness: 2
  ROI_02:
    points: [[500, 600], [700, 600], [700, 800], [500, 800]]
    color: [0, 0, 255]  # BGR format (Red)
    thickness: 2
```

## Working with Annotation Files

Below are standalone functions for working with PhenoTag annotation files without any UI framework dependencies:

```python
import os
import yaml
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_yaml(filepath: str) -> dict:
    """
    Load a YAML file as a dictionary.
    
    Args:
        filepath (str): Path to the YAML file
        
    Returns:
        dict: Contents of the YAML file
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def save_yaml(data: dict, filepath: str) -> None:
    """
    Save a dictionary to a YAML file.
    
    Args:
        data (dict): Data to save
        filepath (str): Path where the YAML file will be saved
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, default_flow_style=False)

def normalize_station_name(station_name: str) -> str:
    """
    Normalize station name for consistent directory structure.
    
    Args:
        station_name (str): Station name to normalize
        
    Returns:
        str: Normalized station name
    """
    # Remove special characters and convert to lowercase
    normalized = station_name.lower()
    normalized = ''.join(c if c.isalnum() else '_' for c in normalized)
    
    # Replace multiple underscores with a single one
    while '__' in normalized:
        normalized = normalized.replace('__', '_')
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    return normalized

def get_annotation_directory(base_dir: str, station_name: str, 
                            instrument_id: str, year: str, day: str) -> str:
    """
    Get the annotation directory for a specific day.
    
    Args:
        base_dir (str): Base directory
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year (padded to 3 digits, e.g., "001")
        
    Returns:
        str: Full path to the annotation directory
    """
    normalized_name = normalize_station_name(station_name)
    return os.path.join(
        base_dir, normalized_name, 'phenocams', 'products', 
        instrument_id, 'L1', str(year), str(day)
    )

def get_annotation_file_path(base_dir: str, station_name: str, 
                           instrument_id: str, year: str, day: str) -> str:
    """
    Get the path to a day's annotation file.
    
    Args:
        base_dir (str): Base directory
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year (padded to 3 digits, e.g., "001")
        
    Returns:
        str: Full path to the annotation file
    """
    day_dir = get_annotation_directory(base_dir, station_name, instrument_id, year, day)
    return os.path.join(day_dir, f"day_status_{day}.yaml")

def get_per_image_annotation_path(annotation_dir: str, image_filename: str) -> str:
    """
    Get the path to a per-image annotation file.
    
    Args:
        annotation_dir (str): Annotation directory
        image_filename (str): Image filename
        
    Returns:
        str: Full path to the per-image annotation file
    """
    base_name = os.path.splitext(image_filename)[0]
    return os.path.join(annotation_dir, f"{base_name}_annotations.yaml")

def load_annotations(base_dir: str, station_name: str, 
                    instrument_id: str, year: str, day: str) -> Dict[str, Any]:
    """
    Load annotations for a specific day.
    
    Args:
        base_dir (str): Base directory
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year (padded to 3 digits)
        
    Returns:
        dict: Loaded annotations
    """
    annotation_dir = get_annotation_directory(
        base_dir, station_name, instrument_id, year, day
    )
    
    # First check for day status file (most recent format)
    day_status_file = os.path.join(annotation_dir, f"day_status_{day}.yaml")
    
    if os.path.exists(day_status_file):
        day_status = load_yaml(day_status_file)
        
        # If day status exists, look for individual image annotation files
        per_image_annotations = {}
        for image_filename in day_status.get('image_annotations', []):
            # Get base name without extension
            base_name = os.path.splitext(image_filename)[0]
            img_annotation_file = os.path.join(
                annotation_dir, f"{base_name}_annotations.yaml"
            )
            
            if os.path.exists(img_annotation_file):
                try:
                    img_data = load_yaml(img_annotation_file)
                    if 'annotations' in img_data:
                        per_image_annotations[image_filename] = img_data['annotations']
                except Exception as img_err:
                    print(f"Error loading per-image annotation file: {img_err}")
        
        # Return per-image annotations if found
        if per_image_annotations:
            return {'annotations': per_image_annotations}
    
    # Then check for individual image annotation files even without day status
    per_image_annotations = {}
    for img_annotation_file in Path(annotation_dir).glob("*_annotations.yaml"):
        try:
            # Skip day status files
            if img_annotation_file.name.startswith('day_status_'):
                continue
                
            img_data = load_yaml(str(img_annotation_file))
            if 'annotations' in img_data and 'filename' in img_data:
                per_image_annotations[img_data['filename']] = img_data['annotations']
        except Exception as img_err:
            print(f"Error loading per-image annotation file: {img_err}")
    
    # Return per-image annotations if found
    if per_image_annotations:
        return {'annotations': per_image_annotations}
        
    # Finally fallback to the old day-level annotation file
    old_annotation_file = os.path.join(annotation_dir, f'annotations_{day}.yaml')
    if os.path.exists(old_annotation_file):
        return load_yaml(old_annotation_file)
        
    # No annotation files found
    return {}

def save_annotation(annotation_dir: str, image_filename: str, 
                   annotations: List[Dict[str, Any]], 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Save annotations for a specific image.
    
    Args:
        annotation_dir (str): Directory to save the annotation
        image_filename (str): Image filename
        annotations (list): List of ROI annotations
        metadata (dict, optional): Additional metadata to include
        
    Returns:
        bool: Success status
    """
    # Ensure directory exists
    os.makedirs(annotation_dir, exist_ok=True)
    
    # Create annotation data with default metadata
    annotation_data = {
        "created": datetime.datetime.now().isoformat(),
        "last_modified": datetime.datetime.now().isoformat(),
        "filename": image_filename,
        "annotations": annotations
    }
    
    # Add additional metadata if provided
    if metadata:
        annotation_data.update(metadata)
    
    # Save to file
    try:
        base_name = os.path.splitext(image_filename)[0]
        file_path = os.path.join(annotation_dir, f"{base_name}_annotations.yaml")
        save_yaml(annotation_data, file_path)
        return True
    except Exception as e:
        print(f"Error saving annotation: {e}")
        return False

def update_day_status(annotation_dir: str, day: str) -> bool:
    """
    Update the day status file with current annotation progress.
    
    Args:
        annotation_dir (str): Directory containing annotations
        day (str): Day of year
        
    Returns:
        bool: Success status
    """
    try:
        # Get all annotation files in the directory
        annotation_files = list(Path(annotation_dir).glob("*_annotations.yaml"))
        annotation_files = [f for f in annotation_files 
                          if not f.name.startswith("day_status_")]
        
        # Count image files
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
            image_files.extend(Path(annotation_dir).glob(f"*{ext}"))
        
        # Get station and instrument from path
        # Path format: base_dir/station/phenocams/products/instrument/L1/year/day
        path_parts = Path(annotation_dir).parts
        year = path_parts[-2]
        instrument = path_parts[-4]
        station = path_parts[-7]
        
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
                    all_annotated = any(
                        ann.get('discard', False) or 
                        ann.get('snow_presence', False) or 
                        ann.get('flags', []) or
                        ann.get('not_needed', False)
                        for ann in annotations
                    )
                    
                    # Set status based on annotation completeness
                    file_status[image_filename] = "completed" if all_annotated else "in_progress"
            except Exception as e:
                print(f"Error processing annotation file {annotation_file}: {e}")
        
        # Create the status data
        status_data = {
            "created": datetime.datetime.now().isoformat(),
            "last_modified": datetime.datetime.now().isoformat(),
            "day_of_year": day,
            "year": year,
            "station": station,
            "instrument": instrument,
            "expected_image_count": expected_count,
            "annotated_image_count": annotated_count,
            "completion_percentage": round(completion_percentage, 2),
            "file_status": file_status,
            "image_annotations": image_annotations
        }
        
        # Save the status file
        status_file_path = os.path.join(annotation_dir, f"day_status_{day}.yaml")
        save_yaml(status_data, status_file_path)
        return True
    except Exception as e:
        print(f"Error updating day status file: {e}")
        return False

def create_default_annotation(roi_name: str = "ROI_00") -> Dict[str, Any]:
    """
    Create a default annotation object for a ROI.
    
    Args:
        roi_name (str): Name of the ROI
        
    Returns:
        dict: Default annotation object
    """
    return {
        "roi_name": roi_name,
        "discard": False,
        "snow_presence": False,
        "flags": []
    }

def get_roi_annotation(annotations: List[Dict[str, Any]], roi_name: str) -> Dict[str, Any]:
    """
    Get annotation for a specific ROI.
    
    Args:
        annotations (list): List of ROI annotations
        roi_name (str): Name of the ROI to find
        
    Returns:
        dict: Annotation for the specified ROI, or default if not found
    """
    for ann in annotations:
        if ann.get('roi_name') == roi_name:
            return ann
    
    # Return default if not found
    return create_default_annotation(roi_name)
```

## Working with ROIs

Below are standalone functions for working with ROIs and displaying them on images:

```python
import cv2
import numpy as np
import os
import yaml
from typing import Dict, List, Tuple, Any

def load_roi_definitions(roi_file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load ROI definitions from a YAML file.
    
    Args:
        roi_file_path (str): Path to the ROI definition file
        
    Returns:
        dict: Dictionary of ROI definitions
    """
    if not os.path.exists(roi_file_path):
        print(f"ROI file not found: {roi_file_path}")
        return {}
        
    try:
        with open(roi_file_path, 'r') as f:
            roi_data = yaml.safe_load(f)
            return roi_data.get('rois', {})
    except Exception as e:
        print(f"Error loading ROI file: {e}")
        return {}

def search_for_roi_file(image_path: str) -> str:
    """
    Search for a ROI definition file near the image.
    
    Args:
        image_path (str): Path to the image
        
    Returns:
        str: Path to the ROI file if found, empty string otherwise
    """
    # Try different locations, starting from the image directory and moving up
    image_dir = os.path.dirname(image_path)
    
    # Try in image directory
    roi_path = os.path.join(image_dir, "rois.yaml")
    if os.path.exists(roi_path):
        return roi_path
    
    # Try one level up (year level)
    parent_dir = os.path.dirname(image_dir)
    roi_path = os.path.join(parent_dir, "rois.yaml")
    if os.path.exists(roi_path):
        return roi_path
    
    # Try two levels up (L1 level)
    grandparent_dir = os.path.dirname(parent_dir)
    roi_path = os.path.join(grandparent_dir, "rois.yaml")
    if os.path.exists(roi_path):
        return roi_path
    
    # Try three levels up (instrument level)
    great_grandparent_dir = os.path.dirname(grandparent_dir)
    roi_path = os.path.join(great_grandparent_dir, "rois.yaml")
    if os.path.exists(roi_path):
        return roi_path
    
    # Not found
    return ""

def deserialize_polygons(yaml_friendly_rois: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Convert YAML-friendly ROI format to a format suitable for display.
    
    Args:
        yaml_friendly_rois (dict): ROI definitions from YAML
        
    Returns:
        dict: Processed ROI definitions ready for display
    """
    original_rois = {}
    
    if not yaml_friendly_rois or not isinstance(yaml_friendly_rois, dict):
        return original_rois
    
    for roi_name, roi_data in yaml_friendly_rois.items():
        try:
            # Validate roi_data
            if not isinstance(roi_data, dict):
                print(f"Warning: ROI data for {roi_name} is not a dictionary. Skipping.")
                continue
                
            # Check for required keys
            if 'points' not in roi_data:
                print(f"Warning: ROI data for {roi_name} has no 'points' key. Skipping.")
                continue
                
            if 'color' not in roi_data:
                print(f"Warning: ROI data for {roi_name} has no 'color' key. Using default.")
                roi_data['color'] = [0, 255, 0]  # Default to green
            
            # Convert points to tuples
            points = []
            for point in roi_data['points']:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    # Convert to int to ensure proper coordinate handling
                    points.append((int(point[0]), int(point[1])))
                else:
                    print(f"Warning: Invalid point format in ROI {roi_name}: {point}. Skipping point.")
            
            # Skip ROIs with fewer than 3 points (can't form a polygon)
            if len(points) < 3:
                print(f"Warning: ROI {roi_name} has fewer than 3 valid points ({len(points)}). Skipping ROI.")
                continue
                
            # Convert color to tuple
            color = tuple(int(c) for c in roi_data['color'][:3])  # Take only first 3 values and convert to int

            # Get thickness (default to 2 if not present)
            thickness = int(roi_data.get('thickness', 2))

            # Set alpha to 0 to disable filling
            alpha = 0.0  # Disable filling

            # Store in a format ready for display
            original_rois[roi_name] = {
                'points': points,
                'color': color,
                'thickness': thickness,
                'alpha': alpha
            }
            
        except Exception as e:
            print(f"Error processing ROI '{roi_name}': {str(e)}")
    
    return original_rois

def serialize_polygons(phenocam_rois: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Convert in-memory ROI format to YAML-friendly format.
    
    Args:
        phenocam_rois (dict): ROI definitions in memory
        
    Returns:
        dict: YAML-friendly ROI definitions
    """
    yaml_friendly_rois = {}
    for roi, polygon in phenocam_rois.items():
        yaml_friendly_polygon = {
            'points': [list(point) for point in polygon['points']],
            'color': list(polygon['color']),
            'thickness': polygon['thickness']
        }
        yaml_friendly_rois[roi] = yaml_friendly_polygon
    return yaml_friendly_rois

def overlay_polygons(image_path: str, phenocam_rois: Dict[str, Dict[str, Any]], 
                    show_names: bool = True, font_scale: float = 2.0) -> np.ndarray:
    """
    Overlay ROI polygons on an image.
    
    Args:
        image_path (str): Path to the image
        phenocam_rois (dict): Dictionary of ROI definitions
        show_names (bool): Whether to show ROI names
        font_scale (float): Font scale for ROI names
        
    Returns:
        numpy.ndarray: Image with ROIs overlaid
    """
    # Read the image
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not found or path is incorrect")
        
    # Get image dimensions to check if ROIs are within bounds
    height, width = img.shape[:2]
    
    for roi_name, roi_data in phenocam_rois.items():
        try:
            # Skip invalid ROIs
            if not isinstance(roi_data, dict) or 'points' not in roi_data:
                continue
                
            # Extract points
            points = roi_data['points']
            
            # Skip if not enough points
            if len(points) < 3:
                continue
                
            # Clip points to stay within image boundaries
            clipped_points = []
            for point in points:
                x, y = point
                clipped_points.append((max(0, min(x, width-1)), max(0, min(y, height-1))))
            points = clipped_points
                
            # Convert to numpy array for OpenCV
            points_array = np.array(points, dtype=np.int32)

            # Extract color (BGR format in OpenCV)
            color = roi_data['color']

            # Extract thickness
            thickness = roi_data.get('thickness', 2)

            # Draw the polygon outline
            cv2.polylines(img, [points_array], isClosed=True, color=color, thickness=thickness)

            if show_names:
                # Calculate the centroid for labeling
                M = cv2.moments(points_array)
                if M['m00'] != 0:
                    cX = int(M['m10'] / M['m00'])
                    cY = int(M['m01'] / M['m00'])
                else:
                    # Fallback if area is zero
                    cX, cY = points_array[0][0], points_array[0][1]

                # Get text size for centering
                text = roi_name
                font = cv2.FONT_HERSHEY_SIMPLEX
                text_thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, text_thickness)

                # Adjust position to center text
                text_x = cX - (text_width // 2)
                text_y = cY + (text_height // 2)
                
                # Ensure text remains within image boundaries
                text_x = max(0, min(text_x, width - text_width))
                text_y = max(text_height, min(text_y, height - baseline))

                # Draw text
                cv2.putText(img, text, (text_x, text_y), font, font_scale, color, text_thickness, cv2.LINE_AA)

        except Exception as e:
            print(f"Error processing ROI '{roi_name}': {str(e)}")
    
    # Convert from BGR to RGB for display in most image libraries
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img_rgb

def create_roi_definition(points: List[Tuple[int, int]], 
                         color: Tuple[int, int, int] = (0, 255, 0),
                         thickness: int = 2) -> Dict[str, Any]:
    """
    Create a new ROI definition.
    
    Args:
        points (list): List of (x, y) point tuples
        color (tuple): BGR color tuple (default: green)
        thickness (int): Line thickness
        
    Returns:
        dict: ROI definition
    """
    return {
        'points': points,
        'color': color,
        'thickness': thickness
    }

def save_roi_definitions(roi_defs: Dict[str, Dict[str, Any]], filepath: str) -> bool:
    """
    Save ROI definitions to a YAML file.
    
    Args:
        roi_defs (dict): Dictionary of ROI definitions
        filepath (str): Path to save the YAML file
        
    Returns:
        bool: Success status
    """
    try:
        # Convert to YAML-friendly format
        yaml_friendly = serialize_polygons(roi_defs)
        
        # Create the data structure
        data = {'rois': yaml_friendly}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save to file
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        
        return True
    except Exception as e:
        print(f"Error saving ROI definitions: {e}")
        return False
```

## Integration Examples

Here are complete examples showing how to use these core functions in your own application:

### Example 1: Loading and Displaying ROIs

```python
import cv2
import matplotlib.pyplot as plt
from pathlib import Path

# Assume the functions from above are available

def display_image_with_rois(image_path):
    """
    Load and display an image with its ROIs.
    
    Args:
        image_path (str): Path to the image
    """
    # Search for ROI definition file
    roi_file = search_for_roi_file(image_path)
    
    if not roi_file:
        print("No ROI file found. Displaying original image.")
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(img_rgb)
        plt.axis('off')
        plt.show()
        return
    
    # Load ROI definitions
    roi_defs = load_roi_definitions(roi_file)
    
    # Convert to display format
    rois = deserialize_polygons(roi_defs)
    
    # Overlay ROIs on image
    img_with_rois = overlay_polygons(image_path, rois, show_names=True)
    
    # Display the result
    plt.figure(figsize=(10, 8))
    plt.imshow(img_with_rois)
    plt.axis('off')
    plt.title(f"Image with {len(rois)} ROIs")
    plt.show()

# Example usage
if __name__ == "__main__":
    # Replace with your image path
    image_path = "/data/sites/abisko/phenocams/products/PC01/L1/2023/001/abisko_PC01_2023_001_1200.jpg"
    display_image_with_rois(image_path)
```

### Example 2: Working with Annotations

```python
from pathlib import Path

# Assume the functions from above are available

def process_day_annotations(base_dir, station_name, instrument_id, year, day):
    """
    Process annotations for a specific day.
    
    Args:
        base_dir (str): Base directory
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year (padded to 3 digits)
    """
    # Load annotations
    annotations = load_annotations(base_dir, station_name, instrument_id, year, day)
    
    if not annotations or 'annotations' not in annotations:
        print(f"No annotations found for {station_name}/{instrument_id}/{year}/{day}")
        return
    
    # Process each image's annotations
    for image_filename, roi_annotations in annotations['annotations'].items():
        print(f"\nImage: {image_filename}")
        
        # Get the annotation directory
        annotation_dir = get_annotation_directory(
            base_dir, station_name, instrument_id, year, day
        )
        
        # Get the image path
        image_path = os.path.join(annotation_dir, image_filename)
        
        # Find ROI definitions
        roi_file = search_for_roi_file(image_path)
        if not roi_file:
            print("  No ROI definitions found")
            continue
            
        # Load ROI definitions
        roi_defs = load_roi_definitions(roi_file)
        rois = deserialize_polygons(roi_defs)
        
        # Display annotation status for each ROI
        for roi_name in rois.keys():
            # Find annotation for this ROI
            roi_annotation = get_roi_annotation(roi_annotations, roi_name)
            
            # Display
            discard = "Yes" if roi_annotation.get('discard', False) else "No"
            snow = "Yes" if roi_annotation.get('snow_presence', False) else "No"
            flags = ", ".join(roi_annotation.get('flags', [])) or "None"
            
            print(f"  ROI: {roi_name}")
            print(f"    Discard: {discard}")
            print(f"    Snow presence: {snow}")
            print(f"    Flags: {flags}")

# Example usage
if __name__ == "__main__":
    # Replace with your data
    base_dir = "/data/sites"
    station_name = "abisko"
    instrument_id = "PC01"
    year = "2023"
    day = "001"
    
    process_day_annotations(base_dir, station_name, instrument_id, year, day)
```

### Example 3: Creating and Saving Annotations

```python
# Assume the functions from above are available

def annotate_image(image_path, roi_annotations, metadata=None):
    """
    Create and save annotations for an image.
    
    Args:
        image_path (str): Path to the image
        roi_annotations (dict): Dictionary mapping ROI names to annotation values
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    # Extract directory and filename
    image_dir = os.path.dirname(image_path)
    image_filename = os.path.basename(image_path)
    
    # Find ROI definitions
    roi_file = search_for_roi_file(image_path)
    if not roi_file:
        print("No ROI definitions found")
        return False
        
    # Load ROI definitions
    roi_defs = load_roi_definitions(roi_file)
    rois = deserialize_polygons(roi_defs)
    
    # Create annotation objects for each ROI
    annotations = []
    
    for roi_name in rois.keys():
        # Get annotation values for this ROI
        values = roi_annotations.get(roi_name, {})
        
        # Create annotation object
        annotation = {
            "roi_name": roi_name,
            "discard": values.get('discard', False),
            "snow_presence": values.get('snow_presence', False),
            "flags": values.get('flags', [])
        }
        
        annotations.append(annotation)
    
    # Save the annotation
    return save_annotation(image_dir, image_filename, annotations, metadata)

# Example usage
if __name__ == "__main__":
    # Replace with your data
    image_path = "/data/sites/abisko/phenocams/products/PC01/L1/2023/001/abisko_PC01_2023_001_1200.jpg"
    
    # Example annotation values
    roi_annotations = {
        "ROI_01": {
            "discard": False,
            "snow_presence": True,
            "flags": ["sunny", "clouds"]
        },
        "ROI_02": {
            "discard": False,
            "snow_presence": False,
            "flags": ["high_brightness"]
        }
    }
    
    # Additional metadata
    metadata = {
        "day_of_year": "001",
        "year": "2023",
        "station": "abisko",
        "instrument": "PC01",
        "annotation_time_minutes": 5.2
    }
    
    # Save annotations
    success = annotate_image(image_path, roi_annotations, metadata)
    
    if success:
        print("Annotations saved successfully")
        
        # Update day status
        image_dir = os.path.dirname(image_path)
        day = "001"  # Extract from path or metadata
        update_day_status(image_dir, day)
    else:
        print("Failed to save annotations")
```

## Best Practices

1. **Path Handling**: Use the provided path construction functions consistently to ensure compatibility with PhenoTag's directory structure.

2. **ROI Management**: Validate ROI definitions before using them to ensure they have valid points, colors, and thicknesses.

3. **Error Handling**: Implement robust error handling when loading and processing files, as they may be created by multiple users or systems.

4. **Serialization**: Use the provided serialization/deserialization functions to maintain consistent format between YAML files and in-memory data.

5. **Directory Structure**: Maintain the expected directory structure to ensure compatibility with other tools that might use the same data.

6. **Image Coordinates**: Remember that ROI coordinates are in pixel coordinates (origin at top-left), and are in the format (x, y).

7. **Color Format**: ROI colors in YAML and OpenCV are in BGR format (not RGB), so be careful when converting between color systems.

8. **Memory Management**: When working with large batches of images, process them in chunks to avoid excessive memory usage.

9. **Date Formats**: Always pad day-of-year values to 3 digits (e.g., "001" instead of "1") for consistent path construction.

10. **Backups**: Create backups before making batch changes to annotation files, especially when migrating between formats.