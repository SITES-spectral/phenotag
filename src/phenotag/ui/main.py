import streamlit as st
import os
import pandas as pd
import numpy as np
import time
import cv2
import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Use absolute imports
from phenotag.config import load_config_files
from phenotag.io_tools import find_phenocam_images, save_yaml, save_annotations, load_session_config
from phenotag.processors.image_processor import ImageProcessor
from phenotag.ui.calendar_component import create_calendar, get_month_with_most_images, format_day_range


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
        "selected_days": st.session_state.selected_days if 'selected_days' in st.session_state else [],
        "selected_month": st.session_state.selected_month if 'selected_month' in st.session_state else None,
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
    if 'selected_days' not in st.session_state:
        st.session_state.selected_days = []
    if 'selected_month' not in st.session_state:
        st.session_state.selected_month = None
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
        
        # Reset notification flag if station selection changed
        if st.session_state.selected_station != selected_station and hasattr(st.session_state, 'ready_notified'):
            st.session_state.ready_notified = False
            
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
                
                # Reset notification flag if instrument selection changed
                if st.session_state.selected_instrument != selected_instrument and hasattr(st.session_state, 'ready_notified'):
                    st.session_state.ready_notified = False
                    
                st.session_state.selected_instrument = selected_instrument
                
                # Add year selector if we have image data for this instrument
                key = f"{normalized_name}_{selected_instrument}"
                if 'image_data' in st.session_state and key in st.session_state.image_data:
                    # Get years from image data
                    image_data = st.session_state.image_data[key]
                    years = list(image_data.keys())
                    years.sort(reverse=True)  # Sort in descending order (newest first)
                    
                    if years:
                        
                        # Default to the latest year if none selected
                        if ('selected_year' not in st.session_state or 
                            st.session_state.selected_year not in years):
                            st.session_state.selected_year = years[0]
                        
                        # Year selector
                        selected_year = st.selectbox(
                            "Select Year", 
                            years,
                            index=years.index(st.session_state.selected_year) if st.session_state.selected_year in years else 0,
                            help="Choose a year to view"
                        )
                        
                        # Update session state if changed
                        if selected_year != st.session_state.selected_year:
                            st.session_state.selected_year = selected_year
                            # Reset day selection when year changes
                            if 'selected_day' in st.session_state:
                                st.session_state.selected_day = None
                            # Reset month selection
                            st.session_state.selected_month = None
                            # Reset selected days
                            st.session_state.selected_days = []
                            # Auto-save when selection changes
                            save_session_config()
                            # Trigger a rerun to update the UI
                            st.rerun()

                        # Get the month with most images to display in calendar if not set
                        if st.session_state.selected_month is None:
                            st.session_state.selected_month = get_month_with_most_images(selected_year, image_data)

                        # Create a container for month and day selectors
                        with st.container():
                            # Create two columns for month and day selectors
                            month_col, day_col = st.columns(2)
                            
                            with month_col:
                                # Month selector
                                month_names = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, 13)]
                                selected_month_idx = st.selectbox(
                                    "Select Month",
                                    range(1, 13),
                                    format_func=lambda m: month_names[m-1],
                                    index=st.session_state.selected_month-1,
                                    help="Choose a month to view in the calendar"
                                )

                                # Update month if changed
                                if selected_month_idx != st.session_state.selected_month:
                                    st.session_state.selected_month = selected_month_idx
                                    # Reset selected days when month changes
                                    st.session_state.selected_days = []
                                    st.rerun()

                            with day_col:
                                # Get days for the selected year and month
                                year_data = image_data[selected_year]
                                days = list(year_data.keys())
                                days.sort(reverse=True)  # Sort days in descending order

                                

                        # Add calendar view below month and day selection
                        with st.expander("📅 Calendar View (Select Days)", expanded=True):
                            selected_days, selected_week = create_calendar(
                                int(selected_year),
                                st.session_state.selected_month,
                                image_data
                            )

                        # Store selected days
                        if selected_days:
                            st.session_state.selected_days = selected_days
                            # Select the first day as current day if no day is selected
                            if not st.session_state.selected_day or st.session_state.selected_day not in selected_days:
                                st.session_state.selected_day = str(selected_days[0])
                                save_session_config()
            else:
                st.warning("No phenocams available for this station")
                selected_instrument = None
                st.session_state.selected_instrument = None
        
        st.divider()
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
                # Reset the notification flag when directory changes
                if hasattr(st.session_state, 'ready_notified'):
                    st.session_state.ready_notified = False
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
                                'selected_year', 'selected_day', 'selected_days', 'selected_month',
                                'image_data', 'ready_notified']:
                        if key in st.session_state:
                            if key == 'image_data':
                                st.session_state[key] = {}
                            elif key == 'selected_days':
                                st.session_state[key] = []
                            else:
                                st.session_state[key] = None
                    
                    st.session_state.data_directory = ""
                    st.success("Session reset successfully!")
                    time.sleep(1)  # Brief pause to show the message
                    st.rerun()
        
        
        # Check if we have the necessary data to enable the scan button
        can_scan = normalized_name and selected_instrument and st.session_state.data_directory
        valid_dir = can_scan and os.path.isdir(st.session_state.data_directory)
        
        
        # Use toast for ready status notification
        if valid_dir and not hasattr(st.session_state, 'ready_notified'):
            st.toast("Scanner is ready! Click 'Scan for Images' to continue.", icon="✅")
            st.session_state.ready_notified = True
        
        # Only show warnings/info if there's an issue
        if can_scan and not valid_dir:
            st.warning("Invalid directory path. Please enter a valid data directory.", icon="⚠️")
        elif not can_scan and st.session_state.data_directory:
            st.info("Please select a station and instrument to continue.", icon="ℹ️")
        
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
                
                # Get the years from the image data first
                years = list(image_data.keys())
                years.sort(reverse=True)

                # Set the year to the latest year regardless of scan mode
                # This ensures we always have a year selected after scanning
                if years:
                    st.session_state.selected_year = years[0]  # Latest year (they're sorted in reverse)

                    # Also set a default day if available for that year
                    if years[0] in image_data and image_data[years[0]]:
                        days = list(image_data[years[0]].keys())
                        days.sort(reverse=True)  # Sort days in reverse order too
                        if days:
                            st.session_state.selected_day = days[0]

                # Auto-save the session
                save_session_config()
                
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

            # Add a small delay to ensure metrics are visible, then rerun to refresh UI
            time.sleep(1.5)
            st.rerun()
    
    # Create three main containers for the new layout
    top_container = st.container()
    center_container = st.container()
    bottom_container = st.container()

    # Check if we have image data in the session state
    key = f"{normalized_name}_{selected_instrument}" if normalized_name and selected_instrument else None
    image_data = st.session_state.image_data.get(key, {}) if key and 'image_data' in st.session_state else {}

    # Debug info to help with troubleshooting
    with st.sidebar.expander("Debug Info", expanded=False):
        st.write(f"Selected key: {key}")
        st.write(f"Year: {st.session_state.selected_year if 'selected_year' in st.session_state else 'None'}")
        if image_data:
            st.write(f"Years in data: {list(image_data.keys())}")
        else:
            st.write("No image data found")

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
                # Auto-save this change
                save_session_config()

        # Only continue if we now have a valid year
        if selected_year and selected_year in image_data:
            # Top container is left empty as requested
            with top_container:
                # No titles or subtitles in the main canvas
                doys = list(image_data[selected_year].keys())
                doys.sort(reverse=True)  # Sort days in descending order

                # Get the selected days from calendar if available
                if 'selected_days' in st.session_state and st.session_state.selected_days:
                    selection_text = format_day_range(st.session_state.selected_days, int(selected_year))
                    st.write(f"**Selected: {selection_text}**")

                    # Build a list of day strings from selected days
                    selected_doys = [str(day) for day in st.session_state.selected_days]

                    # Filter to only include days that have data
                    valid_selected_doys = [day for day in selected_doys if day in doys]

                    if valid_selected_doys:
                        # Used for UI display and filtering images
                        selected_day = valid_selected_doys[0]  # Use first day for display
                        st.session_state.selected_day = selected_day
                    else:
                        # Fallback if none of the selected days have data
                        selected_day = doys[0] if doys else None
                        st.session_state.selected_day = selected_day
                # Handle case when no day is selected or no days from calendar
                elif 'selected_day' not in st.session_state or not st.session_state.selected_day or st.session_state.selected_day not in doys:
                    selected_day = doys[0] if doys else None
                    st.session_state.selected_day = selected_day
                else:
                    selected_day = st.session_state.selected_day

                # Get file paths for all selected days
                daily_filepaths = []

                # If we have selected days from the calendar, use those
                if 'selected_days' in st.session_state and st.session_state.selected_days:
                    for doy in st.session_state.selected_days:
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
        
        with center_container:
            # Only display image data if we have both a year and a day selected
            if (selected_year and selected_year in image_data and
                'selected_day' in st.session_state and st.session_state.selected_day in image_data[selected_year]):

                selected_day = st.session_state.selected_day

                # Create two columns with the specified ratio [2,5]
                left_col, main_col = st.columns([2, 5])

                # Make sure we have file paths before attempting to display them
                if daily_filepaths:
                    with left_col:
                        # Create a DataFrame with filenames and paths
                        filenames = [os.path.basename(path) for path in daily_filepaths]
                        df = pd.DataFrame(
                            index=enumerate(daily_filepaths),
                            data={"Filename": filenames}
                        )

                        # Show the interactive dataframe with row selection
                        event = st.dataframe(
                            df,
                            column_config={
                                "Filename": st.column_config.TextColumn(
                                    "File",
                                    help="Click to select this file",
                                    width="medium"
                                )
                            },
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row"
                        )

                        # Also add a text description of how many images are available
                        if 'selected_days' in st.session_state and st.session_state.selected_days:
                            selection_text = format_day_range(st.session_state.selected_days, int(selected_year))
                            st.write(f"{len(daily_filepaths)} images available for {selection_text}")
                        else:
                            st.write(f"{len(daily_filepaths)} images available for day {selected_day}")

                        # Instructions for the user
                        st.write("**Click on a row to view the image**")

                    # Display the selected image in the main column
                    with main_col:
                        if event and event.selection.rows:
                            index = event.selection.rows[0]
                            filepath = daily_filepaths[index]
                            
                            if filepath:
                                processor = ImageProcessor()
                                processor.load_image(filepath)
                                img = processor.get_image()
                                st.image(img, caption=os.path.basename(filepath), use_container_width=True)
                        else:
                            st.info("No image selected. Click on a row to view an image.")
                else:
                    # No files found for the selected days
                    if 'selected_days' in st.session_state and st.session_state.selected_days:
                        st.warning(f"No image files found for the selected days in year {selected_year}")
                    else:
                        st.warning(f"No image files found for day {selected_day} in year {selected_year}")
            else:
                # No year or day selected
                st.info("Select a year and day to view images")

        # Bottom container for additional information
        with bottom_container:
            if selected_year and selected_year in image_data:
                # Create an expander to show the raw data (useful for debugging)
                with st.expander("Raw Data for Selected Year", expanded=False):
                    st.write(image_data.get(selected_year))
        # Store important data in session state, but don't display titles/subtitles
    if selected_station:
        # Store station info in session state but don't display
        st.session_state.current_station = selected_station
        if selected_instrument:
            # Store instrument info in session state but don't display
            st.session_state.current_instrument = selected_instrument
            
            # Skip most of the image data display for now during refactoring
            key = f"{normalized_name}_{selected_instrument}"
            if False and 'image_data' in st.session_state and key in st.session_state.image_data:
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
                # Minimal placeholder for info message
                if st.session_state.data_directory and os.path.isdir(st.session_state.data_directory):
                    # This info will be displayed in the main layout in the future
                    pass
                else:
                    # This info will be displayed in the main layout in the future
                    pass


def handle_file_selection(edited_df):
    """Handle file selection from the data editor."""
    if edited_df is not None:
        # Get the current selection from the data editor
        selected_rows = edited_df[edited_df['Filename'].notna()]
        if not selected_rows.empty:
            # Update the selected index in session state
            st.session_state.selected_image_index = selected_rows.index[0]
            st.rerun()


if __name__ == "__main__":
    main() 