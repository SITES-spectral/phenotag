# Default ROI CLI Examples and Use Cases

This document provides practical examples and common use cases for the `phenotag images default-roi` CLI command, demonstrating how to integrate it into various workflows for phenocam image processing.

## Basic Usage Examples

### Example 1: Generate Default ROI for a Single Image

```bash
# Basic usage - outputs YAML format compatible with stations.yaml
phenotag images default-roi /path/to/phenocam/image.jpg
```

**Output:**
```yaml
ROI_00:
  color:
  - 0
  - 255
  - 0
  points:
  - - 0
    - 245
  - - 2047
    - 245
  - - 2047
    - 1535
  - - 0
    - 1535
  thickness: 7
```

### Example 2: JSON Output for API Integration

```bash
# Generate JSON output for API or programmatic use
phenotag images default-roi /path/to/image.jpg --format json
```

**Output:**
```json
{
  "ROI_00": {
    "points": [
      [0, 245],
      [2047, 245],
      [2047, 1535],
      [0, 1535]
    ],
    "color": [0, 255, 0],
    "thickness": 7
  }
}
```

### Example 3: Custom ROI Parameters

```bash
# Generate ROI with custom name, color, and thickness
phenotag images default-roi /path/to/image.jpg \
  --roi-name "Forest_ROI" \
  --color "255,0,0" \
  --thickness 5 \
  --format yaml
```

**Output:**
```yaml
Forest_ROI:
  color:
  - 255
  - 0
  - 0
  points:
  - - 0
    - 245
  - - 2047
    - 245
  - - 2047
    - 1535
  - - 0
    - 1535
  thickness: 5
```

## Workflow Integration Examples

### Example 4: Batch Processing Script

```bash
#!/bin/bash
# Process all JPEG images in a directory

INPUT_DIR="/data/phenocam/images"
OUTPUT_DIR="/data/phenocam/rois"

mkdir -p "$OUTPUT_DIR"

for image_file in "$INPUT_DIR"/*.jpg; do
    filename=$(basename "$image_file" .jpg)
    echo "Processing $filename..."
    
    phenotag images default-roi "$image_file" \
        --format json \
        --roi-name "ROI_01" \
        > "$OUTPUT_DIR/${filename}_roi.json"
done

echo "Batch processing complete!"
```

### Example 5: Station Configuration Generation

```bash
#!/bin/bash
# Generate ROI configuration for a new station

STATION_NAME="new_station"
IMAGE_PATH="/data/$STATION_NAME/sample_image.jpg"
CONFIG_FILE="/data/$STATION_NAME/roi_config.yaml"

echo "Generating ROI configuration for station: $STATION_NAME"

# Generate multiple ROIs with different parameters
echo "# Auto-generated ROI configuration for $STATION_NAME" > "$CONFIG_FILE"
echo "# Generated on $(date)" >> "$CONFIG_FILE"
echo "" >> "$CONFIG_FILE"

# Primary ROI (vegetation)
echo "# Primary vegetation ROI" >> "$CONFIG_FILE"
phenotag images default-roi "$IMAGE_PATH" \
    --roi-name "ROI_01" \
    --color "0,255,0" \
    --thickness 7 >> "$CONFIG_FILE"

echo "" >> "$CONFIG_FILE"

# Secondary ROI (canopy)
echo "# Secondary canopy ROI" >> "$CONFIG_FILE"
phenotag images default-roi "$IMAGE_PATH" \
    --roi-name "ROI_02" \
    --color "0,0,255" \
    --thickness 5 >> "$CONFIG_FILE"

echo "Configuration saved to: $CONFIG_FILE"
```

### Example 6: Quality Assurance Check

```bash
#!/bin/bash
# Compare existing ROIs with auto-generated defaults

STATIONS_CONFIG="/path/to/stations.yaml"
SAMPLE_IMAGES_DIR="/path/to/sample_images"
QA_OUTPUT_DIR="/path/to/qa_results"

mkdir -p "$QA_OUTPUT_DIR"

# For each station with sample images
for station_dir in "$SAMPLE_IMAGES_DIR"/*/; do
    station_name=$(basename "$station_dir")
    sample_image="$station_dir/sample.jpg"
    
    if [[ -f "$sample_image" ]]; then
        echo "QA check for station: $station_name"
        
        # Generate default ROI
        phenotag images default-roi "$sample_image" \
            --format json \
            --roi-name "AUTO_ROI" \
            > "$QA_OUTPUT_DIR/${station_name}_auto_roi.json"
        
        echo "Auto-generated ROI saved for $station_name"
    fi
done
```

## Integration with Existing Workflows

### Example 7: Python Script Integration

```python
#!/usr/bin/env python3
"""
Example Python script showing how to integrate the CLI command
"""

import subprocess
import json
import os
from pathlib import Path

def generate_default_roi(image_path, roi_name="ROI_00", color="0,255,0", thickness=7):
    """Generate default ROI using the CLI command"""
    cmd = [
        "phenotag", "images", "default-roi", 
        str(image_path),
        "--format", "json",
        "--roi-name", roi_name,
        "--color", color,
        "--thickness", str(thickness)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        roi_data = json.loads(result.stdout)
        return roi_data
    except subprocess.CalledProcessError as e:
        print(f"Error generating ROI: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        return None

def process_image_directory(input_dir, output_dir):
    """Process all images in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for image_file in input_path.glob("*.jpg"):
        print(f"Processing {image_file.name}...")
        
        roi_data = generate_default_roi(image_file)
        if roi_data:
            output_file = output_path / f"{image_file.stem}_roi.json"
            with open(output_file, 'w') as f:
                json.dump(roi_data, f, indent=2)
            print(f"ROI saved to {output_file}")
        else:
            print(f"Failed to process {image_file.name}")

if __name__ == "__main__":
    process_image_directory("/path/to/images", "/path/to/output")
```

### Example 8: Makefile Integration

```makefile
# Makefile for automated ROI generation

IMAGES_DIR := data/images
ROI_DIR := data/rois
IMAGES := $(wildcard $(IMAGES_DIR)/*.jpg)
ROI_FILES := $(patsubst $(IMAGES_DIR)/%.jpg,$(ROI_DIR)/%.yaml,$(IMAGES))

.PHONY: all clean rois

all: rois

rois: $(ROI_FILES)

$(ROI_DIR)/%.yaml: $(IMAGES_DIR)/%.jpg | $(ROI_DIR)
	@echo "Generating ROI for $<..."
	@phenotag images default-roi "$<" \
		--roi-name "ROI_01" \
		--color "0,255,0" \
		--thickness 7 > "$@"

$(ROI_DIR):
	@mkdir -p $(ROI_DIR)

clean:
	@rm -rf $(ROI_DIR)

# Example targets for different ROI types
forest-rois: ROI_NAME = Forest_ROI
forest-rois: COLOR = 34,139,34
forest-rois: $(ROI_FILES)

crop-rois: ROI_NAME = Crop_ROI  
crop-rois: COLOR = 255,215,0
crop-rois: $(ROI_FILES)
```

## Advanced Use Cases

### Example 9: Multi-Station Batch Processing

```bash
#!/bin/bash
# Process multiple stations with different configurations

declare -A STATION_CONFIGS=(
    ["abisko"]="0,255,0:Forest_ROI:7"
    ["grimso"]="34,139,34:Forest_ROI:5"
    ["lonnstorp"]="255,215,0:Crop_ROI:7"
    ["skogaryd"]="0,128,0:Mixed_ROI:6"
)

DATA_ROOT="/data/phenocam"
OUTPUT_ROOT="/data/roi_configs"

for station in "${!STATION_CONFIGS[@]}"; do
    IFS=':' read -r color roi_name thickness <<< "${STATION_CONFIGS[$station]}"
    
    station_dir="$DATA_ROOT/$station"
    output_dir="$OUTPUT_ROOT/$station"
    mkdir -p "$output_dir"
    
    echo "Processing station: $station"
    echo "  ROI Name: $roi_name"
    echo "  Color: $color"
    echo "  Thickness: $thickness"
    
    # Find representative image
    sample_image=$(find "$station_dir" -name "*.jpg" | head -1)
    
    if [[ -n "$sample_image" ]]; then
        phenotag images default-roi "$sample_image" \
            --roi-name "$roi_name" \
            --color "$color" \
            --thickness "$thickness" \
            --format yaml > "$output_dir/default_roi.yaml"
        
        echo "  ✓ ROI generated successfully"
    else
        echo "  ✗ No sample image found"
    fi
    echo ""
done
```

### Example 10: Continuous Integration Pipeline

```yaml
# .github/workflows/roi-validation.yml
name: ROI Validation Pipeline

on:
  push:
    paths:
      - 'data/test_images/**'
      - 'config/stations.yaml'

jobs:
  validate-rois:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install PhenoTag
      run: |
        pip install -e .
    
    - name: Generate Test ROIs
      run: |
        mkdir -p test_outputs
        for image in data/test_images/*.jpg; do
          filename=$(basename "$image" .jpg)
          phenotag images default-roi "$image" \
            --format json \
            --roi-name "TEST_ROI" \
            > "test_outputs/${filename}_roi.json"
        done
    
    - name: Validate ROI Quality
      run: |
        python scripts/validate_rois.py test_outputs/
    
    - name: Upload Results
      uses: actions/upload-artifact@v3
      with:
        name: roi-validation-results
        path: test_outputs/
```

## Error Handling Examples

### Example 11: Robust Error Handling Script

```bash
#!/bin/bash
# Robust script with comprehensive error handling

process_image_with_fallback() {
    local image_path="$1"
    local output_path="$2"
    local roi_name="${3:-ROI_00}"
    local max_retries=3
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        echo "Attempt $((retry_count + 1)) for $(basename "$image_path")"
        
        if phenotag images default-roi "$image_path" \
           --roi-name "$roi_name" \
           --format yaml > "$output_path" 2>/dev/null; then
            echo "✓ Successfully processed $(basename "$image_path")"
            return 0
        else
            echo "✗ Failed to process $(basename "$image_path")"
            ((retry_count++))
            
            if [[ $retry_count -lt $max_retries ]]; then
                echo "  Retrying in 2 seconds..."
                sleep 2
            fi
        fi
    done
    
    echo "✗ Failed to process $(basename "$image_path") after $max_retries attempts"
    
    # Create a fallback full-frame ROI
    cat > "$output_path" << EOF
$roi_name:
  color: [255, 0, 0]  # Red color to indicate fallback
  points: [[0, 0], [1, 0], [1, 1], [0, 1]]  # Placeholder coordinates
  thickness: 7
  comment: "Fallback ROI - automatic generation failed"
EOF
    
    return 1
}

# Usage example
INPUT_DIR="/data/problematic_images"
OUTPUT_DIR="/data/roi_outputs"

mkdir -p "$OUTPUT_DIR"

success_count=0
failure_count=0

for image in "$INPUT_DIR"/*.jpg; do
    if [[ -f "$image" ]]; then
        output_file="$OUTPUT_DIR/$(basename "$image" .jpg)_roi.yaml"
        
        if process_image_with_fallback "$image" "$output_file" "AUTO_ROI"; then
            ((success_count++))
        else
            ((failure_count++))
        fi
    fi
done

echo ""
echo "Processing Summary:"
echo "  Successful: $success_count"
echo "  Failed: $failure_count"
echo "  Total: $((success_count + failure_count))"
```

## Performance Optimization Examples

### Example 12: Parallel Processing

```bash
#!/bin/bash
# Parallel processing for large image datasets

IMAGES_DIR="/data/large_dataset"
OUTPUT_DIR="/data/roi_outputs"
MAX_PARALLEL=8  # Adjust based on system capabilities

mkdir -p "$OUTPUT_DIR"

# Function to process a single image
process_single_image() {
    local image_path="$1"
    local filename=$(basename "$image_path" .jpg)
    local output_path="$OUTPUT_DIR/${filename}_roi.yaml"
    
    echo "Processing $filename..."
    
    if phenotag images default-roi "$image_path" \
       --roi-name "BATCH_ROI" \
       --color "0,255,0" \
       --thickness 7 > "$output_path"; then
        echo "✓ Completed $filename"
    else
        echo "✗ Failed $filename"
    fi
}

# Export function for parallel execution
export -f process_single_image
export OUTPUT_DIR

# Use GNU parallel for efficient processing
find "$IMAGES_DIR" -name "*.jpg" | \
    parallel -j "$MAX_PARALLEL" process_single_image {}

echo "Parallel processing complete!"
```

These examples demonstrate the versatility and power of the `phenotag images default-roi` command across various workflows, from simple single-image processing to complex batch operations and CI/CD pipeline integration.