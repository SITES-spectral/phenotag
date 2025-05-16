"""
PhenoTag main UI application.

This module serves as the entry point for the PhenoTag UI application,
integrating all UI components into a cohesive interface.
"""
import streamlit as st
import os
import sys
import time
import datetime
import calendar

from phenotag.config import load_config_files
from phenotag.ui.components.session_state import initialize_session_state, load_config, save_session_config
from phenotag.ui.components.sidebar import render_sidebar
from phenotag.ui.components.scanner import handle_scan, should_auto_scan, setup_auto_scan
from phenotag.ui.components.calendar_view import display_calendar_view
from phenotag.ui.components.image_display import display_images
from phenotag.ui.components.annotation import (
    load_day_annotations, 
    save_all_annotations, 
    create_annotation_summary,
    display_annotation_completion_status
)
from phenotag.ui.components.memory_management import memory_manager, memory_dashboard, MemoryTracker
from phenotag.ui.components.annotation_status import check_day_annotation_status
from phenotag.ui.components.annotation_timer import annotation_timer


def load_instrument_rois():
    """
    Load ROI definitions for current instrument from stations configuration.
    Returns True if ROIs were successfully loaded, False otherwise.
    """
    # Get the current station and instrument from session state
    station_name = st.session_state.get('selected_station_normalized')
    instrument_id = st.session_state.get('selected_instrument')
    
    # If no station or instrument is selected, try to get from scan_info
    if not station_name or not instrument_id:
        if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
            scan_info = st.session_state.scan_info
            station_name = scan_info.get('station_name')
            instrument_id = scan_info.get('instrument_id')
    
    # Ensure we have a normalized station name
    if not station_name and 'selected_station' in st.session_state:
        # Get the normalized name from the display name
        config = load_config_files()
        stations_config = config.get('stations', {}).get('stations', {})
        for norm_name, station_info in stations_config.items():
            if station_info.get('name') == st.session_state.selected_station:
                station_name = norm_name
                # Store for future use
                st.session_state.selected_station_normalized = norm_name
                break
    
    # If we still don't have both station name and instrument id, return False
    if not station_name or not instrument_id:
        print(f"Cannot load ROIs: Missing station name ({station_name}) or instrument ID ({instrument_id})")
        return False

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
                                from phenotag.ui.components.roi_utils import deserialize_polygons
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
                            print(f"Successfully loaded ROIs for instrument {instrument_id} in station {station_name}: {roi_names}")
                            return True  # Successfully loaded ROIs

    # If we get here, no ROIs were found
    if not rois_found:
        print(f"No ROI definitions found for instrument {instrument_id} in station {station_name}")
        
        # Add debug information about the station config
        print(f"Available stations in config: {list(stations_config.keys())}")
        if station_name in stations_config:
            if 'phenocams' in stations_config[station_name]:
                if 'platforms' in stations_config[station_name]['phenocams']:
                    platforms = stations_config[station_name]['phenocams']['platforms']
                    print(f"Available platforms: {list(platforms.keys())}")
                    for platform_type, platform_data in platforms.items():
                        if 'instruments' in platform_data:
                            print(f"Instruments in platform {platform_type}: {list(platform_data['instruments'].keys())}")
                else:
                    print("No 'platforms' key in phenocams data")
            else:
                print("No 'phenocams' key in station data")
        else:
            print(f"Station {station_name} not found in config")
            
        return False


def main():
    """
    Main function to run the PhenoTag application.
    """
    # Initialize memory monitoring
    with MemoryTracker("App Initialization"):
        # Start memory monitoring
        memory_manager.start_memory_monitoring(
            interval=30.0,  # Check every 30 seconds
            threshold_mb=2000  # Alert if process exceeds 2GB
        )
        
        # Get memory optimization flag from command line
        memory_optimized = False
        if len(sys.argv) > 1:
            memory_optimized = "--memory-optimized" in sys.argv or "-m" in sys.argv
            
        # Store memory optimization setting in session state
        if 'memory_optimized' not in st.session_state:
            st.session_state.memory_optimized = memory_optimized
            
        # Initialize memory threshold
        if 'memory_threshold_mb' not in st.session_state:
            st.session_state.memory_threshold_mb = 1000  # Default 1GB
    
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
        
        # Initialize annotation timer state
        from phenotag.ui.components.annotation_timer import annotation_timer
        annotation_timer.initialize_session_state()
        
        # Create all annotation timer session state variables explicitly
        if 'annotation_timer_active' not in st.session_state:
            st.session_state.annotation_timer_active = False
        if 'annotation_timer_start' not in st.session_state:
            st.session_state.annotation_timer_start = None
        if 'annotation_timer_accumulated' not in st.session_state:
            st.session_state.annotation_timer_accumulated = {}
        if 'annotation_timer_last_interaction' not in st.session_state:
            st.session_state.annotation_timer_last_interaction = time.time()
        if 'annotation_timer_current_day' not in st.session_state:
            st.session_state.annotation_timer_current_day = None
        
        # Initialize annotation status map if not exists
        if 'annotation_status_map' not in st.session_state:
            st.session_state.annotation_status_map = {}
    
    # Memory dashboard will be added at the bottom of the sidebar later
    
    # Render sidebar and get current selection
    with MemoryTracker("Render Sidebar"):
        normalized_name, selected_instrument = render_sidebar()
    
    # Handle scanning if requested
    if hasattr(st.session_state, 'scan_requested') and st.session_state.scan_requested:
        # No need to explicitly save before scanning - annotations managed by popover
        print("Scanning for images - annotations are saved when made in the annotation panel")
            
        with MemoryTracker("Image Scanning"):
            if handle_scan(normalized_name, selected_instrument):
                # If scan was performed, no need to continue
                return
    
    # Check if we should auto-scan
    if should_auto_scan(normalized_name, selected_instrument):
        setup_auto_scan(normalized_name, selected_instrument)
        st.rerun()
    
    # We've removed the tab system, so we'll now just use a single container
    # Set active_tab to "Current" for backward compatibility
    st.session_state.active_tab = "Current"
    
    # Create the main container for the application
    current_tab = st.container()
    
    # Get current selections from session state
    previous_year = st.session_state.get('previous_year')
    previous_day = st.session_state.get('previous_day')
    selected_year = st.session_state.selected_year if 'selected_year' in st.session_state else None
    selected_days = st.session_state.selected_days if 'selected_days' in st.session_state else []
    selected_day = st.session_state.selected_day if 'selected_day' in st.session_state else None
    
    # Set selected_tab for compatibility with remaining code
    selected_tab = "Current"
    
    # Day or year change is now handled by the popover - no need to force save
    if (previous_day is not None and selected_day is not None and previous_day != selected_day) or \
       (previous_year is not None and selected_year is not None and previous_year != selected_year):
        print(f"Changed from day {previous_day} to {selected_day} or year {previous_year} to {selected_year}")
    
    # Store current values as previous for next run
    st.session_state['previous_year'] = selected_year
    st.session_state['previous_day'] = selected_day
    
    # Track the current selection for day/instrument/station changes
    current_selection = {
        'day': selected_day,
        'instrument': selected_instrument,
        'station': normalized_name,
        'year': selected_year
    }
    
    # Create a key to track if we've loaded annotations for this combination
    selection_key = f"{normalized_name}_{selected_instrument}_{selected_year}_{selected_day}"
    annotations_loaded_key = f"annotations_loaded_{selection_key}"
    
    # Reset the annotations_loaded flag on every run to ensure we always load the latest annotations
    st.session_state[annotations_loaded_key] = False
    
    # Create three main containers for the layout
    top_container = st.container()
    center_container = st.container()
    bottom_container = st.container()
    
    with top_container:
        with MemoryTracker("Load Annotations"):
            # Calendar view is now moved to the sidebar
            
            # Display a header with the current selection if available
            if selected_year and selected_day:
                st.subheader(f"Viewing images for Year {selected_year}, Day {selected_day}")
                
                # Show selection range if multiple days are selected
                if selected_days and len(selected_days) > 0:
                    from phenotag.ui.calendar_component import format_day_range
                    selection_text = format_day_range(selected_days, int(selected_year))
                    st.write(f"Selected range: {selection_text}")
                
                # Display annotation completion status if available
                if selected_day:
                    display_annotation_completion_status(selected_day)
            
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
                
                # Create a loading key that's specific to this day
                day_load_key = f"annotations_loaded_day_{selected_day}"
                
                # Check if we need to reload annotations (either not loaded or force reload)
                if not st.session_state.get(day_load_key, False) or not st.session_state.get(annotations_loaded_key, False):
                    print(f"Loading annotations for day {selected_day} - this is {'not' if not st.session_state.get(day_load_key, False) else ''} loaded by day key")
                    print(f"Loading annotations for day {selected_day} - this is {'not' if not st.session_state.get(annotations_loaded_key, False) else ''} loaded by general key")
                    
                    # Clear any existing annotations for this day to avoid stale data
                    if 'image_annotations' in st.session_state:
                        filepaths_to_clear = []
                        for filepath in st.session_state.image_annotations:
                            img_dir = os.path.dirname(filepath)
                            img_doy = os.path.basename(img_dir)
                            if img_doy == selected_day:
                                filepaths_to_clear.append(filepath)
                        
                        for filepath in filepaths_to_clear:
                            if filepath in st.session_state.image_annotations:
                                del st.session_state.image_annotations[filepath]
                    
                    # Attempt to load annotations
                    load_successful = load_day_annotations(selected_day, daily_filepaths)
                    
                    # Mark as loaded in both places if successful
                    if load_successful:
                        st.session_state[annotations_loaded_key] = True
                        st.session_state[day_load_key] = True
                    else:
                        print(f"WARNING: Failed to load annotations for day {selected_day}")
                else:
                    print(f"Skipping annotation load for day {selected_day} - already loaded")
                
                # Mark this day as in_progress in the annotation status cache
                try:
                    if 'annotation_status_map' in st.session_state:
                        # Extract month from day number
                        date = datetime.datetime.strptime(f"{selected_year}-{selected_day}", "%Y-%j")
                        month = date.month
                        
                        # Create status key
                        status_key = f"{normalized_name}_{selected_instrument}_{selected_year}_{month}"
                        
                        # Update or create cache entry
                        if status_key not in st.session_state.annotation_status_map:
                            st.session_state.annotation_status_map[status_key] = {}
                            
                        # Only update to in_progress if not already completed
                        if selected_day in st.session_state.annotation_status_map[status_key]:
                            current_status = st.session_state.annotation_status_map[status_key][selected_day]
                            if current_status != 'completed':  # Don't downgrade from completed
                                st.session_state.annotation_status_map[status_key][selected_day] = 'in_progress'
                        else:
                            st.session_state.annotation_status_map[status_key][selected_day] = 'in_progress'
                            
                        print(f"Updated status cache for current day {selected_day}")
                except Exception as e:
                    print(f"Error updating status cache for current tab: {str(e)}")
    
    with center_container:
        with MemoryTracker("Image Display"):
            # Display images with annotation panel
            displayed_filepath = display_images(
                normalized_name,
                selected_instrument,
                selected_year,
                selected_day,
                selected_days
            )
            
            # Removed the raw annotation data button - using annotation panel instead
    
    # We've moved the annotation panel to the image selection column
    # Make sure ROIs are loaded for use by the annotation panel
    with MemoryTracker("Load ROIs"):
        if selected_instrument and 'instrument_rois' not in st.session_state:
            # Try to load ROIs before showing annotation panel
            print("Explicitly loading ROIs before annotation panel display")
            load_instrument_rois()
        
        # Print info about ROIs
        if 'instrument_rois' in st.session_state:
            print(f"ROIs available for annotation: {list(st.session_state.instrument_rois.keys())}")
    
    # Store important data in session state
    if selected_instrument:
        # Store instrument info in session state
        st.session_state.current_instrument = selected_instrument
        
        # Try to load ROIs if showing overlays but not yet loaded
        if (st.session_state.get('show_roi_overlays', False) and 
            ('instrument_rois' not in st.session_state or not st.session_state.instrument_rois)):
            with MemoryTracker("Load ROIs"):
                load_instrument_rois()
                
    # No need to save annotations when leaving the page - annotations managed by popover
    # Only reset ROI toggle flag
    if 'roi_toggle_changed' in st.session_state:
        del st.session_state['roi_toggle_changed']
    
    # Check memory usage and reclaim if necessary
    if memory_manager.check_memory_threshold():
        memory_manager.clear_memory()
        
    # Memory information is now displayed in an expander at the bottom of the sidebar


if __name__ == "__main__":
    main()