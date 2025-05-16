# Annotation Loading and Saving Documentation

This document explains how annotation loading and saving works in PhenoTag, including the improved process implemented to provide better user experience and data safety.

## ⚠️ CRITICAL IMPLEMENTATION NOTES ⚠️

> **IMPORTANT:** The annotation loading and saving system has been significantly improved to address persistent issues where annotations would not load properly. These improvements MUST be maintained in any future updates to prevent regressions.

### Key Implementation Patterns to Preserve

1. **Day-specific annotation tracking** using keys like `annotations_loaded_day_{day}` must be maintained to ensure proper loading
2. **Aggressive annotation clearing before loading** prevents stale data from appearing in the UI
3. **Self-healing mechanisms** in the annotation panel will attempt to reload annotations if they exist but aren't loaded
4. **Clear file path matching** ensures annotations are correctly associated with the right images
5. **Comprehensive logging** helps identify issues quickly
6. **ROI toggle state tracking** with `roi_toggle_changed` prevents unwanted saves when just toggling overlay display

### Common Issues and Solutions

1. **Symptoms**: Annotations visible in calendar but not loading in the UI
   - **Solution**: The annotation panel now includes self-healing code that will attempt to reload from disk

2. **Symptoms**: Wrong image count displayed when saving
   - **Solution**: Day-specific counting logic ensures accurate counts

3. **Symptoms**: Toggling ROI overlays triggers unwanted saves
   - **Solution**: Special flag tracks UI-only changes vs annotation changes

## Overview

PhenoTag annotations are stored as YAML files at the day level. When users interact with the annotation system, they need to:

1. Load annotations when viewing a particular day
2. Save annotations when changes are made
3. Receive appropriate feedback about the loading/saving process

## Annotation Loading Process (Enhanced)

When a user selects a day to view/edit:

1. The `load_day_annotations` function is called with the selected day and file paths
2. A loading flag is set to prevent concurrent saves during loading: `st.session_state.loading_annotations = True`
3. Day-specific tracking is implemented via `day_load_key = f"annotations_loaded_day_{selected_day}"`
4. Existing annotations for this day are explicitly cleared from memory to avoid stale data
5. The system attempts to find and load the annotations file: `annotations_{day}.yaml`
6. A fast filename-to-path lookup map is created for efficient matching
7. Annotations are processed and normalized to ensure consistent format
8. A final verification step confirms annotations were actually loaded into memory
9. When loading is complete, success flags are set for both general and day-specific keys
10. If errors occur, they are caught, displayed to the user, and the loading flag is still cleared via a `finally` block

## Self-Healing Mechanisms

The annotation panel includes self-healing capabilities:

1. When attempting to display annotations, it checks if annotations should exist but aren't loaded
2. If an annotations file exists but isn't in memory, it will attempt a reload automatically
3. This provides a fallback mechanism when annotations don't load correctly during normal page transitions

```python
# Check if annotations should be loaded but aren't
annotations_file = os.path.join(img_dir, f"annotations_{current_day}.yaml")
if os.path.exists(annotations_file) and not st.session_state.get(day_load_key, False):
    # Try to reload annotations
    load_day_annotations(current_day, daily_filepaths)
```

## Annotation Saving Process (Enhanced)

Annotations can be saved in three ways:

1. **Manual Save**: User clicks the "Save Annotations" button (default approach)
2. **Timed Auto-Save**: If enabled, annotations are saved automatically every 60 seconds
3. **Immediate Auto-Save**: If enabled, annotations are saved immediately when changes are made

The enhanced save process:

1. First checks if a loading operation is in progress: `st.session_state.get('loading_annotations', False)`
2. Verifies ROI toggle state isn't triggering save: `not st.session_state.get('roi_toggle_changed', False)`
3. Groups annotations by day for efficient storage
4. Uses day-specific filtering to ensure accurate image counting
5. Processes each annotation to ensure it's in the correct format
6. Saves the annotations to disk as YAML files
7. Updates the annotation status map for calendar view
8. Provides visual feedback via toast notifications

## State Management (Enhanced)

Several session state variables are used to track the state of annotations:

- `loading_annotations`: Boolean flag indicating if annotations are currently being loaded
- `annotations_loaded_day_{day}`: Day-specific flag tracking if annotations for a specific day are loaded
- `annotations_just_loaded`: Flag to prevent marking annotations as changed immediately after loading
- `unsaved_changes`: Indicates if there are unsaved changes to annotations
- `last_save_time`: Timestamp of the last successful save
- `auto_save_enabled`: User preference for enabling/disabling auto-save
- `immediate_save_enabled`: User preference for immediate saving on changes
- `auto_save_time`: Timestamp for next scheduled auto-save (if enabled)
- `roi_toggle_changed`: Special flag to track UI-only changes (toggle ROI display) vs annotation changes

## UI Components

The annotation panel provides several UI components for user feedback:

1. **Loading Spinner**: Appears during annotation loading
2. **Save Button**: Primary method for saving annotations, displayed prominently
3. **Save Status Indicator**: Shows whether changes are saved or unsaved
4. **Auto-Save Settings**: Available in an expandable "advanced" section
5. **Success/Error Messages**: Provide feedback about loading/saving operations
6. **Verification Messages**: Alert if annotations should be loading but aren't

## Best Practices and Requirements

- **DEVELOPERS MUST maintain the day-specific annotation tracking when modifying the code**
- **DEVELOPERS MUST preserve the self-healing mechanisms in the annotation panel**
- **DEVELOPERS MUST keep the ROI toggle state tracking to prevent unwanted saves**
- Always save annotations before switching to another day
- Use the manual save button for more control over when saves occur
- Only enable auto-save if preferred (disabled by default)
- Observe the save status indicator to know if you have unsaved changes

## Debugging Annotation Issues

The enhanced annotation system includes extensive logging:

1. Complete start and end markers for annotation loading operations
2. File-by-file tracking of which annotations get loaded
3. Verification of loaded annotations in memory before and after loading
4. Detailed error messages and stack traces
5. Explicit warnings when expected annotations aren't loaded

When troubleshooting annotation issues, check the Streamlit logs for these markers to identify where the problem might be occurring.