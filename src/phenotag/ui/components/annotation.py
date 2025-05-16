"""
Annotation component for PhenoTag UI.

This module provides functionality for annotating images, including
ROI management and quality flag assignment.
"""
import os
import streamlit as st
import datetime
import pandas as pd
import re
import time
import yaml
from typing import List, Dict, Any

from phenotag.config import load_config_files
from phenotag.io_tools import save_yaml

# Import ROI utilities
from phenotag.ui.components.roi_utils import serialize_polygons, deserialize_polygons
from phenotag.ui.components.flags_processor import FlagsProcessor


def display_annotation_panel(current_filepath):
    """
    Display and manage ROI annotation panel in a popup.
    
    Args:
        current_filepath (str): Path to the current image
    """
    if not current_filepath:
        print("Cannot display annotation panel - no current filepath")
        return
        
    # Get annotation timer to track activity
    from phenotag.ui.components.annotation_timer import annotation_timer
    
    # Initialize the timer state first to ensure it's available
    annotation_timer.initialize_session_state()
    
    # Create a unique key for this image
    image_key = current_filepath
    
    # Debug log for troubleshooting
    print(f"Displaying annotation panel for image: {os.path.basename(current_filepath)}")
    
    # Check if we have any annotations for this image
    has_annotations = False
    if 'image_annotations' in st.session_state and image_key in st.session_state.image_annotations:
        has_annotations = True
        annotation_count = len(st.session_state.image_annotations[image_key])
        print(f"Found existing annotations with {annotation_count} ROI entries")
    else:
        print("No annotations found for this image in session state")
        
        # Check if we should force a day reload
        img_dir = os.path.dirname(current_filepath)
        current_day = os.path.basename(img_dir)
        day_load_key = f"annotations_loaded_day_{current_day}"
        
        # If annotations should be loaded but aren't, try to reload
        annotations_file = os.path.join(img_dir, f"annotations_{current_day}.yaml")
        if os.path.exists(annotations_file) and not st.session_state.get(day_load_key, False):
            print(f"Annotations file exists but not loaded in memory. Will try to reload.")
            # Get file paths for this day
            from phenotag.ui.components.image_display import get_filtered_file_paths
            selected_station = st.session_state.selected_station if 'selected_station' in st.session_state else None
            selected_instrument = st.session_state.selected_instrument if 'selected_instrument' in st.session_state else None
            selected_year = st.session_state.selected_year if 'selected_year' in st.session_state else None
            
            daily_filepaths = get_filtered_file_paths(
                selected_station,
                selected_instrument,
                selected_year,
                current_day
            )
            
            # Try to reload
            load_day_annotations(current_day, daily_filepaths)
            
            # Check again if we have annotations
            if image_key in st.session_state.image_annotations:
                has_annotations = True
                annotation_count = len(st.session_state.image_annotations[image_key])
                print(f"After reload: Found annotations with {annotation_count} ROI entries")
    
    # Create a row for annotation status and buttons
    if has_annotations:
        st.success("Annotated", icon="✅")
    else:
        # Show button to mark as completed without annotation
        if st.button("No annotation needed", use_container_width=True):
            # Create default annotations with "not needed" flag
            create_default_annotations(current_filepath)
            
            # Force save
            save_all_annotations(force_save=True)
            
            # Rerun to update the UI
            st.rerun()
    
    # Add the annotation panel as a popover
    with st.popover("Annotation Panel"):
        # Record user interaction when annotation is viewed
        annotation_timer.record_interaction()
        
        # Add the reset all annotations button at the top
        if st.button("🔄 Reset All Annotations", key="reset_all_annotations", use_container_width=True):
            # Get the current day
            img_dir = os.path.dirname(current_filepath)
            current_day = os.path.basename(img_dir)
            
            # Get all images for this day
            daily_filepaths = []
            for img_path in st.session_state.image_annotations:
                img_dir = os.path.dirname(img_path)
                img_doy = os.path.basename(img_dir)
                if img_doy == current_day:
                    daily_filepaths.append(img_path)
            
            # Clear annotations for all images in this day
            for filepath in daily_filepaths:
                if filepath in st.session_state.image_annotations:
                    del st.session_state.image_annotations[filepath]
                    
            # Show confirmation
            st.success(f"Reset all annotations for day {current_day}")
            
            # Rerun to update UI
            st.rerun()
        
        # Now include the actual annotation interface in the popup
        _create_annotation_interface(current_filepath)


def create_default_annotations(current_filepath):
    """
    Create default annotations for an image marked as "not needed".
    
    Args:
        current_filepath (str): Path to the current image
    """
    if not current_filepath or 'image_annotations' not in st.session_state:
        return
        
    # Get ROI names
    roi_names = []
    if 'instrument_rois' in st.session_state and st.session_state.instrument_rois:
        roi_names = list(st.session_state.instrument_rois.keys())
    
    # Force ROI loading if we need to create annotations but don't have ROIs loaded
    if not roi_names and 'selected_instrument' in st.session_state:
        # Try to load instrument ROIs
        try:
            from phenotag.ui.main import load_instrument_rois
            if load_instrument_rois():
                print("ROIs loaded automatically for default annotations")
                # Update roi_names from the freshly loaded ROIs
                if 'instrument_rois' in st.session_state:
                    roi_names = list(st.session_state.instrument_rois.keys())
        except Exception as e:
            print(f"Error loading ROIs: {str(e)}")
    
    # Create default annotations
    annotation_data = [
        {
            "roi_name": "ROI_00",  #(Default - Full Image)
            "discard": False,
            "snow_presence": False,
            "flags": [],  # Empty list - no actual quality flags
            "not_needed": True,  # Separate field for not needed status
        }
    ]
    
    # Add an entry for each custom ROI
    for roi_name in roi_names:
        annotation_data.append({
            "roi_name": roi_name,
            "discard": False,
            "snow_presence": False,
            "flags": [],  # Empty list - no actual quality flags
            "not_needed": True,  # Separate field for not needed status
        })
    
    # Store in session state
    st.session_state.image_annotations[current_filepath] = annotation_data
    
    print(f"Created default 'not needed' annotations for {os.path.basename(current_filepath)}")


# This function has been merged into display_annotation_panel
    
    
def create_annotation_summary(current_filepath):
    """
    Create a summary of annotations for the current image to display in the main container.
    
    Args:
        current_filepath (str): Path to the current image
        
    Returns:
        dict: Summary data including dataframe and metrics
    """
    if not current_filepath or 'image_annotations' not in st.session_state:
        return None
    
    # Create a unique key for this image
    image_key = current_filepath
    
    # Check if we have annotations for this image
    if image_key not in st.session_state.image_annotations:
        return None
    
    # Get the annotation data
    annotation_data = st.session_state.image_annotations[image_key]
    
    # Load config for quality flags
    config = load_config_files()
    
    # Initialize the flags processor with the flags data
    flags_processor = FlagsProcessor(config.get('flags', {}))
    
    # Get the formatted flag options for UI display
    flag_options = flags_processor.get_flag_options()
    
    # Organize flags by category for better display
    flags_by_category = {}
    for option in flag_options:
        category = option.get("category", "Other")
        if category not in flags_by_category:
            flags_by_category[category] = []
        flags_by_category[category].append((option["value"], f"{option['value']} ({category})"))
    
    # Build summary data
    summary_data = []
    
    for annotation in annotation_data:
        roi_name = annotation["roi_name"]
        discard = annotation.get("discard", False)
        snow_presence = annotation.get("snow_presence", False)
        flags = annotation.get("flags", [])
        
        # Format the flags as a readable string with categories
        formatted_flags = []
        for flag in flags:
            # Find the display name with category
            for category, options in flags_by_category.items():
                for value, label in options:
                    if value == flag:
                        formatted_flags.append(label)
                        break
        
        flags_str = ", ".join(formatted_flags) if formatted_flags else "None"
        
        # Add to summary data
        summary_data.append({
            "Filename": os.path.basename(current_filepath),
            "ROI": roi_name,
            "Discard": "Yes" if discard else "No",
            "Snow Present": "Yes" if snow_presence else "No",
            "No annotation needed": "Yes" if annotation.get("not_needed", False) else "No",
            "Flag Count": len(flags),
            "Flags": flags_str
        })
    
    # Create summary metrics
    metrics = {}
    if summary_data:
        total_rois = len(summary_data)
        metrics["total_rois"] = total_rois
        
        discarded_rois = sum(1 for item in summary_data if item["Discard"] == "Yes")
        metrics["discarded_rois"] = discarded_rois
        metrics["discarded_pct"] = f"{100 * discarded_rois / total_rois:.1f}%" if total_rois > 0 else "0%"
        
        flagged_rois = sum(1 for item in summary_data if item["Flag Count"] > 0)
        metrics["flagged_rois"] = flagged_rois
        metrics["flagged_pct"] = f"{100 * flagged_rois / total_rois:.1f}%" if total_rois > 0 else "0%"
    
    return {
        "summary_data": summary_data,
        "metrics": metrics
    }

def _create_annotation_interface(current_filepath):
    """
    Internal function to create the ROI annotation interface.
    
    Args:
        current_filepath (str): Path to the current image
    """
    # Create a unique key for this image
    image_key = current_filepath
    
    # Get list of ROI names from loaded ROIs
    roi_names = []
    if 'instrument_rois' in st.session_state and st.session_state.instrument_rois:
        # Print debugging info about ROIs
        print(f"Found instrument_rois in session state: {list(st.session_state.instrument_rois.keys())}")
        roi_names = list(st.session_state.instrument_rois.keys())
    
    # Force ROI loading if not loaded yet
    if not roi_names and 'selected_instrument' in st.session_state:
        # Try to load instrument ROIs
        try:
            from phenotag.ui.main import load_instrument_rois
            if load_instrument_rois():
                print("ROIs loaded automatically for annotation")
                # Update roi_names from the freshly loaded ROIs
                if 'instrument_rois' in st.session_state:
                    roi_names = list(st.session_state.instrument_rois.keys())
                    print(f"ROI names updated: {roi_names}")
        except Exception as e:
            print(f"Error loading ROIs: {str(e)}")
            
    # Load config for quality flags
    config = load_config_files()
    
    # Initialize the flags processor with the flags data
    flags_processor = FlagsProcessor(config.get('flags', {}))
    
    # Get the formatted flag options for UI display
    flag_options = flags_processor.get_flag_options()

    # Initialize annotations dictionary if not exists
    if 'image_annotations' not in st.session_state:
        st.session_state.image_annotations = {}

    # Create or retrieve annotations for current image
    if image_key not in st.session_state.image_annotations:
        # Create default annotations for this image
        annotation_data = [
            {
                "roi_name": "ROI_00",  #(Default - Full Image)
                "discard": False,
                "snow_presence": False,
                "flags": [],  # Empty list for no flags selected - must be list for ListColumn
                "not_needed": False  # Not marked as "not needed" by default
            }
        ]

        # Add a row for each custom ROI
        for roi_name in roi_names:
            annotation_data.append({
                "roi_name": roi_name,
                "discard": False,
                "snow_presence": False,
                "flags": [],  # Empty list for no flags selected - must be list for ListColumn
                "not_needed": False  # Not marked as "not needed" by default
            })
            
        # Debug message for new annotations
        print(f"Created new default annotations for {os.path.basename(image_key)}")
        print(f"Default annotation data: {annotation_data}")
        print(f"ROI names used: {roi_names}")
    else:
        # Use existing annotations
        annotation_data = st.session_state.image_annotations[image_key]
        print(f"Loaded existing annotations for {os.path.basename(image_key)}")
        print(f"Existing annotation data: {annotation_data}")
        print(f"ROI names that should be available: {roi_names}")
        
    # Add the flag selector column for UI purposes (not stored in annotations)
    for row in annotation_data:
        row['_flag_selector'] = ""  # Empty by default, not stored permanently
    
    # Convert to DataFrame
    annotation_df = pd.DataFrame(annotation_data)
    
    # Add a title for the annotation panel
    st.markdown("### ROI Annotations")
    st.caption("Use the tabs below to annotate each Region of Interest")
    
    # Organize flags by category for the multiselect
    flags_by_category = {}
    for option in flag_options:
        category = option.get("category", "Other")
        if category not in flags_by_category:
            flags_by_category[category] = []
        flags_by_category[category].append((option["value"], f"{option['value']} ({category})"))
    
    # Create a list of all ROI names for tabs
    all_roi_names = [row["roi_name"] for row in annotation_data]
    
    # Create tabs for each ROI
    roi_tabs = st.tabs(all_roi_names)
    
    # Dictionary to track updated flag selections for each ROI
    updated_flag_selections = {}
    
    # Add a button to copy ROI_00 settings to all other ROIs
    if "ROI_00" in all_roi_names and len(all_roi_names) > 1:
        # Find ROI_00 data
        roi00_data = next((data for data in annotation_data if data["roi_name"] == "ROI_00"), None)
        if roi00_data:
            # Create a button to copy ROI_00 settings to all other ROIs
            if st.button("📋 Copy ROI_00 Settings to All ROIs", use_container_width=True):
                # Apply ROI_00 settings to all other ROIs
                for i, data in enumerate(annotation_data):
                    if data["roi_name"] != "ROI_00":
                        # Copy discard, snow_presence, and flags from ROI_00
                        annotation_data[i]["discard"] = roi00_data["discard"]
                        annotation_data[i]["snow_presence"] = roi00_data["snow_presence"]
                        annotation_data[i]["flags"] = roi00_data["flags"].copy()
                
                # Show success message
                st.success(f"Applied ROI_00 settings to all {len(all_roi_names)-1} ROIs")
                
                # Force save
                st.session_state.image_annotations[image_key] = annotation_data
                
                # Rerun to update UI
                st.rerun()
    
    # Process each ROI in its own tab
    for idx, (roi_name, roi_tab) in enumerate(zip(all_roi_names, roi_tabs)):
        with roi_tab:
            # Get the current ROI data
            roi_data = annotation_data[idx]
            
            # Create a unique key based on roi_name and image_key
            roi_key = f"{roi_name}_{image_key}_popup"
            
            # Create columns for the ROI settings
            roi_col1, roi_col2 = st.columns([1, 1])
            
            with roi_col1:
                # Create checkbox for discard
                discard = st.checkbox(
                    "Discard", 
                    value=roi_data.get('discard', False),
                    key=f"discard_{roi_key}",
                    help="Mark this image/ROI as not suitable for analysis"
                )
                
                # Create checkbox for snow presence
                snow_presence = st.checkbox(
                    "Snow Present", 
                    value=roi_data.get('snow_presence', False),
                    key=f"snow_{roi_key}",
                    help="Mark if snow is present in this ROI"
                )
                
                # Create checkbox for not needed status
                not_needed = st.checkbox(
                    "No annotation needed", 
                    value=roi_data.get('not_needed', False),
                    key=f"not_needed_{roi_key}",
                    help="Mark if this ROI doesn't need detailed annotation"
                )
            
            with roi_col2:
                # Flatten the options for the multiselect
                multiselect_options = []
                for category in sorted(flags_by_category.keys()):
                    multiselect_options.extend(flags_by_category[category])
                
                # Select flags with this multiselect
                selected_flags = st.multiselect(
                    "Quality Flags",
                    options=[value for value, _ in multiselect_options],
                    format_func=lambda x: next((label for value, label in multiselect_options if value == x), x),
                    default=roi_data.get('flags', []),
                    key=f"flags_{roi_key}",
                    help="Select quality flags applicable to this ROI"
                )
            
            # Store the selected flags and settings
            updated_flag_selections[roi_name] = {
                "discard": discard,
                "snow_presence": snow_presence,
                "flags": selected_flags,
                "not_needed": not_needed
            }
    
    # Process the UI state to update annotations
    updated_annotations = []
    for idx, roi_name in enumerate(all_roi_names):
        if roi_name in updated_flag_selections:
            selections = updated_flag_selections[roi_name]
            
            # Build the ROI data with all settings
            updated_annotations.append({
                "roi_name": roi_name,
                "discard": selections["discard"],
                "snow_presence": selections["snow_presence"],
                "flags": selections["flags"],
                "not_needed": selections["not_needed"]
            })
        else:
            # Fallback to original data if not updated
            updated_annotations.append(annotation_data[idx])
    
    # Save the updated annotations to session state
    st.session_state.image_annotations[image_key] = updated_annotations
    
    # Save and close button at the bottom
    st.button("💾 Save & Close", 
              type="primary", 
              use_container_width=True,
              key="save_annotations_popup",
              on_click=lambda: _handle_popup_save(image_key))


def display_annotation_completion_status(selected_day):
    """
    Display a progress bar and metrics showing annotation completion status.
    
    Args:
        selected_day (str): The currently selected day
    """
    if not selected_day or 'annotation_completion' not in st.session_state:
        return
    
    # Check if we have completion data for this day
    if selected_day not in st.session_state.annotation_completion:
        return
    
    # Get the completion data
    completion_data = st.session_state.annotation_completion[selected_day]
    expected = completion_data['expected']
    annotated = completion_data['annotated']
    percentage = completion_data['percentage']
    
    # Create an expandable section for annotation progress
    with st.expander("Annotation Progress", expanded=True):
        # Display a progress bar
        st.progress(percentage / 100)
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        # Display metrics
        with col1:
            st.metric("Expected Images", expected)
        
        with col2:
            st.metric("Annotated Images", annotated)
        
        with col3:
            st.metric("Completion", f"{percentage}%")
        
        # If file_status is available, show a table of file status
        if 'file_status' in completion_data and completion_data['file_status']:
            st.subheader("Individual Image Status")
            
            # Prepare data for the table
            status_data = []
            for filename, status in completion_data['file_status'].items():
                status_data.append({
                    "Filename": filename,
                    "Status": status.capitalize()
                })
            
            # Create a dataframe and display it
            if status_data:
                status_df = pd.DataFrame(status_data)
                st.dataframe(
                    status_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Filename": st.column_config.TextColumn("Filename", width="large"),
                        "Status": st.column_config.TextColumn("Status", width="medium")
                    }
                )

def _handle_popup_save(image_key):
    """
    Handle saving annotations when the save button in the popup is clicked.
    
    Args:
        image_key (str): Path to the image
    """
    # Save annotations
    save_all_annotations(force_save=True)
    
    # Clear the popup flag
    st.session_state.show_annotation_popup = False


def save_all_annotations(force_save=False):
    """
    Save all image annotations to YAML files.
    
    Args:
        force_save: If True, save regardless of auto-save settings
    """
    # Check if we're currently loading annotations - never save during load
    if st.session_state.get('loading_annotations', False):
        print("Skipping annotation save: currently loading annotations")
        return
        
    # Check if we should save based on auto-save settings
    auto_save_enabled = st.session_state.get('auto_save_enabled', True)
    immediate_save_enabled = st.session_state.get('immediate_save_enabled', True)
    
    # Skip saving if auto-save is disabled and not forcing
    if not auto_save_enabled and not force_save and not immediate_save_enabled:
        print("Skipping annotation save: auto-save is disabled and not forcing")
        return
        
    # Organize annotations by day for better storage
    annotations_by_day = {}
    saved_count = 0

    try:
        # Get the annotation timer to record elapsed times
        from phenotag.ui.components.annotation_timer import annotation_timer
        
        # Pause the timer to capture current elapsed time
        annotation_timer.pause_timer()
        
        # Group annotations by day (DOY)
        for img_path, annotations in st.session_state.image_annotations.items():
            if isinstance(img_path, str) and os.path.exists(img_path):
                # Extract day of year from the filename or path
                img_dir = os.path.dirname(img_path)
                # The DOY is typically the directory name in the L1 structure
                doy = os.path.basename(img_dir)

                # Skip if we can't determine the DOY
                if not doy.isdigit():
                    continue

                # Initialize dict for this DOY if not exists
                if doy not in annotations_by_day:
                    annotations_by_day[doy] = {}

                # Store annotations for this image
                img_filename = os.path.basename(img_path)
                
                # Make sure annotations is in the expected format (list of dicts, one per ROI)
                if isinstance(annotations, list):
                    # Already in correct format
                    annotations_by_day[doy][img_filename] = annotations
                    saved_count += 1
                elif isinstance(annotations, dict):
                    # If it's a dict of ROIs, we need to convert to list format
                    try:
                        converted_annotations = []
                        for roi_name, roi_data in annotations.items():
                            if isinstance(roi_data, dict):
                                # Make sure roi_name is in the dict
                                roi_data_copy = roi_data.copy()
                                roi_data_copy['roi_name'] = roi_name
                                converted_annotations.append(roi_data_copy)
                        
                        if converted_annotations:
                            annotations_by_day[doy][img_filename] = converted_annotations
                            saved_count += 1
                            print(f"Converted and saved annotations for image: {img_filename}")
                    except Exception as e:
                        print(f"Error converting annotations for saving: {str(e)}")
                else:
                    print(f"Warning: Unexpected annotations format for {img_filename}: {type(annotations)}")
                    # Save anyway to avoid data loss
                    annotations_by_day[doy][img_filename] = annotations
                    saved_count += 1

        # Save annotations by day
        for doy, day_annotations in annotations_by_day.items():
            if day_annotations:
                # Determine the directory path - use the L1 directory of the first image in this day
                for img_path in st.session_state.image_annotations:
                    if isinstance(img_path, str) and os.path.exists(img_path) and doy == os.path.basename(os.path.dirname(img_path)):
                        # L1 directory is the parent of the image file
                        l1_dir = os.path.dirname(img_path)

                        # Create annotations file for this day
                        annotations_file = os.path.join(l1_dir, f"annotations_{doy}.yaml")
                        
                        # Get elapsed annotation time for this day in minutes
                        current_session_time = annotation_timer.get_elapsed_time_minutes(doy)

                        # Check if existing annotations file exists and load it to preserve data
                        existing_data = {}
                        existing_time_minutes = 0.0
                        if os.path.exists(annotations_file):
                            try:
                                with open(annotations_file, 'r') as f:
                                    existing_data = yaml.safe_load(f) or {}
                                
                                # Get existing annotation time if available
                                if "annotation_time_minutes" in existing_data:
                                    existing_time_minutes = existing_data["annotation_time_minutes"]
                                    print(f"Found existing annotation time: {existing_time_minutes:.2f} minutes")
                                
                                print(f"Loaded existing annotations file to preserve data: {annotations_file}")
                            except Exception as e:
                                print(f"Error loading existing annotations: {str(e)}")

                        # Calculate total annotation time (add current session to existing time)
                        # Only add current session time if it's greater than 0 (to avoid adding time when just loading)
                        total_annotation_time = existing_time_minutes
                        if current_session_time > 0:
                            total_annotation_time += current_session_time
                            print(f"Added current session time: {current_session_time:.2f} minutes. Total now: {total_annotation_time:.2f} minutes")

                        # Get the total number of images for this day from the file system
                        from phenotag.ui.components.image_display import get_filtered_file_paths
                        selected_station = st.session_state.selected_station if 'selected_station' in st.session_state else None
                        selected_instrument = st.session_state.selected_instrument if 'selected_instrument' in st.session_state else None
                        selected_year = st.session_state.selected_year if 'selected_year' in st.session_state else None
                        
                        # Only get files for the current day that's being saved
                        all_files = get_filtered_file_paths(
                            selected_station,
                            selected_instrument,
                            selected_year,
                            doy  # This ensures we only count files for the current day
                        )
                        
                        # Count how many images have annotations for this specific day
                        # Make sure we're only counting annotations for this day
                        day_specific_annotations = {}
                        for img_path, img_anno in st.session_state.image_annotations.items():
                            # Only count images from this specific day
                            img_dir = os.path.dirname(img_path)
                            img_doy = os.path.basename(img_dir)
                            if img_doy == doy:
                                filename = os.path.basename(img_path)
                                day_specific_annotations[filename] = img_anno
                        
                        # Now count the real annotations for this day only
                        annotated_count = len(day_annotations)  # This counts files in the day_annotations object
                        expected_count = len(all_files)         # This counts files found in the file system
                        
                        print(f"Day {doy}: Found {annotated_count} annotations and {expected_count} expected images")
                        
                        # Determine the completion status of each annotated file
                        file_status = {}
                        for filename, annotations in day_annotations.items():
                            # If any ROI is missing annotations, the file is incomplete
                            all_rois_annotated = True
                            for roi in annotations:
                                # Check if this ROI has any annotations (flags, properties, or not_needed set)
                                has_annotations = (
                                    roi.get('discard', False) or
                                    roi.get('snow_presence', False) or
                                    len(roi.get('flags', [])) > 0 or
                                    roi.get('not_needed', False)
                                )
                                if not has_annotations:
                                    all_rois_annotated = False
                                    break
                            
                            # Set status based on whether all ROIs are annotated
                            file_status[filename] = "completed" if all_rois_annotated else "in_progress"
                        
                        # Calculate overall completion percentage
                        completion_percentage = (annotated_count / expected_count * 100) if expected_count > 0 else 0
                        
                        # Create basic annotations data structure
                        annotations_data = {
                            "created": existing_data.get("created", datetime.datetime.now().isoformat()),
                            "last_modified": datetime.datetime.now().isoformat(),
                            "day_of_year": doy,
                            "year": selected_year,
                            "station": selected_station,
                            "instrument": selected_instrument,
                            "annotation_time_minutes": total_annotation_time,
                            "expected_image_count": expected_count,
                            "annotated_image_count": annotated_count,
                            "completion_percentage": round(completion_percentage, 2),
                            "file_status": file_status,
                            "annotations": day_annotations
                        }
                        
                        # Preserve any additional fields that were in the existing file
                        # (but don't overwrite the ones we specifically want to update)
                        for key, value in existing_data.items():
                            if key not in ["created", "day_of_year", "station", "instrument", 
                                         "annotation_time_minutes", "annotations"]:
                                annotations_data[key] = value

                        # Save using the utility function
                        save_yaml(annotations_data, annotations_file)
                        print(f"Saved annotations to {annotations_file} (annotation time: {total_annotation_time:.2f} minutes)")
                        
                        # Update status cache if it exists
                        try:
                            if 'annotation_status_map' in st.session_state:
                                # Extract month from day number
                                selected_station = st.session_state.selected_station if 'selected_station' in st.session_state else 'unknown'
                                selected_instrument = st.session_state.selected_instrument if 'selected_instrument' in st.session_state else 'unknown'
                                current_year = st.session_state.selected_year if 'selected_year' in st.session_state else None
                                date = datetime.datetime.strptime(f"{current_year}-{doy}", "%Y-%j") if current_year else datetime.datetime.now()
                                month = date.month
                                
                                # Print info about annotation status
                                print(f"Setting annotation status for day {doy} in month {month}, year {current_year}")
                                
                                # Create status key
                                status_key = f"{selected_station}_{selected_instrument}_{current_year}_{month}"
                                
                                # Update or create cache entry
                                if status_key not in st.session_state.annotation_status_map:
                                    st.session_state.annotation_status_map[status_key] = {}
                                    
                                # Check if all images in this day are annotated AND all ROIs in each image
                                all_annotated = True
                                day_filepaths = []
                                
                                # Get all filepaths for this day
                                day_filepaths = []
                                for img_path in st.session_state.image_annotations:
                                    img_dir = os.path.dirname(img_path)
                                    img_doy = os.path.basename(img_dir)
                                    if img_doy == doy:
                                        day_filepaths.append(img_path)
                                
                                print(f"Found {len(day_filepaths)} annotated images in memory for day {doy}")
                                
                                # Check if we have all images for this day
                                from phenotag.ui.components.image_display import get_filtered_file_paths
                                all_day_filepaths = get_filtered_file_paths(
                                    selected_station,
                                    selected_instrument,
                                    current_year,
                                    doy
                                )
                                print(f"Found {len(all_day_filepaths)} expected images in filesystem for day {doy}")
                                
                                # FIRST check if all images exist in annotations
                                if len(day_filepaths) < len(all_day_filepaths):
                                    print(f"Not all images annotated for day {doy}: {len(day_filepaths)}/{len(all_day_filepaths)}")
                                    all_annotated = False
                                else:
                                    print(f"All {len(all_day_filepaths)} images have annotation entries for day {doy}")
                                    
                                    # SECOND, verify that each image has complete annotations for all ROIs
                                    # Check that each annotation has ROI entries
                                    for img_path in day_filepaths:
                                        if img_path in st.session_state.image_annotations:
                                            img_annotations = st.session_state.image_annotations[img_path]
                                            
                                            # Check if instrument_rois exists and get expected ROI count
                                            expected_roi_count = 1  # At minimum, should have ROI_00
                                            if 'instrument_rois' in st.session_state and st.session_state.instrument_rois:
                                                # Add 1 for each custom ROI plus the default ROI_00
                                                expected_roi_count = len(st.session_state.instrument_rois) + 1
                                            
                                            # Check if all expected ROIs are annotated
                                            if len(img_annotations) < expected_roi_count:
                                                print(f"Image {os.path.basename(img_path)} missing some ROI annotations: has {len(img_annotations)}, expected {expected_roi_count}")
                                                all_annotated = False
                                                break
                                
                                # Only mark as completed if ALL images have ALL ROIs annotated
                                if all_annotated:
                                    print(f"All images fully annotated for day {doy} - marking as completed")
                                    st.session_state.annotation_status_map[status_key][doy] = 'completed'
                                else:
                                    print(f"Annotation incomplete for day {doy} - marking as in_progress")
                                    st.session_state.annotation_status_map[status_key][doy] = 'in_progress'
                                
                                print(f"Updated annotation status cache for day {doy} to {st.session_state.annotation_status_map[status_key][doy]}")
                                
                                # Save status to L1 parent folder
                                try:
                                    # We need to get base_dir from l1_dir or scan_info
                                    if 'scan_info' in st.session_state:
                                        current_base_dir = st.session_state.scan_info.get('base_dir')
                                    else:
                                        # Extract base_dir from the l1_dir path
                                        # l1_dir is something like: /path/to/base_dir/station/phenocams/products/instrument/L1
                                        # We need to remove the station/phenocams/products/instrument/L1 part
                                        path_parts = l1_dir.split(os.sep)
                                        # Remove the last 5 parts: station/phenocams/products/instrument/L1
                                        base_path_parts = path_parts[:-5]
                                        current_base_dir = os.sep.join(base_path_parts)
                                        
                                    from phenotag.ui.components.annotation_status_manager import save_status_to_l1_parent
                                    # Use the current status (completed or in_progress)
                                    current_status = st.session_state.annotation_status_map[status_key][doy]
                                    save_status_to_l1_parent(
                                        current_base_dir,
                                        selected_station,
                                        selected_instrument,
                                        current_year,
                                        month,
                                        doy,
                                        current_status
                                    )
                                    print(f"Saved annotation status to L1 parent folder for day {doy}")
                                except Exception as status_error:
                                    print(f"Error saving status to L1 parent: {str(status_error)}")
                                
                                # Also update status for historical view if needed
                                if 'historical_year' in st.session_state and 'historical_month' in st.session_state:
                                    # Create historical status key
                                    historical_year = st.session_state.historical_year if 'historical_year' in st.session_state else None
                                    historical_month = st.session_state.historical_month if 'historical_month' in st.session_state else None
                                    hist_status_key = f"{selected_station}_{selected_instrument}_{historical_year}_{historical_month}"
                                    
                                    # Only update if the day is from the historical month/year
                                    hist_year = int(historical_year) if historical_year is not None else 0
                                    hist_month = historical_month
                                    
                                    if hist_year == int(current_year) and hist_month == month:
                                        # Update historical cache
                                        if hist_status_key not in st.session_state.annotation_status_map:
                                            st.session_state.annotation_status_map[hist_status_key] = {}
                                            
                                        # Use the same status as the main status key (completed or in_progress)
                                        main_status = st.session_state.annotation_status_map[status_key][doy]
                                        st.session_state.annotation_status_map[hist_status_key][doy] = main_status
                                        print(f"Updated historical annotation status cache for day {doy} to {main_status}")
                        except Exception as e:
                            print(f"Error updating status cache: {str(e)}")
                        break

        # Update session state to indicate changes are saved
        if 'unsaved_changes' in st.session_state:
            st.session_state.unsaved_changes = False
            
        # Update last save time
        st.session_state.last_save_time = datetime.datetime.now()
        
        # Restart timer for current day if it exists
        if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
            annotation_timer.start_timer(st.session_state.annotation_timer_current_day)

        if saved_count > 0:
            st.toast(f"Saved annotations for {saved_count} images across {len(annotations_by_day)} days!")
        else:
            st.toast("No valid images to save annotations for.")
    except Exception as e:
        st.error(f"Error saving annotations: {str(e)}")


def load_day_annotations(selected_day, daily_filepaths):
    """
    Load annotations for a specific day.
    
    Args:
        selected_day (str): The selected day
        daily_filepaths (list): List of file paths for the selected day
    """
    if not daily_filepaths:
        print(f"Warning: No daily_filepaths provided for day {selected_day}")
        return
        
    # Set loading flag to prevent concurrent saves while loading
    st.session_state.loading_annotations = True
    
    # Create a placeholder for the logging
    print(f"===== LOADING ANNOTATIONS FOR DAY {selected_day} =====")
    print(f"Found {len(daily_filepaths)} image files in the filesystem")
    
    # Create a key to track successful loading for this day
    day_load_key = f"annotations_loaded_day_{selected_day}"
    
    # Track which images have annotations in memory before loading
    existing_annotations_before = []
    if 'image_annotations' in st.session_state:
        for filepath in st.session_state.image_annotations:
            img_dir = os.path.dirname(filepath)
            img_doy = os.path.basename(img_dir)
            if img_doy == selected_day:
                existing_annotations_before.append(os.path.basename(filepath))
    
    if existing_annotations_before:
        print(f"Before loading: Found {len(existing_annotations_before)} images with annotations in memory")
    else:
        print(f"Before loading: No images with annotations found in memory")
    
    # Create a placeholder for the loading indicator
    with st.spinner(f"Loading annotations for day {selected_day}..."):
        try:
            # Initialize image_annotations if it doesn't exist
            if 'image_annotations' not in st.session_state:
                st.session_state.image_annotations = {}
                
            # Get the directory where we expect to find the annotations file
            if daily_filepaths:
                img_dir = os.path.dirname(daily_filepaths[0])
                annotations_file = os.path.join(img_dir, f"annotations_{selected_day}.yaml")
                print(f"Looking for annotations file at: {annotations_file}")
            else:
                print(f"ERROR: daily_filepaths is empty, cannot determine annotations file path")
                annotations_file = None
                
            # Import the annotation timer
            from phenotag.ui.components.annotation_timer import annotation_timer
            
            # Start the timer for this day
            annotation_timer.start_timer(selected_day)
            
            # Force clear annotations for this day first to avoid stale data
            print(f"Clearing existing annotations for day {selected_day}")
            day_filepaths_to_clear = []
            for filepath in st.session_state.image_annotations:
                img_dir = os.path.dirname(filepath)
                img_doy = os.path.basename(img_dir)
                if img_doy == selected_day:
                    day_filepaths_to_clear.append(filepath)
            
            for filepath in day_filepaths_to_clear:
                if filepath in st.session_state.image_annotations:
                    del st.session_state.image_annotations[filepath]
                    print(f"Cleared annotations for {os.path.basename(filepath)}")
            
            print(f"Cleared annotations for {len(day_filepaths_to_clear)} images")

            # If annotations file exists, load it
            if annotations_file and os.path.exists(annotations_file):
                print(f"Loading annotations from file: {annotations_file}")
                try:
                    with open(annotations_file, 'r') as f:
                        import yaml
                        annotation_data = yaml.safe_load(f)
                    
                    # Get file stats for logging
                    import os
                    file_size = os.path.getsize(annotations_file)
                    print(f"Annotations file size: {file_size} bytes")
                    
                    # Log the structure of the file for debugging
                    print(f"Annotations file structure keys: {list(annotation_data.keys())}")
                    if 'annotations' in annotation_data:
                        print(f"File contains annotations for {len(annotation_data['annotations'])} images")
                    else:
                        print(f"WARNING: No 'annotations' key found in the file!")
                        
                    # Load previous annotation time if available
                    if 'annotation_time_minutes' in annotation_data:
                        previous_time = annotation_data['annotation_time_minutes']
                        print(f"Loading previous annotation time: {previous_time:.2f} minutes")
                        
                        # Set the previous time as accumulated time for this day
                        # Only if we don't already have accumulated time (to avoid double-counting)
                        current_accumulated = annotation_timer.get_accumulated_time(selected_day)
                        if current_accumulated == 0:
                            annotation_timer.set_accumulated_time(selected_day, previous_time)
                            print(f"Set accumulated time to previous time: {previous_time:.2f} minutes")
                        else:
                            print(f"Already have accumulated time: {current_accumulated:.2f} minutes. Not setting to previous: {previous_time:.2f}")

                    if 'annotations' in annotation_data:
                        # Convert the loaded annotations to our format
                        loaded_count = 0
                        loaded_filenames = []
                        
                        # Log the image names in the file vs filesystem for debugging
                        annotation_image_names = list(annotation_data['annotations'].keys())
                        filesystem_image_names = [os.path.basename(path) for path in daily_filepaths]
                        print(f"Images in annotation file: {annotation_image_names}")
                        print(f"Images in filesystem: {filesystem_image_names}")
                        
                        # Map between image names in annotations file and filepaths
                        name_to_path_map = {}
                        for filepath in daily_filepaths:
                            name_to_path_map[os.path.basename(filepath)] = filepath
                        
                        for img_name, img_annotations in annotation_data['annotations'].items():
                            # First look in our map for faster matching
                            if img_name in name_to_path_map:
                                filepath = name_to_path_map[img_name]
                                
                                # Process the annotations
                                if isinstance(img_annotations, list):
                                    # This is the correct format - a list of dictionaries, one per ROI
                                    processed_annotations = []
                                    
                                    # Process each annotation to ensure it has all expected fields
                                    for anno in img_annotations:
                                        # Normalize annotation format
                                        processed_anno = anno.copy()
                                        
                                        # Ensure we have all required fields with proper types
                                        if 'roi_name' not in processed_anno:
                                            processed_anno['roi_name'] = "ROI_00"
                                        if 'discard' not in processed_anno:
                                            processed_anno['discard'] = False
                                        if 'snow_presence' not in processed_anno:
                                            processed_anno['snow_presence'] = False
                                        if 'flags' not in processed_anno or processed_anno['flags'] is None:
                                            processed_anno['flags'] = []
                                        
                                        # Handle the not_needed field
                                        if 'not_needed' not in processed_anno:
                                            # Check if the "not_needed" flag is in the flags list
                                            if 'flags' in processed_anno and "not_needed" in processed_anno['flags']:
                                                # Remove it from flags and set the dedicated field
                                                processed_anno['flags'].remove("not_needed")
                                                processed_anno['not_needed'] = True
                                            else:
                                                processed_anno['not_needed'] = False
                                        
                                        # Make sure flags is a list of strings
                                        processed_anno['flags'] = [str(flag) for flag in processed_anno['flags']]
                                        
                                        # Add to processed list
                                        processed_annotations.append(processed_anno)
                                    
                                    # After processing, store the annotations
                                    st.session_state.image_annotations[filepath] = processed_annotations
                                    
                                    loaded_count += 1
                                    loaded_filenames.append(img_name)
                                    print(f"Loaded annotations for image: {img_name} - {len(processed_annotations)} ROIs")
                                
                                elif isinstance(img_annotations, dict):
                                    # Try to convert dict format to list format
                                    try:
                                        converted_annotations = []
                                        for roi_name, roi_data in img_annotations.items():
                                            if isinstance(roi_data, dict):
                                                # Make sure roi_name is in the dict
                                                processed_anno = roi_data.copy()
                                                processed_anno['roi_name'] = roi_name
                                                
                                                # Normalize fields
                                                if 'discard' not in processed_anno:
                                                    processed_anno['discard'] = False
                                                if 'snow_presence' not in processed_anno:
                                                    processed_anno['snow_presence'] = False
                                                if 'flags' not in processed_anno or processed_anno['flags'] is None:
                                                    processed_anno['flags'] = []
                                                    
                                                # Handle the not_needed field
                                                if 'not_needed' not in processed_anno:
                                                    # Check if the "not_needed" flag is in the flags list
                                                    if 'flags' in processed_anno and "not_needed" in processed_anno['flags']:
                                                        # Remove it from flags and set the dedicated field
                                                        processed_anno['flags'].remove("not_needed")
                                                        processed_anno['not_needed'] = True
                                                    else:
                                                        processed_anno['not_needed'] = False
                                                    
                                                # Make sure flags is a list of strings
                                                processed_anno['flags'] = [str(flag) for flag in processed_anno['flags']]
                                                
                                                converted_annotations.append(processed_anno)
                                            else:
                                                print(f"Warning: Unexpected ROI data format for {roi_name}: {type(roi_data)}")
                                        
                                        if converted_annotations:
                                            # Store the annotations
                                            st.session_state.image_annotations[filepath] = converted_annotations
                                            
                                            loaded_count += 1
                                            loaded_filenames.append(img_name)
                                            print(f"Converted and loaded annotations for image: {img_name} - {len(converted_annotations)} ROIs")
                                    except Exception as conv_error:
                                        print(f"Error converting annotations for {img_name}: {str(conv_error)}")
                                else:
                                    print(f"Warning: Unexpected annotation format for {img_name}: {type(img_annotations)}")
                            else:
                                # Fallback to slower search if the map doesn't have it
                                print(f"Image {img_name} not found in name_to_path_map, using slower search")
                                found = False
                                for filepath in daily_filepaths:
                                    if os.path.basename(filepath) == img_name:
                                        # Process similar to above
                                        found = True
                                        break
                                
                                if not found:
                                    print(f"Warning: Could not find filepath for {img_name}")
                        
                        print(f"Successfully loaded annotations for {loaded_count} images: {', '.join(loaded_filenames)}")
                        
                        # Set a flag to indicate annotations were loaded
                        st.session_state.annotations_just_loaded = True
                        st.session_state[day_load_key] = True
                        
                        # Analyze and display annotation completion status
                        if 'expected_image_count' in annotation_data and 'annotated_image_count' in annotation_data:
                            expected = annotation_data['expected_image_count']
                            annotated = annotation_data['annotated_image_count']
                            completion = annotation_data.get('completion_percentage', 0)
                            
                            # Show notification with completion status
                            st.success(f"Loaded annotations for day {selected_day}: {annotated}/{expected} images ({completion}% complete)", icon="✅")
                            
                            # Store completion info in session state
                            if 'annotation_completion' not in st.session_state:
                                st.session_state.annotation_completion = {}
                            st.session_state.annotation_completion[selected_day] = {
                                'expected': expected,
                                'annotated': annotated,
                                'percentage': completion,
                                'file_status': annotation_data.get('file_status', {})
                            }
                        else:
                            # Just show basic notification for older annotation files
                            st.success(f"Loaded annotations for day {selected_day}", icon="✅")
                except Exception as file_error:
                    print(f"Error loading annotations file: {str(file_error)}")
                    st.error(f"Error loading annotations file: {str(file_error)}")
            else:
                print(f"No annotations file found for day {selected_day} at {annotations_file}")
                st.session_state[day_load_key] = False
            
            # Final check to make sure annotations were properly loaded
            annotations_after_loading = []
            if 'image_annotations' in st.session_state:
                for filepath in st.session_state.image_annotations:
                    img_dir = os.path.dirname(filepath)
                    img_doy = os.path.basename(img_dir)
                    if img_doy == selected_day:
                        annotations_after_loading.append(os.path.basename(filepath))
            
            print(f"After loading: Found {len(annotations_after_loading)} images with annotations in memory")
            print(f"Annotations loaded: {', '.join(annotations_after_loading)}")
            
            # Force reload if we didn't load any annotations but we know the file exists
            if not annotations_after_loading and annotations_file and os.path.exists(annotations_file):
                print("WARNING: No annotations loaded despite file existing. Will need manual intervention.")
                st.warning(f"Failed to load annotations for day {selected_day} despite file existing. Please try switching to another day and back.")
        except Exception as e:
            print(f"Critical error loading annotations: {str(e)}")
            st.error(f"Error loading annotations: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            st.session_state[day_load_key] = False
        finally:
            # Always clear the loading flag
            st.session_state.loading_annotations = False
            print(f"===== COMPLETED LOADING ANNOTATIONS FOR DAY {selected_day} =====")
    
    # Return success status
    return st.session_state.get(day_load_key, False)