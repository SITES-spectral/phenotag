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
        # Add debug info
        print(f"Annotation data type: {type(annotation_data)}")
        print(f"Annotation data contains {len(annotation_data)} items")
        if len(annotation_data) > 0:
            print(f"First item type: {type(annotation_data[0])}")
            print(f"First item keys: {annotation_data[0].keys() if isinstance(annotation_data[0], dict) else 'Not a dict'}")
            
        if not isinstance(annotation_data, list):
            print(f"WARNING: annotations are not in list format. Converting to list...")
            # Try to convert to list format
            try:
                if isinstance(annotation_data, dict):
                    converted_data = []
                    for roi_name, roi_data in annotation_data.items():
                        if isinstance(roi_data, dict):
                            roi_data['roi_name'] = roi_name
                            converted_data.append(roi_data)
                    annotation_data = converted_data
                    # Update in session state
                    st.session_state.image_annotations[image_key] = annotation_data
                    print(f"Successfully converted annotations to list format with {len(annotation_data)} items")
            except Exception as e:
                print(f"Error converting annotations: {str(e)}")

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
                
                # Initialize key variables
                roi00_apply_key = f"apply_all_ROI_00_{image_key}"
                roi00_flags_key = f"roi00_flags_{image_key}"
                roi00_discard_key = f"roi00_discard_{image_key}"
                roi00_snow_key = f"roi00_snow_{image_key}"
                
                # Default to current flags and settings
                current_flags = roi_data.get("flags", [])
                current_discard = roi_data.get("discard", False)
                current_snow = roi_data.get("snow_presence", False)
                
                # We no longer apply settings automatically from ROI_00 at render time
                # This is now handled as a one-time copy operation when the button is clicked
                # Each ROI maintains its own state after the copy
                apply_from_roi00 = False
                
                # Set default apply_to_all flag
                apply_to_all = False
                if roi_name == "ROI_00":
                    # Get the apply_all state from session
                    apply_to_all = st.session_state.get(f"apply_all_{roi_key}", False)
                
                with roi_col1:
                    # Create checkbox for discard
                    discard = st.checkbox(
                        "Discard", 
                        value=current_discard,
                        key=f"discard_{roi_key}",
                        help="Mark this image/ROI as not suitable for analysis"
                    )
                    
                    # Create checkbox for snow presence
                    snow_presence = st.checkbox(
                        "Snow Present", 
                        value=current_snow,
                        key=f"snow_{roi_key}",
                        help="Mark if snow is present in this ROI"
                    )
                
                with roi_col2:
                    # Create multiselect for flags with categories
                    # Flatten the options for the multiselect
                    multiselect_options = []
                    for category in sorted(flags_by_category.keys()):
                        multiselect_options.extend(flags_by_category[category])
                    
                    # We no longer show the ROI_00 indicator since settings are now independent
                    
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
                
                # Now add the "Apply to all ROIs" button after both columns
                # to ensure selected_flags is already defined
                # Store the selected flags and settings for ALL ROIs
                updated_flag_selections[roi_name] = {
                    "discard": discard,
                    "snow_presence": snow_presence,
                    "flags": selected_flags,
                    "apply_to_all": apply_to_all if roi_name == "ROI_00" else False
                }
                
                # ROI_00 specific actions
                if roi_name == "ROI_00":
                    # Add checkboxes for what to copy - all False by default
                    st.caption("Choose which settings to copy to other ROIs:")
                    copy_cols = st.columns(3)
                    with copy_cols[0]:
                        st.checkbox("Copy Flags", value=False, key=f"copy_flags_{roi_key}")
                    with copy_cols[1]:
                        st.checkbox("Copy Discard", value=False, key=f"copy_discard_{roi_key}")
                    with copy_cols[2]:
                        st.checkbox("Copy Snow", value=False, key=f"copy_snow_{roi_key}")
                    
                    # Create a button to apply ROI_00 settings to all other ROIs
                    if st.button(
                        "Copy Selected ROI_00 Settings to All ROIs", 
                        key=f"apply_all_button_{roi_key}",
                        help="Copy the selected settings (flags, discard, snow) from ROI_00 to all other ROIs. This is a one-time copy that still allows individual ROI customization.",
                        type="primary",
                        use_container_width=True
                    ):
                        try:
                            # Directly update the annotations for all other ROIs in memory
                            # Get current annotations for this image
                            if image_key in st.session_state.image_annotations:
                                current_annotations = st.session_state.image_annotations[image_key]
                                
                                # Log the settings being applied
                                print(f"[ROI_00 Settings] Applying settings to all ROIs for {os.path.basename(image_key)}")
                                print(f"[ROI_00 Settings] Flags: {selected_flags}")
                                print(f"[ROI_00 Settings] Discard: {discard}")
                                print(f"[ROI_00 Settings] Snow Presence: {snow_presence}")
                                
                                # Update annotations for all ROIs except ROI_00
                                for anno in current_annotations:
                                    if anno.get("roi_name") != "ROI_00":
                                        # Only update the fields the user wants (based on checkboxes)
                                        if st.session_state.get(f"copy_flags_{roi_key}", True):
                                            anno["flags"] = selected_flags.copy()
                                        if st.session_state.get(f"copy_discard_{roi_key}", True):
                                            anno["discard"] = discard
                                        if st.session_state.get(f"copy_snow_{roi_key}", True):
                                            anno["snow_presence"] = snow_presence
                                
                                # Store updated annotations back to session state
                                st.session_state.image_annotations[image_key] = current_annotations
                            
                            # We no longer need to set a persistent flag - this will just be a one-time operation
                            # that copies the current ROI_00 settings to the other ROIs without locking them
                            print(f"[ROI_00 Settings] This is now a one-time copy operation (no persistent lock)")
                            
                            # Clear any existing apply flags to ensure they don't persist
                            if roi00_apply_key in st.session_state:
                                del st.session_state[roi00_apply_key]
                                print(f"[ROI_00 Settings] Cleared ROI_00 apply flag: {roi00_apply_key}")
                            
                            # Get the list of ROIs that will receive these settings
                            affected_rois = [r for r in all_roi_names if r != "ROI_00"]
                            print(f"[ROI_00 Settings] Settings will be applied to {len(affected_rois)} ROIs: {', '.join(affected_rois)}")
                            
                            # Save annotations to ensure they're persisted
                            try:
                                print(f"[ROI_00 Settings] Saving annotations...")
                                save_all_annotations(force_save=True)
                                print(f"[ROI_00 Settings] Annotations saved successfully")
                            except Exception as save_error:
                                print(f"[ROI_00 Settings] Error during save: {str(save_error)}")
                                st.error(f"Error saving annotations: {str(save_error)}", icon="⚠️")
                                # Continue with the process even if save fails
                            
                            # Show a success message with details on what was copied
                            roi_count = len(affected_rois)
                            copied_items = []
                            if st.session_state.get(f"copy_flags_{roi_key}", True):
                                copied_items.append("flags")
                            if st.session_state.get(f"copy_discard_{roi_key}", True):
                                copied_items.append("discard status")
                            if st.session_state.get(f"copy_snow_{roi_key}", True):
                                copied_items.append("snow presence")
                                
                            copied_str = ", ".join(copied_items)
                            st.success(f"Copied ROI_00 {copied_str} to {roi_count} other ROIs and saved", icon="✅")
                            
                            # Force a rerun to update all tabs
                            print(f"[ROI_00 Settings] Waiting briefly before UI refresh...")
                            time.sleep(1)  # Brief pause to ensure save completes
                            print(f"[ROI_00 Settings] Triggering UI refresh...")
                            st.rerun()
                        except Exception as e:
                            # Provide detailed error information
                            print(f"[ROI_00 Settings] ERROR: {str(e)}")
                            
                            # Show error message to user
                            st.error(f"Error applying ROI_00 settings: {str(e)}", icon="⚠️")
                            
                            # Try to reset the state to prevent issues
                            try:
                                st.session_state[f"apply_all_{roi_key}"] = False
                                st.session_state[roi00_apply_key] = False
                                print(f"[ROI_00 Settings] Reset apply flags after error")
                            except Exception:
                                pass
                                                
                # Show current flags
                if not selected_flags:
                    st.info("No flags selected for this ROI", icon="ℹ️")
                
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
                    
                    # Each ROI now maintains its own settings after the copy operation
                    # from ROI_00, so we just use the current selections directly
                    display_flags = selections["flags"]
                    display_discard = selections["discard"]
                    display_snow = selections["snow_presence"]
                    
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
                        "Discard": "Yes" if display_discard else "No",
                        "Snow Present": "Yes" if display_snow else "No",
                        "Flag Count": len(display_flags),
                        "Flags": flags_str
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
                        "Flags": st.column_config.TextColumn("Flags", width="large")
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
            else:
                st.info("No annotation data available for summary")
        
        # Convert the UI state to a dataframe for processing
        edited_data = []
        for idx, roi_name in enumerate(all_roi_names):
            if roi_name in updated_flag_selections:
                selections = updated_flag_selections[roi_name]
                
                # Each ROI now maintains its own settings independently
                # Just use the current selections directly
                roi_flags = selections["flags"]
                roi_discard = selections["discard"]
                roi_snow = selections["snow_presence"]
                
                # Build the ROI data with all settings
                edited_data.append({
                    "roi_name": roi_name,
                    "discard": roi_discard,
                    "snow_presence": roi_snow,
                    "flags": roi_flags
                })
            else:
                # Fallback to original data if not updated
                edited_data.append(annotation_data[idx])
        
        # Convert to DataFrame for further processing
        edited_annotations = pd.DataFrame(edited_data)

        # Check if annotations have changed - using normalized comparison
        if image_key in st.session_state.image_annotations:
            old_annotations = st.session_state.image_annotations[image_key]
            new_annotations = edited_annotations.to_dict('records')
            
            # Normalize and compare annotations to avoid false change detection
            def normalize_annotations(annotations):
                if not annotations:
                    return []
                result = []
                for item in sorted(annotations, key=lambda x: x.get('roi_name', '')):
                    normalized = item.copy()
                    # Ensure flags is always a sorted list of strings 
                    if 'flags' in normalized:
                        normalized['flags'] = sorted([str(flag) for flag in (normalized['flags'] or [])])
                    # Remove any temporary keys used for UI purposes
                    if '_flag_selector' in normalized:
                        del normalized['_flag_selector']
                    result.append(normalized)
                return result
            
            old_normalized = normalize_annotations(old_annotations)
            new_normalized = normalize_annotations(new_annotations)
            
            # Deep comparison of annotations
            def deep_compare_annotations(old, new):
                if len(old) != len(new):
                    print(f"Different number of annotations: {len(old)} vs {len(new)}")
                    return True
                
                # Compare each annotation by ROI
                for old_item, new_item in zip(old, new):
                    # Check all basic fields except flags
                    for key in set(old_item.keys()) & set(new_item.keys()):
                        if key != 'flags':
                            if old_item.get(key) != new_item.get(key):
                                print(f"Change detected in {key}: {old_item.get(key)} -> {new_item.get(key)}")
                                return True
                    
                    # Check flags separately (as sets to ignore order)
                    old_flags = set(old_item.get('flags', []))
                    new_flags = set(new_item.get('flags', []))
                    if old_flags != new_flags:
                        print(f"Flags changed for {old_item.get('roi_name')}: {old_flags} -> {new_flags}")
                        return True
                
                return False  # No changes detected
            
            # Perform the deep comparison
            annotations_changed = deep_compare_annotations(old_normalized, new_normalized)
            
            if annotations_changed:
                print(f"Detected changes in annotations for {os.path.basename(image_key)}")
            else:
                print(f"No changes detected in annotations for {os.path.basename(image_key)}")
        else:
            annotations_changed = True
            print(f"New annotations created for {os.path.basename(image_key)}")
            
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
        
        # Handle changes to annotations
        if annotations_changed:
            # Check if the annotations were just loaded (in which case, don't auto-save)
            just_loaded = st.session_state.get('annotations_just_loaded', False)
            
            if just_loaded:
                # Clear the just_loaded flag
                st.session_state.annotations_just_loaded = False
                print(f"Annotations were just loaded - not marking as changed yet")
                
                # Update the UI but don't trigger auto-save
                if 'unsaved_changes' in st.session_state:
                    st.session_state.unsaved_changes = False
            else:
                # This is a real user change, not just a load operation
                # Set a flag to indicate annotations have changed
                if 'unsaved_changes' not in st.session_state:
                    st.session_state.unsaved_changes = True
                    
                # Record interaction for annotation timer
                from phenotag.ui.components.annotation_timer import annotation_timer
                annotation_timer.record_interaction()
                
                # Get auto-save settings
                auto_save_enabled = st.session_state.get('auto_save_enabled', True)
                immediate_save_enabled = st.session_state.get('immediate_save_enabled', True)
                
                # If immediate saving is enabled, save annotations right away
                if auto_save_enabled and immediate_save_enabled:
                    # Save annotations immediately without waiting for timeout
                    save_all_annotations()
                    st.session_state.unsaved_changes = False
                    st.session_state.last_save_time = datetime.datetime.now()
                    if 'auto_save_time' in st.session_state:
                        # Reset the auto-save timer
                        st.session_state.auto_save_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
        
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
        
        # Initialize auto-save settings if not already set
        # Default to disabled auto-save per user request
        if 'auto_save_enabled' not in st.session_state:
            st.session_state.auto_save_enabled = False
        if 'immediate_save_enabled' not in st.session_state:
            st.session_state.immediate_save_enabled = False
        
        # Display a warning about auto-save being disabled
        if st.session_state.get('unsaved_changes', False):
            st.warning("⚠️ You have unsaved changes. Use the 'Save Now' button to save your work.")
            
        # Show information about when to save
        st.info("Remember to save your annotations before switching to another day or closing the application.", icon="ℹ️")
            
        # Create a prominent save button
        if st.button("💾 Save Annotations", 
                    type="primary", 
                    use_container_width=True,
                    help="Save all annotations to disk"):
            with st.spinner("Saving annotations..."):
                save_all_annotations(force_save=True)
                st.session_state.unsaved_changes = False
                st.session_state.last_save_time = datetime.datetime.now()
                st.rerun()
        
        # Add option to re-enable auto-save if user wants it
        with st.expander("Auto-save settings (advanced)"):
            # Create checkbox widgets for auto-save settings
            auto_save = st.checkbox("Enable auto-save", 
                            value=st.session_state.auto_save_enabled,
                            help="Automatically save annotations every 60 seconds",
                            key=f"auto_save_enabled_{image_key}")
            
            immediate_save = st.checkbox("Save immediately on changes", 
                                    value=st.session_state.immediate_save_enabled,
                                    help="Automatically save annotations immediately when changes are made",
                                    key=f"immediate_save_enabled_{image_key}")
            
            # Update session state from widget values
            st.session_state.auto_save_enabled = auto_save
            st.session_state.immediate_save_enabled = immediate_save
            
            # Handle timed auto-save if enabled (and immediate save is not active or didn't catch all changes)
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
    
        # Show elapsed annotation time here (moved up from below)
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

                        # Create basic annotations data structure
                        annotations_data = {
                            "created": existing_data.get("created", datetime.datetime.now().isoformat()),
                            "day_of_year": doy,
                            "year": selected_year,  # Include the year in metadata
                            "station": st.session_state.selected_station,
                            "instrument": st.session_state.selected_instrument,
                            "annotation_time_minutes": total_annotation_time,
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
                                    save_status_to_l1_parent(
                                        current_base_dir,
                                        st.session_state.selected_station,
                                        st.session_state.selected_instrument,
                                        selected_year,
                                        month,
                                        doy,
                                        'completed'
                                    )
                                    print(f"Saved annotation status to L1 parent folder for day {doy}")
                                except Exception as status_error:
                                    print(f"Error saving status to L1 parent: {str(status_error)}")
                                
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
            st.toast(f"Saved annotations for {saved_count} images across {len(annotations_by_day)} days!", icon="✅")
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
        return
        
    # Set loading flag to prevent concurrent saves while loading
    st.session_state.loading_annotations = True
    
    # Create a placeholder for the loading indicator
    with st.spinner(f"Loading annotations for day {selected_day}..."):
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
                        # Only if we don't already have accumulated time (to avoid double-counting)
                        current_accumulated = annotation_timer.get_accumulated_time(selected_day)
                        if current_accumulated == 0:
                            annotation_timer.set_accumulated_time(selected_day, previous_time)
                            print(f"Set accumulated time to previous time: {previous_time:.2f} minutes")
                        else:
                            print(f"Already have accumulated time: {current_accumulated:.2f} minutes. Not setting to previous: {previous_time:.2f}")

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
                                    # Make sure img_annotations is in the expected format
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
                                            
                                            # Make sure flags is a list of strings
                                            processed_anno['flags'] = [str(flag) for flag in processed_anno['flags']]
                                            
                                            # Add to processed list
                                            processed_annotations.append(processed_anno)
                                        
                                        # After processing, store the annotations
                                        st.session_state.image_annotations[filepath] = processed_annotations
                                        
                                        # Now, directly set the widget states
                                        for anno in processed_annotations:
                                            roi_name = anno.get('roi_name')
                                            roi_key = f"{roi_name}_{filepath}"
                                            
                                            # IMPORTANT: We don't set session state directly for widgets anymore
                                            # as it causes a Streamlit warning. Instead, we'll use the default values
                                            # when creating the widgets. The annotation data is already stored in
                                            # st.session_state.image_annotations, which is used to set the defaults
                                            # when creating the widgets.
                                            pass
                                            
                                            # Old approach that caused warnings:
                                            # flags_key = f"flags_{roi_key}"
                                            # st.session_state[flags_key] = anno.get('flags', [])
                                            # discard_key = f"discard_{roi_key}"
                                            # st.session_state[discard_key] = anno.get('discard', False)
                                            # snow_key = f"snow_{roi_key}"
                                            # st.session_state[snow_key] = anno.get('snow_presence', False)
                                        
                                        loaded_count += 1
                                        print(f"Loaded annotations for image: {img_name} - {len(processed_annotations)} ROIs")
                                        break
                                    
                            # If we didn't find a match, try to convert the format if needed
                            try:
                                converted_annotations = []
                                if isinstance(img_annotations, dict):
                                    # If it's a dict of ROIs, convert to list
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
                                                
                                            # Make sure flags is a list of strings
                                            processed_anno['flags'] = [str(flag) for flag in processed_anno['flags']]
                                            
                                            converted_annotations.append(processed_anno)
                                        else:
                                            print(f"Warning: Unexpected ROI data format for {roi_name}: {type(roi_data)}")
                                    
                                    if converted_annotations:
                                        for filepath in daily_filepaths:
                                            if os.path.basename(filepath) == img_name:
                                                st.session_state.image_annotations[filepath] = converted_annotations
                                                
                                                # We don't need to set widget states directly anymore
                                                # The annotation data is already stored in st.session_state.image_annotations
                                                # and will be used as defaults when creating the widgets
                                                
                                                # Old approach that caused warnings:
                                                # for anno in converted_annotations:
                                                #     roi_name = anno.get('roi_name')
                                                #     roi_key = f"{roi_name}_{filepath}"
                                                #     st.session_state[f"flags_{roi_key}"] = anno.get('flags', [])
                                                #     st.session_state[f"discard_{roi_key}"] = anno.get('discard', False)
                                                #     st.session_state[f"snow_{roi_key}"] = anno.get('snow_presence', False)
                                                
                                                loaded_count += 1
                                                print(f"Converted and loaded annotations for image: {img_name} - {len(converted_annotations)} ROIs")
                                                break
                            except Exception as conv_error:
                                print(f"Error converting annotations for {img_name}: {str(conv_error)}")
                        
                        print(f"Loaded annotations for {loaded_count} images from {annotations_file}")
                        
                        # Set a flag to indicate annotations were loaded
                        st.session_state.annotations_just_loaded = True

                    # Show notification that annotations were loaded
                    st.success(f"Loaded annotations for day {selected_day}", icon="✅")
            else:
                print(f"No annotations file found for day {selected_day} at {annotations_file}")
        except Exception as e:
            print(f"Error loading annotations for day change: {e}")
            st.error(f"Error loading annotations: {e}", icon="❌")
        finally:
            # Always clear the loading flag
            st.session_state.loading_annotations = False