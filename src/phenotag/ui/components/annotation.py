"""
Annotation component for PhenoTag UI.

This module provides functionality for annotating images, including
ROI management and quality flag assignment.
"""
import os
import streamlit as st
import datetime
import pandas as pd

from phenotag.config import load_config_files
from phenotag.io_tools import save_yaml

# Import ROI utilities
from phenotag.ui.components.roi_utils import serialize_polygons, deserialize_polygons


def display_annotation_panel(current_filepath):
    """
    Display and manage ROI annotation panel.
    
    Args:
        current_filepath (str): Path to the current image
    """
    if not current_filepath:
        return
    
    # Create a unique key for this image
    image_key = current_filepath
    
    # Show ROI annotation editor when an image is selected
    st.divider()
    st.subheader("ROI Annotations")

    # Get list of ROI names from loaded ROIs
    roi_names = []
    if 'instrument_rois' in st.session_state and st.session_state.instrument_rois:
        roi_names = list(st.session_state.instrument_rois.keys())

    # Load config for quality flags
    config = load_config_files()
    
    # Create a list of all quality flags from flags.yaml
    flag_options = []
    for flag_key, flag_data in config.get('flags', {}).items():
        # Skip any non-flag entries
        if not isinstance(flag_data, dict) or 'category' not in flag_data:
            continue
        # Create a nice display name with category
        display_name = f"{flag_key[6:] if flag_key.startswith('iflag_') else flag_key} ({flag_data.get('category', 'Other')})"
        flag_options.append({"value": flag_key, "label": display_name})

    # Sort flags by category for better organization
    flag_options.sort(key=lambda x: x['label'])

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
                "has_flags": False,  # Empty string for no selection
            }
        ]

        # Add a row for each custom ROI
        for roi_name in roi_names:
            annotation_data.append({
                "roi_name": roi_name,
                "discard": False,
                "snow_presence": False,
                "has_flags": False,  # Empty string for no selection
            })
            
        # Debug message for new annotations
        print(f"Created new default annotations for {os.path.basename(image_key)}")
    else:
        # Use existing annotations
        annotation_data = st.session_state.image_annotations[image_key]
        print(f"Loaded existing annotations for {os.path.basename(image_key)}")

    # Convert to DataFrame
    annotation_df = pd.DataFrame(annotation_data)
    
    # Add batch update controls
    st.divider()
    
    st.write("**Batch Update Controls**")
    st.caption("Use these controls to set flags for all ROIs at once")
    
    # All ROIs: discard checkbox
    if 'all_discard' not in st.session_state:
        st.session_state.all_discard = False
    
    all_discard = st.checkbox(
        "All ROIs: discard",
        value=st.session_state.all_discard,
        key="all_discard_checkbox",
        help="Set discard flag for all ROIs in this image")
    
    # Update session state when checkbox changes
    if all_discard != st.session_state.all_discard:
        st.session_state.all_discard = all_discard
    
    # All ROIs: snow checkbox
    if 'all_snow' not in st.session_state:
        st.session_state.all_snow = False
    
    all_snow = st.checkbox(
        "All ROIs: snow",
        value=st.session_state.all_snow,
        key="all_snow_checkbox",
        help="Set snow presence flag for all ROIs in this image")
    
    # Update session state when checkbox changes
    if all_snow != st.session_state.all_snow:
        st.session_state.all_snow = all_snow
    
    # All ROIs: flags checkbox
    if 'all_flags' not in st.session_state:
        st.session_state.all_flags = False
    
    all_flags = st.checkbox(
        "All ROIs: flags",
        value=st.session_state.all_flags,
        key="all_flags_checkbox",
        help="Set quality flag for all ROIs in this image")
    
    # Update session state when checkbox changes
    if all_flags != st.session_state.all_flags:
        st.session_state.all_flags = all_flags
    
    # Button to apply batch updates
    if st.button("Apply to All ROIs", use_container_width=True):
        if image_key in st.session_state.image_annotations:
            # Update all rows in the annotations
            for row in st.session_state.image_annotations[image_key]:
                row['discard'] = st.session_state.all_discard
                row['snow_presence'] = st.session_state.all_snow
                row['has_flags'] = st.session_state.all_flags
            # Force a rerun to update the data editor
            st.rerun()

    # Show the data editor with custom configuration
    edited_annotations = st.data_editor(
        annotation_df,
        column_config={
            "roi_name": st.column_config.TextColumn(
                "ROI Name",
                help="Region of Interest name",
                width="medium",
                disabled=True
            ),
            "discard": st.column_config.CheckboxColumn(
                "Discard",
                help="Mark this ROI as not suitable for analysis",
                width="small",
            ),
            "snow_presence": st.column_config.CheckboxColumn(
                "Snow Present",
                help="Mark if snow is present in this ROI",
                width="small",
            ),
            "has_flags": st.column_config.CheckboxColumn(
                "Quality Flag",
                help="Mark if a quality flag is present for this ROI",
                width="large",
                # options=[option["label"] for option in flag_options],
            ),
        },
        hide_index=True,
        num_rows="dynamic",
        key=f"roi_annotations_{image_key}",
        use_container_width=True
    )

    # Check if annotations have changed
    if image_key in st.session_state.image_annotations:
        old_annotations = st.session_state.image_annotations[image_key]
        new_annotations = edited_annotations.to_dict('records')
        
        # Compare if anything has changed
        annotations_changed = old_annotations != new_annotations
    else:
        annotations_changed = True
    
    # Save the edited annotations back to session state
    st.session_state.image_annotations[image_key] = edited_annotations.to_dict('records')

    # Display current annotation status
    st.caption(f"Annotating: {os.path.basename(current_filepath)}")
    
    # Auto-save annotations if they have changed
    if annotations_changed:
        # Set a flag to indicate annotations have changed but not yet saved to disk
        if 'unsaved_changes' not in st.session_state:
            st.session_state.unsaved_changes = True
    
    # Add status indicator and save timestamp
    if 'last_save_time' not in st.session_state:
        st.session_state.last_save_time = None
    
    # Show save status
    status_col, button_col1, button_col2 = st.columns([2, 1, 1])
    with status_col:
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
            import datetime
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
    
    # Add buttons for saving and resetting 
    with button_col1:
        save_label = "Save Now" if st.session_state.get('unsaved_changes', False) else "Save All"
        if st.button(save_label, use_container_width=True):
            save_all_annotations()
            st.session_state.unsaved_changes = False
            st.session_state.last_save_time = datetime.datetime.now()
            if 'auto_save_time' in st.session_state:
                st.session_state.auto_save_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
            st.rerun()
    
    with button_col2:
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

                        # Save annotations to YAML file
                        annotations_data = {
                            "created": datetime.datetime.now().isoformat(),
                            "day_of_year": doy,
                            "station": st.session_state.selected_station,
                            "instrument": st.session_state.selected_instrument,
                            "annotations": day_annotations
                        }

                        # Save using the utility function
                        save_yaml(annotations_data, annotations_file)
                        print(f"Saved annotations to {annotations_file}")
                        break

        # Update session state to indicate changes are saved
        if 'unsaved_changes' in st.session_state:
            st.session_state.unsaved_changes = False
            
        # Update last save time
        import datetime
        st.session_state.last_save_time = datetime.datetime.now()

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
        
        # Track if we already have annotations for this day's files
        existing_annotations = False
        for filepath in daily_filepaths:
            if filepath in st.session_state.image_annotations:
                existing_annotations = True
                break
                
        # Skip loading if we already have annotations for this day's files
        # This prevents unnecessary file reading operations
        if existing_annotations:
            print(f"Already have annotations for day {selected_day} in session state")
            return

        # If annotations file exists, load it
        if os.path.exists(annotations_file):
            print(f"Loading annotations from file: {annotations_file}")
            with open(annotations_file, 'r') as f:
                import yaml
                annotation_data = yaml.safe_load(f)

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