# Annotation Loading and Saving Documentation

This document explains how annotation loading and saving works in PhenoTag, including the improved process implemented to provide better user experience and data safety.

## Overview

PhenoTag annotations are stored as YAML files at the day level. When users interact with the annotation system, they need to:

1. Load annotations when viewing a particular day
2. Save annotations when changes are made
3. Receive appropriate feedback about the loading/saving process

## Annotation Loading Process

When a user selects a day to view/edit:

1. The `load_day_annotations` function is called with the selected day and file paths
2. A loading flag is set to prevent concurrent saves during loading: `st.session_state.loading_annotations = True`
3. A loading spinner is displayed to provide visual feedback: `with st.spinner(f"Loading annotations for day {selected_day}..."):` 
4. The system attempts to find and load the annotations file: `annotations_{day}.yaml`
5. Annotations are processed and normalized to ensure consistent format
6. When loading is complete, a success message is shown, and the loading flag is cleared
7. If errors occur, they are caught, displayed to the user, and the loading flag is still cleared via a `finally` block

## Annotation Saving Process

Annotations can be saved in three ways:

1. **Manual Save**: User clicks the "Save Annotations" button (default approach)
2. **Timed Auto-Save**: If enabled, annotations are saved automatically every 60 seconds
3. **Immediate Auto-Save**: If enabled, annotations are saved immediately when changes are made

The save process:

1. First checks if a loading operation is in progress via `st.session_state.get('loading_annotations', False)`
   - If loading is in progress, the save is skipped to prevent data corruption
2. Checks auto-save settings to determine if saving should proceed
3. Groups annotations by day for efficient storage
4. Processes each annotation to ensure it's in the correct format
5. Saves the annotations to disk as YAML files
6. Updates the annotation status map for calendar view
7. Provides visual feedback via toast notifications

## State Management

Several session state variables are used to track the state of annotations:

- `loading_annotations`: Boolean flag indicating if annotations are currently being loaded
- `annotations_just_loaded`: Flag to prevent marking annotations as changed immediately after loading
- `unsaved_changes`: Indicates if there are unsaved changes to annotations
- `last_save_time`: Timestamp of the last successful save
- `auto_save_enabled`: User preference for enabling/disabling auto-save
- `immediate_save_enabled`: User preference for immediate saving on changes
- `auto_save_time`: Timestamp for next scheduled auto-save (if enabled)

## UI Components

The annotation panel provides several UI components for user feedback:

1. **Loading Spinner**: Appears during annotation loading
2. **Save Button**: Primary method for saving annotations, displayed prominently
3. **Save Status Indicator**: Shows whether changes are saved or unsaved
4. **Auto-Save Settings**: Available in an expandable "advanced" section
5. **Success/Error Messages**: Provide feedback about loading/saving operations

## Best Practices

- Always save annotations before switching to another day
- Use the manual save button for more control over when saves occur
- Only enable auto-save if preferred (disabled by default)
- Observe the save status indicator to know if you have unsaved changes