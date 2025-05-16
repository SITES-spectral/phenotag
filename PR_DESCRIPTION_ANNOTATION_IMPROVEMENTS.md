# Improve Annotation Loading and Saving Process

This PR enhances the annotation loading and saving process in PhenoTag with several improvements focused on user feedback, safety, and control.

## Key Changes

### 1. Loading Indicator and State Management
- Added a loading spinner during annotation loading operations
- Implemented a loading state flag to prevent concurrent saves during loading
- Added proper error handling with cleanup of state flags even when errors occur

### 2. Improved Save Controls
- Disabled auto-save by default per user request
- Added a prominent manual save button at the top of the UI
- Moved auto-save options to an expandable "advanced" section
- Added clear visual indicators for unsaved changes

### 3. UI Reorganization
- Reorganized the annotation panel to emphasize manual saving
- Added better visual feedback about the save state
- Improved layout with annotation time display at the top

## Technical Details

- The loading state flag (`st.session_state.loading_annotations`) prevents race conditions between loading and saving operations
- Added a `finally` block to ensure loading flags are always cleared
- Implemented a more robust annotation state handling mechanism that:
  - Properly deals with loading events
  - Displays appropriate visual feedback 
  - Prevents accidental data loss due to concurrent operations

## Testing

This PR includes unit tests that verify:
- The loading spinner appears during annotation loading
- Concurrent saves are prevented during loading operations
- Auto-save settings are correctly respected
- The save button properly triggers saving operations

## How to Test

1. Open PhenoTag and select a station with annotations
2. Observe the loading spinner when selecting a day
3. Make changes to annotations and verify the "unsaved changes" warning appears
4. Test the manual save button and verify the success message
5. Try the advanced auto-save settings if needed