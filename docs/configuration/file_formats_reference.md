# PhenoTag File Formats Reference

This document provides a comprehensive reference for all file formats used in PhenoTag.

## Directory Structure

PhenoTag follows a standardized directory structure for organizing images and annotations:

```
base_path/
├── normalized_station_name/         # e.g., "asa_01" (normalized from "Asa 01")
│   ├── instrument_id/              # e.g., "NDVI01", "RGB01"
│   │   ├── YYYY/                   # Year directory
│   │   │   ├── MM/                 # Month directory (01-12)
│   │   │   │   ├── DD/             # Day directory (01-31)
│   │   │   │   │   ├── image_YYYY-MM-DD_HH-MM-SS.jpg
│   │   │   │   │   └── ...
│   │   └── annotations/            # Annotation files directory
│   │       ├── annotation_2024-01-01.yaml
│   │       ├── annotation_2024-01-02.yaml
│   │       └── ...
```

### Station Name Normalization

Station names are normalized for filesystem compatibility:
- Spaces replaced with underscores
- Special characters removed
- Converted to lowercase

Examples:
- `"Asa 01"` → `"asa_01"`
- `"Lönnstorp (01)"` → `"lonnstorp_01"`
- `"Svartberget"` → `"svartberget"`

## Annotation File Format

### File Naming Convention
- Location: `{base_path}/{normalized_station}/{instrument}/annotations/`
- Filename: `annotation_{YYYY-MM-DD}.yaml`
- Example: `annotation_2024-01-15.yaml`

### File Structure

```yaml
# Required fields
date: "2024-01-15"              # Date in YYYY-MM-DD format
station: "Asa 01"               # Original station name (not normalized)
instrument: "NDVI01"            # Instrument identifier
timestamp: "2024-01-15T14:30:00" # ISO 8601 timestamp of last modification

# Image quality flags
image_flags:
  "08:00:00":                   # Time in HH:MM:SS format
    - "fog"                     # List of quality flags
    - "frost"
  "12:00:00":
    - "clouds"
  "16:00:00":
    - "snow"
    - "partial"

# Annotation timing
annotation_time_seconds: 180.5   # Total time spent annotating (in seconds)

# Optional metadata
metadata:
  annotator: "user@example.com"  # Optional: who made the annotations
  version: "1.0.0"              # Optional: annotation format version
  notes: "Heavy fog in morning"  # Optional: free-form notes
```

### Available Quality Flags

Quality flags are defined in `config/flags.yaml`:

```yaml
flags:
  - fog: "Fog or mist obscuring the view"
  - frost: "Frost on camera lens or vegetation"
  - snow: "Snow covering vegetation or lens"
  - rain: "Rain drops on lens or heavy rain"
  - clouds: "Heavy cloud cover affecting lighting"
  - partial: "Partial image or technical issues"
  - dark: "Too dark/underexposed"
  - bright: "Overexposed/lens flare"
  - other: "Other quality issues"
```

## Station Configuration Format

### File Location
- Path: `config/stations.yaml`
- Purpose: Define camera stations and their ROI configurations

### File Structure

```yaml
# Station definition
"Station Name":                    # Human-readable station name
  location: "Site Location"        # Optional: physical location
  coordinates:                     # Optional: GPS coordinates
    latitude: 55.7047
    longitude: 13.1910
  elevation: 75                    # Optional: elevation in meters
  
  # ROI (Region of Interest) configuration
  roi:
    # Polygon coordinates (list of [x, y] points)
    coordinates:
      - [100, 100]                # Top-left point
      - [500, 100]                # Top-right point
      - [500, 400]                # Bottom-right point
      - [100, 400]                # Bottom-left point
    
    # Visual properties
    color: [0, 255, 0]            # BGR color format (this is green)
    thickness: 7                   # Line thickness in pixels
    
    # Optional ROI metadata
    name: "ROI_01"                # Optional: ROI identifier
    type: "vegetation"            # Optional: ROI type/category

# Example with multiple stations
"Asa 01":
  location: "Asa Research Station"
  roi:
    coordinates:
      - [200, 150]
      - [800, 150]
      - [800, 600]
      - [200, 600]
    color: [0, 255, 0]
    thickness: 7

"Lönnstorp":
  location: "Lönnstorp Field Station"
  roi:
    coordinates:
      - [150, 100]
      - [850, 100]
      - [850, 650]
      - [150, 650]
    color: [255, 0, 0]            # Blue in BGR
    thickness: 5
```

## Image File Format

### Supported Formats
- JPEG (`.jpg`, `.jpeg`) - Primary format
- PNG (`.png`) - Supported but not recommended for large datasets

### File Naming Convention
While PhenoTag can work with various naming conventions, the recommended format is:
- Pattern: `{station}_{instrument}_{YYYY-MM-DD}_{HH-MM-SS}.jpg`
- Example: `asa_01_NDVI01_2024-01-15_12-00-00.jpg`

## Annotation Status File Format

### Purpose
Track which dates have been annotated and by whom.

### File Structure
```yaml
# annotation_status.yaml
status:
  "2024-01-15":
    annotated: true
    annotator: "user@example.com"
    timestamp: "2024-01-15T14:30:00"
    duration_seconds: 180.5
  "2024-01-16":
    annotated: false
    in_progress: true
    started: "2024-01-16T10:00:00"
```

## Memory State File Format

### Purpose
Save and restore UI state for memory-efficient navigation.

### File Structure
```yaml
# .phenotag_state.yaml (in working directory)
current_station: "Asa 01"
current_instrument: "NDVI01"
current_date: "2024-01-15"
data_directory: "/data/phenocam"
last_updated: "2024-01-15T14:30:00"
settings:
  auto_save: true
  roi_visible: true
  thumbnail_size: 150
```

## CLI Configuration Format

### Default ROI Output Format

The CLI `default-roi` command can output in two formats:

#### YAML Format (default)
```yaml
roi:
  coordinates:
  - - 0
    - 480
  - - 640
    - 480
  - - 640
    - 960
  - - 0
    - 960
  color:
  - 0
  - 255
  - 0
  thickness: 7
```

#### JSON Format
```json
{
  "roi": {
    "coordinates": [[0, 480], [640, 480], [640, 960], [0, 960]],
    "color": [0, 255, 0],
    "thickness": 7
  }
}
```

## Best Practices

### 1. File Naming
- Always use normalized station names for directories
- Keep original station names in configuration files
- Use consistent date/time formats (ISO 8601)

### 2. Data Integrity
- Always validate file contents before processing
- Handle missing files gracefully
- Implement proper error handling for corrupted files

### 3. Performance
- Use YAML for human-readable configuration
- Consider JSON for programmatic access if performance is critical
- Implement caching for frequently accessed files

### 4. Backup
- Regular backup annotation files
- Version control station configurations
- Keep annotation history for audit trails

## Migration Notes

When migrating from older versions:

1. **Station Names**: Ensure all directory names are normalized
2. **Annotation Format**: Check for required fields (date, station, instrument)
3. **ROI Format**: Verify coordinate format is list of [x, y] pairs
4. **File Paths**: Update any hardcoded paths to use dynamic path construction