# PhenoTag Memory-Efficient Calendar Navigation

## Summary
This pull request implements a memory-efficient directory scanning system for the PhenoTag application, significantly improving performance when browsing large collections of phenocam images. It adds a calendar-based navigation interface that intelligently loads only the image data that is currently needed, rather than loading all images at once.

## What's New
- **Memory-efficient directory scanning**: Only scans directories as needed rather than loading all image data at once
- **Calendar navigation**: Added a month/day calendar interface for easier browsing of phenocam images
- **Lazy loading**: Images are only loaded when actually viewed, greatly reducing memory usage
- **Path handling improvements**: Now supports directories with and without leading zeros for day-of-year, improving compatibility
- **Month filtering**: Calendar efficiently filters and displays images by month
- **Debug logging**: Added diagnostic logging to help troubleshoot path and filtering issues

## Key Changes
1. Added `/src/phenotag/io_tools/directory_scanner.py` for efficient directory traversal
2. Added `/src/phenotag/io_tools/lazy_scanner.py` for lazy loading of image data
3. Enhanced the UI to display only timestamps instead of full filenames
4. Added UI components for calendar-based navigation
5. Added smart day filtering by month in calendar view
6. Fixed path handling to be more resilient to different directory naming conventions

## Testing Steps
1. Run the application (`python -m phenotag.cli.main run`)
2. Select a station and instrument in the sidebar
3. Try selecting different years and months in the calendar view
4. Verify that images load correctly when clicking on days in the calendar
5. Check that memory usage remains reasonable even with large image collections

## Notes for Reviewers
- The directory scanner was designed to work with your existing directory structure (station/phenocams/products/instrument/L1/year/day)
- We've added path handling that tries both with and without leading zeros for the day-of-year directories
- Added diagnostic logging that can be uncommented for debugging
- Calendar filtering works on day-of-year values rather than calendar dates for efficiency