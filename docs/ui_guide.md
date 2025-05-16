# PhenoTag UI Guide

This document provides a guide to the PhenoTag user interface, explaining its components and features.

## Overview

PhenoTag uses Streamlit to provide a modern, responsive web interface for annotating phenocam images. The interface is designed to be intuitive and user-friendly, with clear labeling and helpful tooltips.

## Interface Structure

The PhenoTag interface is divided into two main sections:
1. **Sidebar** - Contains station/instrument selection and configuration options
2. **Main Content Area** - Displays the selected data and annotation tools

### Sidebar

The sidebar contains the following elements:

- **Title and Caption** - Identifies the application
- **Station Selection** - Dropdown for selecting a monitoring station
- **Instrument Selection** - Dropdown for selecting a phenocam at the chosen station
- **Configuration Panel** - Expandable section for setting up the application
  - Data Directory: Input field for the root data directory
  - Session Management: Buttons for saving and resetting the session
  - Image Scanner: Tools for scanning for images

### Main Content Area

The main content area is organized into a two-column layout:

- **Left Column** (Image Selection):
  - Image selection radio buttons
  - ROI overlay toggle
  - ROI legend (when overlays are enabled)
  - Annotation panel with "No annotation needed" button and popup interface

- **Right Column** (Image Display):
  - Selected image with full detail and optional ROI overlays
  - Annotation summary table
  - Annotation metrics

## Core Workflows

### 1. Configuration

1. Select a station from the dropdown in the sidebar
2. Select a phenocam instrument from the second dropdown
3. Enter the data directory path in the Configuration panel
4. Click "🔍 Scan for Images" to load available images

### 2. Image Selection

1. After scanning, select a year from the dropdown
2. Select a day from the second dropdown
3. The application will load images for that day

### 3. Image Annotation

1. Select an image using the radio buttons in the left column
2. View the image in the right column with optional ROI overlays
3. For images that don't need annotation, click the "No annotation needed" button
4. For images that require annotation:
   - Click on the "Annotation Panel" popover in the left sidebar
   - Use the tabbed interface to annotate each ROI:
     - Mark ROIs for discarding (checkbox)
     - Indicate snow presence (checkbox)
     - Select quality flags (multiselect)
   - Click "💾 Save & Close" to save your annotations and close the panel
5. View the annotation summary below the image in the right column
6. To reset annotations for the current day, use the "🔄 Reset All Annotations" button in the annotation panel

### 4. Session Management

- Session state is automatically saved in `~/.phenotag/sites_spectral_phenocams_session_config.yaml`
- Use "💾 Save Session" to manually save your current selections
- Use "🔄 Reset Session" to clear all selections and start fresh

## Memory-Optimized Mode

When running in memory-optimized mode:
1. Use the `--memory-optimized` flag when launching
2. A memory usage dashboard appears in the sidebar
3. Images are automatically scaled based on available memory
4. Memory usage statistics are displayed in real-time

## Status Indicators

The application uses several types of status indicators:

- **Status Containers** - Show multi-step processes like scanning
- **Progress Bars** - Indicate progress of operations
- **Success/Error Messages** - Provide feedback on operation results
- **Metrics** - Display summary statistics in the annotation summary
- **Annotation Status** - Shows whether an image is annotated with a success icon
- **Summary Table** - Provides detailed information about annotations for the current image

## Keyboard Shortcuts

- **Escape** - Collapse expanded sections
- **Ctrl+Enter** - Submit forms

## Troubleshooting

If you encounter issues:

1. Check that the data directory path is correct
2. Verify that image files follow the expected structure
3. Try resetting the session if unexpected behavior occurs
4. Check the terminal output for any error messages

## Customization

The UI can be customized by modifying:
- Color themes: Through Streamlit's theming system
- Layout: By changing column proportions in the code
- Widgets: By modifying column configuration in data_editor