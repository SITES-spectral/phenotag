"""
Example of main UI with memory monitoring integration.

This file shows how to integrate the memory management components
into the main Streamlit UI.
"""

import streamlit as st
import os
import pandas as pd
import numpy as np
import time
import cv2
from pathlib import Path
from typing import Dict, List, Any

# Import original components
from phenotag.config import load_config_files
from phenotag.io_tools import find_phenocam_images, save_yaml, load_session_config

# Import memory-optimized components instead of standard ones
from phenotag.processors.memory_optimized_processor import MemoryOptimizedProcessor
from phenotag.memory.memory_manager import memory_manager, MemoryTracker
from .memory_dashboard import memory_dashboard


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
    Create a pandas DataFrame for the data_editor with image data.
    
    Args:
        year_data: Dictionary with image data for a specific year
        day: Day of year to display images for
        max_items: Maximum number of items to include
    
    Returns:
        pandas.DataFrame: DataFrame with image data
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
    
    for file_path in file_paths:
        file_info = day_data[file_path]
        quality = file_info['quality']
        
        # Create a row for each file
        row = {
            'file_path': file_path,
            'image': file_path,  # Will be loaded lazily
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
    return df


def save_session_config():
    """Save the current session configuration to a YAML file."""
    # Define the configuration file path
    config_dir = Path(os.path.expanduser("~/.phenotag"))
    config_file = config_dir / "session_config.yaml"
    
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
    # Initialize memory management at application startup
    with MemoryTracker("App Initialization"):
        # Start memory monitoring
        memory_manager.start_memory_monitoring(
            interval=30.0,  # Check every 30 seconds
            threshold_mb=2000  # Alert if process exceeds 2GB
        )
        
        # Define the configuration file path
        config_dir = Path(os.path.expanduser("~/.phenotag"))
        config_file = config_dir / "session_config.yaml"
        
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
        
        # Initialize processor memory threshold
        if 'memory_threshold_mb' not in st.session_state:
            st.session_state.memory_threshold_mb = 1000  # Default 1GB
    
    # Load config data
    with MemoryTracker("Loading Configuration"):
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
    
    # Add memory dashboard to the sidebar
    memory_dashboard.render_mini_dashboard()
    
    # Add dropdown menus and configuration to the sidebar
    with st.sidebar:
        # Select station with default from session
        default_index = 0
        if st.session_state.selected_station in station_names:
            default_index = station_names.index(st.session_state.selected_station)
        
        selected_station = st.selectbox(
            "Select a station", 
            station_names,
            index=default_index
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
                    index=default_instr_index
                )
                st.session_state.selected_instrument = selected_instrument
            else:
                st.info("No phenocams available for this station")
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
            
            # Memory threshold setting
            st.slider(
                "Memory threshold (MB)",
                min_value=500,
                max_value=5000,
                value=st.session_state.memory_threshold_mb,
                step=100,
                help="Maximum memory usage before automatic downscaling is applied",
                key="memory_threshold_mb"
            )
            
            # Session management buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Session"):
                    if save_session_config():
                        st.success("Session saved!")
                    else:
                        st.error("Failed to save session")
            
            with col2:
                if st.button("Reset Session"):
                    # Clear session state
                    for key in ['data_directory', 'selected_station', 'selected_instrument', 
                                'selected_year', 'selected_day', 'image_data']:
                        if key in st.session_state:
                            if key == 'image_data':
                                st.session_state[key] = {}
                            else:
                                st.session_state[key] = None
                    
                    st.session_state.data_directory = ""
                    
                    # Also clear memory cache
                    memory_manager.clear_cache()
                    
                    st.success("Session reset!")
                    st.rerun()
            
            # Display full memory dashboard in an expander
            memory_dashboard.render_dashboard(location="main")
            
            # Scan button
            if normalized_name and selected_instrument and st.session_state.data_directory:
                if os.path.isdir(st.session_state.data_directory):
                    scan_button = st.button("Scan for images")
                    
                    if scan_button:
                        with st.spinner("Scanning for images..."):
                            # Show progress indicator
                            progress_bar = st.progress(0)
                            
                            # Use memory tracking for scanning
                            with MemoryTracker("Scanning for images"):
                                # Find images for the selected instrument
                                image_data = find_phenocam_images(
                                    base_dir=st.session_state.data_directory,
                                    station_name=normalized_name,
                                    instrument_id=selected_instrument
                                )
                            
                            # Update progress
                            progress_bar.progress(100)
                            
                            if image_data:
                                # Store in session state for later use
                                if 'image_data' not in st.session_state:
                                    st.session_state.image_data = {}
                                st.session_state.image_data[f"{normalized_name}_{selected_instrument}"] = image_data
                                
                                # Reset year and day selections
                                st.session_state.selected_year = None
                                st.session_state.selected_day = None
                                
                                # Auto-save the session
                                save_session_config()
                                
                                # Display summary
                                years = list(image_data.keys())
                                years.sort(reverse=True)
                                
                                st.success(f"Found images for {selected_instrument}")
                                st.write(f"Years available: {', '.join(years[:3])}" + 
                                         (f"... and {len(years) - 3} more" if len(years) > 3 else ""))
                            else:
                                st.warning(
                                    f"No images found for {selected_instrument}. "
                                    f"Check that the path follows the structure: "
                                    f"{st.session_state.data_directory}/{normalized_name}/phenocams/products/{selected_instrument}/L1/..."
                                )
                else:
                    st.error("Invalid directory path")
    
    # Display the selected station in the main content area
    if selected_station:
        st.header(f"Station: {selected_station}")
        
        # Display the selected instrument if one was selected
        if selected_instrument:
            st.subheader(f"Phenocam: {selected_instrument}")
            
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
                            
                            # Use memory-optimized processor for image display
                            # Custom display for image column with memory tracking
                            def image_formatter(path):
                                with MemoryTracker(f"Loading thumbnail for {Path(path).name}"):
                                    # Create a memory-optimized processor with small memory threshold
                                    # to ensure we downscale for thumbnails
                                    processor = MemoryOptimizedProcessor(
                                        downscale_factor=0.25,  # Initial downscale for thumbnails
                                        memory_threshold_mb=100  # Low threshold to ensure thumbnails stay small
                                    )
                                    
                                    if processor.load_image(path, keep_original=False):
                                        # Get image from processor
                                        img = processor.get_image()
                                        
                                        # Convert to RGB format for Streamlit
                                        if img is not None:
                                            height, width = img.shape[:2]
                                            # Calculate aspect ratio preserving resize
                                            max_height, max_width = 150, 200
                                            
                                            # Further resize if needed to fit thumbnail constraints
                                            if width > max_width or height > max_height:
                                                aspect = width / height
                                                if aspect > max_width / max_height:  # Width is the limiting factor
                                                    new_width = max_width
                                                    new_height = int(new_width / aspect)
                                                else:  # Height is the limiting factor
                                                    new_height = max_height
                                                    new_width = int(new_height * aspect)
                                                
                                                # Resize to thumbnail
                                                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                                            
                                            # OpenCV uses BGR, convert to RGB for Streamlit
                                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                            return img
                                
                                # Default blank image if loading fails
                                return np.zeros((150, 200, 3), dtype=np.uint8)
                            
                            # Configure column settings
                            column_config = {
                                "file_path": st.column_config.TextColumn("File Path", width="medium"),
                                "image": st.column_config.ImageColumn("Image", help="Phenocam image", width="medium"),
                                "discard_file": st.column_config.CheckboxColumn("Discard File", width="small"),
                                "snow_presence": st.column_config.CheckboxColumn("Snow Presence", width="small"),
                                **{f"{roi}_discard": st.column_config.CheckboxColumn(f"{roi} Discard", width="small") 
                                   for roi in ["ROI_01", "ROI_02", "ROI_03"]},
                                **{f"{roi}_snow": st.column_config.CheckboxColumn(f"{roi} Snow", width="small")
                                   for roi in ["ROI_01", "ROI_02", "ROI_03"]}
                            }
                            
                            # Apply image formatter to lazy load images with memory tracking
                            with st.spinner("Loading image thumbnails..."):
                                df['image'] = df['image'].apply(image_formatter)
                            
                            # Display the data editor
                            edited_df = st.data_editor(
                                df,
                                column_config=column_config,
                                use_container_width=True,
                                num_rows="fixed",
                                key=f"data_editor_{selected_year}_{selected_day}"
                            )
                            
                            # Add a save button
                            if st.button("Save Annotations"):
                                # In a real application, you would save the edited annotations to disk here
                                
                                # Save session config to remember where we left off
                                if save_session_config():
                                    st.success("Annotations and session saved!")
                                else:
                                    st.error("Failed to save session")
                                    st.success("Annotations saved!")
                        else:
                            st.info(f"No images found for Day {selected_day}")
            else:
                if st.session_state.data_directory and os.path.isdir(st.session_state.data_directory):
                    st.info("Click 'Scan for images' in the Configuration panel to view image data")
                else:
                    st.info("Enter a valid data directory in the Configuration section to view image data")
    
    # Add memory metrics to status bar
    memory_dashboard.add_memory_metrics_to_status_bar()


if __name__ == "__main__":
    main()