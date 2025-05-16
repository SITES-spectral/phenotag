"""
Image display component for PhenoTag.

This module handles displaying and selecting images with their metadata.
"""
import os
import datetime
import pandas as pd
import streamlit as st
import cv2
import numpy as np

from phenotag.processors.image_processor import ImageProcessor
from phenotag.io_tools import (
    lazy_find_phenocam_images,
    get_days_in_month,
    get_days_in_year
)
from phenotag.ui.calendar_component import format_day_range




def display_image_list(daily_filepaths):
    """
    Create a set of radio buttons for image selection.
    
    Args:
        daily_filepaths (list): List of file paths for the selected day(s)
        
    Returns:
        dict: A selection event dictionary that mimics the dataframe selection event
    """
    # Extract data from filenames using the pattern
    # Format: {location}_{station_acronym}_{instrument_id}_{year}_{day_of_year}_{timestamp}.jpg
    filenames = [os.path.basename(path) for path in daily_filepaths]
    timestamps = []
    dates = []
    doys = []

    for filename in filenames:
        parts = filename.split('_')
        if len(parts) >= 6:  # Make sure we have enough parts
            try:
                # Extract year and day of year
                year = parts[-3]
                day_of_year = parts[-2]

                # The timestamp is the last part (without extension)
                timestamp = parts[-1].split('.')[0]

                # Format as readable time (HHMMSS)
                if len(timestamp) >= 6:  # Ensure it's at least HHMMSS format
                    formatted_time = f"{timestamp[0:2]}:{timestamp[2:4]}:{timestamp[4:6]}"
                    timestamps.append(formatted_time)
                else:
                    timestamps.append(timestamp)  # Fallback

                # Convert year and DOY to a readable date
                try:
                    # Create date from year and day of year
                    date_obj = datetime.datetime.strptime(f"{year}-{day_of_year}", "%Y-%j").date()
                    formatted_date = date_obj.strftime("%Y-%m-%d")  # ISO format date
                    dates.append(formatted_date)
                    doys.append(f"{int(day_of_year):03d}")  # Just the number with leading zeros
                except ValueError:
                    dates.append(f"{year}")
                    doys.append(f"{day_of_year}")
            except:
                # Handle any parsing errors
                timestamps.append("Unknown")
                dates.append("Unknown")
                doys.append("Unknown")
        else:
            timestamps.append("Unknown")
            dates.append("Unknown")
            doys.append("Unknown")

    # Check annotation status for each file
    # Make sure image_annotations is initialized
    if 'image_annotations' not in st.session_state:
        print("WARNING: image_annotations not in session state in display_image_list, initializing it now")
        st.session_state.image_annotations = {}
    
    annotation_status = []
    for filepath in daily_filepaths:
        annotation_status.append(filepath in st.session_state.image_annotations)
    
    # Create a list of radio options with formatted display labels
    radio_options = []
    for i, (filename, doy, date, time, annotated) in enumerate(zip(filenames, doys, dates, timestamps, annotation_status)):
        # Create a readable label for each radio option - just date and time without annotation status
        label = f"{date} - {time}"
        radio_options.append((label, i))  # Store tuple of (label, index)
    
    # Initialize session state for selected index if it doesn't exist
    if 'selected_image_index' not in st.session_state:
        st.session_state.selected_image_index = 0 if radio_options else None
    
    # Create a selection from radio buttons
    st.markdown("#### Image Selection")
    
    # Check if we have any options
    selection = None
    if radio_options:
        # Find the current value to pre-select
        default_index = st.session_state.selected_image_index
        if default_index is not None and default_index < len(radio_options):
            default_value = radio_options[default_index][0]
        else:
            default_value = radio_options[0][0] if radio_options else None
        
        # Use a persistent key based on the file_paths to maintain selection
        radio_key = "image_radio_selector"
        
        # Instead of using the label (which changes when annotation status changes),
        # we'll use the indices directly and format the labels separately
        options_indices = list(range(len(radio_options)))
        
        # Get formatted labels for display
        formatted_labels = [option[0] for option in radio_options]
        
        # For index selection, use the session state value or default to 0
        index_to_use = default_index if default_index is not None and default_index < len(options_indices) else 0
        
        # Create the radio buttons with indices as values
        selected_index = st.radio(
            "Select an image:",
            options=options_indices,
            format_func=lambda i: formatted_labels[i] if i < len(formatted_labels) else "",
            index=index_to_use,
            key=radio_key,
            label_visibility="collapsed"
        )
        
        # Update session state with the selected index and trigger rerun if changed
        if selected_index is not None:
            # Check if the index changed
            if st.session_state.get('selected_image_index') != selected_index:
                # Update the session state
                st.session_state.selected_image_index = selected_index
                print(f"Updated selected_image_index to {selected_index}")
                
                # Set current_filepath based on the new selection
                if 0 <= selected_index < len(daily_filepaths):
                    st.session_state.current_filepath = daily_filepaths[selected_index]
                    
                # Force a rerun to update the UI and annotation panel
                st.rerun()
            else:
                # No change, just ensure session state is updated
                st.session_state.selected_image_index = selected_index
            
        # Create a selection event that mimics the dataframe selection event
        if selected_index is not None:
            selection = type('obj', (object,), {
                'selection': type('obj', (object,), {
                    'rows': [selected_index]
                })
            })
    else:
        st.info("No images available for selection.")
    
    return selection


def display_selected_image(event, daily_filepaths):
    """
    Display the selected image with ROI overlays as needed.
    
    Args:
        event: Event from the selection (can be radio button or dataframe selection)
        daily_filepaths (list): List of file paths for the selected day(s)
        
    Returns:
        str: Path to the displayed image, or None if no image was displayed
    """
    filepath = None
    
    # Use the selected_image_index from session state if available
    index = None
    
    # First check if we have a radio button selection in session state
    if 'selected_image_index' in st.session_state and st.session_state.selected_image_index is not None:
        index = st.session_state.selected_image_index
        print(f"Using index from session state: {index}")
    # Fall back to the event selection if provided (for backward compatibility)
    elif event and hasattr(event, 'selection') and hasattr(event.selection, 'rows') and event.selection.rows:
        try:
            # Convert to integer index (it might be a string from the dataframe)
            index = int(event.selection.rows[0])
            print(f"Using index from event: {index}")
            
            # Also update the session state for persistence
            st.session_state.selected_image_index = index
        except (ValueError, TypeError) as e:
            print(f"Error processing selection from event: {e}")
            st.error(f"Error processing selection from event: {e}")
            index = None
    else:
        print("No selection found - neither in session state nor in event")
    
    # Process the selection if we have a valid index
    if index is not None:
        try:
            # Ensure index is in range
            if 0 <= index < len(daily_filepaths):
                filepath = daily_filepaths[index]
            else:
                st.error(f"Invalid selection index: {index}, out of range")
                filepath = None
        except (ValueError, TypeError) as e:
            st.error(f"Error processing selection: {e}")
            filepath = None

        if filepath:
            # Load and process the image
            processor = ImageProcessor()
            if processor.load_image(filepath):
                # Check if we have instrument ROIs loaded
                if st.session_state.get('show_roi_overlays', False):
                    if 'instrument_rois' in st.session_state and st.session_state.instrument_rois:
                        # Use the instrument-specific ROIs from the stations configuration
                        # Debug the ROI structure
                        print(f"Applying ROIs: {list(st.session_state.instrument_rois.keys())}")

                        # Try the built-in ImageProcessor function first with our improved ROI format
                        try:
                            # Convert the ROIs from YAML format to ImageProcessor format if needed
                            # If deserialize_polygons was already called, this is already in the right format
                            roi_dict = st.session_state.instrument_rois

                            # Check if we need to deserialize (if it's in the raw YAML format)
                            if roi_dict and isinstance(next(iter(roi_dict.values())), dict):
                                first_roi = next(iter(roi_dict.values()))
                                if 'points' in first_roi and isinstance(first_roi['points'][0], list):
                                    # If points are still lists, convert to tuples
                                    print("ROIs in YAML format detected, performing conversion")
                                    from phenotag.ui.main import deserialize_polygons  # Import here to avoid circular imports
                                    roi_dict = deserialize_polygons(roi_dict)

                            # Apply ROIs using the built-in method
                            processor.overlay_polygons_from_dict(roi_dict, enable_overlay=True)
                            print("Successfully applied ROIs using built-in overlay_polygons_from_dict")

                            # Check if image has the overlays
                            img_with_overlay = processor.get_image(with_overlays=True)
                            if img_with_overlay is not None:
                                print(f"Overlay applied - image shape: {img_with_overlay.shape}")
                            else:
                                print("Warning: overlay image is None, falling back to custom method")
                                raise ValueError("Overlay image not created")
                        except Exception as e:
                            print(f"Error applying ROIs with built-in method: {str(e)}")

                            # Fallback to using our improved custom overlay function
                            try:
                                print("Using custom overlay_polygons function as fallback")

                                # Get the original image (without overlays)
                                original_img = processor.get_image(with_overlays=False)

                                if original_img is None:
                                    raise ValueError("Could not get original image from processor")

                                # Create a new image with our improved overlay function
                                dummy_path = "dummy_path"

                                # Mock the cv2.imread to return our already loaded image
                                original_cv2_imread = cv2.imread
                                try:
                                    cv2.imread = lambda path: original_img if path == dummy_path else original_cv2_imread(path)

                                    # Apply ROIs with our custom function using the default font scale of 2.0
                                    from phenotag.ui.components.roi_utils import overlay_polygons
                                    img_with_rois = overlay_polygons(dummy_path, st.session_state.instrument_rois, show_names=True)

                                    # Convert from RGB to BGR if needed (OpenCV uses BGR)
                                    if img_with_rois is not None:
                                        # Our custom function already returns RGB, but processor expects BGR
                                        img_with_rois = cv2.cvtColor(img_with_rois, cv2.COLOR_RGB2BGR)

                                        # Replace the processor's image with our overlaid version
                                        processor.image = img_with_rois.copy()
                                        print("Successfully applied ROIs using custom overlay_polygons")
                                    else:
                                        raise ValueError("Custom overlay returned None")
                                finally:
                                    # Restore the original cv2.imread function
                                    cv2.imread = original_cv2_imread
                            except Exception as inner_e:
                                print(f"Error with custom overlay: {str(inner_e)}")
                                st.error(f"All ROI display methods failed. Primary error: {str(e)}. Fallback error: {str(inner_e)}")
                                # Don't use default ROI to avoid confusion
                                st.warning("Unable to display instrument ROIs due to format incompatibility.")

                        # Information about ROIs is now provided directly in the image via labels
                        # We don't need to show an info message above the image
                    else:
                        # Now that we've fixed the format issues, re-enable default ROI generation
                        processor.create_default_roi()
                        # No informational message required now that ROIs are labeled in the image

                # Store the image dimensions (for future ROI adjustments if needed)
                img = processor.get_image(with_overlays=False)  # Get the image without overlays first
                if img is not None:
                    height, width = img.shape[:2]
                    st.session_state.image_dimensions = (width, height)

                # Get the image with or without overlays based on toggle
                show_rois = st.session_state.get('show_roi_overlays', False)
                img = processor.get_image(with_overlays=show_rois)

                if img is not None:
                    # Convert BGR to RGB for correct color display
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                    # Add image caption with ROI status
                    caption = os.path.basename(filepath)
                    if st.session_state.get('show_roi_overlays', False):
                        caption += " (with ROI overlays)"

                    # Display the image
                    st.image(img_rgb, caption=caption, use_container_width=True)
                    
                    # Make sure filepath is stored in session state for other components
                    st.session_state.current_filepath = filepath
                    # Print debugging info
                    print(f"Selected image: {filepath}")
                    print(f"Image stored in session state as current_filepath")
                    
                    
                else:
                    st.error(f"Failed to process image: {filepath}")
            else:
                st.error(f"Failed to load image: {filepath}")
    else:
        st.info("No image selected. Select an image to view it.")
        
    return filepath


def get_filtered_file_paths(normalized_name, selected_instrument, selected_year, selected_day=None, selected_days=None):
    """
    Get filtered file paths based on the current selection.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        selected_year (str): Selected year
        selected_day (str, optional): Single selected day
        selected_days (list, optional): List of selected days
        
    Returns:
        list: List of file paths for the selected day(s)
    """
    # Check if we have image data in the session state
    key = f"{normalized_name}_{selected_instrument}" if normalized_name and selected_instrument else None
    image_data = st.session_state.image_data.get(key, {}) if key and 'image_data' in st.session_state else {}
    
    daily_filepaths = []
    
    if image_data and selected_year and selected_year in image_data:
        # Check if we're using lazy loading
        if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
            # Get scan info
            scan_info = st.session_state.scan_info
            base_dir = scan_info['base_dir']
            station_name = scan_info['station_name']
            instrument_id = scan_info['instrument_id']

            # Check if we have selected days from the calendar
            if selected_days:
                # Convert days to strings and ensure proper format
                days_to_load = [str(doy).zfill(3) for doy in selected_days]

                with st.spinner(f"Loading data for {len(days_to_load)} selected days..."):
                    # Only load data for selected days (memory efficient)
                    days_data = lazy_find_phenocam_images(
                        base_dir=base_dir,
                        station_name=station_name,
                        instrument_id=instrument_id,
                        year=selected_year,
                        days=days_to_load
                    )

                    # Extract file paths from the loaded data
                    if selected_year in days_data:
                        for doy_str, doy_data in days_data[selected_year].items():
                            daily_filepaths.extend(list(doy_data.keys()))

                            # Update the image_data for this day
                            if selected_year not in image_data:
                                image_data[selected_year] = {}
                            image_data[selected_year][doy_str] = doy_data

            # Otherwise, just use the single selected day
            elif selected_day:
                with st.spinner(f"Loading data for day {selected_day}..."):
                    # Only load data for the selected day (memory efficient)
                    day_data = lazy_find_phenocam_images(
                        base_dir=base_dir,
                        station_name=station_name,
                        instrument_id=instrument_id,
                        year=selected_year,
                        days=[selected_day]
                    )

                    # Extract file paths from the loaded data
                    if selected_year in day_data and selected_day in day_data[selected_year]:
                        daily_filepaths = list(day_data[selected_year][selected_day].keys())

                        # Update the image_data for this day
                        if selected_year not in image_data:
                            image_data[selected_year] = {}
                        image_data[selected_year][selected_day] = day_data[selected_year][selected_day]

        # For compatibility with existing data structure (non-lazy loading)
        else:
            # If we have selected days from the calendar, use those
            if selected_days:
                for doy in selected_days:
                    doy_str = str(doy)
                    if doy_str in image_data[selected_year]:
                        daily_filepaths.extend([f for f in image_data[selected_year][doy_str]])
            # Otherwise, just use the single selected day
            elif selected_day:
                daily_filepaths = [f for f in image_data[selected_year][selected_day]]
            else:
                daily_filepaths = []

        # Sort filepaths by name
        daily_filepaths.sort()
        
    return daily_filepaths


def display_images(normalized_name, selected_instrument, selected_year=None, selected_day=None, selected_days=None):
    """
    Display the image viewer panel with file list and selected image.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        selected_year (str, optional): Selected year
        selected_day (str, optional): Selected day
        selected_days (list, optional): List of selected days
    
    Returns:
        str: Path to the displayed image, or None if no image was displayed
    """
    # Check if we have image data in the session state
    key = f"{normalized_name}_{selected_instrument}" if normalized_name and selected_instrument else None
    image_data = st.session_state.image_data.get(key, {}) if key and 'image_data' in st.session_state else {}
    
    displayed_filepath = None
    
    if image_data:
        # Check if we have a selected year
        selected_year = st.session_state.selected_year if 'selected_year' in st.session_state else None

        # If no year or the selected year isn't in our data, select the most recent one
        if not selected_year or selected_year not in image_data:
            years = list(image_data.keys())
            years.sort(reverse=True)
            if years:
                selected_year = years[0]
                st.session_state.selected_year = selected_year
                # Save this selection to session config - not an annotation auto-save
                from phenotag.ui.components.session_state import save_session_config
                save_session_config()

        # Only continue if we now have a valid year
        if selected_year and selected_year in image_data:
            # Get file paths for all selected days
            daily_filepaths = get_filtered_file_paths(
                normalized_name, 
                selected_instrument, 
                selected_year, 
                selected_day, 
                selected_days
            )

            # Only display image data if we have both a year and a day selected
            if daily_filepaths:
                # Create two columns with the specified ratio [2,5]
                left_col, main_col = st.columns([2, 5])

                with left_col:
                    # Add ROI toggle with session state persistence
                    if 'show_roi_overlays' not in st.session_state:
                        st.session_state.show_roi_overlays = False

                    # Simple toggle for ROI display
                    show_rois = st.toggle("Show ROI Overlays", value=st.session_state.show_roi_overlays,
                                        help="Toggle to show region of interest overlays on the image",
                                        key="show_roi_toggle")

                    # Update session state when toggle changes
                    if show_rois != st.session_state.show_roi_overlays:
                        # Flag to indicate this is just a UI toggle, not an annotation change
                        st.session_state.roi_toggle_changed = True
                        
                        # Update the toggle state
                        st.session_state.show_roi_overlays = show_rois

                        # If ROIs are enabled but haven't been loaded yet, load them automatically
                        if show_rois and ('instrument_rois' not in st.session_state or not st.session_state.instrument_rois):
                            # Try to load the instrument ROIs silently
                            from phenotag.ui.main import load_instrument_rois  # Import here to avoid circular imports
                            if load_instrument_rois():
                                print("ROIs loaded automatically when toggle was turned on")
                            else:
                                print("No ROIs found for current instrument when toggle was turned on")

                        # Force a rerun to update the UI
                        st.rerun()
                    
                    # Display ROI legend if we have ROIs loaded AND the overlay toggle is on
                    if 'instrument_rois' in st.session_state and st.session_state.instrument_rois and st.session_state.get('show_roi_overlays', False):
                        st.markdown("#### ROI Legend")
                        
                        # Create a simple table to display ROI names and colors
                        legend_data = []
                        for roi_name, roi_info in st.session_state.instrument_rois.items():
                            # Get color in RGB format for display
                            if 'color' in roi_info:
                                color = roi_info['color']
                                # Convert to hex for CSS styling
                                if isinstance(color, tuple) and len(color) >= 3:
                                    # OpenCV uses BGR, convert to RGB for hex display
                                    hex_color = f"#{color[2]:02x}{color[1]:02x}{color[0]:02x}"
                                    legend_data.append({
                                        "ROI": roi_name,
                                        "Color": f'<div style="background-color: {hex_color}; width: 20px; height: 20px; border-radius: 3px;"></div>'
                                    })

                        # Display the legend if we have data
                        if legend_data:
                            with st.expander("ROI Legend", expanded=True):                               

                                # Create a simple vertical list of ROIs with colors
                                for item in legend_data:
                                    st.markdown(
                                        f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
                                        f'<div style="margin-right: 10px;">{item["Color"]}</div>'
                                        f'<div>{item["ROI"]}</div>'
                                        f'</div>',
                                        unsafe_allow_html=True
                                    )
                    
                    # Display the image selection list
                    event = display_image_list(daily_filepaths)
                    
                    # Also add a text description of how many images are available
                    if selected_days:
                        selection_text = format_day_range(selected_days, int(selected_year))
                        st.write(f"{len(daily_filepaths)} images available for {selection_text}")
                    else:
                        st.write(f"{len(daily_filepaths)} images available for day {selected_day}")
                    
                    # No navigation buttons - users will select directly from radio buttons
                    
                    # Add annotation button at the bottom of the image selection column
                    if 'current_filepath' in st.session_state and st.session_state.current_filepath:
                        st.markdown("---")
                        from phenotag.ui.components.annotation import display_annotation_button
                        
                        # Create a key using just the filename and the current timestamp to force refresh
                        filename = os.path.basename(st.session_state.current_filepath)
                        # Add selected_image_index to the key to ensure it refreshes when selection changes
                        selected_idx = st.session_state.get('selected_image_index', 0)
                        refresh_key = f"annotation_button_{filename}_{selected_idx}"
                        
                        # Display the annotation button with the unique key to ensure it refreshes
                        with st.container(key=refresh_key):
                            display_annotation_button(st.session_state.current_filepath)

                # Display the selected image in the main column
                with main_col:
                    # Get the selected index directly from session state
                    selected_index = st.session_state.get('selected_image_index')
                    
                    # Directly set the current filepath from the index if possible
                    if selected_index is not None and 0 <= selected_index < len(daily_filepaths):
                        selected_filepath = daily_filepaths[selected_index]
                        # Set the current filepath in session state BEFORE displaying
                        st.session_state.current_filepath = selected_filepath
                        print(f"Set current_filepath directly from selected_index: {selected_filepath}")
                    
                    # Now display the image (still using the event for compatibility)
                    displayed_filepath = display_selected_image(event, daily_filepaths)
                    
                    # As a fallback, update current filepath in session state from the displayed result
                    if displayed_filepath and displayed_filepath != st.session_state.get('current_filepath'):
                        st.session_state.current_filepath = displayed_filepath
                        print(f"Updated current_filepath from display result: {displayed_filepath}")
            else:
                # No files found for the selected days
                if selected_days:
                    st.warning(f"No image files found for the selected days in year {selected_year}")
                else:
                    st.warning(f"No image files found for day {selected_day} in year {selected_year}")
        else:
            # No year or day selected
            st.info("Select a year and day to view images")
    else:
        st.info("No image data available. Please scan for images first.")
    
    return displayed_filepath