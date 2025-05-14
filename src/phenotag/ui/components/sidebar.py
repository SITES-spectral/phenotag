"""
Sidebar component for PhenoTag UI.

This module contains functions to create and manage the sidebar navigation
and controls.
"""
import os
import streamlit as st

from phenotag.config import load_config_files
from phenotag.ui.components.session_state import save_session_config


def get_phenocam_instruments(station_data):
    """
    Extract phenocam instruments from station data.
    
    Args:
        station_data (dict): Station configuration data
        
    Returns:
        list: List of instrument IDs
    """
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


def render_sidebar():
    """
    Render the application sidebar with station, instrument selectors and configuration.
    
    Returns:
        tuple: (normalized_name, selected_instrument) containing the current selection
    """
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

        # If station is changing, save current annotations and reset
        if station_changed and 'image_annotations' in st.session_state:
            # Save annotations first to avoid losing data
            if hasattr(st.session_state, 'image_annotations') and st.session_state.image_annotations:
                from phenotag.ui.components.annotation import save_all_annotations
                save_all_annotations(force_save=True)
                
            # Pause the annotation timer when changing station
            if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
                from phenotag.ui.components.annotation_timer import annotation_timer
                annotation_timer.pause_timer()
                
            # Clear annotations since we're changing station
            st.session_state.image_annotations = {}
            
            # Clear annotation status cache when changing station
            if 'annotation_status_map' in st.session_state:
                st.session_state.annotation_status_map = {}
                print("Cleared annotation status cache due to station change")

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
                
                # If instrument is changing, save current annotations and reset
                if instrument_changed and 'image_annotations' in st.session_state:
                    # Save annotations first to avoid losing data
                    if hasattr(st.session_state, 'image_annotations') and st.session_state.image_annotations:
                        from phenotag.ui.components.annotation import save_all_annotations
                        save_all_annotations(force_save=True)
                        
                    # Pause the annotation timer when changing instrument
                    if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
                        from phenotag.ui.components.annotation_timer import annotation_timer
                        annotation_timer.pause_timer()
                        
                    # Clear annotations since we're changing instrument
                    st.session_state.image_annotations = {}
                    
                    # Clear annotation status cache when changing instrument
                    if 'annotation_status_map' in st.session_state:
                        st.session_state.annotation_status_map = {}
                        print("Cleared annotation status cache due to instrument change")

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
            else:
                st.warning("No phenocams available for this station")
                selected_instrument = None
                st.session_state.selected_instrument = None
                
        # Add calendar view in the sidebar if station and instrument are selected
        if normalized_name and selected_instrument:
            st.divider()
            
            # Use calendar view component inside the sidebar
            from phenotag.ui.components.calendar_view import render_year_month_selectors, render_calendar
            
            # Check if we have image data to display
            key = f"{normalized_name}_{selected_instrument}"
            image_data = st.session_state.image_data.get(key, {}) if key and 'image_data' in st.session_state else {}
            
            # Only show calendar if we have image data
            if image_data and key in st.session_state.image_data and len(st.session_state.image_data[key]) > 0:
                # Special no_l1_data case handling
                if len(st.session_state.image_data[key]) == 1 and "_no_l1_data" in st.session_state.image_data[key]:
                    # Already showing warning about missing L1 data in selector
                    pass
                else:
                    # Render year and month selectors
                    st.subheader("Calendar View")
                    selected_year, selected_month = render_year_month_selectors(normalized_name, selected_instrument, image_data)
                    
                    if selected_year and selected_month:
                        # Render calendar for the selected year and month
                        selected_days = render_calendar(normalized_name, selected_instrument, selected_year, selected_month)
                        
                        # Update session state with selected days
                        if selected_days:
                            st.session_state.selected_days = selected_days
                            # Select the first day as current day if no day is selected
                            if (not st.session_state.selected_day or 
                                st.session_state.selected_day not in [str(day) for day in selected_days]):
                                st.session_state.selected_day = str(selected_days[0])
                                save_session_config()
                                
                        # Display selected day range if available
                        if selected_days:
                            from phenotag.ui.calendar_component import format_day_range
                            selection_text = format_day_range(selected_days, int(selected_year))
                            st.write(f"**Selected: {selection_text}**")
        
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
                    from phenotag.ui.components.session_state import reset_session
                    reset_session()
                    st.success("Session reset successfully!")
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
    
    # Debug info to help with troubleshooting
    with st.sidebar.expander("Debug Info", expanded=False):
        key = f"{normalized_name}_{selected_instrument}" if normalized_name and selected_instrument else None
        st.write(f"Selected key: {key}")
        st.write(f"Year: {st.session_state.selected_year if 'selected_year' in st.session_state else 'None'}")
        if 'image_data' in st.session_state and key in st.session_state.image_data:
            st.write(f"Years in data: {list(st.session_state.image_data[key].keys())}")
        else:
            st.write("No image data found")
    
    # Add memory usage info at the bottom of the sidebar if memory optimization is enabled
    if st.session_state.get('memory_optimized', False):
        # Add a spacer to push the memory info to the bottom
        for _ in range(3):
            st.sidebar.markdown("&nbsp;", unsafe_allow_html=True)
            
        with st.sidebar.expander("💾 Memory Usage", expanded=False):
            from phenotag.ui.components.memory_management import memory_dashboard
            memory_dashboard.render_mini_dashboard()
            
            if st.button("Clear Memory"):
                from phenotag.ui.components.memory_management import memory_manager
                memory_manager.clear_memory()
                st.success("Memory cleared")
                st.rerun()
            
    return normalized_name, selected_instrument