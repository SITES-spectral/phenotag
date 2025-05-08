# PhenoTag Annotation System

This document describes the annotation storage system in PhenoTag, detailing how image annotations are persisted to disk and loaded back when needed.

## Storage Structure

PhenoTag stores annotations in YAML files alongside the images they describe, using the following path structure:

```
{base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/annotations.yaml
```

For example, if your data directory is `/data/sites/`, your station is `abisko`, and the instrument ID is `PC01`, the annotations for images from January 1, 2023 (day 001) would be stored at:

```
/data/sites/abisko/phenocams/products/PC01/L1/2023/001/annotations.yaml
```

## Annotation Format

The annotations are stored in YAML format with the following structure:

```yaml
'file_path1.jpg':
  quality:
    discard_file: false
    snow_presence: false
  rois:
    ROI_01:
      discard_roi: false
      snow_presence: false
      annotated_flags: []
    ROI_02:
      discard_roi: false
      snow_presence: false
      annotated_flags: []
    ROI_03:
      discard_roi: false
      snow_presence: false
      annotated_flags: []
'file_path2.jpg':
  quality:
    # ...similar structure as above
```

Each image has:
- A `quality` section for whole-image flags
- An `rois` section containing annotations for specific Regions of Interest

## Key Functions

The annotation system is implemented through several key functions in the `phenotag.io_tools` module:

### `save_annotations(image_data, base_dir, station_name, instrument_id, year, day)`

Saves annotations for a specific day to a YAML file.

- **Parameters**:
  - `image_data`: Dictionary containing annotation data for images
  - `base_dir`: Base directory where data is stored
  - `station_name`: Name of the station
  - `instrument_id`: ID of the instrument
  - `year`: Year the images were taken
  - `day`: Day of year the images were taken
  
- **Returns**:
  - `Tuple[bool, str]`: Success status and path to saved file (or error message)

### `load_annotations(base_dir, station_name, instrument_id, year, day)`

Loads annotations from a YAML file for a specific day.

- **Parameters**: Same as `save_annotations`
- **Returns**:
  - `Dict`: Annotation data if file exists, empty dict otherwise

## Integration with UI

The annotation system is integrated with the PhenoTag UI through the following workflow:

1. **Loading Images**:
   - When images are scanned using `find_phenocam_images()`, the function automatically looks for existing annotation files
   - If annotations exist, they are loaded and applied to the image data
   - If no annotations exist, default values are used

2. **Saving Annotations**:
   - When the user clicks the "Save Annotations" button in the UI, the current state of annotations is extracted from the data editor
   - The in-memory data structure is updated with these values
   - The updated annotations are saved to disk using `save_annotations()`

3. **Feedback**:
   - The UI provides clear feedback about the success or failure of the save operation
   - The path where annotations were saved is shown to the user

## Default Values

When no annotations exist for an image, the following default values are used:

- **Quality** defaults:
  ```python
  {'discard_file': False, 'snow_presence': False}
  ```

- **ROI** defaults:
  ```python
  {
      'ROI_01': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
      'ROI_02': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
      'ROI_03': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []}
  }
  ```

## Example Usage

The following code demonstrates how to save and load annotations programmatically:

```python
from phenotag.io_tools import save_annotations, load_annotations

# Save annotations
success, filepath = save_annotations(
    image_data,
    '/data/sites/',
    'abisko',
    'PC01',
    '2023',
    '001'
)

# Load annotations
annotations = load_annotations(
    '/data/sites/',
    'abisko',
    'PC01',
    '2023',
    '001'
)
```

However, in normal usage, the UI handles saving and loading annotations automatically.