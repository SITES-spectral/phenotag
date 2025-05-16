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
import glob
from typing import List, Dict, Any, Tuple, Optional

from phenotag.config import load_config_files
from phenotag.io_tools import save_yaml

# Import ROI utilities
from phenotag.ui.components.roi_utils import serialize_polygons, deserialize_polygons
from phenotag.ui.components.flags_processor import FlagsProcessor

# Helper functions for annotation file management
def get_annotation_file_path(image_path: str) -> str:
    """
    Generate the file path for an image's annotation file.
    
    Args:
        image_path (str): Path to the image
        
    Returns:
        str: Path to the annotation file for this image
    """
    img_dir = os.path.dirname(image_path)
    img_filename = os.path.basename(image_path)
    # Remove file extension and add _annotations.yaml
    base_name = os.path.splitext(img_filename)[0]
    return os.path.join(img_dir, f"{base_name}_annotations.yaml")

def scan_day_annotation_files(day_dir: str) -> Dict[str, str]:
    """
    Scan a day directory for all annotation files.
    
    Args:
        day_dir (str): Path to the day directory
        
    Returns:
        dict: Dictionary mapping image filenames to annotation file paths
    """
    annotation_files = {}
    for file in glob.glob(os.path.join(day_dir, "*_annotations.yaml")):
        # Extract the base name of the annotation file
        annotation_filename = os.path.basename(file)
        base_name = annotation_filename.replace("_annotations.yaml", "")
        
        # Try to find the corresponding image file with different extensions
        for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
            img_filename = f"{base_name}{ext}"
            img_path = os.path.join(day_dir, img_filename)
            if os.path.exists(img_path):
                annotation_files[img_filename] = file
                break
    
    print(f"Found {len(annotation_files)} annotation files in {day_dir}")
    return annotation_files

def update_day_status_file(day_dir: str, images_data: Dict[str, Dict]) -> bool:
    """
    Update the day-level status file with aggregated information from all images.
    
    Args:
        day_dir (str): Path to the day directory
        images_data (dict): Dictionary with metadata from all image annotation files
        
    Returns:
        bool: Success status
    """
    # Extract day from directory name
    day = os.path.basename(day_dir)
    year_dir = os.path.dirname(day_dir)
    year = os.path.basename(year_dir)
    
    # Extract station and instrument from path
    # Path format: base_dir/station/phenocams/products/instrument/L1/year/day
    l1_dir = os.path.dirname(year_dir)  # L1 directory
    instrument_dir = os.path.dirname(l1_dir)  # Instrument directory
    instrument = os.path.basename(instrument_dir)
    products_dir = os.path.dirname(instrument_dir)  # Products directory
    phenocams_dir = os.path.dirname(products_dir)  # Phenocams directory
    station_dir = os.path.dirname(phenocams_dir)  # Station directory
    station = os.path.basename(station_dir)
    
    # Count expected images in the directory
    image_files = [f for f in os.listdir(day_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))]
    expected_count = len(image_files)
    
    # Count annotated images
    annotated_count = len(images_data)
    
    # Calculate completion percentage
    completion_percentage = (annotated_count / expected_count * 100) if expected_count > 0 else 0
    
    # Aggregated annotation time
    total_time = sum(data.get('annotation_time_minutes', 0) for data in images_data.values())
    
    # Create file status mapping
    file_status = {}
    for img_name, data in images_data.items():
        # Check if annotations exist for all ROIs
        annotations = data.get('annotations', [])
        all_annotated = True
        for roi in annotations:
            has_annotations = (
                roi.get('discard', False) or
                roi.get('snow_presence', False) or
                len(roi.get('flags', [])) > 0 or
                roi.get('not_needed', False)
            )
            if not has_annotations:
                all_annotated = False
                break
        
        # Set status based on annotation completeness
        file_status[img_name] = "completed" if all_annotated else "in_progress"
    
    # Create the status data
    status_data = {
        "created": datetime.datetime.now().isoformat(),
        "last_modified": datetime.datetime.now().isoformat(),
        "day_of_year": day,
        "year": year,
        "station": station,
        "instrument": instrument,
        "annotation_time_minutes": total_time,
        "expected_image_count": expected_count,
        "annotated_image_count": annotated_count,
        "completion_percentage": round(completion_percentage, 2),
        "file_status": file_status,
        "image_annotations": list(images_data.keys())
    }
    
    # Save the status file
    status_file_path = os.path.join(day_dir, f"day_status_{day}.yaml")
    try:
        save_yaml(status_data, status_file_path)
        print(f"Updated day status file: {status_file_path}")
        return True
    except Exception as e:
        print(f"Error updating day status file: {e}")
        return False

def migrate_day_annotations_to_per_image(day_annotations_file: str) -> List[str]:
    """
    Migrate a day-level annotations file to individual per-image files.
    
    Args:
        day_annotations_file (str): Path to the day annotations file
        
    Returns:
        list: Paths to the created per-image annotation files
    """
    # Load the day annotations
    try:
        with open(day_annotations_file, 'r') as f:
            day_data = yaml.safe_load(f)
            
        if not day_data:
            print(f"No data found in day annotations file: {day_annotations_file}")
            return []
            
        # Extract the common metadata
        common_metadata = {
            "created": day_data.get("created", datetime.datetime.now().isoformat()),
            "last_modified": datetime.datetime.now().isoformat(),
            "day_of_year": day_data.get("day_of_year", ""),
            "year": day_data.get("year", ""),
            "station": day_data.get("station", ""),
            "instrument": day_data.get("instrument", "")
        }
        
        created_files = []
        images_data = {}
        
        # Process each image's annotations
        if 'annotations' in day_data:
            for img_name, annotations in day_data['annotations'].items():
                # Create per-image annotation file
                img_dir = os.path.dirname(day_annotations_file)
                base_name = os.path.splitext(img_name)[0]
                img_annotation_file = os.path.join(img_dir, f"{base_name}_annotations.yaml")
                
                # Create image-specific metadata
                img_metadata = common_metadata.copy()
                img_metadata.update({
                    "filename": img_name,
                    "annotation_time_minutes": day_data.get("annotation_time_minutes", 0) / len(day_data['annotations']) if day_data.get("annotation_time_minutes") else 0,
                    "annotations": annotations,
                    "status": day_data.get("file_status", {}).get(img_name, "in_progress")
                })
                
                # Save the per-image annotation file
                save_yaml(img_metadata, img_annotation_file)
                
                created_files.append(img_annotation_file)
                
                # Store image data for day status update
                images_data[img_name] = img_metadata
            
            # Create or update the day status file
            update_day_status_file(os.path.dirname(day_annotations_file), images_data)
            
            print(f"Migrated {len(created_files)} annotation files from {day_annotations_file}")
            return created_files
        else:
            print(f"No annotations found in day file: {day_annotations_file}")
            return []
    
    except Exception as e:
        print(f"Error migrating day annotations: {e}")
        return []


def display_annotation_button(current_filepath):
    """
    Display a button that opens the annotation panel in a popover when clicked.
    
    Args:
        current_filepath (str): Path to the current image
    """
    if not current_filepath:
        print("Cannot display annotation button - no current filepath")
        return
    
    # Debug log for troubleshooting
    filename = os.path.basename(current_filepath)
    print(f"Displaying annotation button for image: {filename}")
    
    # Make sure image_annotations is initialized
    if 'image_annotations' not in st.session_state:
        print("WARNING: image_annotations not in session state, initializing it now")
        st.session_state.image_annotations = {}
    
    # Check if we have any annotations for this image in memory
    has_annotations_in_memory = current_filepath in st.session_state.image_annotations
    
    # Check if we have annotations on disk
    has_annotations_on_disk = False
    annotation_file_path = get_annotation_file_path(current_filepath)
    
    if os.path.exists(annotation_file_path):
        has_annotations_on_disk = True
        print(f"Found per-image annotation file on disk: {annotation_file_path}")
    else:
        # Check for legacy day-level annotations
        img_dir = os.path.dirname(current_filepath)
        current_day = os.path.basename(img_dir)
        img_filename = os.path.basename(current_filepath)
        old_annotations_file = os.path.join(img_dir, f"annotations_{current_day}.yaml")
        
        if os.path.exists(old_annotations_file):
            try:
                # Check if this specific image has annotations in the legacy file
                with open(old_annotations_file, 'r') as f:
                    day_data = yaml.safe_load(f)
                if day_data and 'annotations' in day_data and img_filename in day_data['annotations']:
                    has_annotations_on_disk = True
                    print(f"Found image in legacy day annotation file: {old_annotations_file}")
            except Exception as e:
                print(f"Error checking legacy annotation file: {str(e)}")
    
    # Combined annotation status (either in memory or on disk)
    has_annotations = has_annotations_in_memory or has_annotations_on_disk
    
    # Try to load annotations from disk if they're not in memory
    if not has_annotations_in_memory and has_annotations_on_disk:
        # First check for per-image annotation file
        if os.path.exists(annotation_file_path):
            print(f"Loading per-image annotation file into memory: {annotation_file_path}")
            try:
                # Load the annotation file
                with open(annotation_file_path, 'r') as f:
                    annotation_data = yaml.safe_load(f)
                
                if annotation_data and 'annotations' in annotation_data:
                    # Process annotations
                    annotations_list = annotation_data['annotations']
                    
                    # Normalize annotations
                    processed_annotations = []
                    for anno in annotations_list:
                        # Create a clean copy
                        processed_anno = anno.copy()
                        
                        # Ensure all fields exist
                        if 'roi_name' not in processed_anno:
                            processed_anno['roi_name'] = "ROI_00"
                        if 'discard' not in processed_anno:
                            processed_anno['discard'] = False
                        if 'snow_presence' not in processed_anno:
                            processed_anno['snow_presence'] = False
                        if 'flags' not in processed_anno or processed_anno['flags'] is None:
                            processed_anno['flags'] = []
                        if 'not_needed' not in processed_anno:
                            processed_anno['not_needed'] = False
                            
                        # Make sure flags is a list of strings
                        processed_anno['flags'] = [str(flag) for flag in processed_anno['flags']]
                        
                        # Add to processed list
                        processed_annotations.append(processed_anno)
                    
                    # Store in session state
                    st.session_state.image_annotations[current_filepath] = processed_annotations
                    has_annotations_in_memory = True
                    print(f"Loaded individual annotation file for {filename} into memory")
                else:
                    print(f"No annotation data found in file: {annotation_file_path}")
            except Exception as e:
                print(f"Error loading individual annotation file: {str(e)}")
        
        # If still no annotations in memory, check if old day file exists and load it
        if not has_annotations_in_memory:
            img_dir = os.path.dirname(current_filepath)
            current_day = os.path.basename(img_dir)
            old_annotations_file = os.path.join(img_dir, f"annotations_{current_day}.yaml")
            
            if os.path.exists(old_annotations_file):
                print(f"Loading legacy day annotation file: {old_annotations_file}")
                
                # Check if day is already loaded
                day_load_key = f"annotations_loaded_day_{current_day}"
                if not st.session_state.get(day_load_key, False):
                    print(f"Old-format annotations file exists but not loaded in memory. Will load all day annotations.")
                    
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
                    
                    # Load and potentially migrate all annotations for the day
                    load_day_annotations(current_day, daily_filepaths)
                    
                    # Check again if we have annotations for this image
                    has_annotations_in_memory = current_filepath in st.session_state.image_annotations
    
    # Always ensure we have temporary annotations for the annotation panel
    if not has_annotations_in_memory and not has_annotations_on_disk:
        # Create default annotations just for the annotation panel - don't save to disk yet
        create_default_annotations(current_filepath, use_temp_storage=False)
        print(f"Created default annotations for {filename} for annotation panel")

    # Show the annotation panel when the button is clicked
    show_annotation_panel(current_filepath)
        
    # Display annotation status below the button - only if no annotations exist anywhere
    if not has_annotations:
        st.warning("Not annotated", icon="⚠️")


def show_annotation_panel(current_filepath):
    """
    Display the annotation panel in a popover.
    
    Args:
        current_filepath (str): Path to the current image
    """
    # Get annotation timer to track activity
    from phenotag.ui.components.annotation_timer import annotation_timer
    
    # Initialize the timer state first to ensure it's available
    annotation_timer.initialize_session_state()
    
    # Create a unique key for this image
    image_key = current_filepath
    filename = os.path.basename(current_filepath)
    
    # Record user interaction when annotation is viewed
    annotation_timer.record_interaction()
    
    # Initialize temporary annotations if needed
    if 'temp_annotations' not in st.session_state:
        st.session_state.temp_annotations = {}
    
    # Initialize permanent storage if needed
    if 'image_annotations' not in st.session_state:
        st.session_state.image_annotations = {}
    
    # Ensure we have annotations in both storages for this image
    # Check permanent storage first
    in_permanent_storage = current_filepath in st.session_state.image_annotations
    in_temporary_storage = current_filepath in st.session_state.temp_annotations
    
    print(f"DEBUG: Annotations for {filename} - in permanent storage: {in_permanent_storage}, in temporary storage: {in_temporary_storage}")
    if in_permanent_storage:
        print(f"DEBUG: Permanent storage annotation data: {st.session_state.image_annotations[current_filepath]}")
    if in_temporary_storage:
        print(f"DEBUG: Temporary storage annotation data: {st.session_state.temp_annotations[current_filepath]}")
    
    # If in permanent but not temporary, copy to temporary
    if in_permanent_storage and not in_temporary_storage:
        # Deep copy to avoid reference issues
        import copy
        st.session_state.temp_annotations[current_filepath] = copy.deepcopy(
            st.session_state.image_annotations[current_filepath]
        )
        print(f"Copied annotations from permanent to temporary storage for {filename}")
    
    # If in temporary but not permanent, copy to permanent
    elif in_temporary_storage and not in_permanent_storage:
        # Deep copy to avoid reference issues
        import copy
        st.session_state.image_annotations[current_filepath] = copy.deepcopy(
            st.session_state.temp_annotations[current_filepath]
        )
        print(f"Copied annotations from temporary to permanent storage for {filename}")
    
    # If not in either storage, create default annotations in both
    elif not in_permanent_storage and not in_temporary_storage:
        # Create in permanent storage
        create_default_annotations(current_filepath, use_temp_storage=False)
        print(f"Created default annotations in permanent storage for {filename}")
        
        # Copy to temporary storage
        import copy
        st.session_state.temp_annotations[current_filepath] = copy.deepcopy(
            st.session_state.image_annotations[current_filepath]
        )
        print(f"Copied default annotations to temporary storage for {filename}")
    
    # Display the popover
    with st.popover(f'Annotation Panel - {filename}'):
        # Show image filename at the top for confirmation
        st.markdown(f"**Currently annotating:** {filename}")
        st.markdown("---")
        
        # Include the actual annotation interface first (will use temp storage)
        _create_annotation_interface(current_filepath, use_temp_storage=True)
        
        # Add separator after ROI tabs
        st.markdown("---")
        
        # Reset button removed as per user request
        
        # Add save button at the bottom
        save_key = f"final_save_annotations_{filename}"
        if st.button("💾 Save Annotations", key=save_key, type="primary", use_container_width=True):
            # Save the temporary annotations to permanent storage
            if current_filepath in st.session_state.temp_annotations:
                # Make sure image_annotations is initialized
                if 'image_annotations' not in st.session_state:
                    st.session_state.image_annotations = {}
                
                # Copy from temp to permanent storage and save directly
                import copy
                
                # First ensure the temporary annotations are updated with the latest UI values
                print(f"Saving annotations for {filename} - copying from temporary to permanent storage")
                st.session_state.image_annotations[current_filepath] = copy.deepcopy(
                    st.session_state.temp_annotations[current_filepath]
                )
                
                # Log the annotation data being saved
                print(f"Annotation data being saved: {st.session_state.image_annotations[current_filepath]}")
                
                # Save to disk explicitly - only triggered by Save button
                save_all_annotations(force_save=True)
                
                # Show success message
                st.success(f"Annotations for {filename} saved successfully!")
                st.toast(f"Annotations saved for {filename}", icon="✅")
            else:
                st.warning("No annotations to save")
        
        # Add a note about the Save button behavior
        st.caption("Note: Click the Save button to save your annotations, then click outside to close the panel.")


# This function has been replaced with display_annotation_button


def display_raw_annotation_button(station_name, instrument_id, year, day):
    """
    Display a button that opens a popover with the raw annotation data.
    
    Args:
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year
    """
    if not day:
        return
        
    # Create a unique key for the button
    button_key = f"view_raw_annotations_{day}"
    
    # Add some space before the button
    st.markdown("---")
    
    # Create the button to view raw annotations
    if st.button("📄 View Raw Annotation Data", key=button_key, use_container_width=True):
        # When the button is clicked, show the raw annotation data
        display_raw_annotation_data(station_name, instrument_id, year, day)


def display_raw_annotation_data(station_name, instrument_id, year, day):
    """
    Display the raw annotation data in a popover with tabs for dataframe and JSON views.
    
    Args:
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year
    """
    import json
    import yaml
    import pandas as pd
    import glob
    from io import StringIO
    
    # Find the day directory path
    if 'scan_info' in st.session_state:
        base_dir = st.session_state.scan_info.get('base_dir')
        if base_dir:
            day_dir = os.path.join(
                base_dir,
                station_name,
                "phenocams",
                "products",
                instrument_id,
                "L1",
                year,
                day
            )
            
            # Check if the directory exists
            if os.path.exists(day_dir):
                # Get all annotation files in the directory
                per_image_files = glob.glob(os.path.join(day_dir, "*_annotations.yaml"))
                day_status_file = os.path.join(day_dir, f"day_status_{day}.yaml")
                old_format_file = os.path.join(day_dir, f"annotations_{day}.yaml")
                
                # Check if files exist
                has_per_image_files = len(per_image_files) > 0
                has_day_status = os.path.exists(day_status_file)
                has_old_format = os.path.exists(old_format_file)
                
                if has_per_image_files or has_day_status or has_old_format:
                    # Open the popover to show the data
                    with st.popover(f"Annotation Data for Day {day}"):
                        # Add tabs for different views
                        day_tab, images_tab = st.tabs(["Day Summary", "Individual Images"])
                        
                        # Day Summary Tab
                        with day_tab:
                            try:
                                # Try to load day status file first
                                day_data = None
                                
                                if has_day_status:
                                    with open(day_status_file, 'r') as f:
                                        day_data = yaml.safe_load(f)
                                    st.success(f"Loaded day status file from {day_status_file}")
                                elif has_old_format:
                                    # Fall back to old format file
                                    with open(old_format_file, 'r') as f:
                                        day_data = yaml.safe_load(f)
                                    st.info(f"Loaded legacy day annotation file from {old_format_file}")
                                    
                                    # Show migration button if we have old format but no per-image files
                                    if not has_per_image_files:
                                        migrate_key = f"migrate_{day}"
                                        if st.button("🔄 Migrate to Per-Image Format", key=migrate_key):
                                            migrated_files = migrate_day_annotations_to_per_image(old_format_file)
                                            if migrated_files:
                                                st.success(f"Migrated {len(migrated_files)} annotation files")
                                                st.rerun()
                                            else:
                                                st.error("Failed to migrate annotations")
                                
                                if day_data:
                                    # Metadata section
                                    st.subheader("Day Summary")
                                    
                                    # Extract metadata (exclude large fields)
                                    metadata = {k: v for k, v in day_data.items() 
                                              if k not in ['annotations', 'file_status', 'image_annotations']}
                                    
                                    # Display as dataframe
                                    st.dataframe(pd.DataFrame([metadata]), use_container_width=True)
                                    
                                    # Display annotation status for each image
                                    st.subheader("Image Status")
                                    
                                    # Get status data
                                    file_status = day_data.get('file_status', {})
                                    if file_status:
                                        # Create dataframe
                                        status_df = pd.DataFrame([
                                            {'Filename': filename, 'Status': status.capitalize()}
                                            for filename, status in file_status.items()
                                        ])
                                        
                                        # Display as dataframe
                                        st.dataframe(
                                            status_df,
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                "Filename": st.column_config.TextColumn("Filename", width="large"),
                                                "Status": st.column_config.TextColumn("Status", width="medium")
                                            }
                                        )
                                    else:
                                        st.info("No status information available")
                                    
                                    # Format as JSON for download
                                    day_json = json.dumps(day_data, indent=2, default=str)
                                    
                                    # Add download button
                                    st.download_button(
                                        "Download Day Summary", 
                                        day_json, 
                                        file_name=f"day_status_{day}.json", 
                                        mime="application/json",
                                        key=f"download_day_{day}"
                                    )
                                else:
                                    # Generate summary from per-image files
                                    if has_per_image_files:
                                        st.subheader("Generated Summary")
                                        
                                        # Load all per-image files
                                        image_data = {}
                                        for file_path in per_image_files:
                                            try:
                                                with open(file_path, 'r') as f:
                                                    file_data = yaml.safe_load(f)
                                                if file_data and 'filename' in file_data:
                                                    image_data[file_data['filename']] = file_data
                                            except Exception as file_error:
                                                print(f"Error loading {file_path}: {file_error}")
                                        
                                        # Display summary stats
                                        st.metric("Total Images", len(image_data))
                                        
                                        # Count completed images
                                        completed = sum(1 for data in image_data.values() 
                                                      if data.get('status') == 'completed')
                                        st.metric("Completed Images", completed)
                                        
                                        # Get total annotation time
                                        total_time = sum(data.get('annotation_time_minutes', 0) 
                                                       for data in image_data.values())
                                        st.metric("Total Annotation Time (minutes)", f"{total_time:.1f}")
                                        
                                        # Create status summary
                                        status_df = pd.DataFrame([
                                            {'Filename': filename, 
                                             'Status': data.get('status', 'unknown').capitalize(),
                                             'Time (min)': data.get('annotation_time_minutes', 0)}
                                            for filename, data in image_data.items()
                                        ])
                                        
                                        if not status_df.empty:
                                            st.dataframe(
                                                status_df,
                                                use_container_width=True,
                                                hide_index=True
                                            )
                                    else:
                                        st.warning("No day status data available")
                            except Exception as e:
                                st.error(f"Error loading day summary: {str(e)}")
                                
                        # Individual Images Tab
                        with images_tab:
                            try:
                                # Check for in-memory annotations that might not be saved yet
                                has_memory_annotations = False
                                memory_annotations = {}
                                
                                if 'image_annotations' in st.session_state:
                                    for img_path, annotations in st.session_state.image_annotations.items():
                                        # Check if this image is for the current day
                                        img_dir = os.path.dirname(img_path)
                                        img_day = os.path.basename(img_dir)
                                        if img_day == day:
                                            img_name = os.path.basename(img_path)
                                            memory_annotations[img_name] = annotations
                                            has_memory_annotations = True
                                
                                # Combine disk annotations with memory annotations
                                all_image_options = set()
                                
                                # Add files from disk
                                if has_per_image_files:
                                    for f in per_image_files:
                                        img_name = os.path.basename(f).replace("_annotations.yaml", "")
                                        # Find full image filename if possible
                                        for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
                                            full_img_name = f"{img_name}{ext}"
                                            if os.path.exists(os.path.join(day_dir, full_img_name)):
                                                all_image_options.add(full_img_name)
                                                break
                                        else:
                                            # If no image file found, just use the base name
                                            all_image_options.add(f"{img_name}.jpg")  # Assume jpg as fallback
                                
                                # Add files from memory annotations
                                if has_memory_annotations:
                                    for img_name in memory_annotations.keys():
                                        all_image_options.add(img_name)
                                
                                # Create selectbox options
                                file_options = ["Select an image..."] + sorted(list(all_image_options))
                                
                                # Add a note if memory annotations exist
                                if has_memory_annotations and has_per_image_files:
                                    st.info("Showing annotations from both memory and disk files. Some may not be saved yet.")
                                
                                # Create tabs for alternative views if both sources available
                                if has_memory_annotations and has_per_image_files:
                                    img_tab1, img_tab2 = st.tabs(["Memory & Disk", "Just Disk Files"])
                                    view_container = img_tab1
                                else:
                                    view_container = st
                                
                                with view_container:
                                    selected_file = st.selectbox(
                                        "Select Image",
                                        options=file_options,
                                        key=f"select_image_{day}"
                                    )
                                    
                                    if selected_file and selected_file != "Select an image...":
                                        # Check for memory annotations first
                                        memory_annotation = memory_annotations.get(selected_file)
                                        
                                        # If not in memory, try to find annotation file
                                        image_data = None
                                        data_source = None
                                        
                                        # First try memory annotations
                                        if memory_annotation is not None:
                                            # Create a structure similar to file annotations
                                            image_data = {
                                                'filename': selected_file,
                                                'annotations': memory_annotation,
                                                'status': 'in_memory',
                                                'loaded_from': 'memory'
                                            }
                                            data_source = "memory (may not be saved yet)"
                                        
                                        # Then check for disk file
                                        base_name = os.path.splitext(selected_file)[0]
                                        annotation_file = os.path.join(day_dir, f"{base_name}_annotations.yaml")
                                        
                                        if os.path.exists(annotation_file):
                                            # If we already have memory data, add a note
                                            disk_source = "disk file"
                                            
                                            # Load the file data
                                            with open(annotation_file, 'r') as f:
                                                file_data = yaml.safe_load(f)
                                            
                                            # If memory annotations exist, we need to handle both
                                            if image_data:
                                                # Create a second tab for disk-only view
                                                with img_tab2:
                                                    # Display file data here
                                                    st.warning(f"Showing only disk file data for {selected_file}")
                                                    
                                                    # Display metadata
                                                    st.subheader("Image Metadata (from disk)")
                                                    file_metadata = {k: v for k, v in file_data.items() if k != 'annotations'}
                                                    st.dataframe(pd.DataFrame([file_metadata]), use_container_width=True)
                                                    
                                                    # Display annotations
                                                    st.subheader("ROI Annotations (from disk)")
                                                    
                                                    if 'annotations' in file_data:
                                                        # Create flattened view of annotations
                                                        flat_file_data = []
                                                        
                                                        for roi in file_data['annotations']:
                                                            row = {
                                                                'ROI': roi.get('roi_name', 'Unknown'),
                                                                'Discard': roi.get('discard', False),
                                                                'Snow Present': roi.get('snow_presence', False),
                                                                'Use Default Annotation': roi.get('not_needed', False),
                                                                'Flags': ', '.join(roi.get('flags', []))
                                                            }
                                                            flat_file_data.append(row)
                                                        
                                                        # Display as dataframe
                                                        if flat_file_data:
                                                            disk_df = pd.DataFrame(flat_file_data)
                                                            st.dataframe(
                                                                disk_df,
                                                                use_container_width=True,
                                                                hide_index=True,
                                                                column_config={
                                                                    "ROI": st.column_config.TextColumn("ROI", width="medium"),
                                                                    "Discard": st.column_config.CheckboxColumn("Discard", width="small"),
                                                                    "Snow Present": st.column_config.CheckboxColumn("Snow Present", width="small"),
                                                                    "Use Default Annotation": st.column_config.CheckboxColumn("Use Default Annotation", width="medium"),
                                                                    "Flags": st.column_config.TextColumn("Flags", width="large")
                                                                }
                                                            )
                                                    
                                                    # Add download button for disk file
                                                    file_json = json.dumps(file_data, indent=2, default=str)
                                                    st.download_button(
                                                        "Download Image Annotations (from disk)", 
                                                        file_json, 
                                                        file_name=f"{base_name}_annotations_disk.json", 
                                                        mime="application/json",
                                                        key=f"download_image_disk_{base_name}"
                                                    )
                                            else:
                                                # No memory annotations, just use the file data
                                                image_data = file_data
                                                data_source = disk_source
                                        
                                        # Now display the active data
                                        if image_data:
                                            if data_source:
                                                st.info(f"Showing annotations from {data_source}")
                                            
                                            # Display metadata
                                            st.subheader("Image Metadata")
                                            metadata = {k: v for k, v in image_data.items() if k != 'annotations'}
                                            st.dataframe(pd.DataFrame([metadata]), use_container_width=True)
                                            
                                            # Display annotations
                                            st.subheader("ROI Annotations")
                                            
                                            if 'annotations' in image_data:
                                                # Create flattened view of annotations
                                                flat_data = []
                                                
                                                for roi in image_data['annotations']:
                                                    row = {
                                                        'ROI': roi.get('roi_name', 'Unknown'),
                                                        'Discard': roi.get('discard', False),
                                                        'Snow Present': roi.get('snow_presence', False),
                                                        'Use Default Annotation': roi.get('not_needed', False),
                                                        'Flags': ', '.join(roi.get('flags', []))
                                                    }
                                                    flat_data.append(row)
                                                
                                                # Display as dataframe
                                                if flat_data:
                                                    df = pd.DataFrame(flat_data)
                                                    st.dataframe(
                                                        df,
                                                        use_container_width=True,
                                                        hide_index=True,
                                                        column_config={
                                                            "ROI": st.column_config.TextColumn("ROI", width="medium"),
                                                            "Discard": st.column_config.CheckboxColumn("Discard", width="small"),
                                                            "Snow Present": st.column_config.CheckboxColumn("Snow Present", width="small"),
                                                            "Use Default Annotation": st.column_config.CheckboxColumn("Use Default Annotation", width="medium"),
                                                            "Flags": st.column_config.TextColumn("Flags", width="large")
                                                        }
                                                    )
                                                else:
                                                    st.info("No ROI annotations found")
                                            else:
                                                st.info("No annotation data found")
                                            
                                            # Format as JSON for download
                                            image_json = json.dumps(image_data, indent=2, default=str)
                                            
                                            # Add download button
                                            st.download_button(
                                                "Download Image Annotations", 
                                                image_json, 
                                                file_name=f"{base_name}_annotations.json", 
                                                mime="application/json",
                                                key=f"download_image_{base_name}"
                                            )
                                    elif has_old_format:
                                        # Display old format annotations
                                        with open(old_format_file, 'r') as f:
                                            old_data = yaml.safe_load(f)
                                        
                                        if 'annotations' in old_data:
                                            # Get list of images
                                            image_options = ["Select an image..."] + list(old_data['annotations'].keys())
                                            
                                            selected_img = st.selectbox(
                                                "Select Image (from legacy format)",
                                                options=image_options,
                                                key=f"select_legacy_{day}"
                                            )
                                            
                                            if selected_img and selected_img != "Select an image...":
                                                # Get annotations for this image
                                                img_annotations = old_data['annotations'][selected_img]
                                                
                                                # Create flattened view
                                                flat_data = []
                                                
                                                for roi in img_annotations:
                                                    row = {
                                                        'ROI': roi.get('roi_name', 'Unknown'),
                                                        'Discard': roi.get('discard', False),
                                                        'Snow Present': roi.get('snow_presence', False),
                                                        'Use Default Annotation': roi.get('not_needed', False),
                                                        'Flags': ', '.join(roi.get('flags', []))
                                                    }
                                                    flat_data.append(row)
                                                
                                                # Display as dataframe
                                                if flat_data:
                                                    df = pd.DataFrame(flat_data)
                                                    st.dataframe(
                                                        df,
                                                        use_container_width=True,
                                                        hide_index=True
                                                    )
                                                    
                                                    # Add note about legacy format
                                                    st.info("Note: This data is stored in the legacy day-based format. Consider migrating to the new per-image format.")
                                                else:
                                                    st.info("No ROI annotations found for this image")
                                        else:
                                            st.warning("No annotation data found in legacy file")
                                    else:
                                        st.warning("No image annotation files found")
                            except Exception as e:
                                st.error(f"Error loading image data: {str(e)}")
                else:
                    st.warning(f"No annotation files found for day {day}")
            else:
                st.warning(f"Day directory not found: {day_dir}")
        else:
            st.warning("Base directory not found in scan info")
    else:
        st.warning("Scan info not available. Please scan for images first.")


def create_default_annotations(current_filepath, use_temp_storage=False):
    """
    Create default annotations for an image.
    
    Args:
        current_filepath (str): Path to the current image
        use_temp_storage (bool): Whether to use temporary storage instead of permanent
        
    Returns:
        list: The created annotation data
    """
    if not current_filepath:
        return None
    
    # Choose the appropriate storage
    if use_temp_storage:
        # Initialize temp_annotations if needed
        if 'temp_annotations' not in st.session_state:
            st.session_state.temp_annotations = {}
        annotations_storage = st.session_state.temp_annotations
    else:
        # Make sure image_annotations is initialized
        if 'image_annotations' not in st.session_state:
            print("WARNING: image_annotations not in session state, initializing it now")
            st.session_state.image_annotations = {}
        annotations_storage = st.session_state.image_annotations
    
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
            "not_needed": False  # No longer used but kept for compatibility
        }
    ]
    
    # Add an entry for each custom ROI
    for roi_name in roi_names:
        annotation_data.append({
            "roi_name": roi_name,
            "discard": False,
            "snow_presence": False,
            "flags": [],  # Empty list - no actual quality flags
            "not_needed": False  # No longer used but kept for compatibility
        })
    
    # Store in appropriate session state
    annotations_storage[current_filepath] = annotation_data
    
    print(f"Created default annotations for {os.path.basename(current_filepath)}" + 
          f" in {'temporary' if use_temp_storage else 'permanent'} storage")
    
    return annotation_data


# This function has been merged into display_annotation_panel
    
    
def create_annotation_summary(current_filepath):
    """
    Create a summary of annotations for the current image to display in the main container.
    
    Args:
        current_filepath (str): Path to the current image
        
    Returns:
        dict: Summary data including dataframe and metrics
    """
    if not current_filepath:
        return None
        
    # Make sure image_annotations is initialized
    if 'image_annotations' not in st.session_state:
        print("WARNING: image_annotations not in session state, initializing it now")
        st.session_state.image_annotations = {}
    
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

def update_annotation_value(roi_name, field, value, annotations_storage, image_key, sync_storages=True):
    """
    Update a specific field in the annotation data without triggering a rerun.
    Can optionally sync changes between temporary and permanent storage.
    
    Args:
        roi_name (str): The name of the ROI to update
        field (str): The field to update ('discard', 'snow_presence', or 'flags')
        value: The new value for the field
        annotations_storage (dict): The storage dictionary containing annotations
        image_key (str): The key for the current image
        sync_storages (bool): Whether to sync between temporary and permanent storage
    """
    if image_key not in annotations_storage:
        print(f"Warning: Cannot update {field} for {roi_name}, image key not found")
        return
        
    # Find the ROI in the annotations
    for annotation in annotations_storage[image_key]:
        if annotation.get("roi_name") == roi_name:
            annotation[field] = value
            print(f"Updated {field} to {value} for {roi_name} without rerun")
            break
    else:
        print(f"Warning: ROI {roi_name} not found in annotations")
        return
    
    # Sync between temporary and permanent storage if requested
    if sync_storages:
        # Determine which storage we're working with
        is_temp_storage = False
        if 'temp_annotations' in st.session_state and annotations_storage is st.session_state.temp_annotations:
            is_temp_storage = True
        
        # Initialize other storage if needed
        if is_temp_storage:
            # Sync from temporary to permanent
            if 'image_annotations' not in st.session_state:
                st.session_state.image_annotations = {}
            other_storage = st.session_state.image_annotations
        else:
            # Sync from permanent to temporary
            if 'temp_annotations' not in st.session_state:
                st.session_state.temp_annotations = {}
            other_storage = st.session_state.temp_annotations
        
        # Make sure other_storage is different from annotations_storage
        if other_storage is annotations_storage:
            print(f"Warning: other_storage is the same as annotations_storage, skipping sync")
            return
        
        # Check if the image exists in the other storage
        if image_key in other_storage:
            # Find the same ROI and update the value
            found_roi = False
            for other_anno in other_storage[image_key]:
                if other_anno.get("roi_name") == roi_name:
                    # Deep copy for lists like flags
                    if field == 'flags' and isinstance(value, list):
                        import copy
                        other_anno[field] = copy.deepcopy(value)
                    else:  
                        other_anno[field] = value
                    found_roi = True
                    print(f"Synced update to {'permanent' if is_temp_storage else 'temporary'} storage")
                    break
            
            if not found_roi:
                print(f"Warning: ROI {roi_name} not found in {'permanent' if is_temp_storage else 'temporary'} storage")
        else:
            # Copy the entire annotations list to the other storage
            if image_key in annotations_storage:
                # Create a deep copy to avoid reference issues
                import copy
                other_storage[image_key] = copy.deepcopy(annotations_storage[image_key])
                print(f"Copied annotations to {'permanent' if is_temp_storage else 'temporary'} storage")

def _create_annotation_interface(current_filepath, use_temp_storage=False):
    """
    Internal function to create the ROI annotation interface.
    
    Args:
        current_filepath (str): Path to the current image
        use_temp_storage (bool): Whether to use temporary storage instead of permanent
    """
    if not current_filepath:
        print("Cannot create annotation interface - no current filepath")
        return
        
    # Create a unique key for this image
    image_key = current_filepath
    
    # Choose the appropriate storage
    if use_temp_storage:
        # Initialize temp_annotations if needed
        if 'temp_annotations' not in st.session_state:
            st.session_state.temp_annotations = {}
        annotations_storage = st.session_state.temp_annotations
        storage_name = "temporary"
    else:
        # Initialize image_annotations if needed
        if 'image_annotations' not in st.session_state:
            print("WARNING: image_annotations not in session state in _create_annotation_interface, initializing it now")
            st.session_state.image_annotations = {}
        annotations_storage = st.session_state.image_annotations
        storage_name = "permanent"
    
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

    # Create or retrieve annotations for current image
    if image_key not in annotations_storage:
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
        print(f"Created new default annotations for {os.path.basename(image_key)} in {storage_name} storage")
        print(f"Default annotation data: {annotation_data}")
        print(f"ROI names used: {roi_names}")
    else:
        # Use existing annotations
        annotation_data = annotations_storage[image_key]
        print(f"Loaded existing annotations for {os.path.basename(image_key)} from {storage_name} storage")
        print(f"Existing annotation data: {annotation_data}")
        print(f"ROI names that should be available: {roi_names}")
        
    # Add the flag selector column for UI purposes (not stored in annotations)
    for row in annotation_data:
        row['_flag_selector'] = ""  # Empty by default, not stored permanently
    
    # Convert to DataFrame
    annotation_df = pd.DataFrame(annotation_data)
    
    # Add a title for the annotation panel with image filename
    filename = os.path.basename(current_filepath)
    st.markdown("### ROI Annotations")
    st.caption(f"Image: **{filename}**")
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
    
    # Create tabs for each ROI at the TOP of the UI
    roi_tabs = st.tabs(all_roi_names)
    
    # Process each ROI in its own tab
    for idx, (roi_name, roi_tab) in enumerate(zip(all_roi_names, roi_tabs)):
        with roi_tab:
            # Get the current ROI data
            roi_data = annotation_data[idx]
            
            # Create a unique key based on roi_name and image_key
            roi_key = f"{roi_name}_{os.path.basename(image_key)}_popup_{storage_name}"
            
            # Layout for the annotation controls - avoid nesting columns by putting all controls in a single area
            # Create checkbox for discard with function callback
            discard_key = f"discard_{roi_key}"
            st.checkbox(
                "Discard", 
                value=roi_data.get('discard', False),
                key=discard_key,
                help="Mark this image/ROI as not suitable for analysis",
                on_change=lambda roi=roi_name, dk=discard_key, as_=annotations_storage, ik=image_key: update_annotation_value(
                    roi, 
                    'discard', 
                    st.session_state[dk],  # Get current value from session state
                    as_, 
                    ik,
                    sync_storages=True  # Sync between temporary and permanent storage
                )
            )
            
            # Create checkbox for snow presence with function callback
            snow_key = f"snow_{roi_key}"
            st.checkbox(
                "Snow Present", 
                value=roi_data.get('snow_presence', False),
                key=snow_key,
                help="Mark if snow is present in this ROI",
                on_change=lambda roi=roi_name, sk=snow_key, as_=annotations_storage, ik=image_key: update_annotation_value(
                    roi, 
                    'snow_presence', 
                    st.session_state[sk],  # Get current value from session state
                    as_, 
                    ik,
                    sync_storages=True  # Sync between temporary and permanent storage
                )
            )
            
            # Add a separator
            st.markdown("---")
            
            # Flatten the options for the multiselect
            multiselect_options = []
            for category in sorted(flags_by_category.keys()):
                multiselect_options.extend(flags_by_category[category])
            
            # Get current flags for this ROI
            current_flags = roi_data.get('flags', [])
            
            # Select flags with this multiselect with function callback
            flags_key = f"flags_{roi_key}"
            st.multiselect(
                "Quality Flags",
                options=[value for value, _ in multiselect_options],
                format_func=lambda x: next((label for value, label in multiselect_options if value == x), x),
                default=current_flags,
                key=flags_key,
                help="Select quality flags applicable to this ROI",
                on_change=lambda roi=roi_name, fk=flags_key, as_=annotations_storage, ik=image_key: update_annotation_value(
                    roi,
                    'flags',
                    st.session_state[fk],  # Get current value from session state
                    as_,
                    ik,
                    sync_storages=True  # Sync between temporary and permanent storage
                )
            )
    
    # Make sure annotations exist for this image before we try to access them
    if image_key not in annotations_storage:
        # Create default annotations
        create_default_annotations(current_filepath, use_temp_storage=use_temp_storage)
        print(f"Created default annotations for {os.path.basename(image_key)} in annotation interface")
    
    # Log the status
    print(f"Using direct annotation updates in {'temporary' if use_temp_storage else 'permanent'} storage")
    
    # Add a button to copy ROI_00 settings to all other ROIs
    if "ROI_00" in all_roi_names and len(all_roi_names) > 1:
        copy_key = f"copy_roi00_{os.path.basename(current_filepath)}"
        if st.button("📋 Copy ROI_00 Settings to All ROIs", key=copy_key, use_container_width=True):
            # Ensure annotations exist in both storages
            permanent_storage = st.session_state.image_annotations
            temp_storage = st.session_state.temp_annotations
            
            # Make sure annotations exist in the current storage
            if image_key not in annotations_storage:
                create_default_annotations(current_filepath, use_temp_storage=use_temp_storage)
                print(f"Created default annotations for {os.path.basename(image_key)} in copy operation")
            
            # Make sure annotations exist in both storages
            if image_key not in permanent_storage:
                if image_key in temp_storage:
                    # Copy from temp to permanent
                    import copy
                    permanent_storage[image_key] = copy.deepcopy(temp_storage[image_key])
                    print(f"Copied annotations from temporary to permanent storage for copy operation")
                else:
                    # Create new annotations
                    create_default_annotations(current_filepath, use_temp_storage=False)
                    print(f"Created default annotations in permanent storage for copy operation")
            
            if image_key not in temp_storage:
                if image_key in permanent_storage:
                    # Copy from permanent to temp
                    import copy
                    temp_storage[image_key] = copy.deepcopy(permanent_storage[image_key])
                    print(f"Copied annotations from permanent to temporary storage for copy operation")
                else:
                    # Create new annotations
                    create_default_annotations(current_filepath, use_temp_storage=True)
                    print(f"Created default annotations in temporary storage for copy operation")
                
            # Find ROI_00 data in the current annotations
            roi00_data = None
            for anno in annotations_storage[image_key]:
                if anno["roi_name"] == "ROI_00":
                    roi00_data = anno
                    break
                    
            if roi00_data:
                # Apply ROI_00 settings to all other ROIs in temporary storage first
                import copy
                if image_key in temp_storage:
                    for anno in temp_storage[image_key]:
                        if anno["roi_name"] != "ROI_00":
                            # Copy values directly
                            anno["discard"] = roi00_data["discard"]
                            anno["snow_presence"] = roi00_data["snow_presence"]
                            anno["flags"] = copy.deepcopy(roi00_data["flags"])  # Deep copy the list
                            print(f"Updated {anno['roi_name']} with ROI_00 settings in temporary storage")
                
                # Then deep copy from temporary to permanent
                if image_key in temp_storage:
                    permanent_storage[image_key] = copy.deepcopy(temp_storage[image_key])
                    print(f"Copied updated temporary storage to permanent storage with ROI_00 settings")
                    
                # Verify by checking both storages
                roi_count = 0
                for storage_name, storage in [("temporary", temp_storage), ("permanent", permanent_storage)]:
                    if image_key in storage:
                        for anno in storage[image_key]:
                            if anno["roi_name"] != "ROI_00":
                                roi_count += 1
                
                # Show success message
                st.success(f"Applied ROI_00 settings to all {len(all_roi_names)-1} ROIs")
                print(f"Applied ROI_00 settings to all ROIs in both temporary and permanent storage")
                
                # Rerun to update UI
                st.rerun()
    
    # Show the full annotation data in an expander
    with st.expander("View Raw Annotation Data"):
        import yaml
        
        # Show both temporary and permanent annotations
        temp_storage = st.session_state.temp_annotations if 'temp_annotations' in st.session_state else {}
        permanent_storage = st.session_state.image_annotations if 'image_annotations' in st.session_state else {}
        
        # Get annotations from both storages
        temp_annotations = temp_storage.get(image_key, [])
        perm_annotations = permanent_storage.get(image_key, [])
        
        # Create tabs for the different storage types
        storage_tab1, storage_tab2, storage_tab3 = st.tabs(["Current Working Annotations", "Saved Annotations", "On-Disk File"])
        
        # Tab 1: Current Working Annotations (temporary storage or current edit session)
        with storage_tab1:
            if not temp_annotations:
                st.info("No annotations in temporary storage")
            else:
                # Check if this is using default annotations
                is_using_defaults = all(anno.get('not_needed', False) for anno in temp_annotations) if temp_annotations else True
                if is_using_defaults:
                    st.info("This image is using default annotation values")
                    
                # Display as formatted YAML
                st.code(yaml.dump(temp_annotations, default_flow_style=False, sort_keys=False), language="yaml")
        
        # Tab 2: Saved Annotations (permanent storage, may be different than what's on disk)
        with storage_tab2:
            if not perm_annotations:
                st.info("No annotations in permanent storage")
            else:
                # Check if permanent annotations are different from temporary
                import copy
                temp_copy = copy.deepcopy(temp_annotations) if temp_annotations else []
                perm_copy = copy.deepcopy(perm_annotations) if perm_annotations else []
                
                # Try to normalize formats for comparison
                for anns in [temp_copy, perm_copy]:
                    for ann in anns:
                        # Ensure flags is a sorted list for proper comparison
                        if 'flags' in ann:
                            ann['flags'] = sorted([str(flag) for flag in ann.get('flags', [])])
                
                # Check if different (accounting for potential order differences)
                try:
                    is_different = yaml.dump(sorted(temp_copy, key=lambda x: x.get('roi_name', ''))) != \
                                  yaml.dump(sorted(perm_copy, key=lambda x: x.get('roi_name', '')))
                except:
                    # If comparison fails for any reason, assume they're different
                    is_different = True
                    
                if is_different:
                    st.warning("Permanent storage annotations differ from temporary storage (unsaved changes)")
                
                # Display as formatted YAML
                st.code(yaml.dump(perm_annotations, default_flow_style=False, sort_keys=False), language="yaml")
        
        # Tab 3: On-Disk File (actual saved file)
        with storage_tab3:
            # Check if file exists on disk
            annotation_file_path = get_annotation_file_path(current_filepath)
            if os.path.exists(annotation_file_path):
                try:
                    # Load the file from disk
                    with open(annotation_file_path, 'r') as f:
                        file_data = yaml.safe_load(f)
                    
                    if file_data and 'annotations' in file_data:
                        # Display file metadata
                        metadata = {k: v for k, v in file_data.items() if k != 'annotations'}
                        st.subheader("File Metadata")
                        st.json(metadata)
                        
                        # Display annotations
                        st.subheader("File Annotations")
                        st.code(yaml.dump(file_data['annotations'], default_flow_style=False, sort_keys=False), language="yaml")
                    else:
                        st.warning("File exists but contains no annotations data")
                except Exception as e:
                    st.error(f"Error reading annotation file: {str(e)}")
            else:
                st.info("No annotation file exists on disk yet. Save your annotations to create it.")
    
    # No need to return anything as annotations are directly updated in the storage
    return None


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

# This function has been removed and its functionality integrated into the save button


def save_all_annotations(force_save=False):
    """
    Save all image annotations to individual YAML files.
    Only saves when explicitly triggered by "Save Annotations" button.
    
    Args:
        force_save: If True, forces the save operation, used only by the explicit save button
    """
    # Check if we're currently loading annotations - never save during load
    if st.session_state.get('loading_annotations', False):
        print("Skipping annotation save: currently loading annotations")
        return
    
    # Make sure image_annotations is initialized
    if 'image_annotations' not in st.session_state:
        print("WARNING: image_annotations not in session state, initializing it now")
        st.session_state.image_annotations = {}
        # No need to proceed if there are no annotations
        if not force_save:
            return
    
    # Track saved annotations by day for status updates
    annotations_by_day = {}  # {day_dir: {img_filename: annotation_data}}
    saved_count = 0

    try:
        # Get the annotation timer to record elapsed times
        from phenotag.ui.components.annotation_timer import annotation_timer
        
        # Pause the timer to capture current elapsed time
        annotation_timer.pause_timer()
        
        # Process each image's annotations
        for img_path, annotations in st.session_state.image_annotations.items():
            if not isinstance(img_path, str) or not os.path.exists(img_path):
                print(f"Skipping invalid image path: {img_path}")
                continue
                
            # Extract day and directory
            img_dir = os.path.dirname(img_path)
            img_filename = os.path.basename(img_path)
            doy = os.path.basename(img_dir)
            
            # Skip if can't determine day
            if not doy.isdigit():
                print(f"Skipping image with invalid day: {img_path}, day: {doy}")
                continue
            
            # Ensure annotations are in list format (one dict per ROI)
            annotation_list = []
            if isinstance(annotations, list):
                # Already in correct format
                annotation_list = annotations
            elif isinstance(annotations, dict):
                # Convert dict format to list format
                try:
                    for roi_name, roi_data in annotations.items():
                        if isinstance(roi_data, dict):
                            roi_data_copy = roi_data.copy()
                            roi_data_copy['roi_name'] = roi_name
                            annotation_list.append(roi_data_copy)
                    print(f"Converted dict annotations to list format for {img_filename}")
                except Exception as e:
                    print(f"Error converting annotations for {img_filename}: {str(e)}")
                    continue
            else:
                print(f"Warning: Unexpected annotations format for {img_filename}: {type(annotations)}")
                continue
            
            # Get the annotation file path for this image
            annotation_file_path = get_annotation_file_path(img_path)
            
            # Calculate annotation time for this image
            # Get overall time for the day and divide by number of images
            current_session_time = annotation_timer.get_elapsed_time_minutes(doy)
            
            # Count images in this day to divide the time fairly
            day_image_count = 0
            for path in st.session_state.image_annotations:
                if isinstance(path, str) and os.path.exists(path):
                    path_dir = os.path.dirname(path)
                    path_doy = os.path.basename(path_dir)
                    if path_doy == doy:
                        day_image_count += 1
            
            # Divide session time by number of images (minimum 1)
            image_annotation_time = current_session_time / max(day_image_count, 1)
            
            # Check for existing annotation file to preserve data
            existing_annotation_time = 0
            existing_data = {}
            if os.path.exists(annotation_file_path):
                try:
                    with open(annotation_file_path, 'r') as f:
                        existing_data = yaml.safe_load(f) or {}
                    
                    # Get existing annotation time
                    if "annotation_time_minutes" in existing_data:
                        existing_annotation_time = existing_data["annotation_time_minutes"]
                        print(f"Found existing annotation time for {img_filename}: {existing_annotation_time:.2f} minutes")
                except Exception as e:
                    print(f"Error loading existing annotation file {annotation_file_path}: {str(e)}")
            
            # Calculate total annotation time
            total_annotation_time = existing_annotation_time
            if current_session_time > 0:
                total_annotation_time += image_annotation_time
                print(f"Added session time for {img_filename}: {image_annotation_time:.2f} minutes. Total: {total_annotation_time:.2f} minutes")
            
            # Extract metadata from path
            # Path format: /path/to/base_dir/station/phenocams/products/instrument/L1/year/day/image.jpg
            year_dir = os.path.dirname(img_dir)
            year = os.path.basename(year_dir)
            l1_dir = os.path.dirname(year_dir)
            instrument_dir = os.path.dirname(l1_dir)
            instrument = os.path.basename(instrument_dir)
            products_dir = os.path.dirname(instrument_dir)
            phenocams_dir = os.path.dirname(products_dir)
            station_dir = os.path.dirname(phenocams_dir)
            station = os.path.basename(station_dir)
            
            # Check annotation completion status
            all_annotated = True
            for roi in annotation_list:
                has_annotations = (
                    roi.get('discard', False) or
                    roi.get('snow_presence', False) or
                    len(roi.get('flags', [])) > 0 or
                    roi.get('not_needed', False)
                )
                if not has_annotations:
                    all_annotated = False
                    break
            
            # Create annotation data structure
            annotation_data = {
                "created": existing_data.get("created", datetime.datetime.now().isoformat()),
                "last_modified": datetime.datetime.now().isoformat(),
                "filename": img_filename,
                "day_of_year": doy,
                "year": year,
                "station": station,
                "instrument": instrument,
                "annotation_time_minutes": total_annotation_time,
                "status": "completed" if all_annotated else "in_progress",
                "annotations": annotation_list
            }
            
            # Save individual annotation file
            save_yaml(annotation_data, annotation_file_path)
            print(f"Saved annotation file for {img_filename} to {annotation_file_path}")
            saved_count += 1
            
            # Track for day status updates
            if doy not in annotations_by_day:
                annotations_by_day[doy] = {}
            annotations_by_day[doy][img_filename] = annotation_data
            
        # Update day status files
        for doy, day_annotations in annotations_by_day.items():
            try:
                # Find the directory for this day from the first image
                first_img = list(day_annotations.keys())[0]
                first_img_data = day_annotations[first_img]
                
                # Construct the path to the day directory
                year = first_img_data["year"]
                station = first_img_data["station"]
                instrument = first_img_data["instrument"]
                
                # Try to get the day directory from session state
                day_dir = None
                if 'scan_info' in st.session_state:
                    base_dir = st.session_state.scan_info.get('base_dir')
                    if base_dir:
                        day_dir = os.path.join(
                            base_dir,
                            station,
                            "phenocams",
                            "products",
                            instrument,
                            "L1",
                            year,
                            doy
                        )
                
                # If we can't get it from session state, try to get it from the file path
                if not day_dir:
                    for img_path in st.session_state.image_annotations:
                        if isinstance(img_path, str) and os.path.exists(img_path):
                            img_dir = os.path.dirname(img_path)
                            img_doy = os.path.basename(img_dir)
                            if img_doy == doy:
                                day_dir = img_dir
                                break
                
                if day_dir and os.path.exists(day_dir):
                    # Update the day status file
                    update_day_status_file(day_dir, day_annotations)
                    
                    # Update annotation status cache
                    if 'annotation_status_map' in st.session_state:
                        try:
                            # Extract month from day number
                            date = datetime.datetime.strptime(f"{year}-{doy}", "%Y-%j")
                            month = date.month
                            
                            # Create status key
                            status_key = f"{station}_{instrument}_{year}_{month}"
                            
                            # Update cache entry
                            if status_key not in st.session_state.annotation_status_map:
                                st.session_state.annotation_status_map[status_key] = {}
                            
                            # Check if all images are fully annotated
                            day_images = [f for f in os.listdir(day_dir) 
                                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))]
                            
                            # For full completion, we need all images to have annotations
                            all_annotated = len(day_annotations) == len(day_images)
                            if all_annotated:
                                # And all images need to be completely annotated
                                for img_data in day_annotations.values():
                                    img_status = img_data.get("status", "")
                                    if img_status != "completed":
                                        all_annotated = False
                                        break
                            
                            # Set the day status
                            if all_annotated:
                                print(f"All images fully annotated for day {doy} - marking as completed")
                                st.session_state.annotation_status_map[status_key][doy] = 'completed'
                            else:
                                print(f"Annotation incomplete for day {doy} - marking as in_progress")
                                st.session_state.annotation_status_map[status_key][doy] = 'in_progress'
                                
                            # Save status to L1 parent folder
                            from phenotag.ui.components.annotation_status_manager import save_status_to_l1_parent
                            
                            # Get base directory
                            base_dir = None
                            if 'scan_info' in st.session_state:
                                base_dir = st.session_state.scan_info.get('base_dir')
                            else:
                                # Extract base_dir from the day_dir path
                                # We need to go up 7 levels: day/year/L1/instrument/products/phenocams/station
                                path_parts = day_dir.split(os.sep)
                                base_path_parts = path_parts[:-7]
                                base_dir = os.sep.join(base_path_parts)
                            
                            if base_dir:
                                # Save the status
                                current_status = st.session_state.annotation_status_map[status_key][doy]
                                save_status_to_l1_parent(
                                    base_dir,
                                    station,
                                    instrument,
                                    year,
                                    month,
                                    doy,
                                    current_status
                                )
                                print(f"Saved annotation status to L1 parent folder for day {doy}")
                                
                                # Update historical view if needed
                                if 'historical_year' in st.session_state and 'historical_month' in st.session_state:
                                    historical_year = st.session_state.historical_year
                                    historical_month = st.session_state.historical_month
                                    
                                    if year == historical_year and month == historical_month:
                                        # Update historical cache
                                        hist_status_key = f"{station}_{instrument}_{historical_year}_{historical_month}"
                                        if hist_status_key not in st.session_state.annotation_status_map:
                                            st.session_state.annotation_status_map[hist_status_key] = {}
                                        
                                        # Use the same status
                                        st.session_state.annotation_status_map[hist_status_key][doy] = current_status
                                        print(f"Updated historical status for day {doy} to {current_status}")
                        except Exception as e:
                            print(f"Error updating annotation status cache for day {doy}: {str(e)}")
            except Exception as e:
                print(f"Error updating day status for {doy}: {str(e)}")

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
        import traceback
        print(f"Detailed error: {traceback.format_exc()}")


def load_day_annotations(selected_day, daily_filepaths):
    """
    Load annotations for a specific day from individual image annotation files.
    
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
                
            # Get the directory where annotations are stored
            if daily_filepaths:
                img_dir = os.path.dirname(daily_filepaths[0])
                
                # Check if we need to migrate from old day-based format
                old_format_file = os.path.join(img_dir, f"annotations_{selected_day}.yaml")
                if os.path.exists(old_format_file):
                    print(f"Found old-format day annotation file: {old_format_file}")
                    # Check if we already have per-image files
                    existing_image_annotations = scan_day_annotation_files(img_dir)
                    if not existing_image_annotations:
                        print("No per-image annotation files found. Starting migration...")
                        # Need to migrate
                        migrated_files = migrate_day_annotations_to_per_image(old_format_file)
                        print(f"Migration complete. Created {len(migrated_files)} per-image annotation files.")
                        
                        # Rename the old file as backup
                        backup_file = f"{old_format_file}.bak"
                        try:
                            os.rename(old_format_file, backup_file)
                            print(f"Renamed old annotation file to: {backup_file}")
                            # Show notification about migration
                            st.toast(f"Migrated annotations to new per-image format for day {selected_day}", icon="🔄")
                        except Exception as rename_error:
                            print(f"Error renaming old annotation file: {rename_error}")
                    else:
                        print(f"Found {len(existing_image_annotations)} existing per-image annotation files. No migration needed.")
                
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
                
                # Scan for all per-image annotation files
                annotation_files = {}
                accumulated_time = 0.0
                loaded_count = 0
                
                # Create mapping of image filenames to paths
                name_to_path_map = {}
                for filepath in daily_filepaths:
                    filename = os.path.basename(filepath)
                    name_to_path_map[filename] = filepath
                
                # Check each image path for corresponding annotation file
                for filepath in daily_filepaths:
                    annotation_file_path = get_annotation_file_path(filepath)
                    
                    if os.path.exists(annotation_file_path):
                        try:
                            # Load the annotation file
                            with open(annotation_file_path, 'r') as f:
                                annotation_data = yaml.safe_load(f)
                            
                            if not annotation_data:
                                print(f"Empty annotation file: {annotation_file_path}")
                                continue
                                
                            # Extract and accumulate annotation time
                            if 'annotation_time_minutes' in annotation_data:
                                image_time = annotation_data.get('annotation_time_minutes', 0)
                                accumulated_time += image_time
                                print(f"Added {image_time:.2f} minutes from {os.path.basename(filepath)}")
                            
                            # Process annotations for this image
                            if 'annotations' in annotation_data:
                                annotations_list = annotation_data['annotations']
                                
                                # Normalize annotations to ensure all required fields
                                processed_annotations = []
                                for anno in annotations_list:
                                    # Create a clean copy
                                    processed_anno = anno.copy()
                                    
                                    # Ensure all fields exist
                                    if 'roi_name' not in processed_anno:
                                        processed_anno['roi_name'] = "ROI_00"
                                    if 'discard' not in processed_anno:
                                        processed_anno['discard'] = False
                                    if 'snow_presence' not in processed_anno:
                                        processed_anno['snow_presence'] = False
                                    if 'flags' not in processed_anno or processed_anno['flags'] is None:
                                        processed_anno['flags'] = []
                                    if 'not_needed' not in processed_anno:
                                        processed_anno['not_needed'] = False
                                        
                                    # Make sure flags is a list of strings
                                    processed_anno['flags'] = [str(flag) for flag in processed_anno['flags']]
                                    
                                    # Add to processed list
                                    processed_annotations.append(processed_anno)
                                
                                # Store in session state
                                st.session_state.image_annotations[filepath] = processed_annotations
                                loaded_count += 1
                                print(f"Loaded annotations for {os.path.basename(filepath)}: {len(processed_annotations)} ROIs")
                            else:
                                print(f"No annotations data in file: {annotation_file_path}")
                                
                        except Exception as load_error:
                            print(f"Error loading annotation file {annotation_file_path}: {str(load_error)}")
                
                # Set accumulated time for the day
                current_accumulated = annotation_timer.get_accumulated_time(selected_day)
                if current_accumulated == 0 and accumulated_time > 0:
                    annotation_timer.set_accumulated_time(selected_day, accumulated_time)
                    print(f"Set accumulated time to {accumulated_time:.2f} minutes from all image annotations")
                
                # Check day status and update completion info
                # Parse day status file if it exists
                day_status_file = os.path.join(img_dir, f"day_status_{selected_day}.yaml")
                day_status_data = None
                
                if os.path.exists(day_status_file):
                    try:
                        with open(day_status_file, 'r') as f:
                            day_status_data = yaml.safe_load(f)
                        print(f"Loaded day status file: {day_status_file}")
                    except Exception as status_error:
                        print(f"Error loading day status file: {status_error}")
                
                # If no status file, generate one
                if not day_status_data:
                    # Gather all loaded annotations
                    loaded_annotations = {}
                    for filepath, annotations in st.session_state.image_annotations.items():
                        img_dir = os.path.dirname(filepath)
                        img_doy = os.path.basename(img_dir)
                        if img_doy == selected_day:
                            filename = os.path.basename(filepath)
                            loaded_annotations[filename] = {
                                "annotations": annotations,
                                "annotation_time_minutes": 0
                            }
                    
                    # Generate a new status file
                    if loaded_annotations:
                        update_day_status_file(img_dir, loaded_annotations)
                        
                        # Re-read the status file
                        try:
                            with open(day_status_file, 'r') as f:
                                day_status_data = yaml.safe_load(f)
                            print(f"Created and loaded new day status file: {day_status_file}")
                        except Exception as new_status_error:
                            print(f"Error loading new day status file: {new_status_error}")
                
                # Set completion information in session state
                if day_status_data:
                    expected = day_status_data.get('expected_image_count', len(daily_filepaths))
                    annotated = day_status_data.get('annotated_image_count', loaded_count)
                    completion = day_status_data.get('completion_percentage', (annotated / max(expected, 1)) * 100)
                    
                    # Show notification with completion status
                    st.success(f"Loaded annotations for day {selected_day}: {annotated}/{expected} images ({completion:.1f}% complete)", icon="✅")
                    
                    # Store completion info in session state
                    if 'annotation_completion' not in st.session_state:
                        st.session_state.annotation_completion = {}
                    
                    st.session_state.annotation_completion[selected_day] = {
                        'expected': expected,
                        'annotated': annotated,
                        'percentage': completion,
                        'file_status': day_status_data.get('file_status', {})
                    }
                elif loaded_count > 0:
                    # Basic notification if no status data available
                    st.success(f"Loaded {loaded_count} annotations for day {selected_day}", icon="✅")
                
                # Set flags to indicate successful loading
                st.session_state.annotations_just_loaded = True
                st.session_state[day_load_key] = True
            else:
                print(f"ERROR: daily_filepaths is empty, cannot determine annotations directory")
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
            if annotations_after_loading:
                print(f"Annotations loaded: {', '.join(annotations_after_loading)}")
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