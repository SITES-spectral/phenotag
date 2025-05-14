# PhenoTag Annotation System

This document describes the annotation storage system in PhenoTag, detailing how image annotations are persisted to disk and loaded back when needed.

## Storage Structure

PhenoTag stores annotations in YAML files alongside the images they describe, using the following path structure:

```
{base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/annotations_{day_of_year}.yaml
```

For example, if your data directory is `/data/sites/`, your station is `abisko`, and the instrument ID is `PC01`, the annotations for images from January 1, 2023 (day 001) would be stored at:

```
/data/sites/abisko/phenocams/products/PC01/L1/2023/001/annotations_001.yaml
```

## Annotation Format

The annotations are stored in YAML format with the following structure:

```yaml
created: "2025-05-14T12:34:56.789012"
day_of_year: "001"
station: "abisko"
instrument: "PC01"
annotation_time_minutes: 45.8
annotations:
  'file_name1.jpg':
    - roi_name: "ROI_00"  # Default - Full Image
      discard: false
      snow_presence: false
      has_flags: false
    - roi_name: "ROI_01"
      discard: false
      snow_presence: false
      has_flags: false
    - roi_name: "ROI_02"
      discard: false
      snow_presence: false
      has_flags: false
  'file_name2.jpg':
    # ...similar structure as above
```

Each image entry contains:
- An array of ROI objects, each with discard, snow_presence, and has_flags properties
- The first ROI entry (ROI_00) represents the entire image

## Auto-Save and Persistence

PhenoTag features an intelligent annotation saving system that includes:

1. **Auto-Save**:
   - Enabled by default, saves annotations automatically every 60 seconds when changes are detected
   - User can toggle auto-save on/off in the annotation panel
   - Visual countdown shows when the next auto-save will occur
   - Status indicators show whether there are unsaved changes

2. **Smart Save on Navigation**:
   - Annotations are automatically saved when:
     - Switching between days
     - Changing instruments
     - Changing stations
     - Changing years or months
   - This ensures no data is lost during normal navigation

3. **Manual Save**:
   - A "Save Now" button allows immediate saving at any time
   - Shows as "Save Now" when there are unsaved changes
   - Shows as "Save All" when everything is saved
   - Displays timestamp of the last save operation

4. **Contextual Status Indicators**:
   - Warning icon when unsaved changes exist
   - Success icon with timestamp when all changes are saved
   - Countdown timer showing seconds until next auto-save

## Annotation Timer

PhenoTag includes an annotation timer system that tracks the time spent annotating each day:

1. **Time Tracking**:
   - Automatically starts when a day is loaded for annotation
   - Tracks active time spent making annotations
   - Pauses after 3 minutes of inactivity
   - Automatically resumes when user interaction is detected
   - Persists time data between sessions

2. **Inactivity Detection**:
   - Monitors user interactions with the annotation interface
   - Pauses timing when no activity is detected for 3 minutes
   - Ensures only active annotation time is recorded
   - Prevents inflated time metrics due to leaving the application open

3. **Persistence and Metadata**:
   - Total annotation time is stored in the annotations YAML file
   - Time is saved in minutes as `annotation_time_minutes` field
   - Time accumulates across multiple annotation sessions
   - Persists even when reopening the application

4. **UI Integration**:
   - Displays current annotation time in HH:MM:SS format
   - Shows in the annotation panel without being distracting
   - Updates in real-time as annotations are made
   - No impact on workflow or performance

5. **Navigation Integration**:
   - Timer is paused when switching between days, stations, or instruments
   - Current time is saved before navigation changes
   - Timer is automatically started for the newly selected day
   - Previous time is loaded when returning to a previously annotated day

## Key Functions

The annotation system is implemented through several key functions:

### `save_all_annotations()`

Organizes and saves annotations for all days to their respective YAML files.

- Groups annotations by day of year
- Creates appropriate directory structure
- Includes metadata like creation timestamp, station, and instrument
- Saves accumulated annotation time for each day
- Updates status indicators and session state

### `load_day_annotations(selected_day, daily_filepaths)`

Loads annotations for a specific day when the user navigates to it.

- Checks if annotations file exists for the selected day
- Loads and maps annotations to the correct file paths
- Loads previous annotation time if available
- Starts the annotation timer for the current day
- Shows notification when annotations are loaded
- Avoids redundant loading if annotations are already in session state

### `AnnotationTimer` Class

Manages tracking of time spent on annotations, with the following methods:

#### `start_timer(day)`
- Starts or resumes timing for a specific day
- Initializes time tracking for new days
- Records the current time as the start time

#### `pause_timer()`
- Temporarily pauses time tracking
- Calculates and accumulates elapsed time
- Used when switching contexts or on inactivity

#### `record_interaction()`
- Records user activity to maintain active timing
- Resets the inactivity counter
- Restarts the timer if it was paused

#### `check_inactivity()`
- Checks if user has been inactive
- Pauses the timer after 3 minutes of inactivity
- Prevents counting idle time as annotation time

#### `get_elapsed_time_minutes(day)`
- Returns the total accumulated time in minutes
- Used for storing in the annotation metadata

#### `get_formatted_time(day)`
- Returns a formatted time string (HH:MM:SS)
- Used for display in the UI

## Annotation Persistence Across Navigation

PhenoTag ensures annotations are properly preserved and loaded when navigating:

1. **When changing days**:
   - Current day's annotations are automatically saved
   - New day's annotations are loaded if they exist
   - UI is updated to reflect loaded annotations

2. **When changing instruments/stations**:
   - Current annotations are saved before switching
   - Session state is cleared to prepare for new context
   - Annotations for the new selection are loaded automatically

3. **When saving manually**:
   - All annotations across all loaded days are saved at once
   - Confirmation message shows success/failure status
   - Last save timestamp is updated

## Default Values

When no annotations exist for an image, the following default values are used:

```python
[
    {
        "roi_name": "ROI_00",  # Default - Full Image
        "discard": False,
        "snow_presence": False,
        "has_flags": False
    }
]
```

Additional ROIs (if defined in stations.yaml) will be added to this list with the same default values.

## Example Usage

In normal usage, the UI handles saving and loading annotations automatically. The auto-save feature ensures data is regularly persisted without user intervention, while also providing clear visual feedback about the save status.