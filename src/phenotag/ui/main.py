import streamlit as st
import os
import pandas as pd
import numpy as np
import time
import cv2
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Use absolute imports
from phenotag.config import load_config_files
from phenotag.io_tools import find_phenocam_images, save_yaml, save_annotations, load_session_config
from phenotag.processors.image_processor import ImageProcessor


def get_phenocam_instruments(station_data):
    """Extract phenocam instruments from station data."""
    instruments = []
    
    # Check if the station has phenocams data
    if 'phenocams' in station_data and 'platforms' in station_data['phenocams']:
        platforms = station_data['phenocams']['platforms']
        
        # Go through each platform (BL, PL, etc.)
        for platform_type, platform_data in platforms.items():
            if 'instruments' in platform_data:
                # Add each instrument ID to the list
                for instrument_id, instrument_info in platform_data['instruments'].items():
                    instruments.append(instrument_id)
    
    return instruments


def create_image_dataframe(year_data, day, max_items=10):
    """
    Create a pandas DataFrame for the data_editor with image data and thumbnails.
    
    Args:
        year_data: Dictionary with image data for a specific year
        day: Day of year to display images for
        max_items: Maximum number of items to include
    
    Returns:
        pandas.DataFrame: DataFrame with image data and thumbnails
    """
    # Get the day's data
    if day not in year_data:
        return pd.DataFrame()
    
    day_data = year_data[day]
    file_paths = list(day_data.keys())
    
    # Limit to max_items
    if len(file_paths) > max_items:
        file_paths = file_paths[:max_items]
    
    # Create data for the dataframe
    data = []
    
    # Show a loading message
    with st.spinner(f"Loading {len(file_paths)} images and generating thumbnails..."):
        # Create an image processor instance once
        processor = ImageProcessor()
        
        for file_path in file_paths:
            file_info = day_data[file_path]
            quality = file_info['quality']
            
            # Load image and generate thumbnail using ImageProcessor
            if processor.load_image(file_path):
                # Generate a thumbnail for this image (max size 100x100 pixels)
                thumbnail = processor.create_thumbnail(max_size=(100, 100))
            else:
                thumbnail = None
            
            # Create a row for each file
            row = {
                'file_path': file_path,
                'filename': os.path.basename(file_path),  # Store the filename for display
                'thumbnail': thumbnail,  # Store the base64 thumbnail
                'discard_file': quality['discard_file'],
                'snow_presence': quality['snow_presence']
            }
            
            # Add ROI data
            for roi_name, roi_data in file_info['rois'].items():
                row[f"{roi_name}_discard"] = roi_data['discard_roi']
                row[f"{roi_name}_snow"] = roi_data['snow_presence']
            
            data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Store the DataFrame in session state with a unique key based on year and day
    key = f"images_{year_data}_{day}"
    st.session_state[key] = df
    
    return df


def save_session_config():
    """Save the current session configuration to a YAML file."""
    # Define the configuration file path
    config_dir = Path(os.path.expanduser("~/.phenotag"))
    config_file = config_dir / "sites_spectral_phenocams_session_config.yaml"
    
    # Create the configuration data
    config_data = {
        "data_directory": st.session_state.data_directory,
        "selected_station": st.session_state.selected_station if 'selected_station' in st.session_state else None,
        "selected_instrument": st.session_state.selected_instrument if 'selected_instrument' in st.session_state else None,
        "selected_year": st.session_state.selected_year,
        "selected_day": st.session_state.selected_day,
        "last_saved": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save the configuration
    success = save_yaml(config_data, config_file)
    return success


def main():
    # Set page configuration with better defaults
    st.set_page_config(
        page_title="PhenoTag",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Define the configuration file path
    config_dir = Path(os.path.expanduser("~/.phenotag"))
    config_file = config_dir / "sites_spectral_phenocams_session_config.yaml"
    
    # Load previous session configuration if available
    session_config = load_session_config(config_file)
    
    # Initialize session state for configuration
    if 'data_directory' not in st.session_state:
        st.session_state.data_directory = session_config.get('data_directory', "")
    if 'selected_station' not in st.session_state:
        st.session_state.selected_station = session_config.get('selected_station')
    if 'selected_instrument' not in st.session_state:
        st.session_state.selected_instrument = session_config.get('selected_instrument')
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = session_config.get('selected_year')
    if 'selected_day' not in st.session_state:
        st.session_state.selected_day = session_config.get('selected_day')
    if 'image_data' not in st.session_state:
        st.session_state.image_data = {}
        
    # Automatic scanning is handled after sidebar creation
    
    # Load config data
    config = load_config_files()
    
    # Get the stations from the config
    stations_data = config.get('stations', {}).get('stations', {})
    
    # Create a list of station names for the dropdown
    station_names = []
    station_name_to_normalized = {}
    
    for normalized_name, station_info in stations_data.items():
        if 'name' in station_info:
            station_names.append(station_info['name'])
            station_name_to_normalized[station_info['name']] = normalized_name
    
    # Add title to the sidebar
    with st.sidebar:
        st.title("PhenoTag")
        st.caption("Phenological Annotation Tool")
        
        # Add separator for visual clarity
        st.divider()
        
        # Select station with default from session
        default_index = 0
        if st.session_state.selected_station in station_names:
            default_index = station_names.index(st.session_state.selected_station)
        
        selected_station = st.selectbox(
            "Select a station", 
            station_names,
            index=default_index,
            help="Choose a monitoring station from the list"
        )
        st.session_state.selected_station = selected_station
        
        normalized_name = None
        selected_instrument = None
        
        # Get the normalized name for the selected station
        if selected_station:
            normalized_name = station_name_to_normalized[selected_station]
            station_data = stations_data[normalized_name]
            
            # Get phenocam instruments for the selected station
            instruments = get_phenocam_instruments(station_data)
            
            # Add a dropdown for instruments if there are any
            if instruments:
                # Select instrument with default from session
                default_instr_index = 0
                if st.session_state.selected_instrument in instruments:
                    default_instr_index = instruments.index(st.session_state.selected_instrument)
                
                selected_instrument = st.selectbox(
                    "Select a phenocam", 
                    instruments,
                    index=default_instr_index,
                    help="Choose a phenocam instrument from the selected station"
                )
                st.session_state.selected_instrument = selected_instrument
            else:
                st.warning("No phenocams available for this station")
                selected_instrument = None
                st.session_state.selected_instrument = None
        
        # Add configuration expander
        with st.expander("Configuration"):
            # Data directory input with session persistence
            data_dir = st.text_input(
                "Data Directory", 
                value=st.session_state.data_directory,
                placeholder="/path/to/data",
                help="Root directory containing phenocam data. Expected structure: {data_dir}/{station}/phenocams/products/{instrument}/L1/{year}/{doy}",
            )
            
            # Update session state if changed
            if data_dir != st.session_state.data_directory:
                st.session_state.data_directory = data_dir
                # Auto-save when data directory changes
                save_session_config()
            
            # Session management buttons with improved layout
            st.subheader("Session Management")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Session", use_container_width=True):
                    # Use success message instead of status container
                    if save_session_config():
                        st.success("Session saved successfully!")
                    else:
                        st.error("Failed to save session")
            
            with col2:
                if st.button("🔄 Reset Session", use_container_width=True):
                    # Clear session state without using status container
                    for key in ['data_directory', 'selected_station', 'selected_instrument', 
                                'selected_year', 'selected_day', 'image_data']:
                        if key in st.session_state:
                            if key == 'image_data':
                                st.session_state[key] = {}
                            else:
                                st.session_state[key] = None
                    
                    st.session_state.data_directory = ""
                    st.success("Session reset successfully!")
                    time.sleep(1)  # Brief pause to show the message
                    st.rerun()
        
        # Move scan button outside the expander for better visibility
        st.divider()
        
        # Check if we have the necessary data to enable the scan button
        can_scan = normalized_name and selected_instrument and st.session_state.data_directory
        valid_dir = can_scan and os.path.isdir(st.session_state.data_directory)
        
        # Status section with scan button
        scan_header_col1, scan_header_col2 = st.columns([3, 1])
        with scan_header_col1:
            st.subheader("Image Scanner")
        with scan_header_col2:
            # Show a small status indicator
            if valid_dir:
                st.success("Ready", icon="✅")
            elif can_scan:
                st.warning("Invalid path", icon="⚠️")
            else:
                st.info("Configure", icon="ℹ️")
        
        # Create the scan button with appropriate state
        if can_scan:
            if valid_dir:
                if st.button("🔍 Scan for Images", type="primary", use_container_width=True):
                    st.session_state.scan_requested = True
                    st.session_state.scan_instrument = selected_instrument
                    st.session_state.scan_station = normalized_name
                    st.write("Starting scan...")
                    st.rerun()  # Rerun to start the scan in a clean state
            else:
                st.error("⚠️ Invalid directory path. Please enter a valid data directory.")
                # Disabled button for better UX
                st.button("🔍 Scan for Images", disabled=True, use_container_width=True)
        else:
            # Show a disabled button with tooltip
            st.button(
                "🔍 Scan for Images", 
                disabled=True, 
                help="Select a station, instrument, and valid data directory first",
                use_container_width=True
            )
    
    # Check if we need to auto-scan based on loaded configuration
    if (not hasattr(st.session_state, 'scan_requested') or not st.session_state.scan_requested) and \
       'image_data' not in st.session_state and \
       st.session_state.data_directory and \
       st.session_state.selected_station and \
       st.session_state.selected_instrument and \
       os.path.isdir(st.session_state.data_directory):
        # We have valid configuration but no image data - set up auto-scan
        normalized_name = station_name_to_normalized.get(st.session_state.selected_station)
        if normalized_name:
            st.session_state.scan_requested = True
            st.session_state.scan_station = normalized_name
            st.session_state.scan_instrument = st.session_state.selected_instrument
            st.session_state.auto_scan = True  # Flag to indicate this is an automatic scan
            st.rerun()  # Rerun to trigger the scan in a clean state
    
    # Handle scanning request outside of expander
    if hasattr(st.session_state, 'scan_requested') and st.session_state.scan_requested:
        scan_container = st.container()
        with scan_container:
            # Check if this is an automatic scan
            is_auto_scan = hasattr(st.session_state, 'auto_scan') and st.session_state.auto_scan
            
            # Display appropriate heading based on scan type
            if is_auto_scan:
                st.subheader("Auto-scanning based on saved configuration...")
            else:
                st.subheader("Scanning for images...")
            
            st.write("Starting image scan...")
            # Show progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Get values from session state
            normalized_name = st.session_state.scan_station
            selected_instrument = st.session_state.scan_instrument
            
            # Find images for the selected instrument
            status_text.write(f"Looking for images in {normalized_name}/{selected_instrument}...")
            progress_bar.progress(25)
            
            try:
                # Execute the search with progress updates
                image_data = find_phenocam_images(
                    base_dir=st.session_state.data_directory,
                    station_name=normalized_name,
                    instrument_id=selected_instrument
                )
                
                # Update progress between steps
                progress_bar.progress(50)
                status_text.write("Processing image data...")
                
                # Small delay to show progress
                time.sleep(0.5)
                progress_bar.progress(75)
                status_text.write("Finalizing...")
                
                # Small delay for visual feedback
                time.sleep(0.5)
                progress_bar.progress(100)
                status_text.write("✅ Scan completed successfully!")
            except Exception as e:
                # Handle errors
                progress_bar.progress(100)
                status_text.write(f"❌ Error during scan: {str(e)}")
                st.error(f"Error during scan: {str(e)}")
                image_data = {}
            
            if image_data:
                # Store in session state for later use
                if 'image_data' not in st.session_state:
                    st.session_state.image_data = {}
                st.session_state.image_data[f"{normalized_name}_{selected_instrument}"] = image_data
                
                # Reset year and day selections only if not in auto-scan mode
                if not is_auto_scan:
                    st.session_state.selected_year = None
                    st.session_state.selected_day = None
                
                # Auto-save the session
                save_session_config()
                
                # Display summary
                years = list(image_data.keys())
                years.sort(reverse=True)
                
                # Show success message
                if is_auto_scan:
                    st.success(f"Successfully loaded images for {selected_instrument} from saved session!")
                else:
                    st.success(f"Found images for {selected_instrument}!")
                
                # Show metrics
                total_days = sum(len(image_data[year]) for year in years)
                total_images = sum(len(files) for year in years for files in image_data[year].values())
                
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("Years", len(years))
                metrics_col2.metric("Days", total_days)
                metrics_col3.metric("Images", total_images)
                
                # Show years
                st.write(f"Years available: {', '.join(years[:3])}" + 
                         (f"... and {len(years) - 3} more" if len(years) > 3 else ""))
            else:
                st.error(f"No images found for {selected_instrument}")
                st.warning(
                    f"No images found for {selected_instrument}. "
                    f"Check that the path follows the structure: "
                    f"{st.session_state.data_directory}/{normalized_name}/phenocams/products/{selected_instrument}/L1/..."
                )
            
            # Reset scan request flags
            st.session_state.scan_requested = False
            if hasattr(st.session_state, 'auto_scan'):
                st.session_state.auto_scan = False
    
    # Display the selected station in the main content area with better styling
    if selected_station:
        st.header(f"Station: {selected_station}", divider="rainbow")
        
        # Display the selected instrument if one was selected
        if selected_instrument:
            st.subheader(f"Phenocam: {selected_instrument}", divider=True)
            
            # Display image data if available in session state
            key = f"{normalized_name}_{selected_instrument}"
            if 'image_data' in st.session_state and key in st.session_state.image_data:
                image_data = st.session_state.image_data[key]
                
                # Show summary statistics
                years = list(image_data.keys())
                years.sort(reverse=True)
                
                if years:
                    total_days = sum(len(image_data[year]) for year in years)
                    total_images = sum(len(files) for year in years for files in image_data[year].values())
                    
                    st.write(f"Total: {len(years)} years, {total_days} days, {total_images} images")
                    
                    # Year and day selection
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Default to the latest year if none selected
                        if st.session_state.selected_year is None or st.session_state.selected_year not in years:
                            st.session_state.selected_year = years[0]
                        
                        selected_year = st.selectbox(
                            "Select Year", 
                            years,
                            index=years.index(st.session_state.selected_year)
                        )
                        
                        # Auto-save if year selection changed
                        if selected_year != st.session_state.selected_year:
                            st.session_state.selected_year = selected_year
                            save_session_config()
                    
                    # Get days for the selected year
                    year_data = image_data[selected_year]
                    days = list(year_data.keys())
                    days.sort(reverse=True)
                    
                    with col2:
                        if days:
                            # Default to the latest day if none selected
                            if st.session_state.selected_day is None or st.session_state.selected_day not in days:
                                st.session_state.selected_day = days[0]
                            
                            selected_day = st.selectbox(
                                "Select Day", 
                                days,
                                index=days.index(st.session_state.selected_day)
                            )
                            
                            # Auto-save if day selection changed
                            if selected_day != st.session_state.selected_day:
                                st.session_state.selected_day = selected_day
                                save_session_config()
                    
                    # Display data for the selected day
                    if days:
                        # Create DataFrame for the data_editor
                        df = create_image_dataframe(year_data, selected_day)
                        
                        if not df.empty:
                            # Display data_editor with images and annotation controls
                            st.write(f"## Images for Year {selected_year}, Day {selected_day}")
                            
                            # Initialize session state for selected image if not exists
                            session_key = f"{selected_year}_{selected_day}_selected_image"
                            if session_key not in st.session_state or st.session_state[session_key] is None:
                                # Set the first image as default if there are any images
                                if not df.empty:
                                    st.session_state[session_key] = df.iloc[0]['file_path']
                                else:
                                    st.session_state[session_key] = None
                            
                            # Function to display the selected image in full size
                            def display_selected_image(image_path):
                                if image_path and image_path in df['file_path'].values:
                                    # Find the index of this image in the dataframe
                                    image_index = df[df['file_path'] == image_path].index[0]
                                    st.write(f"Displaying image {image_index + 1} of {len(df)}")
                                    
                                    processor = ImageProcessor()
                                    if processor.load_image(image_path):
                                        img = processor.get_image()
                                        if img is not None:
                                            # Convert BGR to RGB for Streamlit
                                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                            # Display image in a centered layout
                                            col1, col2, col3 = st.columns([1, 3, 1])
                                            with col2:
                                                st.image(img, caption=os.path.basename(image_path), use_container_width=True)
                                            return True
                                    else:
                                        st.error(f"Failed to load image: {image_path}")
                                        return False
                                return False
                            
                            # Create container for the image display
                            with st.container():
                                # Display selected image
                                st.subheader("Image Preview", divider=True)
                                current_image_path = st.session_state[session_key]
                                display_selected_image(current_image_path)
                            
                            # Add a spacing between image preview and data editor
                            st.write("")
                            
                            # Add navigation buttons above the data editor
                            st.subheader("Image Navigation", divider=True)
                            nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
                            
                            # Find current index in the dataframe
                            current_index = 0
                            if current_image_path in df['file_path'].values:
                                current_index = df[df['file_path'] == current_image_path].index[0]
                            
                            with nav_col1:
                                # Create a unique key for prev button to avoid interference
                                prev_button_key = f"prev_button_{selected_year}_{selected_day}"
                                if st.button("⬅️ Previous Image", 
                                           disabled=current_index <= 0,
                                           use_container_width=True,
                                           key=prev_button_key):
                                    # Get the previous image path
                                    prev_index = max(0, current_index - 1)
                                    prev_image_path = df.iloc[prev_index]['file_path']
                                    # Update session state
                                    st.session_state[session_key] = prev_image_path
                                    st.rerun()
                                    
                            with nav_col2:
                                # Display current position
                                st.markdown(f"**Image {current_index + 1} of {len(df)}**", 
                                           help="Current image position")
                                
                            with nav_col3:
                                # Create a unique key for next button to avoid interference
                                next_button_key = f"next_button_{selected_year}_{selected_day}"
                                if st.button("Next Image ➡️", 
                                           disabled=current_index >= len(df) - 1,
                                           use_container_width=True,
                                           key=next_button_key):
                                    # Get the next image path
                                    next_index = min(len(df) - 1, current_index + 1)
                                    next_image_path = df.iloc[next_index]['file_path']
                                    # Update session state
                                    st.session_state[session_key] = next_image_path
                                    st.rerun()
                            
                            # Configure column settings for data editor with thumbnails
                            column_config = {
                                "thumbnail": st.column_config.ImageColumn(
                                    "Preview", help="Click to select this image", width="medium"),
                                "filename": st.column_config.TextColumn("Filename", width="medium"),
                                "file_path": st.column_config.TextColumn("File Path", width="medium"),
                                "discard_file": st.column_config.CheckboxColumn("Discard File", width="small"),
                                "snow_presence": st.column_config.CheckboxColumn("Snow Presence", width="small"),
                                **{f"{roi}_discard": st.column_config.CheckboxColumn(f"{roi} Discard", width="small") 
                                   for roi in ["ROI_01", "ROI_02", "ROI_03"]},
                                **{f"{roi}_snow": st.column_config.CheckboxColumn(f"{roi} Snow", width="small")
                                   for roi in ["ROI_01", "ROI_02", "ROI_03"]}
                            }
                            
                            # Add a selection widget to allow direct image selection
                            st.subheader("Image Selection", divider=True)
                            
                            # Create a selectbox for selecting an image by filename
                            filenames = df['filename'].tolist()
                            file_paths = df['file_path'].tolist()
                            file_dict = dict(zip(filenames, file_paths))
                            
                            # Find current filename
                            current_filename = os.path.basename(current_image_path) if current_image_path else filenames[0] if filenames else ""
                            
                            selected_filename = st.selectbox(
                                "Select image by filename",
                                options=filenames,
                                index=filenames.index(current_filename) if current_filename in filenames else 0,
                                key=f"filename_selector_{selected_year}_{selected_day}"
                            )
                            
                            # Track the previous filename selection to prevent infinite loops
                            filename_state_key = f"prev_filename_{selected_year}_{selected_day}"
                            if filename_state_key not in st.session_state:
                                st.session_state[filename_state_key] = current_filename
                            
                            # Only rerun if the selection actually changed from the last known state
                            if (selected_filename in file_dict and 
                                file_dict[selected_filename] != current_image_path and 
                                selected_filename != st.session_state[filename_state_key]):
                                # Store the current selection to avoid infinite loops
                                st.session_state[filename_state_key] = selected_filename
                                # Update the selected image
                                st.session_state[session_key] = file_dict[selected_filename]
                                # Rerun to update the display
                                st.rerun()
                                
                            # Add a spacing before the data editor
                            st.write("")
                            
                            # Subheader for data editor section
                            st.subheader("Image Annotations and Data", divider=True)
                            
                            # Add instructions for using thumbnails
                            st.info("👉 Click on a thumbnail to select that image for viewing.")
                            
                            # Enable image selection by clicking on thumbnails
                            if current_image_path:
                                # Find the index of the current file in the dataframe
                                current_row_index = df[df['file_path'] == current_image_path].index[0] if current_image_path in df['file_path'].values else 0
                                
                                # Create the data editor with thumbnails
                                edited_df = st.data_editor(
                                    df,
                                    column_config=column_config,
                                    use_container_width=True,
                                    num_rows="fixed",
                                    hide_index=False,  # Show index for easier selection
                                    column_order=["thumbnail", "filename", "discard_file", "snow_presence"] + 
                                                [f"{roi}_{attr}" for roi in ["ROI_01", "ROI_02", "ROI_03"] 
                                                 for attr in ["discard", "snow"]],
                                    key=f"data_editor_{selected_year}_{selected_day}"
                                )
                                
                                # Store the last edited data in session_state to prevent infinite loops
                                editor_state_key = f"last_editor_state_{selected_year}_{selected_day}"
                                if editor_state_key not in st.session_state:
                                    st.session_state[editor_state_key] = None
                                
                                # Check if an image was clicked by detecting changes in edited dataframe
                                if edited_df is not None and 'thumbnail' in edited_df.columns:
                                    # Convert current dataframe to a hashable representation for comparison
                                    current_df_state = tuple(row['file_path'] for i, row in edited_df.iterrows())
                                    
                                    # Only update if this is a new edit (prevents infinite loops)
                                    if st.session_state[editor_state_key] != current_df_state:
                                        # Store current state to avoid repeating
                                        st.session_state[editor_state_key] = current_df_state
                                        
                                        # Check for changes in thumbnail that might indicate a click
                                        for i, row in edited_df.iterrows():
                                            if row['file_path'] != current_image_path:
                                                # Different thumbnail clicked, update selection
                                                st.session_state[session_key] = row['file_path']
                                                st.rerun()
                                                break
                            
                            
                            # Add a save button with better UI
                            st.divider()
                            save_col1, save_col2 = st.columns([1, 1])
                            with save_col1:
                                # Use success/error messages instead of status to avoid nested expanders
                                if st.button("💾 Save Annotations", type="primary", use_container_width=True):
                                    # Get the image data key
                                    key = f"{normalized_name}_{selected_instrument}"
                                    
                                    if key in st.session_state.image_data:
                                        # Update image data with values from the edited DataFrame
                                        if edited_df is not None:
                                            for i, row in edited_df.iterrows():
                                                file_path = row['file_path']
                                                
                                                # Update quality data
                                                st.session_state.image_data[key][selected_year][selected_day][file_path]['quality'] = {
                                                    'discard_file': row['discard_file'],
                                                    'snow_presence': row['snow_presence']
                                                }
                                                
                                                # Update ROI data
                                                for roi in ["ROI_01", "ROI_02", "ROI_03"]:
                                                    if f"{roi}_discard" in row and f"{roi}_snow" in row:
                                                        st.session_state.image_data[key][selected_year][selected_day][file_path]['rois'][roi] = {
                                                            'discard_roi': row[f"{roi}_discard"],
                                                            'snow_presence': row[f"{roi}_snow"],
                                                            'annotated_flags': st.session_state.image_data[key][selected_year][selected_day][file_path]['rois'][roi].get('annotated_flags', [])
                                                        }
                                        
                                        # Save annotations to disk
                                        success, msg = save_annotations(
                                            st.session_state.image_data[key],
                                            st.session_state.data_directory,
                                            normalized_name,
                                            selected_instrument,
                                            selected_year,
                                            selected_day
                                        )
                                        
                                        # Save session config to remember where we left off
                                        session_saved = save_session_config()
                                        
                                        if success and session_saved:
                                            st.success(f"Annotations saved to {msg} and session saved successfully!")
                                        elif success:
                                            st.warning(f"Annotations saved to {msg}, but failed to save session.")
                                        elif session_saved:
                                            st.warning(f"Failed to save annotations: {msg}, but session saved successfully.")
                                        else:
                                            st.error(f"Failed to save annotations: {msg} and failed to save session.")
                            
                            with save_col2:
                                if st.button("🔄 Reset Annotations", use_container_width=True):
                                    st.rerun()  # Simply reload the page to reset the editor
                        else:
                            st.info(f"No images found for Day {selected_day}")
            else:
                if st.session_state.data_directory and os.path.isdir(st.session_state.data_directory):
                    st.info("Click 'Scan for images' in the Configuration panel to view image data")
                else:
                    st.info("Enter a valid data directory in the Configuration section to view image data")


if __name__ == "__main__":
    main() 