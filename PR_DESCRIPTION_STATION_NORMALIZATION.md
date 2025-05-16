# PhenoTag Station Name Normalization Fix

## Summary
This pull request fixes an issue with station name normalization in file paths and filenames. Previously, the application was using the display name with Swedish characters (e.g., "Röbäcksdalen") instead of the normalized ASCII-friendly name (e.g., "robacksdalen") in some file operations, causing inconsistency in annotation file paths and filenames.

## What's Fixed
- **File path consistency**: All file paths now use the normalized station name from stations.yaml
- **Annotation status paths**: L1 annotation status files now use normalized names for both paths and filenames
- **Swedish character handling**: Properly handles the conversion of names with Swedish characters
- **Cross-module consistency**: Ensures consistent normalization across all modules that handle file paths

## Key Changes
1. Added a robust `get_normalized_station_name` function to annotation_status_manager.py to handle conversion of station names
2. Updated the following files to use normalized station names:
   - src/phenotag/ui/components/annotation_status_manager.py
   - src/phenotag/ui/components/annotation_status.py
   - src/phenotag/io_tools/load_annotations.py
   - src/phenotag/io_tools/directory_scanner.py
   - src/phenotag/io_tools/lazy_scanner.py
3. Added documentation in docs/station_name_normalization.md
4. Added test scripts to verify the correct normalization

## Testing Steps
1. Run the test scripts:
   ```
   python test_annotation_paths.py
   python test_annotation_status_paths.py
   ```
2. Run the application and select a station with Swedish characters (e.g., "Grimsö", "Lönnstorp", "Röbäcksdalen")
3. Verify that the application can load and save annotation files correctly

## Notes for Reviewers
- The fix ensures backward compatibility by accepting both normalized names and display names as input to functions
- The normalization function uses station data from stations.yaml for consistency
- All filesystem operations now use the ASCII-friendly normalized names, while the UI continues to display the proper names with Swedish characters