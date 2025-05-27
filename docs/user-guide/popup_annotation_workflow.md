# Popup Annotation Workflow

This document explains the streamlined popup-based annotation workflow in PhenoTag.

## Overview

PhenoTag now features a popup-based annotation system that:

1. Places all annotation controls within the image selection sidebar
2. Uses a popover to expand the annotation interface when needed
3. Displays the annotation summary below the image in the main panel
4. Preserves selection state during annotation

## Annotation Components

### 1. Annotation Panel in Sidebar

The annotation panel appears at the bottom of the image selection sidebar and includes:

- **Annotation Status** - Shows "Annotated" with a checkmark if the image has annotations
- **No Annotation Needed Button** - For images that don't require detailed annotation
- **Annotation Panel Popover** - Expands to show the full annotation interface

### 2. Annotation Popover

When clicked, the "Annotation Panel" popover expands to show:

- **Reset Annotations Button** - Resets all annotations for the current day
- **Copy ROI_00 Settings Button** - Applies settings from ROI_00 to all other ROIs
- **ROI Tabs** - One tab for each Region of Interest
- **Annotation Controls** - Per-ROI settings for discard, snow presence, and quality flags
- **Save & Close Button** - Saves annotations and closes the popover

### 3. Annotation Summary

A comprehensive summary appears below the image in the main panel:

- **Summary Table** - Shows all ROIs with their annotation details:
  - Filename
  - ROI name
  - Discard status
  - Snow presence
  - Quality flags with categories
- **Metrics** - Shows statistics about annotations:
  - Total ROIs
  - Discarded ROIs with percentage
  - ROIs with flags with percentage

## Annotation Workflow

### Basic Annotation

1. Select an image using the radio buttons in the sidebar
2. If the image doesn't need annotation:
   - Click the "No annotation needed" button
   - The image will be marked with a special "not_needed" flag
   - The annotation status will update to show "Annotated"

3. If the image needs detailed annotation:
   - Click on the "Annotation Panel" popover
   - The annotation interface will expand
   - Navigate through ROI tabs to annotate each region:
     - Set discard status with checkbox
     - Set snow presence with checkbox
     - Select quality flags from the multiselect
   - Click "Save & Close" when finished

### Viewing Annotation Summary

- The annotation summary appears automatically below the image
- It updates in real-time as annotations are made
- It shows:
  - Detailed information for each ROI
  - Metrics summarizing annotation status
  - Visual indicators for key metrics

### Resetting Annotations

If you need to clear annotations for an entire day:

1. Click on the "Annotation Panel" popover
2. Click the "Reset All Annotations" button
3. All annotations for images from the current day will be removed
4. A confirmation message will appear

## Key Benefits

This streamlined popup-based annotation workflow offers several advantages:

1. **Maintains Context** - Keeps the image visible while annotating
2. **Preserves Selection** - Doesn't lose radio button selection during annotation
3. **Reduces UI Clutter** - Hides complex annotation controls until needed
4. **Centralizes Controls** - Places all annotation functionality in one area
5. **Provides Clear Summary** - Shows annotation details in a comprehensive view

## Example Usage Scenarios

### Scenario 1: Quick "No Annotation Needed" Marking

1. Select a low-quality or irrelevant image
2. Click "No annotation needed"
3. The image is marked and the application is ready for the next image

### Scenario 2: Detailed ROI Annotation

1. Select an image with visible features of interest
2. Click on "Annotation Panel"
3. Annotate the ROI_00 (full image) with appropriate settings
4. For images where most ROIs should have the same settings:
   - Click "Copy ROI_00 Settings to All ROIs" to apply ROI_00 settings to all regions
   - Adjust individual ROI settings as needed for exceptions
5. For images with unique ROI settings:
   - Navigate through ROI tabs to mark each region individually
6. Click "Save & Close"
7. Review the annotation summary below the image

### Scenario 3: Reviewing Annotations

1. Select a previously annotated image
2. The annotation status shows "Annotated"
3. View the detailed annotation summary below the image
4. To make changes, click "Annotation Panel" and modify as needed

## Keyboard Navigation

For efficiency, you can use keyboard navigation:

- **Tab** - Move between controls in the annotation interface
- **Space** - Toggle checkboxes
- **Enter** - Activate buttons
- **Arrow Keys** - Navigate multiselect options
- **Escape** - Close the annotation panel (in some browsers)