import streamlit as st
import os
import pandas as pd
import numpy as np
import time
import cv2
import datetime
import calendar
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# Use absolute imports
from phenotag.config import load_config_files
from phenotag.io_tools import (
    find_phenocam_images, save_yaml, save_annotations, load_session_config,
    # Directory scanner functions (new implementation)
    get_available_years, get_days_in_year, get_days_in_month,
    count_images_in_days, format_month_year, create_placeholder_data,
    # Lazy loader function
    lazy_find_phenocam_images,
    # Importing get_available_days_in_year from lazy_scanner
    get_available_days_in_year
)
# Import directory scanner's get_month_with_most_images with a renamed alias
from phenotag.io_tools import get_month_with_most_images as find_best_month
from phenotag.processors.image_processor import ImageProcessor
from phenotag.ui.calendar_component import create_calendar, format_day_range
# Import calendar's get_month_with_most_images for backward compatibility
from phenotag.ui.calendar_component import get_month_with_most_images


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
        
        # Check if station selection changed
        station_changed = st.session_state.selected_station != selected_station

        # Reset notification flag if station selection changed
        if station_changed and hasattr(st.session_state, 'ready_notified'):
            st.session_state.ready_notified = False

        # Store the old station for later check
        old_station = st.session_state.selected_station

        # Update the selected station
        st.session_state.selected_station = selected_station

        # Clear selected instrument when station changes to force rescanning
        if station_changed:
            st.session_state.selected_instrument = None
        
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
                
                # Check if instrument selection changed
                instrument_changed = st.session_state.selected_instrument != selected_instrument

                # Reset notification flag if instrument selection changed
                if instrument_changed and hasattr(st.session_state, 'ready_notified'):
                    st.session_state.ready_notified = False

                # Store the old instrument for later check
                old_instrument = st.session_state.selected_instrument

                st.session_state.selected_instrument = selected_instrument

                # If the instrument changed, we need to check if we need to scan for this combination
                if instrument_changed:
                    # Get the key for this station+instrument combination
                    key = f"{normalized_name}_{selected_instrument}"

                    # If we don't have data for this combination or only have a no_l1_data marker, trigger a scan
                    needs_scan = False
                    if 'image_data' not in st.session_state or key not in st.session_state.image_data:
                        needs_scan = True
                    # Check if we only have the special no_l1_data marker and the user is trying again
                    elif len(st.session_state.image_data[key]) == 1 and "_no_l1_data" in st.session_state.image_data[key]:
                        # Remove the marker and trigger a new scan (allows user to try again after processing L1)
                        st.session_state.image_data.pop(key, None)
                        needs_scan = True

                    if needs_scan:
                        if st.session_state.data_directory and os.path.isdir(st.session_state.data_directory):
                            st.session_state.scan_requested = True
                            st.session_state.scan_station = normalized_name
                            st.session_state.scan_instrument = selected_instrument
                            st.session_state.auto_scan = True
                            st.rerun()  # Rerun to trigger the scan
                
                # Add year selector if we have image data for this instrument
                key = f"{normalized_name}_{selected_instrument}"

                # Check if we have the special no_l1_data flag
                if ('image_data' in st.session_state and
                    key in st.session_state.image_data and
                    len(st.session_state.image_data[key]) == 1 and
                    "_no_l1_data" in st.session_state.image_data[key]):
                    # Show a reminder message about missing L1 data
                    st.warning(f"No L1 data found for {selected_instrument}. Process L0 images to L1 before annotation.")
                    st.info("Click 'Scan for Images' again after processing images to refresh.")

                # Normal case - we have actual image data
                elif ('image_data' in st.session_state and
                      key in st.session_state.image_data):
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
                            # Check if we're using lazy loading
                            if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                # For lazy loading, we need to build month information from directory structure
                                scan_info = st.session_state.scan_info
                                base_dir = scan_info['base_dir']
                                station_name = scan_info['station_name']
                                instrument_id = scan_info['instrument_id']

                                # Get days for this year
                                # Find the month with most images
                                best_month = find_best_month(
                                    base_dir,
                                    station_name,
                                    instrument_id,
                                    selected_year
                                )

                                # Get all available days for the year
                                all_days = get_days_in_year(
                                    base_dir,
                                    station_name,
                                    instrument_id,
                                    selected_year
                                )

                                # Create placeholder data structure
                                calendar_data = create_placeholder_data(selected_year, all_days)

                                # Use best month for selection
                                st.session_state.selected_month = best_month
                            else:
                                # Use the full image data with the calendar component's function
                                # This takes different arguments (year, image_data) than the directory scanner version
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

                                    # Force a refresh of the calendar for the new month if using lazy loading
                                    if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                        # Get scan info
                                        scan_info = st.session_state.scan_info
                                        base_dir = scan_info['base_dir']
                                        station_name = scan_info['station_name']
                                        instrument_id = scan_info['instrument_id']

                                        # Get all days for this year
                                        all_days = get_days_in_year(
                                            base_dir,
                                            station_name,
                                            instrument_id,
                                            selected_year
                                        )

                                        # Filter to days in the selected month
                                        available_days = get_days_in_month(
                                            selected_year,
                                            selected_month_idx,  # Use the newly selected month
                                            all_days
                                        )

                                        # Create placeholder data structure for the calendar
                                        calendar_data = create_placeholder_data(selected_year, available_days)

                                        # Update the image_data with days for the new month
                                        if key in st.session_state.image_data:
                                            st.session_state.image_data[key] = calendar_data

                                    # Rerun to update the UI
                                    st.rerun()

                            # Create a three-column layout for buttons
                            button_col1, button_col2, button_col3 = st.columns(3)

                            with button_col1:
                                # Add space to align with selectbox
                                st.write("&nbsp;")
                                # Add button to load instrument ROIs from configuration
                                if st.button("🔍 Load Instrument ROIs", key="load_instrument_rois_button",
                                          help="Load ROI definitions for this instrument from stations configuration"):
                                    # Get the station and instrument data
                                    if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                        scan_info = st.session_state.scan_info
                                        station_name = scan_info['station_name']
                                        instrument_id = scan_info['instrument_id']

                                        # Load configuration
                                        config = load_config_files()
                                        stations_config = config.get('stations', {}).get('stations', {})

                                        # Extract ROIs for this instrument
                                        rois_found = False

                                        # Add detailed debug output
                                        print(f"DEBUGGING ROI LOOKUP:")
                                        print(f"1. Looking for normalized station name: '{station_name}'")
                                        print(f"2. Available stations in config: {list(stations_config.keys())}")
                                        print(f"3. Instrument ID to find: '{instrument_id}'")

                                        # Find the station in the configuration by normalized name
                                        # The station_name in scan_info should already be the normalized name
                                        if station_name in stations_config:
                                            station_data = stations_config[station_name]
                                            print(f"4. Found station '{station_name}' in config")

                                            # Add more debugging for station data structure
                                            print(f"5. Station data keys: {list(station_data.keys())}")

                                            # Check if phenocams exists
                                            if 'phenocams' not in station_data:
                                                print(f"ERROR: 'phenocams' key missing in station data")
                                                st.error(f"Configuration error: 'phenocams' key missing for station {station_name}")
                                            elif 'platforms' not in station_data['phenocams']:
                                                print(f"ERROR: 'platforms' key missing in phenocams data")
                                                st.error(f"Configuration error: 'platforms' key missing for station {station_name}")
                                            else:
                                                # List available platforms
                                                platforms = station_data['phenocams']['platforms']
                                                print(f"6. Available platforms: {list(platforms.keys())}")

                                                # Check each platform for the instrument
                                                for platform_type, platform_data in platforms.items():
                                                    print(f"7. Checking platform: {platform_type}")

                                                    if 'instruments' not in platform_data:
                                                        print(f"   - No instruments in platform {platform_type}")
                                                        continue

                                                    # List instruments in this platform
                                                    instruments = platform_data['instruments']
                                                    print(f"8. Instruments in platform {platform_type}: {list(instruments.keys())}")

                                                    if instrument_id in instruments:
                                                        print(f"9. Found instrument {instrument_id} in platform {platform_type}")
                                                        instrument_config = instruments[instrument_id]

                                                        # Check if the instrument has ROIs
                                                        print(f"10. Instrument keys: {list(instrument_config.keys())}")

                                                        if 'rois' in instrument_config:
                                                            rois = instrument_config['rois']
                                                            if rois:
                                                                print(f"11. Found ROIs: {list(rois.keys())}")
                                                            else:
                                                                print(f"11. 'rois' exists but is empty")

                                                            # Check if it has ROIs defined
                                                            if rois:
                                                                # Store the ROIs in session state with metadata
                                                                # Enhanced debugging of the ROI structure
                                                                print("\n===== DETAILED ROI STRUCTURE ANALYSIS =====")
                                                                print(f"Raw ROIs from config: {instrument_config['rois']}")

                                                                # Analyze the structure of the first ROI as a sample
                                                                if instrument_config['rois']:
                                                                    first_roi_name = next(iter(instrument_config['rois']))
                                                                    first_roi = instrument_config['rois'][first_roi_name]
                                                                    print(f"\nFirst ROI name: {first_roi_name}")
                                                                    print(f"First ROI value: {first_roi}")
                                                                    print(f"First ROI type: {type(first_roi)}")
                                                                    print(f"First ROI keys: {first_roi.keys() if isinstance(first_roi, dict) else 'Not a dictionary'}")

                                                                    # Analyze points structure
                                                                    if isinstance(first_roi, dict) and 'points' in first_roi:
                                                                        points = first_roi['points']
                                                                        print(f"\nPoints: {points}")
                                                                        print(f"Points type: {type(points)}")
                                                                        if points and len(points) > 0:
                                                                            print(f"First point: {points[0]}")
                                                                            print(f"First point type: {type(points[0])}")
                                                                            if points[0] and len(points[0]) > 0:
                                                                                print(f"First coordinate: {points[0][0]}")
                                                                                print(f"First coordinate type: {type(points[0][0])}")

                                                                    # Analyze color structure
                                                                    if isinstance(first_roi, dict) and 'color' in first_roi:
                                                                        color = first_roi['color']
                                                                        print(f"\nColor: {color}")
                                                                        print(f"Color type: {type(color)}")
                                                                        if color and len(color) > 0:
                                                                            print(f"First color component: {color[0]}")
                                                                            print(f"First color component type: {type(color[0])}")

                                                                # The ROIs in the YAML are in a YAML-friendly format (lists of lists)
                                                                # We need to convert them to a format the ImageProcessor can use
                                                                print("\n===== ATTEMPTING FORMAT CONVERSION =====")
                                                                try:
                                                                    # First, print debug info about ImageProcessor expectations
                                                                    processor = ImageProcessor()

                                                                    # Process the ROIs using our improved deserialize function
                                                                    processed_rois = deserialize_polygons(instrument_config['rois'])
                                                                    print(f"Processed ROIs structure (with tuples):")

                                                                    # Analyze the converted structure
                                                                    if processed_rois:
                                                                        first_proc_roi_name = next(iter(processed_rois))
                                                                        first_proc_roi = processed_rois[first_proc_roi_name]
                                                                        print(f"\nFirst processed ROI name: {first_proc_roi_name}")
                                                                        print(f"First processed ROI: {first_proc_roi}")
                                                                        print(f"First processed ROI type: {type(first_proc_roi)}")
                                                                        print(f"First processed ROI keys: {first_proc_roi.keys()}")

                                                                        if isinstance(first_proc_roi, dict) and 'points' in first_proc_roi:
                                                                            proc_points = first_proc_roi['points']
                                                                            print(f"\nProcessed points: {proc_points[:2]}...")
                                                                            print(f"Processed points type: {type(proc_points)}")
                                                                            if proc_points and len(proc_points) > 0:
                                                                                print(f"First processed point: {proc_points[0]}")
                                                                                print(f"First processed point type: {type(proc_points[0])}")

                                                                        if isinstance(first_proc_roi, dict) and 'color' in first_proc_roi:
                                                                            print(f"\nProcessed color: {first_proc_roi['color']}")
                                                                            print(f"Processed color type: {type(first_proc_roi['color'])}")

                                                                    # Check if the structure matches what ImageProcessor expects
                                                                    expected_structure = {
                                                                        'points': 'list of tuples [(x1,y1), (x2,y2), ...]',
                                                                        'color': 'tuple (B,G,R)',
                                                                        'thickness': 'integer',
                                                                        'alpha': 'float 0-1'
                                                                    }
                                                                    print(f"\nImageProcessor expected ROI structure: {expected_structure}")

                                                                    # Store the processed ROIs in session state
                                                                    st.session_state.instrument_rois = processed_rois
                                                                    print("\nROIs processed successfully and stored in session state.")
                                                                except Exception as e:
                                                                    print(f"Error processing ROIs: {str(e)}")
                                                                    st.warning(f"Error processing ROIs: {str(e)}. Using original format.")
                                                                    # Fallback to storing the original format which our custom overlay function can handle
                                                                    st.session_state.instrument_rois = instrument_config['rois']

                                                                st.session_state.roi_instrument_id = instrument_id
                                                                st.session_state.roi_source = f"stations.yaml - {station_name}"

                                                                # Get ROI names for display
                                                                roi_names = list(instrument_config['rois'].keys())
                                                                print(f"12. Found ROIs: {roi_names}")

                                                                # Show success message with details
                                                                st.success(f"Loaded {len(roi_names)} ROI definitions for {instrument_id}: {', '.join(roi_names)}")
                                                                rois_found = True
                                                                break

                                        if not rois_found:
                                            st.warning(f"No ROI definitions found for instrument {instrument_id} in station {station_name}")
                                            # Look for the instrument across all stations (in case it was moved)
                                            for station_id, station_config in stations_config.items():
                                                if 'phenocams' in station_config and 'platforms' in station_config['phenocams']:
                                                    for platform_type, platform_data in station_config['phenocams']['platforms'].items():
                                                        if 'instruments' in platform_data and instrument_id in platform_data['instruments']:
                                                            instr_config = platform_data['instruments'][instrument_id]
                                                            if 'rois' in instr_config and instr_config['rois']:
                                                                st.info(f"Found ROIs for {instrument_id} in station {station_id}. Click 'Load Instrument ROIs' again to load them.")
                                                                # Don't immediately load them - just inform the user
                                    else:
                                        st.warning("Scan information not available. Please scan for images first.")

                            with button_col2:
                                # Add a single comprehensive refresh button
                                st.write("&nbsp;") # Add space to align with selectbox
                                if st.button("🔄 Refresh Data", key="refresh_data_button",
                                          help="Refresh all data for the current selection"):
                                    # Request a full refresh but in a non-destructive way
                                    if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                        scan_info = st.session_state.scan_info
                                        station_name = scan_info['station_name']
                                        instrument_id = scan_info['instrument_id']

                                        # Set up a controlled refresh request
                                        st.session_state.scan_requested = True
                                        st.session_state.scan_station = station_name
                                        st.session_state.scan_instrument = instrument_id
                                        st.session_state.preserve_data = True  # Don't destroy existing data
                                        st.session_state.refresh_mode = True  # Mark this as a refresh operation

                                        # Clear all calendar scan cache keys to force refresh
                                        for key in list(st.session_state.keys()):
                                            if key.startswith('calendar_scanned_'):
                                                st.session_state[key] = False

                                        with st.spinner("Refreshing all data..."):
                                            # Create a small progress bar for visual feedback
                                            progress = st.progress(0)
                                            for i in range(5):
                                                progress.progress((i+1) * 20)
                                                time.sleep(0.1)  # Much shorter delays with progress
                                            st.success("Refresh complete!")
                                        st.rerun()

                                # Get days for the selected year and month
                                year_data = image_data[selected_year]
                                days = list(year_data.keys())
                                days.sort(reverse=True)  # Sort days in descending order

                                # Update the calendar image counts for lazy-loaded data
                                if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                    scan_info = st.session_state.scan_info
                                    base_dir = scan_info['base_dir']
                                    station_name = scan_info['station_name']
                                    instrument_id = scan_info['instrument_id']

                                    # Update image counts for days with placeholder data
                                    for day in days:
                                        # Skip days that aren't in the data
                                        if day not in year_data:
                                            continue

                                        # For placeholder data, count actual images
                                        if isinstance(year_data[day], dict) and '_placeholder' in year_data[day]:
                                            # Try all possible directory format variations
                                            # 1. With leading zeros (e.g., 090)
                                            day_with_zeros = day
                                            # 2. Without leading zeros (e.g., 90)
                                            day_without_zeros = day.lstrip('0') if day else '0'
                                            # 3. As plain integer (e.g., 90)
                                            day_as_int = str(int(day.lstrip('0') or '0'))

                                            # First try with the original format
                                            day_path = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / selected_year / day_with_zeros

                                            # If that doesn't exist, try without leading zeros
                                            if not day_path.exists() or not day_path.is_dir():
                                                day_path = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / selected_year / day_without_zeros

                                                # If that still doesn't exist, try as integer
                                                if not day_path.exists() or not day_path.is_dir():
                                                    day_path = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / selected_year / day_as_int

                                            # Count the images if directory exists
                                            if day_path.exists() and day_path.is_dir():
                                                # Count image files with detailed debug output
                                                image_files = list(day_path.glob("*.jp*g"))
                                                image_count = len([f for f in image_files if f.is_file()])

                                                # Print debug info
                                                print(f"Day {day} ({day_path.name}): Found {image_count} images in {day_path}")
                                                if image_count > 0:
                                                    print(f"  Sample images: {[f.name for f in image_files[:3]]}")

                                                # Update the placeholder with the actual count
                                                year_data[day]['_image_count'] = image_count

                                                # Debug output for day 90 (common problem area)
                                                if int(day.lstrip('0') or '0') == 90:
                                                    print(f"DEBUG: Updated day 90 (represented as '{day}') with count {image_count}")

                                

                        # Add calendar view below month and day selection
                        with st.expander("📅 Calendar View (Select Days)", expanded=True):
                            # Key to track if we've already scanned for this month
                            calendar_scan_key = f"calendar_scanned_{selected_year}_{st.session_state.selected_month}"

                            # Determine if we need to scan based on:
                            # 1. We haven't scanned this month/year yet
                            # 2. User explicitly requested a refresh
                            # 3. We changed months or years
                            month_changed = st.session_state.get('last_month', None) != st.session_state.selected_month
                            year_changed = st.session_state.get('last_year', None) != selected_year

                            need_scan = (not st.session_state.get(calendar_scan_key, False) or
                                        st.session_state.get('refresh_mode', False) or
                                        month_changed or year_changed)

                            # Update last month/year tracking
                            st.session_state['last_month'] = st.session_state.selected_month
                            st.session_state['last_year'] = selected_year

                            # Reset the refresh flag after checking
                            if st.session_state.get('refresh_mode', False):
                                st.session_state.refresh_mode = False

                            # Check if we need to scan days for this month
                            if need_scan and hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                with st.spinner(f"Scanning for days in {calendar.month_name[st.session_state.selected_month]} {selected_year}..."):
                                    # Add visual feedback with progress bar
                                    calendar_progress = st.progress(0)

                                    # We need to get day metadata for the calendar
                                    scan_info = st.session_state.scan_info
                                    base_dir = scan_info['base_dir']
                                    station_name = scan_info['station_name']
                                    instrument_id = scan_info['instrument_id']

                                    # Update progress
                                    calendar_progress.progress(20)

                                    # Get all available days for the year
                                    all_days = get_days_in_year(
                                        base_dir,
                                        station_name,
                                        instrument_id,
                                        selected_year
                                    )

                                    # Update progress
                                    calendar_progress.progress(40)

                                    # Log available days before filtering
                                    print(f"Calendar - Available days before filtering: {all_days}")

                                    # Update progress
                                    calendar_progress.progress(60)

                                    # Filter days to those in the selected month
                                    month_filtered_days = get_days_in_month(
                                        selected_year,
                                        st.session_state.selected_month,
                                        all_days
                                    )

                                    # Log available days after filtering
                                    print(f"Calendar - Days in month {st.session_state.selected_month}: {month_filtered_days}")

                                    available_days = month_filtered_days

                                    # Update progress
                                    calendar_progress.progress(70)

                                    # Create placeholder data structure for the calendar
                                    calendar_image_data = create_placeholder_data(selected_year, available_days)

                                    # Store the data in session state
                                    key = f"{station_name}_{instrument_id}"

                                    # Initialize image_data structure if needed
                                    if 'image_data' not in st.session_state:
                                        st.session_state.image_data = {}

                                    if key not in st.session_state.image_data:
                                        st.session_state.image_data[key] = {}

                                    # Update the image data with our placeholder for this year
                                    if selected_year not in st.session_state.image_data[key]:
                                        st.session_state.image_data[key][selected_year] = {}

                                    # Update progress
                                    calendar_progress.progress(85)

                                    # Add days to the image data
                                    for day in available_days:
                                        st.session_state.image_data[key][selected_year][day] = {"_placeholder": True}

                                    # Finish progress with animation
                                    for i in range(85, 101, 5):
                                        calendar_progress.progress(i)
                                        time.sleep(0.02)

                                    # Mark this month as scanned
                                    st.session_state[calendar_scan_key] = True

                                    # Provide feedback
                                    if available_days:
                                        st.success(f"Found {len(available_days)} days with images in {calendar.month_name[st.session_state.selected_month]} {selected_year}")
                                    else:
                                        st.info(f"No images found for {calendar.month_name[st.session_state.selected_month]} {selected_year}")

                            # Check if we're using lazy loading and have data
                            if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                                # Get the key for current station/instrument
                                scan_info = st.session_state.scan_info
                                station_name = scan_info['station_name']
                                instrument_id = scan_info['instrument_id']
                                key = f"{station_name}_{instrument_id}"

                                # See if we have data for this year/month
                                if ('image_data' in st.session_state and
                                    key in st.session_state.image_data and
                                    selected_year in st.session_state.image_data[key]):

                                    # Create calendar with existing data
                                    calendar_data = {selected_year: st.session_state.image_data[key][selected_year]}

                                    # Use data for the calendar
                                    selected_days, selected_week = create_calendar(
                                        int(selected_year),
                                        st.session_state.selected_month,
                                        calendar_data
                                    )
                                else:
                                    # No data yet - automatically trigger a scan by rerunning
                                    st.info("No data available yet. Scanning for available days...")
                                    st.session_state[calendar_scan_key] = False  # Reset the scan flag
                                    time.sleep(0.5)  # Small delay for UI
                                    st.rerun()
                            else:
                                # Use the full image data (original behavior)
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
                    # Set a flag to indicate this is a non-destructive scan
                    st.session_state.preserve_data = True
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
       st.session_state.data_directory and \
       st.session_state.selected_station and \
       st.session_state.selected_instrument and \
       os.path.isdir(st.session_state.data_directory):

        # We'll scan if either we have no image data at all
        should_scan = 'image_data' not in st.session_state

        # Or if we haven't scanned this specific station+instrument combination yet
        if not should_scan and 'image_data' in st.session_state:
            normalized_name = station_name_to_normalized.get(st.session_state.selected_station)
            key = f"{normalized_name}_{st.session_state.selected_instrument}"

            # Need to scan if:
            # 1. We don't have this key at all
            # 2. We have this key but it only contains the "_no_l1_data" flag and user is explicitly requesting a scan
            should_scan = key not in st.session_state.image_data

            # Check if we need to clean up the special no_l1_data marker to allow rescanning
            if not should_scan and key in st.session_state.image_data:
                data = st.session_state.image_data[key]
                # If the data only contains our verification flag and the user clicked "Scan"
                if len(data) == 1 and "_no_l1_data" in data:
                    # Remove the verification flag to allow a fresh scan
                    # This is just clearing our internal tracking flag that we use
                    # to avoid infinite auto-scanning loops - it's not marking any user task as complete
                    st.session_state.image_data.pop(key, None)
                    should_scan = True

        if should_scan:
            # We have valid configuration but need to scan - set up auto-scan
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
                # First, get just the available years (very fast)
                progress_bar.progress(25)
                status_text.write("Finding available years...")

                # Get years for this station/instrument (very fast, no image data loading)
                years_data = lazy_find_phenocam_images(
                    base_dir=st.session_state.data_directory,
                    station_name=normalized_name,
                    instrument_id=selected_instrument
                )

                # Get the key for this station+instrument combo
                station_instrument_key = f"{normalized_name}_{selected_instrument}"

                # Initialize or preserve image data structure
                if not years_data:
                    # No years found - but preserve existing data structure
                    if 'image_data' not in st.session_state:
                        st.session_state.image_data = {}
                    image_data = {}
                else:
                    # Initialize structure with years, preserving existing data if any
                    if 'image_data' not in st.session_state:
                        st.session_state.image_data = {}

                    # If we already have data for this station/instrument, use it
                    if station_instrument_key in st.session_state.image_data:
                        image_data = st.session_state.image_data[station_instrument_key]
                    else:
                        image_data = {}

                    # Add any new years discovered
                    for year in years_data:
                        if year not in image_data:
                            # Only initialize years we don't already have
                            image_data[year] = {}

                    progress_bar.progress(50)
                    status_text.write(f"Found {len(years_data)} years. Scanning metadata...")

                    # Set up lazy loading information - we'll only load specific
                    # data when it's actually requested by the UI
                    scan_info = {
                        "base_dir": st.session_state.data_directory,
                        "station_name": normalized_name,
                        "instrument_id": selected_instrument,
                        "years": list(years_data.keys()),
                        "lazy_loaded": True
                    }

                    # Store this scan info for later lazy loading
                    st.session_state.scan_info = scan_info

                # Progress updates
                progress_bar.progress(80)
                status_text.write("Finalizing...")

                # Better visual feedback with animated progress
                for i in range(80, 101, 5):
                    progress_bar.progress(i)
                    status_text.write(f"Finalizing scan... {i}%")
                    time.sleep(0.05)  # Much shorter incremental delays

                progress_bar.progress(100)
                status_text.write("✅ Scan completed successfully!")
            except Exception as e:
                # Handle errors
                progress_bar.progress(100)
                status_text.write(f"❌ Error during scan: {str(e)}")
                st.error(f"Error during scan: {str(e)}")
                image_data = {}
            
            if image_data:
                # Store in session state for later use - handle refresh mode specially
                if st.session_state.get('refresh_mode', False):
                    # Special handling for refresh mode - merge new data with existing
                    if station_instrument_key in st.session_state.image_data:
                        # Log refresh operation
                        print(f"Refresh mode: Merging data for {station_instrument_key}")

                        # Merge existing data with new discoveries
                        existing_data = st.session_state.image_data[station_instrument_key]

                        # Add any new years
                        for year in image_data:
                            if year not in existing_data:
                                existing_data[year] = {}

                            # For each year, merge days but don't replace existing day data
                            for day in image_data[year]:
                                if day not in existing_data[year]:
                                    existing_data[year][day] = image_data[year][day]

                        # Use the merged data
                        st.session_state.image_data[station_instrument_key] = existing_data
                    else:
                        # No existing data, just use the new data
                        st.session_state.image_data[station_instrument_key] = image_data
                else:
                    # Normal mode - replace with new data
                    st.session_state.image_data[station_instrument_key] = image_data
                
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
                
                # Show metrics - handle lazy loading differently
                if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                    # For lazy loading, we don't know total images yet, just show years
                    years_count = len(years)

                    # Get approximate day count from metadata
                    days_count = 0
                    sample_year = years[0] if years else None

                    if sample_year:
                        # Get station and instrument from scan info
                        scan_info = st.session_state.scan_info
                        base_dir = scan_info['base_dir']
                        station_name = scan_info['station_name']
                        instrument_id = scan_info['instrument_id']

                        # Get available days for the sample year
                        days = get_available_days_in_year(base_dir, station_name, instrument_id, sample_year)
                        days_count = len(days)

                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    metrics_col1.metric("Years", years_count)
                    metrics_col2.metric("Days", f"~{days_count}" if sample_year else "Unknown")
                    metrics_col3.metric("Images", "Lazy loaded")
                else:
                    # For regular loading, use the full count
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
                st.error(f"No L1 images found for {selected_instrument}")

                # Create expandable section with guidance on how to process L0 to L1
                with st.expander("How to generate L1 data for annotation", expanded=True):
                    st.markdown(f"""
                    ### No L1 data found

                    Before you can annotate images with PhenoTag, you need to process your raw images
                    to Level 1 (L1) products using the SITES Phenocams package.

                    #### Steps to generate L1 data:

                    1. **Check for L0 data**: Verify that you have raw (L0) images for this instrument

                    2. **Process L0 to L1**: Use the phenocams CLI to process raw images:
                    ```bash
                    # Activate the phenocams environment
                    source /path/to/phenocams/activate_env.sh

                    # Process L0 images to L1 products
                    phenocams l1 process --station {normalized_name} --instrument {selected_instrument}
                    ```

                    3. **Verify L1 generation**: After processing, make sure the L1 data is in the correct location:
                    ```
                    {st.session_state.data_directory}/{normalized_name}/phenocams/products/{selected_instrument}/L1/
                    ```

                    4. **Run scan again**: After generating L1 data, click 'Scan for Images' again in PhenoTag
                    """)

                # Show the structure warning after the expandable section
                st.warning(
                    f"No L1 images found for {selected_instrument}. "
                    f"Check that the path follows the structure: "
                    f"{st.session_state.data_directory}/{normalized_name}/phenocams/products/{selected_instrument}/L1/..."
                )

                # Store metadata in image_data with a special flag to prevent auto-scanning loop
                # This records that we've already checked for L1 data for this station+instrument
                if 'image_data' not in st.session_state:
                    st.session_state.image_data = {}

                # Store with a special verification flag to indicate no L1 data was found
                # This is NOT marking a task as "done" - it's just a record that we've
                # verified no L1 data exists so we don't keep auto-scanning
                st.session_state.image_data[f"{normalized_name}_{selected_instrument}"] = {"_no_l1_data": True}
            
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

                # Check if we're using lazy loading
                if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
                    # Get scan info
                    scan_info = st.session_state.scan_info
                    base_dir = scan_info['base_dir']
                    station_name = scan_info['station_name']
                    instrument_id = scan_info['instrument_id']

                    # Check if we have selected days from the calendar
                    if 'selected_days' in st.session_state and st.session_state.selected_days:
                        # Convert days to strings and ensure proper format
                        days_to_load = [str(doy).zfill(3) for doy in st.session_state.selected_days]

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
                        # Add instructional text for users
                        st.info("👇 Select a time below to view the corresponding image")

                        # Create a DataFrame with filenames, paths, and timestamps
                        filenames = [os.path.basename(path) for path in daily_filepaths]

                        # Extract data from filenames using the pattern
                        # Format: {location}_{station_acronym}_{instrument_id}_{year}_{day_of_year}_{timestamp}.jpg
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

                        # Create a dataframe with proper index to avoid PyArrow conversion issues
                        df = pd.DataFrame(
                            data={
                                # Keep the same data in the same columns
                                "DOY": doys,          # Column with DOY values
                                "Date": dates,        # Column with Date values
                                "Time": timestamps,   # Column with Time values
                                "_index": list(range(len(daily_filepaths)))  # Add proper numeric index
                            }
                        )
                        # Set the index
                        df.set_index("_index", inplace=True)

                        # Show the interactive dataframe with row selection
                        event = st.dataframe(
                            df,
                            column_config={
                                # Swap the display names but keep the same data mapping
                                "DOY": st.column_config.TextColumn(
                                    "Date",     # First column shows DOY values with "Date" label
                                    help="Calendar date (YYYY-MM-DD)",
                                    width="small"
                                ),
                                "Date": st.column_config.TextColumn(
                                    "DOY",      # Second column shows Date values with "DOY" label
                                    help="Day of Year (1-365/366)",
                                    width="small"
                                ),
                                "Time": st.column_config.TextColumn(
                                    "Time",
                                    help="Click to select this file",
                                    width="small"
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
                            try:
                                # Convert to integer index (it might be a string from the dataframe)
                                index = int(event.selection.rows[0])

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
                                # Add ROI toggle above the image with session state persistence
                                if 'show_roi_overlays' not in st.session_state:
                                    st.session_state.show_roi_overlays = False
                                show_rois = st.toggle("Show ROI Overlays", value=st.session_state.show_roi_overlays,
                                                    help="Toggle to show region of interest overlays on the image",
                                                    key="show_roi_toggle")

                                # Update session state when toggle changes
                                if show_rois != st.session_state.show_roi_overlays:
                                    st.session_state.show_roi_overlays = show_rois

                                # Load and process the image
                                processor = ImageProcessor()
                                if processor.load_image(filepath):
                                    # Check if we have instrument ROIs loaded
                                    if show_rois:
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

                                                        # Apply ROIs with our custom function (now handles both formats)
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

                                            # Add additional info in overlay mode with ROI details
                                            roi_names = list(st.session_state.instrument_rois.keys())
                                            roi_source = st.session_state.get('roi_source', 'configuration')
                                            instrument_id = st.session_state.get('roi_instrument_id', 'unknown')

                                            # Create a nicer formatted info message
                                            st.info(
                                                f"Showing {len(roi_names)} instrument-specific ROIs for {instrument_id} from {roi_source}:\n"
                                                f"ROIs: {', '.join(roi_names)}"
                                            )
                                        else:
                                            # Now that we've fixed the format issues, re-enable default ROI generation
                                            processor.create_default_roi()
                                            # Show informational message about default ROI
                                            st.info("Using default ROI that covers the entire image (excluding sky). Click 'Load Instrument ROIs' to load predefined ROIs for this instrument.")

                                    # Store the image dimensions (for future ROI adjustments if needed)
                                    img = processor.get_image(with_overlays=False)  # Get the image without overlays first
                                    if img is not None:
                                        height, width = img.shape[:2]
                                        st.session_state.image_dimensions = (width, height)

                                    # Get the image with or without overlays based on toggle
                                    img = processor.get_image(with_overlays=show_rois)

                                    if img is not None:
                                        # Convert BGR to RGB for correct color display
                                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                                        # Add image caption with ROI status
                                        caption = os.path.basename(filepath)
                                        if show_rois:
                                            caption += " (with ROI overlays)"

                                        # Display the image
                                        st.image(img_rgb, caption=caption, use_container_width=True)
                                    else:
                                        st.error(f"Failed to process image: {filepath}")
                                else:
                                    st.error(f"Failed to load image: {filepath}")
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

            # Add station configuration visualization
            st.divider()
            st.subheader("Station Configuration")

            # Button to load all station data from stations.yaml
            if selected_station:
                normalized_name = station_name_to_normalized.get(selected_station)
                if normalized_name:
                    # Load station button with feedback
                    if st.button("📋 Load Full Station Configuration", key="load_station_config"):
                        with st.spinner(f"Loading configuration for {selected_station}..."):
                            try:
                                # Get the full station configuration from stations.yaml
                                config = load_config_files()
                                stations_config = config.get('stations', {}).get('stations', {})

                                if normalized_name in stations_config:
                                    station_data = stations_config[normalized_name]

                                    # Store in session state for display
                                    st.session_state.station_config = station_data

                                    # Success message
                                    st.success(f"Loaded configuration for {selected_station}")
                                else:
                                    st.error(f"Station {normalized_name} not found in configuration")
                            except Exception as e:
                                st.error(f"Error loading station configuration: {e}")

                    # Display the station configuration as JSON if available
                    if hasattr(st.session_state, 'station_config'):
                        with st.expander("Station Configuration Details", expanded=True):
                            # Create tabs for different views
                            tab1, tab2 = st.tabs(["Formatted View", "Raw JSON"])

                            with tab1:
                                # Show a more structured view with key information
                                st.write("### Station Information")
                                st.write(f"**Name:** {st.session_state.station_config.get('name')}")
                                st.write(f"**Acronym:** {st.session_state.station_config.get('acronym')}")
                                st.write(f"**Normalized Name:** {st.session_state.station_config.get('normalized_name')}")

                                # Show available platforms
                                if 'phenocams' in st.session_state.station_config and 'platforms' in st.session_state.station_config['phenocams']:
                                    platforms = st.session_state.station_config['phenocams']['platforms']
                                    st.write(f"### Available Platforms: {list(platforms.keys())}")

                                    # Show instruments for each platform
                                    for platform, platform_data in platforms.items():
                                        if 'instruments' in platform_data:
                                            instruments = platform_data['instruments']
                                            st.write(f"#### Platform {platform} Instruments:")

                                            for instrument_id, instrument_info in instruments.items():
                                                st.write(f"- **{instrument_id}**")
                                                # Show ROIs if available
                                                if 'rois' in instrument_info:
                                                    rois = list(instrument_info['rois'].keys())
                                                    st.write(f"  - ROIs: {', '.join(rois)}")

                            with tab2:
                                # Show raw JSON
                                st.json(st.session_state.station_config)
            else:
                st.info("Select a station to view its configuration")

        # Store important data in session state
    if selected_station:
        # Store station info in session state
        st.session_state.current_station = selected_station
        if selected_instrument:
            # Store instrument info in session state
            st.session_state.current_instrument = selected_instrument


def serialize_polygons(phenocam_rois):
    """
    Converts a dictionary of polygons to be YAML-friendly by converting tuples to lists.

    Parameters:
        phenocam_rois (dict of dict): Dictionary where keys are ROI names and values are dictionaries representing polygons.

    Returns:
        yaml_friendly_rois (dict of dict): Dictionary with tuples converted to lists.
    """
    yaml_friendly_rois = {}
    for roi, polygon in phenocam_rois.items():
        yaml_friendly_polygon = {
            'points': [list(point) for point in polygon['points']],
            'color': list(polygon['color']),
            'thickness': polygon['thickness']
        }
        yaml_friendly_rois[roi] = yaml_friendly_polygon
    return yaml_friendly_rois


def deserialize_polygons(yaml_friendly_rois):
    """
    Converts YAML-friendly polygons back to their original format with tuples.
    Makes the ROI format compatible with ImageProcessor.overlay_polygons_from_dict.

    Parameters:
        yaml_friendly_rois (dict of dict): Dictionary where keys are ROI names and values are dictionaries representing polygons in YAML-friendly format.

    Returns:
        original_rois (dict of dict): Dictionary with points and color as tuples.
    """
    original_rois = {}
    for roi_name, roi_data in yaml_friendly_rois.items():
        # Convert points to tuples and ensure they're in the correct format
        points = [tuple(point) for point in roi_data['points']]

        # Convert color to tuple
        color = tuple(roi_data['color'])

        # Get thickness (default to 2 if not present)
        thickness = roi_data.get('thickness', 2)

        # Default alpha value if not present
        alpha = roi_data.get('alpha', 0.3)

        # Store in the format expected by overlay_polygons_from_dict
        original_rois[roi_name] = {
            'points': points,
            'color': color,
            'thickness': thickness,
            'alpha': alpha
        }

    return original_rois


def overlay_polygons(image_path, phenocam_rois: dict, show_names: bool = True, font_scale: float = 1.0):
    """
    Overlays polygons on an image and optionally labels them with their respective ROI names.
    This version handles both tuple and list formats for points and colors.

    Parameters:
        image_path (str): Path to the image file.
        phenocam_rois (dict): Dictionary where keys are ROI names and values are dictionaries representing polygons.
        Each dictionary should have the following keys:
        - 'points' (list of tuple or list of list): List of (x, y) coordinates representing the vertices of the polygon.
        - 'color' (tuple or list): (B, G, R) or [B, G, R] color of the polygon border.
        - 'thickness' (int): Thickness of the polygon border.
        show_names (bool): Whether to display the ROI names on the image. Default is True.
        font_scale (float): Scale factor for the font size of the ROI names. Default is 1.0.

    Returns:
        numpy.ndarray: The image with polygons overlaid, in RGB format.
    """
    # Read the image
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not found or path is incorrect")

    # Process each ROI
    for roi_name, roi_data in phenocam_rois.items():
        try:
            # Extract points - support both formats (list of tuples or list of lists)
            points = roi_data['points']
            # Convert to numpy array for OpenCV
            points_array = np.array(points, dtype=np.int32)

            # Extract color - support both tuple and list formats
            color = roi_data['color']
            # BGR color order for OpenCV
            if len(color) == 3:
                # OpenCV uses BGR format, but our ROIs may be defined as RGB
                # Check if we need to convert based on context
                # For YAML configs, colors are typically defined as [R,G,B]
                # So we need to reverse them for OpenCV's BGR
                color = (color[2], color[1], color[0])  # Swap R and B

            # Extract thickness with default
            thickness = roi_data.get('thickness', 2)

            # Draw the polygon on the image
            cv2.polylines(img, [points_array], isClosed=True, color=color, thickness=thickness)

            # Optional fill with transparency
            alpha = roi_data.get('alpha', 0.3)
            if alpha > 0:
                # Create a copy of the image for blending
                overlay = img.copy()
                # Fill the polygon
                cv2.fillPoly(overlay, [points_array], color)
                # Blend the images
                cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

            # Add ROI name if requested
            if show_names:
                # Calculate the centroid of the polygon for labeling
                M = cv2.moments(points_array)
                if M['m00'] != 0:
                    cX = int(M['m10'] / M['m00'])
                    cY = int(M['m01'] / M['m00'])
                else:
                    # In case of a degenerate polygon where area is zero
                    cX, cY = points_array[0][0], points_array[0][1]

                # Adjust text color for visibility - use white if color is dark
                text_color = color
                brightness = sum(color) / 3
                if brightness < 128:  # If average color value is dark
                    text_color = (255, 255, 255)  # Use white text

                # Overlay the ROI name at the centroid of the polygon
                cv2.putText(img, roi_name, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
                            font_scale, text_color, 2, cv2.LINE_AA)

        except Exception as e:
            print(f"Error processing ROI '{roi_name}': {str(e)}")
            # Continue with other ROIs even if one fails

    # Convert the image from BGR to RGB before returning
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img_rgb


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