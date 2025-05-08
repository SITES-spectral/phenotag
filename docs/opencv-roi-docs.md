# OpenCV ROI Image Processor Documentation

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Image Processor Class](#image-processor-class)
  - [Initialization](#initialization)
  - [Loading and Saving Images](#loading-and-saving-images)
  - [ROI Management](#roi-management)
  - [Band Processing](#band-processing)
  - [ROI Analysis](#roi-analysis)
- [Standalone Function](#standalone-function)
- [Memory Efficiency](#memory-efficiency)
- [Batch Processing](#batch-processing)
- [Output Format](#output-format)
- [Examples](#examples)
  - [Basic ROI Analysis](#basic-roi-analysis)
  - [Working with Chromatic Coordinates](#working-with-chromatic-coordinates)
  - [Vegetation Analysis](#vegetation-analysis)
  - [Batch Processing](#batch-processing-example)
- [Troubleshooting](#troubleshooting)

## Introduction

The OpenCV ROI Image Processor is a Python tool for analyzing regions of interest (ROIs) in images, with a focus on agricultural, vegetation, and remote sensing applications. It provides functionality to:

- Define polygon ROIs manually or load them from YAML files
- Calculate and visualize RGB and chromatic coordinate bands
- Perform statistical analysis on ROIs, including mean, standard deviation, min, max, and sum
- Automatically detect and exclude sky regions when no ROIs are provided
- Process images in a memory-efficient way, suitable for large files
- Batch process multiple images with the same ROI definitions

The tool is designed with memory efficiency in mind, implementing chunked processing and on-demand calculation to handle large images without excessive memory usage.

## Installation

The ROI Image Processor requires the following dependencies:

```python
import cv2
import numpy as np
import yaml
import os
from typing import Dict, List, Tuple, Optional, Union, Any
import gc  # For garbage collection
```

Make sure to install them before using the tool:

```bash
pip install opencv-python numpy pyyaml
```

Save the ImageProcessor class implementation to a Python file (e.g., `roi_processor.py`).

## Quick Start

Here's a simple example to get started:

```python
from roi_processor import ImageProcessor

# Create an instance and load an image
processor = ImageProcessor("forest_image.jpg")

# Load ROIs from a YAML file or create a default ROI
processor.overlay_polygons_from_yaml("rois.yaml")
# Alternatively: processor.create_default_roi()

# Analyze ROIs
roi_stats = processor.analyze_all_roi_bands()

# Export statistics
processor.export_roi_band_stats("forest_stats.yaml")

# Save the image with ROI overlays
processor.save("forest_with_rois.jpg")
```

## Core Features

1. **ROI Definition and Visualization**: Define polygon regions of interest on images
2. **Chromatic Coordinate Calculation**: Compute and extract r, g, b chromatic coordinates
3. **Band Extraction**: Extract individual R, G, B bands from images
4. **Statistical Analysis**: Calculate comprehensive statistics for each ROI and band
5. **Memory-Efficient Processing**: Handle large images with chunked processing
6. **Automatic Sky Detection**: Create a default ROI that excludes sky regions
7. **Batch Processing**: Process multiple images with the same settings

## Image Processor Class

### Initialization

```python
processor = ImageProcessor(image_path=None, downscale_factor=1.0)
```

Parameters:
- `image_path`: Optional path to an image file
- `downscale_factor`: Factor to downscale images (1.0 = original size, 0.5 = half size). Use this to reduce memory usage for large images.

### Loading and Saving Images

```python
# Load an image
processor.load_image("path/to/image.jpg", keep_original=True)

# Get the current image
image = processor.get_image(with_overlays=True)

# Save the image
processor.save("output.jpg", quality=95)

# Show the image
processor.show(window_name="Image", wait=True)

# Reset the image (clear overlays)
processor.reset_image()

# Release the original image to save memory
processor.release_original()
```

### ROI Management

```python
# Create a default ROI that excludes sky
processor.create_default_roi()

# Overlay a single polygon
processor.overlay_polygon(
    points=[[100, 100], [300, 100], [300, 300], [100, 300]],
    color=[0, 255, 0],  # BGR
    thickness=2,
    closed=True,
    roi_name="ROI_01",
    alpha=0.3  # Transparency for filled regions
)

# Overlay polygons from a dictionary
roi_dict = {
    "ROI_01": {"points": [[100, 100], [300, 100], [300, 300], [100, 300]], "color": [0, 255, 0], "thickness": 2}
}
processor.overlay_polygons_from_dict(roi_dict, enable_overlay=True)

# Overlay polygons from a YAML file
processor.overlay_polygons_from_yaml("path/to/rois.yaml", enable_overlay=True)

# Extract a specific ROI as a separate image
roi_image = processor.extract_roi("ROI_01")
```

### Band Processing

```python
# Calculate chromatic coordinates (r, g, b)
chromatic_bands = processor.compute_chromatic_coordinates(force_recompute=False)

# Extract RGB bands
rgb_bands = processor.get_rgb_bands(force_recompute=False)

# Get a specific band as an image
r_band = processor.get_band_image('rgb', 'r')
chrom_b = processor.get_band_image('chromatic', 'b')
composite = processor.get_band_image('chromatic', 'composite')

# Save a band as an image
processor.save_band_image('rgb', 'g', "green_band.png")
```

### ROI Analysis

```python
# Analyze a specific ROI with band statistics
roi_stats = processor.analyze_roi_bands("ROI_01", skip_chromatic=False, skip_rgb=False)

# Analyze all ROIs (except those in skip_list)
all_roi_stats = processor.analyze_all_roi_bands(skip_list=["ROI_bad"], skip_chromatic=False, skip_rgb=False)

# Get general ROI information (area, bounds, vegetation index)
roi_info = processor.analyze_roi("ROI_01", compute_histograms=True, compute_vegetation=True)

# Export ROI band statistics to a YAML file
processor.export_roi_band_stats("roi_stats.yaml")
```

## Standalone Function

For convenience, you can use the standalone function for common tasks:

```python
from roi_processor import process_image_with_rois

result_image = process_image_with_rois(
    image_path="forest.jpg",
    yaml_path="rois.yaml",
    output_path="result.jpg",
    show_image=True,
    enable_overlay=True,
    downscale_factor=0.5,
    keep_original=False,
    export_bands=True,
    band_types=['rgb-r', 'chromatic-composite'],
    output_dir="output",
    analyze_rois=True,
    skip_list=["ROI_03"]
)
```

## Memory Efficiency

The processor is designed to be memory-efficient:

1. `downscale_factor`: Load images at reduced resolution
2. `keep_original`: Control whether to keep two copies of the image
3. Chunked processing: Process large images in smaller chunks
4. On-demand calculation: Compute bands and masks only when needed
5. `release_original()`: Free memory when original image is no longer needed
6. Explicit garbage collection: Clean up after intensive operations

## Batch Processing

Process multiple images with the same ROI definitions:

```python
processor.process_batch(
    images_list=["img1.jpg", "img2.jpg", "img3.jpg"],
    yaml_path="rois.yaml",
    output_dir="processed_images",
    enable_overlay=True,
    export_bands=True,
    band_types=['rgb-r', 'chromatic-composite'],
    analyze_rois=True,
    skip_list=["ROI_bad"]
)
```

## Output Format

### ROI Statistics Format

The ROI band statistics are exported as YAML with this structure:

```yaml
roi_band_stats:
  ROI_01:
    rgb:
      r:
        mean: 127.5
        std: 45.2
        min: 25.0
        max: 245.0
        sum: 3187500.0  # Sum of all red pixel values
        pixels: 25000
      g:
        # similar structure
      b:
        # similar structure
    chromatic:
      r:
        mean: 0.35
        std: 0.12
        min: 0.08
        max: 0.62
        sum: 8750.0  # Sum of all red chromatic values
        pixels: 25000
      g:
        # similar structure
      b:
        # similar structure
```

### ROI Analysis Format

The general ROI analysis includes:

```python
{
    'mean_color': [b, g, r],  # BGR values
    'pixel_sum': {
        'blue': 2320000.0,
        'green': 3632500.0,
        'red': 3187500.0,
        'total': 9140000.0,
        'pixel_count': 25000
    },
    'histograms': {
        'blue': [...],  # 256 values
        'green': [...],  # 256 values
        'red': [...]  # 256 values
    },
    'area_pixels': 25000,
    'bounding_rect': {
        'x': 100,
        'y': 150,
        'width': 250,
        'height': 350,
        'aspect_ratio': 0.714
    },
    'vegetation_index': {
        'mean': 0.21,
        'min': -0.34,
        'max': 0.76,
        'std': 0.15,
        'sum': 5250.0
    }
}
```

## Examples

### Basic ROI Analysis

```python
# Load image and define ROIs
processor = ImageProcessor("field.jpg")
processor.overlay_polygons_from_yaml("field_rois.yaml")

# Analyze all ROIs and export results
stats = processor.analyze_all_roi_bands()
processor.export_roi_band_stats("field_stats.yaml")

# Check pixel counts in each ROI
for roi_name, roi_data in stats.items():
    pixel_count = roi_data['rgb']['r']['pixels']
    print(f"{roi_name}: {pixel_count} pixels")

# Compare mean values across ROIs
for roi_name, roi_data in stats.items():
    r_mean = roi_data['rgb']['r']['mean']
    g_mean = roi_data['rgb']['g']['mean']
    b_mean = roi_data['rgb']['b']['mean']
    print(f"{roi_name}: R={r_mean:.1f}, G={g_mean:.1f}, B={b_mean:.1f}")
```

### Working with Chromatic Coordinates

```python
# Load image and calculate chromatic coordinates
processor = ImageProcessor("forest.jpg")
processor.compute_chromatic_coordinates()

# Extract and save individual bands
r_chrom = processor.get_band_image('chromatic', 'r')
g_chrom = processor.get_band_image('chromatic', 'g')
b_chrom = processor.get_band_image('chromatic', 'b')
composite = processor.get_band_image('chromatic', 'composite')

cv2.imwrite("r_chromatic.png", r_chrom)
cv2.imwrite("g_chromatic.png", g_chrom)
cv2.imwrite("b_chromatic.png", b_chrom)
cv2.imwrite("composite_chromatic.png", composite)

# Define ROIs and analyze chromatic values
processor.overlay_polygons_from_yaml("forest_rois.yaml")
chrom_stats = processor.analyze_all_roi_bands(skip_rgb=True)  # Only analyze chromatic coordinates

# Compare chromatic coordinate values between ROIs
for roi_name, roi_data in chrom_stats.items():
    r_mean = roi_data['chromatic']['r']['mean']
    g_mean = roi_data['chromatic']['g']['mean']
    b_mean = roi_data['chromatic']['b']['mean']
    print(f"{roi_name}: r={r_mean:.3f}, g={g_mean:.3f}, b={b_mean:.3f}")
```

### Vegetation Analysis

```python
# Load image and define ROIs
processor = ImageProcessor("crops.jpg")
processor.overlay_polygons_from_yaml("crop_rois.yaml")

# Analyze vegetation indices for all ROIs
for roi_name in processor.rois.keys():
    roi_info = processor.analyze_roi(roi_name, compute_vegetation=True)
    
    if 'vegetation_index' in roi_info:
        veg_index = roi_info['vegetation_index']
        print(f"{roi_name} Vegetation Index:")
        print(f"  Mean: {veg_index['mean']:.3f}")
        print(f"  Min: {veg_index['min']:.3f}")
        print(f"  Max: {veg_index['max']:.3f}")
        print(f"  Std Dev: {veg_index['std']:.3f}")
        print(f"  Sum: {veg_index['sum']:.1f}")
```

### Batch Processing Example

```python
import os
import glob

# Get all JPG files in a directory
image_files = glob.glob("input_directory/*.jpg")

# Create processor and batch process all images
processor = ImageProcessor(downscale_factor=0.5)  # Use lower resolution for efficiency
processor.process_batch(
    images_list=image_files,
    yaml_path="field_rois.yaml",
    output_dir="processed_outputs",
    enable_overlay=True,
    export_bands=True,
    band_types=['rgb-r', 'rgb-g', 'rgb-b', 'chromatic-composite'],
    analyze_rois=True
)

# Process results
for image_file in image_files:
    base_name = os.path.splitext(os.path.basename(image_file))[0]
    stats_file = f"processed_outputs/statistics/{base_name}_roi_stats.yaml"
    
    # Load stats from YAML (if needed for further processing)
    with open(stats_file, 'r') as f:
        stats_data = yaml.safe_load(f)
    
    # Process or compare statistics as needed
    # ...
```

## Troubleshooting

### Memory Issues

If encountering memory problems with large images:

1. Use a smaller `downscale_factor` when initializing the processor
2. Set `keep_original=False` when loading images if you don't need to reset overlays
3. Call `release_original()` after applying ROIs to free up memory
4. Adjust the chunk size (`chunk_size = min(500, height)`) in the code for very large images
5. Use `skip_chromatic=True` or `skip_rgb=True` in analysis functions if you only need one type of data

### Performance Optimization

1. Only compute the bands you need (RGB or chromatic)
2. Use `skip_list` to exclude ROIs that don't need analysis
3. Set `compute_histograms=False` in `analyze_roi()` if you don't need histograms
4. If working with many images, use batch processing rather than processing each one individually

### ROI Format

ROIs in YAML files should follow this format:

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