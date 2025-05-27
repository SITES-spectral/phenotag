# PhenoTag Annotation System

This document describes the annotation storage system in PhenoTag, detailing how image annotations are persisted to disk and loaded back when needed.

## Storage Structure

### Individual Day Annotations

PhenoTag stores day-level annotations in YAML files alongside the images they describe, using the following path structure:

```
{base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/annotations_{day_of_year}.yaml
```

For example, if your data directory is `/data/sites/`, your station is `abisko`, and the instrument ID is `PC01`, the annotations for images from January 1, 2023 (day 001) would be stored at:

```
/data/sites/abisko/phenocams/products/PC01/L1/2023/001/annotations_001.yaml
```

### Centralized Annotation Status

In addition to individual day annotation files, PhenoTag also maintains a centralized annotation status file at the L1 parent level:

```
{base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/L1_annotation_status_{station_name}_{instrument_id}.yaml
```

For example:

```
/data/sites/abisko/phenocams/products/PC01/L1/L1_annotation_status_abisko_PC01.yaml
```

This centralized file tracks the annotation status (not_annotated, in_progress, or completed) for all days in each month/year, enabling:

1. Faster scanning of annotation status for calendar view indicators
2. Improved performance when displaying annotation progress
3. Centralized tracking of annotation completion across all days
4. Better synchronization between different annotation sessions

## Annotation Format

The annotations are stored in YAML format with the following structure:

```yaml
created: "2025-05-14T12:34:56.789012"
day_of_year: "001"
station: "abisko"
instrument: "PC01"
year: "2025"
annotation_time_minutes: 45.8
annotations:
  'file_name1.jpg':
    - roi_name: "ROI_00"  # Default - Full Image
      discard: false
      snow_presence: false
      flags: []  # Empty list means no flags are set
    - roi_name: "ROI_01"
      discard: false
      snow_presence: false
      flags: ["sunny", "clouds"]  # List of applied flags
    - roi_name: "ROI_02"
      discard: false
      snow_presence: false
      flags: ["high_brightness"]  # Another example with one flag
  'file_name2.jpg':
    # ...similar structure as above
```

Each image entry contains:
- An array of ROI objects, each with discard, snow_presence, and flags properties
- The flags property is a list of flag names that apply to this ROI
- The first ROI entry (ROI_00) represents the entire image

Images can be marked as "not needing annotation" with a special flag:

```yaml
annotations:
  'file_name1.jpg':
    - roi_name: "ROI_00"
      discard: false
      snow_presence: false
      flags: ["not_needed"]  # Special flag indicating no annotation needed
    # Additional ROIs will also have the not_needed flag
```

## Annotation Tracking and Persistence

PhenoTag features an enhanced annotation tracking and saving system that includes:

> **⚠️ VERY IMPORTANT: UI-ONLY STATE CHANGES AND SAVING**
>
> Some UI actions, like toggling ROI overlays, are purely visual and should not trigger annotation saves.
> PhenoTag implements a pattern to prevent unwanted saves:
>
> 1. Set a flag in session state when making UI-only changes:
>    ```python
>    # Flag to indicate this is just a UI toggle, not an annotation change
>    st.session_state.roi_toggle_changed = True
>    ```
>
> 2. Check this flag before saving:
>    ```python
>    # Skip saving if just toggling UI elements
>    if not st.session_state.get('roi_toggle_changed', False):
>        save_all_annotations()
>    ```
>
> 3. Reset the flag after checking:
>    ```python
>    # Reset the toggle flag for the next run
>    if 'roi_toggle_changed' in st.session_state:
>        del st.session_state['roi_toggle_changed']
>    ```
>
> This pattern MUST be followed for any UI-only state changes to prevent:
> - Accidental saving of empty/incomplete annotations
> - Overwriting existing annotations with default values
> - Data loss or corruption during UI interaction
>
> **Always use this pattern when adding new UI toggles or controls that should not affect annotation data.**

1. **Progress Tracking**:
   - Tracks the expected number of images for each day
   - Counts how many images have annotations
   - Calculates and displays completion percentage
   - Shows a progress bar to visualize completion status
   - Displays metrics for total, completed, and in-progress images

2. **Individual File Status**:
   - Tracks the annotation status of each image file
   - Marks files as "completed" when all ROIs are properly annotated
   - Marks files as "in_progress" when some ROIs need annotation
   - Displays status in a table view for easy monitoring

3. **Auto-Save**:
   - Saves annotations automatically when closing the annotation panel
   - Updates completion statistics during each save operation
   - Preserves annotation time tracking for reporting

4. **Self-Contained Saving**:
   - Annotations are automatically saved when:
     - Clicking the "Save Annotations" button in the popover
     - Clicking outside the popover to close it
     - Marking an image as "No annotation needed"
   - No need for explicit saves when changing days, instruments, or stations
   - Each annotation is managed within its own popover context

5. **Progress Visualization**:
   - Shows progress bar for day completion
   - Displays metrics for expected vs. annotated image counts
   - Updates the annotation completion percentage in real-time
   - Provides a detailed view of individual file status

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

### `save_all_annotations(force_save=False)`

Organizes and saves annotations for all days to their respective YAML files.

- Takes an optional `force_save` parameter to bypass auto-save settings
- Groups annotations by day of year
- Creates appropriate directory structure
- Includes metadata like creation timestamp, station, and instrument
- Saves accumulated annotation time for each day
- Updates status indicators and session state
- Respects auto-save and immediate-save settings when not forcing
- Used automatically during context changes with `force_save=True`

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
   - All annotations for the current day are saved at once
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
        "flags": []  # Empty list for no flags
    }
]
```

Additional ROIs (if defined in stations.yaml) will be added to this list with the same default values.

## Annotation Interface

PhenoTag features a button-triggered popover interface for ROI annotations:

1. **Annotation Button and Status**:
   - Located in the image selection sidebar
   - Shows annotation status for the current image ("Annotated" or "Not annotated")
   - Provides a button that says "Annotate" for non-annotated images or "Edit" for annotated ones
   - Clicking the button opens the annotation panel popover
   - Changes are automatically saved when closing the popover

2. **Annotation Panel Popover**:
   - Opens when the Annotate/Edit button is clicked
   - Self-contained - handles loading, managing, and saving its own data
   - Shows the filename being annotated for confirmation
   - Contains the "No annotation needed" and "Reset All Annotations" buttons
   - Automatically closes and saves when clicked outside
   - Eliminates the need for explicit saves when changing days/stations/instruments

3. **ROI Tabs**:
   - Each ROI has its own dedicated tab for focused annotation
   - Tabs are automatically generated based on available ROIs
   - Easy navigation between different ROIs
   - Clear context of which ROI is being annotated

4. **Quality Flags Selection**:
   - Each ROI tab contains a multiselect widget for flag selection
   - Flags are organized by category for easier browsing
   - Flags display their category for better context
   - Selected flags are displayed with their categories

5. **Copy ROI_00 Settings**:
   - "Copy ROI_00 Settings to All ROIs" button applies settings from ROI_00 to all other ROIs
   - Copies discard status, snow presence, and quality flags
   - Useful for applying common settings across all regions
   - Individual ROIs can still be customized after copying

6. **Reset Annotations**:
   - "Reset All Annotations" button allows clearing all annotations for the current day
   - Useful when starting over or when annotations need to be recreated
   - Provides immediate feedback when annotations are reset

7. **Save Annotations**:
   - Save button within the popover saves annotations immediately
   - Changes are also auto-saved when closing the popover
   - Provides feedback when annotations are successfully saved

8. **Annotation Summary**:
   - Displayed below the main image
   - Shows a comprehensive table of all ROIs for the current image
   - Includes filename, ROI name, discard status, snow presence, and flags
   - Features metrics for total ROIs, discarded ROIs, and flagged ROIs with percentages

## Example Usage

In normal usage, the UI handles saving and loading annotations automatically. The auto-save feature ensures data is regularly persisted without user intervention, while also providing clear visual feedback about the save status.