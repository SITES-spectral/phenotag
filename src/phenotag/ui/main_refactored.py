"""
PhenoTag main UI application.

This module serves as the entry point for the PhenoTag UI application,
integrating all UI components into a cohesive interface.
"""
import streamlit as st
import os

from phenotag.config import load_config_files
from phenotag.ui.components.session_state import initialize_session_state, load_config, save_session_config
from phenotag.ui.components.sidebar import render_sidebar
from phenotag.ui.components.scanner import handle_scan, should_auto_scan, setup_auto_scan
from phenotag.ui.components.calendar_view import display_calendar_view
from phenotag.ui.components.image_display import display_images
from phenotag.ui.components.annotation import display_annotation_panel, load_day_annotations


def load_instrument_rois():
    """
    Load ROI definitions for current instrument from stations configuration.
    Returns True if ROIs were successfully loaded, False otherwise.
    """
    if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
        scan_info = st.session_state.scan_info
        station_name = scan_info['station_name']
        instrument_id = scan_info['instrument_id']

        # Load configuration
        config = load_config_files()
        stations_config = config.get('stations', {}).get('stations', {})

        # Extract ROIs for this instrument
        rois_found = False

        # Find the station in the configuration by normalized name
        if station_name in stations_config:
            station_data = stations_config[station_name]

            # Check if phenocams exists
            if 'phenocams' not in station_data:
                print(f"ERROR: 'phenocams' key missing in station data")
                return False
            elif 'platforms' not in station_data['phenocams']:
                print(f"ERROR: 'platforms' key missing in phenocams data")
                return False
            else:
                # List available platforms
                platforms = station_data['phenocams']['platforms']

                # Check each platform for the instrument
                for platform_type, platform_data in platforms.items():
                    if 'instruments' not in platform_data:
                        continue

                    # List instruments in this platform
                    instruments = platform_data['instruments']

                    if instrument_id in instruments:
                        instrument_config = instruments[instrument_id]

                        # Check if the instrument has ROIs
                        if 'rois' in instrument_config:
                            rois = instrument_config['rois']

                            # Check if it has ROIs defined
                            if rois:
                                try:
                                    # Process the ROIs using our improved deserialize function
                                    from phenotag.ui.components.annotation import deserialize_polygons
                                    processed_rois = deserialize_polygons(instrument_config['rois'])

                                    # Store the processed ROIs in session state
                                    st.session_state.instrument_rois = processed_rois
                                except Exception as e:
                                    print(f"Error processing ROIs: {str(e)}")
                                    # Fallback to storing the original format which our custom overlay function can handle
                                    st.session_state.instrument_rois = instrument_config['rois']

                                st.session_state.roi_instrument_id = instrument_id
                                st.session_state.roi_source = f"stations.yaml - {station_name}"

                                # Get ROI names for display
                                roi_names = list(instrument_config['rois'].keys())
                                rois_found = True
                                return True  # Successfully loaded ROIs

        # If we get here, no ROIs were found
        if not rois_found:
            print(f"No ROI definitions found for instrument {instrument_id} in station {station_name}")
            return False
    else:
        print("Scan information not available. Please scan for images first.")
        return False


def main():
    """
    Main function to run the PhenoTag application.
    """
    # Set page configuration with better defaults
    st.set_page_config(
        page_title="PhenoTag",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load session config
    session_config = load_config()
    
    # Initialize session state
    initialize_session_state(session_config)
    
    # Render sidebar and get current selection
    normalized_name, selected_instrument = render_sidebar()
    
    # Handle scanning if requested
    if hasattr(st.session_state, 'scan_requested') and st.session_state.scan_requested:
        if handle_scan(normalized_name, selected_instrument):
            # If scan was performed, no need to continue
            return
    
    # Check if we should auto-scan
    if should_auto_scan(normalized_name, selected_instrument):
        setup_auto_scan(normalized_name, selected_instrument)
        st.rerun()
    
    # Create three main containers for the layout
    top_container = st.container()
    center_container = st.container()
    bottom_container = st.container()
    
    with top_container:
        # Display calendar view
        selected_year, selected_days = display_calendar_view(normalized_name, selected_instrument)
        
        # Get current day from session state
        selected_day = st.session_state.selected_day if 'selected_day' in st.session_state else None
        
        # Load annotations for the current day
        if selected_day:
            # Get file paths for the day to load annotations
            from phenotag.ui.components.image_display import get_filtered_file_paths
            daily_filepaths = get_filtered_file_paths(
                normalized_name, 
                selected_instrument, 
                selected_year, 
                selected_day
            )
            
            # Load annotations for the current day
            load_day_annotations(selected_day, daily_filepaths)
    
    with center_container:
        # Display images with annotation panel
        displayed_filepath = display_images(
            normalized_name,
            selected_instrument,
            selected_year,
            selected_day,
            selected_days
        )
    
    with bottom_container:
        # Display annotation panel for the current image
        if 'current_filepath' in st.session_state and st.session_state.current_filepath:
            display_annotation_panel(st.session_state.current_filepath)
    
    # Store important data in session state
    if selected_instrument:
        # Store instrument info in session state
        st.session_state.current_instrument = selected_instrument
        
        # Try to load ROIs if showing overlays but not yet loaded
        if (st.session_state.get('show_roi_overlays', False) and 
            ('instrument_rois' not in st.session_state or not st.session_state.instrument_rois)):
            load_instrument_rois()


if __name__ == "__main__":
    main()