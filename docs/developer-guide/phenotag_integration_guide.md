# PhenoTag Integration Guide

This comprehensive guide covers how to integrate PhenoTag's functionality into your own applications, including both UI-based and standalone implementations.

## Table of Contents

1. [Overview](#overview)
2. [Core Functionality Integration](#core-functionality-integration)
3. [Annotation System Integration](#annotation-system-integration)
4. [ROI (Region of Interest) Integration](#roi-region-of-interest-integration)
5. [File Formats Reference](#file-formats-reference)
6. [Best Practices](#best-practices)
7. [Common Issues and Solutions](#common-issues-and-solutions)

## Overview

PhenoTag provides two main integration approaches:

1. **UI Integration**: Using PhenoTag's Streamlit components in your application
2. **Standalone Integration**: Using PhenoTag's core functionality without the UI

### Key Features Available for Integration

- Annotation loading and saving
- ROI (Region of Interest) management
- Image quality flag handling
- Station configuration management
- Memory-efficient image processing

## Core Functionality Integration

### Setting Up Core Components

```python
from phenotag.io_tools import load_annotations, save_annotations, get_annotation_file_path
from phenotag.config import stations
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
```

### Directory Path Construction

PhenoTag uses a standardized directory structure. Here's how to construct paths:

```python
def get_directory_path(base_path: str, station: str, instrument: str) -> str:
    """
    Construct directory path following PhenoTag conventions.
    
    Args:
        base_path: Base data directory
        station: Station name (will be normalized)
        instrument: Instrument identifier
        
    Returns:
        Full directory path
    """
    from phenotag.io_tools.defaults import normalize_station_name
    normalized_station = normalize_station_name(station)
    return os.path.join(base_path, normalized_station, instrument)
```

### Station Name Normalization

Station names are normalized for filesystem compatibility:

```python
def normalize_station_name(name: str) -> str:
    """
    Normalize station name for filesystem usage.
    
    Rules:
    - Spaces replaced with underscores
    - Special characters removed
    - Lowercase conversion
    
    Examples:
    - "Asa 01" -> "asa_01"
    - "Lönnstorp (01)" -> "lonnstorp_01"
    """
    import re
    # Implementation provided by phenotag.io_tools.defaults
```

## Annotation System Integration

### Loading Annotations

```python
def load_annotations_for_date(
    base_path: str,
    station: str,
    instrument: str,
    date: str
) -> Dict:
    """
    Load annotations for a specific date.
    
    Args:
        base_path: Base data directory
        station: Station name
        instrument: Instrument identifier
        date: Date in YYYY-MM-DD format
        
    Returns:
        Dictionary containing annotations and metadata
    """
    from phenotag.io_tools import load_annotations, get_annotation_file_path
    
    # Get the annotation file path
    annotation_path = get_annotation_file_path(
        base_path, station, instrument, date
    )
    
    # Load annotations (returns empty dict if file doesn't exist)
    return load_annotations(annotation_path)
```

### Saving Annotations

```python
def save_annotations_for_date(
    base_path: str,
    station: str,
    instrument: str,
    date: str,
    annotations: Dict
) -> bool:
    """
    Save annotations for a specific date.
    
    Args:
        base_path: Base data directory
        station: Station name
        instrument: Instrument identifier
        date: Date in YYYY-MM-DD format
        annotations: Annotation data dictionary
        
    Returns:
        True if saved successfully
    """
    from phenotag.io_tools import save_annotations, get_annotation_file_path
    
    # Get the annotation file path
    annotation_path = get_annotation_file_path(
        base_path, station, instrument, date
    )
    
    # Save annotations
    return save_annotations(annotations, annotation_path)
```

### Annotation Data Structure

```yaml
# annotation_YYYY-MM-DD.yaml
date: "2024-01-15"
station: "Asa 01"
instrument: "NDVI01"
timestamp: "2024-01-15T14:30:00"
image_flags:
  08:00:00: ["fog", "frost"]
  12:00:00: ["clouds"]
annotation_time_seconds: 180.5
metadata:
  annotator: "user@example.com"
  version: "1.0.0"
```

## ROI (Region of Interest) Integration

### Loading ROI Configuration

```python
def load_roi_for_station(station_name: str) -> Optional[Dict]:
    """
    Load ROI configuration for a station.
    
    Args:
        station_name: Name of the station
        
    Returns:
        ROI configuration dict or None if not found
    """
    from phenotag.config import stations
    
    station_config = stations.get(station_name, {})
    return station_config.get('roi')
```

### Applying ROI Overlay

```python
def apply_roi_overlay(
    image: np.ndarray,
    roi_config: Dict,
    copy: bool = True
) -> np.ndarray:
    """
    Apply ROI overlay to an image.
    
    Args:
        image: Input image as numpy array
        roi_config: ROI configuration dictionary
        copy: Whether to copy the image before drawing
        
    Returns:
        Image with ROI overlay
    """
    if copy:
        image = image.copy()
    
    # Extract ROI parameters
    coordinates = roi_config.get('coordinates', [])
    color = roi_config.get('color', [0, 255, 0])  # Default green
    thickness = roi_config.get('thickness', 7)
    
    if coordinates:
        # Convert to numpy array of points
        points = np.array(coordinates, dtype=np.int32)
        
        # Draw polygon
        cv2.polylines(
            image,
            [points],
            isClosed=True,
            color=color,
            thickness=thickness
        )
    
    return image
```

### Complete ROI Integration Example

```python
class PhenoTagROIProcessor:
    """Complete example of ROI processing integration."""
    
    def __init__(self, station_config_path: Optional[str] = None):
        """Initialize with optional custom station config."""
        if station_config_path:
            # Load custom configuration
            import yaml
            with open(station_config_path, 'r') as f:
                self.stations = yaml.safe_load(f)
        else:
            # Use default configuration
            from phenotag.config import stations
            self.stations = stations
    
    def process_image_with_roi(
        self,
        image_path: str,
        station_name: str,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Process an image with ROI overlay.
        
        Args:
            image_path: Path to input image
            station_name: Station name for ROI lookup
            output_path: Optional path to save result
            
        Returns:
            Processed image array or None if error
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error loading image: {image_path}")
            return None
        
        # Get ROI configuration
        roi_config = self.get_roi_config(station_name)
        if not roi_config:
            print(f"No ROI configured for station: {station_name}")
            return image
        
        # Apply ROI overlay
        result = self.apply_roi_overlay(image, roi_config)
        
        # Save if requested
        if output_path:
            cv2.imwrite(output_path, result)
        
        return result
    
    def get_roi_config(self, station_name: str) -> Optional[Dict]:
        """Get ROI configuration for a station."""
        station = self.stations.get(station_name, {})
        return station.get('roi')
    
    def apply_roi_overlay(
        self,
        image: np.ndarray,
        roi_config: Dict
    ) -> np.ndarray:
        """Apply ROI overlay to image."""
        image_copy = image.copy()
        
        coordinates = roi_config.get('coordinates', [])
        color = roi_config.get('color', [0, 255, 0])
        thickness = roi_config.get('thickness', 7)
        
        if coordinates:
            points = np.array(coordinates, dtype=np.int32)
            cv2.polylines(
                image_copy,
                [points],
                isClosed=True,
                color=color,
                thickness=thickness
            )
        
        return image_copy
```

## File Formats Reference

### Annotation File Format

Location: `{base_path}/{normalized_station}/{instrument}/annotations/annotation_{date}.yaml`

Structure:
```yaml
date: "YYYY-MM-DD"
station: "Station Name"
instrument: "InstrumentID"
timestamp: "ISO 8601 timestamp"
image_flags:
  "HH:MM:SS": ["flag1", "flag2"]
annotation_time_seconds: float
metadata:
  annotator: "optional"
  version: "optional"
```

### ROI Configuration Format

Location: In `stations.yaml` under each station

Structure:
```yaml
Station Name:
  roi:
    coordinates:
      - [x1, y1]
      - [x2, y2]
      - [x3, y3]
      - [x4, y4]
    color: [B, G, R]  # BGR format
    thickness: 7
```

### Directory Structure

```
base_path/
├── normalized_station_name/
│   ├── instrument_id/
│   │   ├── YYYY/
│   │   │   ├── MM/
│   │   │   │   ├── DD/
│   │   │   │   │   ├── image_files.jpg
│   │   │   │   │   └── ...
│   │   └── annotations/
│   │       ├── annotation_2024-01-01.yaml
│   │       └── ...
```

## Best Practices

### 1. Error Handling

Always handle missing files and invalid data gracefully:

```python
def safe_load_annotations(file_path: str) -> Dict:
    """Safely load annotations with error handling."""
    try:
        from phenotag.io_tools import load_annotations
        annotations = load_annotations(file_path)
        return annotations if annotations else {}
    except Exception as e:
        print(f"Error loading annotations: {e}")
        return {}
```

### 2. Path Management

Use PhenoTag's built-in path construction:

```python
from phenotag.io_tools import get_annotation_file_path

# Don't construct paths manually
# bad_path = f"{base}/{station}/annotations/annotation_{date}.yaml"

# Use the provided function
good_path = get_annotation_file_path(base, station, instrument, date)
```

### 3. Memory Management

For large image sets, process images one at a time:

```python
def process_image_batch(image_paths: List[str], station: str):
    """Process images with memory efficiency."""
    for path in image_paths:
        # Process one image at a time
        image = cv2.imread(path)
        if image is not None:
            # Process image
            result = process_with_roi(image, station)
            # Save or yield result
            yield result
            # Image is garbage collected here
```

### 4. Configuration Validation

Validate ROI configurations before use:

```python
def validate_roi_config(roi_config: Dict) -> bool:
    """Validate ROI configuration."""
    if not roi_config:
        return False
    
    required_keys = ['coordinates', 'color', 'thickness']
    if not all(key in roi_config for key in required_keys):
        return False
    
    # Validate coordinates
    coords = roi_config.get('coordinates', [])
    if not coords or len(coords) < 3:  # Need at least 3 points
        return False
    
    # Validate color (BGR format)
    color = roi_config.get('color', [])
    if len(color) != 3 or not all(0 <= c <= 255 for c in color):
        return False
    
    return True
```

## Common Issues and Solutions

### Issue 1: Station Name Mismatches

**Problem**: Station names in configurations don't match filesystem names.

**Solution**: Always use normalized station names:
```python
from phenotag.io_tools.defaults import normalize_station_name
normalized = normalize_station_name("Asa 01")  # Returns "asa_01"
```

### Issue 2: Missing Annotation Files

**Problem**: Annotation files don't exist for new dates.

**Solution**: PhenoTag handles this gracefully:
```python
# Returns empty dict if file doesn't exist
annotations = load_annotations(path)
if not annotations:
    annotations = {
        'date': date,
        'station': station,
        'instrument': instrument,
        'image_flags': {}
    }
```

### Issue 3: ROI Coordinate Scaling

**Problem**: ROI coordinates don't match resized images.

**Solution**: Scale coordinates proportionally:
```python
def scale_roi_coordinates(
    roi_config: Dict,
    original_size: Tuple[int, int],
    new_size: Tuple[int, int]
) -> Dict:
    """Scale ROI coordinates to match resized image."""
    scale_x = new_size[0] / original_size[0]
    scale_y = new_size[1] / original_size[1]
    
    scaled_config = roi_config.copy()
    scaled_coords = []
    
    for x, y in roi_config.get('coordinates', []):
        scaled_x = int(x * scale_x)
        scaled_y = int(y * scale_y)
        scaled_coords.append([scaled_x, scaled_y])
    
    scaled_config['coordinates'] = scaled_coords
    return scaled_config
```

### Issue 4: Thread Safety

**Problem**: Concurrent access to annotation files.

**Solution**: Implement file locking:
```python
import fcntl
import yaml

def save_annotations_with_lock(data: Dict, file_path: str):
    """Save annotations with file locking."""
    with open(file_path, 'w') as f:
        # Acquire exclusive lock
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yaml.dump(data, f, default_flow_style=False)
        finally:
            # Release lock
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

## Complete Integration Example

Here's a complete example integrating annotations and ROI:

```python
from phenotag.io_tools import load_annotations, save_annotations, get_annotation_file_path
from phenotag.io_tools.defaults import normalize_station_name
from phenotag.config import stations
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Optional

class PhenoTagIntegration:
    """Complete PhenoTag integration example."""
    
    def __init__(self, base_path: str):
        """Initialize with base data path."""
        self.base_path = base_path
        self.stations = stations
    
    def process_date_images(
        self,
        station: str,
        instrument: str,
        date: str,
        image_times: list
    ) -> Dict:
        """
        Process all images for a specific date.
        
        Args:
            station: Station name
            instrument: Instrument ID
            date: Date in YYYY-MM-DD format
            image_times: List of image timestamps
            
        Returns:
            Processing results
        """
        # Load existing annotations
        annotations = self.load_annotations(station, instrument, date)
        
        # Get ROI configuration
        roi_config = self.get_roi_config(station)
        
        results = {
            'processed': [],
            'errors': [],
            'annotations': annotations
        }
        
        for time in image_times:
            try:
                # Construct image path
                image_path = self.get_image_path(
                    station, instrument, date, time
                )
                
                # Process image
                processed = self.process_single_image(
                    image_path, roi_config
                )
                
                if processed is not None:
                    results['processed'].append({
                        'time': time,
                        'path': image_path,
                        'flags': annotations.get('image_flags', {}).get(time, [])
                    })
                else:
                    results['errors'].append({
                        'time': time,
                        'error': 'Failed to process image'
                    })
                    
            except Exception as e:
                results['errors'].append({
                    'time': time,
                    'error': str(e)
                })
        
        return results
    
    def load_annotations(
        self,
        station: str,
        instrument: str,
        date: str
    ) -> Dict:
        """Load annotations for a specific date."""
        annotation_path = get_annotation_file_path(
            self.base_path, station, instrument, date
        )
        return load_annotations(annotation_path) or {
            'date': date,
            'station': station,
            'instrument': instrument,
            'image_flags': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def save_annotations(
        self,
        station: str,
        instrument: str,
        date: str,
        annotations: Dict
    ) -> bool:
        """Save annotations for a specific date."""
        annotation_path = get_annotation_file_path(
            self.base_path, station, instrument, date
        )
        return save_annotations(annotations, annotation_path)
    
    def get_roi_config(self, station: str) -> Optional[Dict]:
        """Get ROI configuration for a station."""
        station_config = self.stations.get(station, {})
        return station_config.get('roi')
    
    def process_single_image(
        self,
        image_path: str,
        roi_config: Optional[Dict]
    ) -> Optional[np.ndarray]:
        """Process a single image with optional ROI overlay."""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        # Apply ROI if configured
        if roi_config and self.validate_roi_config(roi_config):
            image = self.apply_roi_overlay(image, roi_config)
        
        return image
    
    def apply_roi_overlay(
        self,
        image: np.ndarray,
        roi_config: Dict
    ) -> np.ndarray:
        """Apply ROI overlay to image."""
        result = image.copy()
        
        coordinates = roi_config.get('coordinates', [])
        color = roi_config.get('color', [0, 255, 0])
        thickness = roi_config.get('thickness', 7)
        
        if coordinates:
            points = np.array(coordinates, dtype=np.int32)
            cv2.polylines(
                result,
                [points],
                isClosed=True,
                color=color,
                thickness=thickness
            )
        
        return result
    
    def validate_roi_config(self, roi_config: Dict) -> bool:
        """Validate ROI configuration."""
        required = ['coordinates', 'color', 'thickness']
        return all(key in roi_config for key in required)
    
    def get_image_path(
        self,
        station: str,
        instrument: str,
        date: str,
        time: str
    ) -> str:
        """Construct image file path."""
        # Parse date
        year, month, day = date.split('-')
        
        # Normalize station name
        normalized_station = normalize_station_name(station)
        
        # Build path
        return os.path.join(
            self.base_path,
            normalized_station,
            instrument,
            year,
            month,
            day,
            f"{normalized_station}_{instrument}_{date}_{time}.jpg"
        )

# Usage example
if __name__ == "__main__":
    # Initialize integration
    integration = PhenoTagIntegration("/data/phenocam")
    
    # Process images for a date
    results = integration.process_date_images(
        station="Asa 01",
        instrument="NDVI01",
        date="2024-01-15",
        image_times=["08:00:00", "12:00:00", "16:00:00"]
    )
    
    # Update annotations
    annotations = results['annotations']
    annotations['image_flags']['12:00:00'] = ['clouds', 'partial']
    
    # Save updated annotations
    integration.save_annotations(
        "Asa 01", "NDVI01", "2024-01-15", annotations
    )
```

This guide provides everything needed to integrate PhenoTag's functionality into your own applications. For more specific use cases or advanced features, refer to the API documentation or contact the maintainers.