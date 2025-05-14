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
from typing import List, Dict, Any

from phenotag.config import load_config_files
from phenotag.io_tools import save_yaml

# Import ROI utilities
from phenotag.ui.components.roi_utils import serialize_polygons, deserialize_polygons
from phenotag.ui.components.flags_processor import FlagsProcessor


def display_annotation_panel(current_filepath):
    """
    Display and manage ROI annotation panel.
    
    Args:
        current_filepath (str): Path to the current image
    """
    if not current_filepath:
        return
        
    # Get annotation timer to track activity
    from phenotag.ui.components.annotation_timer import annotation_timer
    
    # Initialize the timer state first to ensure it's available
    annotation_timer.initialize_session_state()
    
    # Record user interaction
    annotation_timer.record_interaction()
    
    # Check for inactivity (will pause the timer if needed)
    annotation_timer.check_inactivity()
    
    # Create a unique key for this image
    image_key = current_filepath
    
    
    
    # Get list of ROI names from loaded ROIs
    roi_names = []
    if 'instrument_rois' in st.session_state and st.session_state.instrument_rois:
        roi_names = list(st.session_state.instrument_rois.keys())

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
            }
        ]

        # Add a row for each custom ROI
        for roi_name in roi_names:
            annotation_data.append({
                "roi_name": roi_name,
                "discard": False,
                "snow_presence": False,
                "flags": [],  # Empty list for no flags selected - must be list for ListColumn
            })
            
        # Debug message for new annotations
        print(f"Created new default annotations for {os.path.basename(image_key)}")
    else:
        # Use existing annotations
        annotation_data = st.session_state.image_annotations[image_key]
        print(f"Loaded existing annotations for {os.path.basename(image_key)}")

    # Add the flag selector column for UI purposes (not stored in annotations)
    for row in annotation_data:
        row['_flag_selector'] = ""  # Empty by default, not stored permanently
    
    # Convert to DataFrame
    annotation_df = pd.DataFrame(annotation_data)
    
    annotation_col, save_col = st.columns([2, 1])
    # Add batch update controls

    
    with annotation_col:
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
        
        # Create tabs for each ROI plus a Summary tab
        roi_tabs = st.tabs(all_roi_names + ["Summary"])
        
        # Dictionary to track updated flag selections for each ROI
        updated_flag_selections = {}
        
        # Process each ROI in its own tab, excluding the summary tab
        summary_tab = roi_tabs[-1]  # Last tab is the summary tab
        roi_tabs_without_summary = roi_tabs[:-1]  # All tabs except the last one
        
        for idx, (roi_name, roi_tab) in enumerate(zip(all_roi_names, roi_tabs_without_summary)):
            with roi_tab:
                # Get the current ROI data
                roi_data = annotation_data[idx]
                
                # Create a unique key based on roi_name and image_key
                roi_key = f"{roi_name}_{image_key}"
                
                # Create columns for the ROI settings
                roi_col1, roi_col2 = st.columns([1, 1])
                
                with roi_col1:
                    # Create checkbox for discard
                    discard = st.checkbox(
                        "Discard ROI", 
                        value=roi_data.get("discard", False),
                        key=f"discard_{roi_key}",
                        help="Mark this ROI as not suitable for analysis"
                    )
                    
                    # Create checkbox for snow presence
                    snow_presence = st.checkbox(
                        "Snow Present", 
                        value=roi_data.get("snow_presence", False),
                        key=f"snow_{roi_key}",
                        help="Mark if snow is present in this ROI"
                    )
                    
                    # Add "Apply to all ROIs" checkbox in the ROI_00 tab
                    apply_to_all = False
                    if roi_name == "ROI_00":
                        # Store the previous state to detect changes
                        if f"apply_all_{roi_key}_prev" not in st.session_state:
                            st.session_state[f"apply_all_{roi_key}_prev"] = False
                        
                        # Initialize ROI_00 flags in session state if not present
                        roi00_flags_key = f"roi00_flags_{image_key}"
                        if roi00_flags_key not in st.session_state:
                            st.session_state[roi00_flags_key] = roi_data.get("flags", [])
                            
                        apply_to_all = st.checkbox(
                            "Apply these flags to all ROIs", 
                            value=st.session_state.get(f"apply_all_{roi_key}", False),
                            key=f"apply_all_{roi_key}",
                            help="Apply the selected flags from ROI_00 to all other ROIs"
                        )
                        
                        # If checkbox state changed, force a rerun to update all tabs
                        if apply_to_all != st.session_state[f"apply_all_{roi_key}_prev"]:
                            st.session_state[f"apply_all_{roi_key}_prev"] = apply_to_all
                            # Use current flags from ROI_00 data, not the selected_flags which isn't defined yet
                            st.rerun()
                
                with roi_col2:
                    # Create multiselect for flags with categories
                    # Flatten the options for the multiselect
                    multiselect_options = []
                    for category in sorted(flags_by_category.keys()):
                        multiselect_options.extend(flags_by_category[category])
                    
                    # Check if we should use flags from ROI_00
                    roi00_apply_key = f"apply_all_ROI_00_{image_key}"
                    roi00_flags_key = f"roi00_flags_{image_key}"
                    
                    # Default to current flags
                    current_flags = roi_data.get("flags", [])
                    
                    # If not ROI_00 and apply_all is checked, use ROI_00's flags
                    if roi_name != "ROI_00" and st.session_state.get(roi00_apply_key, False) and roi00_flags_key in st.session_state:
                        current_flags = st.session_state[roi00_flags_key]
                    
                    # Select flags with this multiselect
                    selected_flags = st.multiselect(
                        "Quality Flags",
                        options=[value for value, _ in multiselect_options],
                        format_func=lambda x: next((label for value, label in multiselect_options if value == x), x),
                        default=current_flags,
                        key=f"flags_{roi_key}",
                        help="Select quality flags applicable to this ROI"
                    )
                    
                    # For ROI_00, update the stored flags when they change
                    if roi_name == "ROI_00" and selected_flags != st.session_state.get(roi00_flags_key, []):
                        st.session_state[roi00_flags_key] = selected_flags
                    
                    # Store the selected flags
                    updated_flag_selections[roi_name] = {
                        "discard": discard,
                        "snow_presence": snow_presence,
                        "flags": selected_flags,
                        "apply_to_all": apply_to_all
                    }
                    
                    # If we're on ROI_00 and apply_to_all is enabled, show a message
                    if roi_name == "ROI_00" and apply_to_all:
                        st.info("These flags will be applied to all other ROIs", icon="ℹ️")
                
                # Show current flags
                if selected_flags:
                    st.write("Current flags:")
                    for flag in selected_flags:
                        # Find the display name with category
                        display_name = next((label for value, label in multiselect_options if value == flag), flag)
                        st.caption(f"- {display_name}")
                else:
                    st.caption("No flags selected for this ROI")
        
        # Display the summary tab
        with summary_tab:
            st.write("### Annotation Summary")
            st.caption("Overview of all ROI annotations for this image")
            
            # Build a summary dataframe with formatted data
            summary_data = []
            
            for roi_name in all_roi_names:
                if roi_name in updated_flag_selections:
                    # Get the selections made in the UI
                    selections = updated_flag_selections[roi_name]
                    
                    # Handle "Apply to all" from ROI_00
                    apply_from_roi00 = False
                    if (roi_name != "ROI_00" and "ROI_00" in updated_flag_selections and 
                        updated_flag_selections["ROI_00"]["apply_to_all"]):
                        apply_from_roi00 = True
                    
                    # Determine which flags to display
                    display_flags = selections["flags"]
                    if apply_from_roi00:
                        display_flags = updated_flag_selections["ROI_00"]["flags"]
                    
                    # Format the flags as a readable string with categories
                    formatted_flags = []
                    for flag in display_flags:
                        # Find the display name with category
                        for category, options in flags_by_category.items():
                            for value, label in options:
                                if value == flag:
                                    formatted_flags.append(label)
                                    break
                    
                    flags_str = ", ".join(formatted_flags) if formatted_flags else "None"
                    
                    # Add to summary data
                    summary_data.append({
                        "ROI": roi_name,
                        "Discard": "Yes" if selections["discard"] else "No",
                        "Snow Present": "Yes" if selections["snow_presence"] else "No",
                        "Flag Count": len(display_flags),
                        "Flags": flags_str,
                        "Applied from ROI_00": "Yes" if apply_from_roi00 else "No" if roi_name != "ROI_00" else "N/A"
                    })
            
            # Create and display the summary dataframe
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                
                # Style the dataframe
                st.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ROI": st.column_config.TextColumn("ROI", width="small"),
                        "Discard": st.column_config.TextColumn("Discard", width="small"),
                        "Snow Present": st.column_config.TextColumn("Snow Present", width="small"),
                        "Flag Count": st.column_config.NumberColumn("Flag Count", width="small"),
                        "Flags": st.column_config.TextColumn("Flags", width="large"),
                        "Applied from ROI_00": st.column_config.TextColumn("From ROI_00", width="small")
                    }
                )
                
                # Add summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_rois = len(summary_data)
                    st.metric("Total ROIs", total_rois)
                
                with col2:
                    discarded_rois = sum(1 for item in summary_data if item["Discard"] == "Yes")
                    st.metric("Discarded ROIs", discarded_rois, 
                             delta=f"{100 * discarded_rois / total_rois:.1f}%" if total_rois > 0 else "0%")
                
                with col3:
                    flagged_rois = sum(1 for item in summary_data if item["Flag Count"] > 0)
                    st.metric("ROIs with Flags", flagged_rois,
                             delta=f"{100 * flagged_rois / total_rois:.1f}%" if total_rois > 0 else "0%")
                
                # Add flag statistics
                st.write("### Flag Distribution")
                
                # Count occurrences of each flag
                flag_counts = {}
                for item in summary_data:
                    flags_str = item["Flags"]
                    if flags_str != "None":
                        for flag_entry in flags_str.split(", "):
                            # Extract just the flag name from "flag_name (category)"
                            if " (" in flag_entry:
                                flag_name = flag_entry.split(" (")[0].strip()
                                category = flag_entry.split(" (")[1].replace(")", "").strip()
                            else:
                                flag_name = flag_entry
                                category = "Unknown"
                                
                            if flag_name not in flag_counts:
                                flag_counts[flag_name] = {"count": 0, "category": category}
                            flag_counts[flag_name]["count"] += 1
                
                # Display flag counts as a bar chart if there are any flags
                if flag_counts:
                    flag_data = pd.DataFrame([
                        {"Flag": f"{flag} ({info['category']})", "Count": info["count"]}
                        for flag, info in flag_counts.items()
                    ])
                    
                    flag_data = flag_data.sort_values("Count", ascending=False)
                    
                    st.bar_chart(flag_data, x="Flag", y="Count", use_container_width=True)
                else:
                    st.caption("No flags have been applied to any ROIs")
            else:
                st.info("No annotation data available for summary")
        
        # Convert the UI state to a dataframe for processing
        edited_data = []
        for idx, roi_name in enumerate(all_roi_names):
            if roi_name in updated_flag_selections:
                selections = updated_flag_selections[roi_name]
                
                # Handle "Apply to all" from ROI_00
                apply_from_roi00 = False
                if "ROI_00" in updated_flag_selections and updated_flag_selections["ROI_00"]["apply_to_all"]:
                    # Only apply flags from ROI_00 to other ROIs if checkbox is checked
                    apply_from_roi00 = roi_name != "ROI_00"  # Don't apply to ROI_00 itself
                
                roi_flags = selections["flags"]
                if apply_from_roi00:
                    # Use ROI_00's flags instead
                    roi_flags = updated_flag_selections["ROI_00"]["flags"]
                
                edited_data.append({
                    "roi_name": roi_name,
                    "discard": selections["discard"],
                    "snow_presence": selections["snow_presence"],
                    "flags": roi_flags
                })
            else:
                # Fallback to original data if not updated
                edited_data.append(annotation_data[idx])
        
        # Convert to DataFrame for further processing
        edited_annotations = pd.DataFrame(edited_data)

        # Check if annotations have changed
        if image_key in st.session_state.image_annotations:
            old_annotations = st.session_state.image_annotations[image_key]
            new_annotations = edited_annotations.to_dict('records')
            
            # Compare if anything has changed
            annotations_changed = old_annotations != new_annotations
        else:
            annotations_changed = True
            
        # Process selections and ensure consistency
        new_records = edited_annotations.to_dict('records')
        for record in new_records:
            # Ensure flags is always a list
            if 'flags' not in record or record['flags'] is None:
                record['flags'] = []
                
            # Make sure all flag values are strings (not dictionaries or other types)
            record['flags'] = [str(flag) for flag in record['flags']]
        
        # Save the edited annotations back to session state
        st.session_state.image_annotations[image_key] = new_records

        # Display current annotation status
        st.caption(f"Annotating: {os.path.basename(current_filepath)}")
        
        # Auto-save annotations if they have changed
        if annotations_changed:
            # Set a flag to indicate annotations have changed but not yet saved to disk
            if 'unsaved_changes' not in st.session_state:
                st.session_state.unsaved_changes = True
                
            # Record interaction for annotation timer
            from phenotag.ui.components.annotation_timer import annotation_timer
            annotation_timer.record_interaction()
        
        # Add status indicator and save timestamp
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = None

    with save_col:
        # Show save status
        if st.session_state.get('unsaved_changes', False):
            st.warning("You have unsaved changes", icon="⚠️")
        elif st.session_state.last_save_time:
            last_save = st.session_state.last_save_time.strftime("%H:%M:%S") if st.session_state.last_save_time else "Never"
            st.success(f"All changes saved at {last_save}", icon="✅")
        
        # Setup auto-save if enabled
        auto_save = st.checkbox("Enable auto-save", value=True, 
                            help="Automatically save annotations every 60 seconds")
        if auto_save and st.session_state.get('unsaved_changes', False):
            # Add a placeholder for auto-save countdown
            if 'auto_save_time' not in st.session_state:
                st.session_state.auto_save_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
            
            # Calculate time until auto-save
            now = datetime.datetime.now()
            if now >= st.session_state.auto_save_time:
                # Time to auto-save
                save_all_annotations()
                st.session_state.unsaved_changes = False
                st.session_state.last_save_time = now
                st.session_state.auto_save_time = now + datetime.timedelta(seconds=60)
                st.rerun()
            else:
                # Show countdown
                seconds_left = int((st.session_state.auto_save_time - now).total_seconds())
                if seconds_left > 0:
                    st.caption(f"Auto-save in {seconds_left} seconds...")
    
        # Show elapsed annotation time
    
        if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
            from phenotag.ui.components.annotation_timer import annotation_timer
            current_day = st.session_state.annotation_timer_current_day
            formatted_time = annotation_timer.get_formatted_time(current_day)
            
            st.metric(
                "Annotation Time",
                formatted_time,
                help="Total time spent annotating this day (HH:MM:SS)",
                delta=None,
                delta_color="off"
            )
    
        # Add buttons for saving and resetting 
    
        save_label = "Save Now" if st.session_state.get('unsaved_changes', False) else "Save All"
        if st.button(save_label, use_container_width=True):
            save_all_annotations()
            st.session_state.unsaved_changes = False
            st.session_state.last_save_time = datetime.datetime.now()
            if 'auto_save_time' in st.session_state:
                st.session_state.auto_save_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
            st.rerun()
        
        # Create a dropdown menu for reset options
        reset_option = st.selectbox(
            "Reset Options",
            ["Reset Current", "Reset All"],
            label_visibility="collapsed"
        )
        
        if st.button("Apply Reset", use_container_width=True):
            if reset_option == "Reset Current":
                # Remove annotations for current image
                if image_key in st.session_state.image_annotations:
                    del st.session_state.image_annotations[image_key]
                    st.session_state.unsaved_changes = True
                st.rerun()
            elif reset_option == "Reset All":
                # Clear all annotations
                st.session_state.image_annotations = {}
                st.session_state.unsaved_changes = True
                st.rerun()


def save_all_annotations():
    """Save all image annotations to YAML files."""
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
                        annotation_time_minutes = annotation_timer.get_elapsed_time_minutes(doy)

                        # Save annotations to YAML file
                        annotations_data = {
                            "created": datetime.datetime.now().isoformat(),
                            "day_of_year": doy,
                            "station": st.session_state.selected_station,
                            "instrument": st.session_state.selected_instrument,
                            "annotation_time_minutes": annotation_time_minutes,
                            "annotations": day_annotations
                        }

                        # Save using the utility function
                        save_yaml(annotations_data, annotations_file)
                        print(f"Saved annotations to {annotations_file} (annotation time: {annotation_time_minutes:.2f} minutes)")
                        
                        # Update status cache if it exists
                        try:
                            if 'annotation_status_map' in st.session_state:
                                # Extract month from day number
                                selected_year = st.session_state.selected_year if 'selected_year' in st.session_state else None
                                date = datetime.datetime.strptime(f"{selected_year}-{doy}", "%Y-%j") if selected_year else datetime.datetime.now()
                                month = date.month
                                
                                # Create status key
                                status_key = f"{st.session_state.selected_station}_{st.session_state.selected_instrument}_{selected_year}_{month}"
                                
                                # Update or create cache entry
                                if status_key not in st.session_state.annotation_status_map:
                                    st.session_state.annotation_status_map[status_key] = {}
                                    
                                # Mark this day as completed in cache
                                st.session_state.annotation_status_map[status_key][doy] = 'completed'
                                print(f"Updated annotation status cache for day {doy}")
                                
                                # Also update status for historical view if needed
                                if 'historical_year' in st.session_state and 'historical_month' in st.session_state:
                                    # Create historical status key
                                    hist_status_key = f"{st.session_state.selected_station}_{st.session_state.selected_instrument}_{st.session_state.historical_year}_{st.session_state.historical_month}"
                                    
                                    # Only update if the day is from the historical month/year
                                    hist_year = int(st.session_state.historical_year)
                                    hist_month = st.session_state.historical_month
                                    
                                    if hist_year == int(selected_year) and hist_month == month:
                                        # Update historical cache
                                        if hist_status_key not in st.session_state.annotation_status_map:
                                            st.session_state.annotation_status_map[hist_status_key] = {}
                                            
                                        st.session_state.annotation_status_map[hist_status_key][doy] = 'completed'
                                        print(f"Updated historical annotation status cache for day {doy}")
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
            st.success(f"Saved annotations for {saved_count} images across {len(annotations_by_day)} days!")
        else:
            st.warning("No valid images to save annotations for.")
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
        return
        
    try:
        # Initialize image_annotations if it doesn't exist
        if 'image_annotations' not in st.session_state:
            st.session_state.image_annotations = {}
            
        # Get the directory where we expect to find the annotations file
        img_dir = os.path.dirname(daily_filepaths[0])
        annotations_file = os.path.join(img_dir, f"annotations_{selected_day}.yaml")
        
        # Import the annotation timer
        from phenotag.ui.components.annotation_timer import annotation_timer
        
        # Start the timer for this day
        annotation_timer.start_timer(selected_day)
        
        # We'll now always load annotations from disk to ensure we have the latest data
        # This is important when switching between tabs or when annotations are modified
        print(f"Attempting to load annotations for day {selected_day} from disk")

        # If annotations file exists, load it
        if os.path.exists(annotations_file):
            print(f"Loading annotations from file: {annotations_file}")
            with open(annotations_file, 'r') as f:
                import yaml
                annotation_data = yaml.safe_load(f)
                
                # Load previous annotation time if available
                if 'annotation_time_minutes' in annotation_data:
                    previous_time = annotation_data['annotation_time_minutes']
                    print(f"Loading previous annotation time: {previous_time:.2f} minutes")
                    
                    # Set the previous time as accumulated time for this day
                    annotation_timer.set_accumulated_time(selected_day, previous_time)

                # Clear existing annotations for files in this day
                # (to avoid mixing with annotations from other days)
                for filepath in daily_filepaths:
                    if filepath in st.session_state.image_annotations:
                        del st.session_state.image_annotations[filepath]

                if 'annotations' in annotation_data:
                    # Convert the loaded annotations to our format
                    loaded_count = 0
                    for img_name, img_annotations in annotation_data['annotations'].items():
                        # Find the full path for this filename
                        for filepath in daily_filepaths:
                            if os.path.basename(filepath) == img_name:
                                # Store annotations using full path as key
                                st.session_state.image_annotations[filepath] = img_annotations
                                loaded_count += 1
                                break
                    
                    print(f"Loaded annotations for {loaded_count} images from {annotations_file}")

                # Show notification that annotations were loaded
                st.toast(f"Loaded annotations for day {selected_day}", icon="✅")
        else:
            print(f"No annotations file found for day {selected_day} at {annotations_file}")
    except Exception as e:
        print(f"Error loading annotations for day change: {e}")