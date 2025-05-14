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
from phenotag.ui.components.annotation import display_annotation_panel, load_day_annotations, save_all_annotations
from phenotag.ui.components.memory_management import memory_manager, memory_dashboard, MemoryTracker
from phenotag.ui.components.annotation_status import check_day_annotation_status
from phenotag.ui.components.annotation_timer import annotation_timer


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
        # Save any existing annotations before scanning
        if 'image_annotations' in st.session_state and st.session_state.image_annotations:
            save_all_annotations(force_save=True)
            print("Saved annotations before scanning for images")
            
        with MemoryTracker("Image Scanning"):
            if handle_scan(normalized_name, selected_instrument):
                # If scan was performed, no need to continue
                return
    
    # Check if we should auto-scan
    if should_auto_scan(normalized_name, selected_instrument):
        setup_auto_scan(normalized_name, selected_instrument)
        st.rerun()
    
    # Initialize active tab in session state if not exists
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Current"
    
    # Store previous tab to detect tab changes
    prev_tab = st.session_state.active_tab
    
    # Create a radio button for tab selection
    tab_options = ["Current", "Historical"]
    selected_tab = st.radio("View", tab_options, horizontal=True, label_visibility="collapsed", index=tab_options.index(st.session_state.active_tab))
    
    # Update active tab
    st.session_state.active_tab = selected_tab
    
    # Detect tab change
    tab_changed = prev_tab != st.session_state.active_tab
    
    # Save annotations when changing tabs
    if tab_changed and 'image_annotations' in st.session_state and st.session_state.image_annotations:
        save_all_annotations(force_save=True)
        print(f"Saved annotations when switching from {prev_tab} to {selected_tab} tab")
    
    # Create a tab system based on the selected tab
    if selected_tab == "Current":
        current_tab = st.container()
        historical_tab = None
    else:  # Historical
        current_tab = None
        historical_tab = st.container()
    
    # Get current selections from session state
    previous_year = st.session_state.get('previous_year')
    previous_day = st.session_state.get('previous_day')
    selected_year = st.session_state.selected_year if 'selected_year' in st.session_state else None
    selected_days = st.session_state.selected_days if 'selected_days' in st.session_state else []
    selected_day = st.session_state.selected_day if 'selected_day' in st.session_state else None
    
    # Check if day or year changed and save annotations if needed
    if (previous_day is not None and selected_day is not None and previous_day != selected_day) or \
       (previous_year is not None and selected_year is not None and previous_year != selected_year):
        if 'image_annotations' in st.session_state and st.session_state.image_annotations:
            save_all_annotations(force_save=True)
            print(f"Saved annotations when changing from day {previous_day} to {selected_day} or year {previous_year} to {selected_year}")
    
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
    
    # Save the previous view state when switching tabs
    if tab_changed:
        # Save annotations before switching tabs
        if 'image_annotations' in st.session_state and st.session_state.image_annotations:
            save_all_annotations(force_save=True)
            print(f"Saved annotations when switching from {prev_tab} to {selected_tab} tab")
            
        # Pause the annotation timer when switching tabs
        if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
            annotation_timer.pause_timer()
            
        # Store current state in session state under the previous tab's key
        tab_key = f"{prev_tab}_state"
        st.session_state[tab_key] = {
            'selection_key': selection_key,
            'current_filepath': st.session_state.get('current_filepath'),
            'current_day': st.session_state.get('annotation_timer_current_day')
        }
        print(f"Saved state for {prev_tab} tab: {st.session_state[tab_key]}")
        
        # Force annotations to be reloaded when switching tabs by clearing current annotations
        # This ensures we get the freshest data from disk
        if 'image_annotations' in st.session_state:
            st.session_state.image_annotations = {}
    
    # Handle the Current tab view
    if selected_tab == "Current":
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
                    
                    # Always attempt to load annotations
                    load_day_annotations(selected_day, daily_filepaths)
                    
                    # Mark as loaded
                    st.session_state[annotations_loaded_key] = True
                    
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
        
        with bottom_container:
            with MemoryTracker("Annotation Panel"):
                # Display annotation panel for the current image
                if 'current_filepath' in st.session_state and st.session_state.current_filepath:
                    display_annotation_panel(st.session_state.current_filepath)
    
    # Handle the Historical tab view
    if selected_tab == "Historical":
        # Create containers for historical view
        hist_top_container = st.container()
        hist_center_container = st.container()
        hist_bottom_container = st.container()
        
        with hist_top_container:
            st.subheader("Historical Annotation View")
            st.write("View your annotation history and previously annotated days.")
            
            # Add year/month selector for historical view
            hist_year_col, hist_month_col = st.columns(2)
            
            with hist_year_col:
                # Get available years from session state
                key = f"{normalized_name}_{selected_instrument}"
                image_data = st.session_state.image_data.get(key, {}) if key and 'image_data' in st.session_state else {}
                years = list(image_data.keys())
                years.sort(reverse=True)  # Newest first
                
                if years:
                    # Initialize historical year if not set
                    if 'historical_year' not in st.session_state:
                        st.session_state.historical_year = years[0]
                    
                    # Year selector
                    historical_year = st.selectbox(
                        "Select Historical Year",
                        years,
                        index=years.index(st.session_state.historical_year) if st.session_state.historical_year in years else 0,
                        key="hist_year_select"
                    )
                    
                    # Update session state if changed
                    if historical_year != st.session_state.historical_year:
                        # Save current annotations before changing year
                        if 'image_annotations' in st.session_state and st.session_state.image_annotations:
                            save_all_annotations()
                            print(f"Saved annotations when changing year from {st.session_state.historical_year} to {historical_year}")
                        
                        st.session_state.historical_year = historical_year
                        # Reset historical day selection
                        if 'historical_day' in st.session_state:
                            st.session_state.historical_day = None
                        # Reset historical month selection
                        if 'historical_month' in st.session_state:
                            st.session_state.historical_month = None
                else:
                    st.warning("No years available. Please scan for images first.")
            
            with hist_month_col:
                # Initialize historical month if not set
                if 'historical_month' not in st.session_state:
                    st.session_state.historical_month = datetime.datetime.now().month
                
                # Month selector
                month_names = [calendar.month_name[m] for m in range(1, 13)]
                historical_month = st.selectbox(
                    "Select Historical Month",
                    range(1, 13),
                    format_func=lambda m: month_names[m-1],
                    index=st.session_state.historical_month-1,
                    key="hist_month_select"
                )
                
                # Update session state if changed
                if historical_month != st.session_state.historical_month:
                    # Save current annotations before changing month
                    if 'image_annotations' in st.session_state and st.session_state.image_annotations:
                        save_all_annotations()
                        print(f"Saved annotations when changing month from {st.session_state.historical_month} to {historical_month}")
                    
                    st.session_state.historical_month = historical_month
                    # Reset historical day selection
                    if 'historical_day' in st.session_state:
                        st.session_state.historical_day = None
            
            # Add a status filter
            status_filter = st.multiselect(
                "Filter by annotation status",
                ["not_annotated", "in_progress", "completed"],
                default=["completed", "in_progress"],
                key="hist_status_filter"
            )
            
            # Add button to load annotated days
            if st.button("Load Annotated Days", use_container_width=True, key="load_hist_days"):
                # Show a spinner while loading
                with st.spinner("Loading annotation history..."):
                    # Get the annotation status map for this combination
                    if 'annotation_status_map' in st.session_state:
                        status_key = f"{normalized_name}_{selected_instrument}_{st.session_state.historical_year}_{st.session_state.historical_month}"
                        
                        # If we don't have this combo in the status map, try to load it
                        if status_key not in st.session_state.annotation_status_map:
                            from phenotag.ui.components.annotation_status import check_day_annotation_status
                            
                            # Create a new status map for this month
                            status_map = {}
                            
                            # Get days in this month (basic calculation)
                            _, num_days = calendar.monthrange(int(st.session_state.historical_year), st.session_state.historical_month)
                            
                            # Check each day in the month
                            month_start = datetime.datetime(int(st.session_state.historical_year), st.session_state.historical_month, 1)
                            for day in range(1, num_days + 1):
                                # Calculate day of year
                                this_date = month_start + datetime.timedelta(days=day-1)
                                doy = this_date.timetuple().tm_yday
                                padded_doy = f"{doy:03d}"
                                
                                # Check status using scan info
                                if hasattr(st.session_state, 'scan_info'):
                                    scan_info = st.session_state.scan_info
                                    base_dir = scan_info['base_dir']
                                    station_name = scan_info['station_name']
                                    instrument_id = scan_info['instrument_id']
                                    
                                    status = check_day_annotation_status(
                                        base_dir, 
                                        station_name, 
                                        instrument_id, 
                                        st.session_state.historical_year, 
                                        padded_doy
                                    )
                                    
                                    # Store in map
                                    status_map[padded_doy] = status
                            
                            # Store the map
                            st.session_state.annotation_status_map[status_key] = status_map
                            print(f"Loaded annotation status for {len(status_map)} days in {st.session_state.historical_month}/{st.session_state.historical_year}")
                        
                        # Now display the status map
                        st.session_state.historical_status_map_loaded = True
        
        with hist_center_container:
            # Display a table of annotated days if status map is loaded
            if st.session_state.get('historical_status_map_loaded', False):
                # Get the status map for the selected year/month
                status_key = f"{normalized_name}_{selected_instrument}_{st.session_state.historical_year}_{st.session_state.historical_month}"
                status_map = st.session_state.annotation_status_map.get(status_key, {})
                
                if status_map:
                    # Create a dataframe with days and their status
                    import pandas as pd
                    
                    data = []
                    for doy, status in status_map.items():
                        # Only include days that match the status filter
                        if status in status_filter:
                            # Calculate month day and week day
                            try:
                                date_obj = datetime.datetime.strptime(f"{st.session_state.historical_year}-{doy}", "%Y-%j")
                                month_day = date_obj.day
                                week_day = date_obj.strftime("%A")
                                readable_date = date_obj.strftime("%Y-%m-%d")
                                
                                # Skip days that aren't in the selected month
                                if date_obj.month != st.session_state.historical_month:
                                    continue
                                
                                data.append({
                                    "DOY": doy,
                                    "Date": readable_date,
                                    "Day": month_day, 
                                    "Weekday": week_day,
                                    "Status": status
                                })
                            except ValueError:
                                # Skip invalid dates
                                continue
                    
                    # Create dataframe and display
                    if data:
                        df = pd.DataFrame(data)
                        df = df.sort_values(by="DOY")
                        
                        # Set up column config for the dataframe
                        column_config = {
                            "DOY": st.column_config.TextColumn("DOY", help="Day of Year"),
                            "Date": st.column_config.TextColumn("Date", help="Calendar date"),
                            "Day": st.column_config.NumberColumn("Day", help="Day of the month"),
                            "Weekday": st.column_config.TextColumn("Weekday", help="Day of the week"),
                            "Status": st.column_config.TextColumn(
                                "Status",
                                help="Annotation status",
                                formatter=lambda s: {
                                    "not_annotated": "⚪ Not Started", 
                                    "in_progress": "🟠 In Progress", 
                                    "completed": "🟢 Completed"
                                }.get(s, s)
                            )
                        }
                        
                        # Display dataframe with click to select functionality
                        hist_event = st.dataframe(
                            df,
                            column_config=column_config,
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row"
                        )
                        
                        # Handle selection event
                        if hist_event and hist_event.selection.rows:
                            # Get the selected DOY
                            selected_row_idx = hist_event.selection.rows[0]
                            selected_doy = df.iloc[selected_row_idx]["DOY"]
                            
                            # Save current annotations before changing selected day
                            if 'image_annotations' in st.session_state and st.session_state.image_annotations:
                                save_all_annotations()
                                print(f"Saved annotations when changing to historical day {selected_doy}")
                            
                            # Store in session state
                            st.session_state.historical_day = selected_doy
                            
                            # Get file paths for the day to load annotations
                            from phenotag.ui.components.image_display import get_filtered_file_paths
                            hist_filepaths = get_filtered_file_paths(
                                normalized_name, 
                                selected_instrument, 
                                st.session_state.historical_year, 
                                selected_doy
                            )
                            
                            # Store selected paths
                            st.session_state.historical_filepaths = hist_filepaths
                            
                            # First clear any existing annotations to force a reload from disk
                            if 'image_annotations' in st.session_state:
                                # Only clear annotations for the current day's images
                                for filepath in list(st.session_state.image_annotations.keys()):
                                    if os.path.basename(os.path.dirname(filepath)) == selected_doy:
                                        del st.session_state.image_annotations[filepath]
                                        
                            # Try to load annotations for this day
                            load_day_annotations(selected_doy, hist_filepaths)
                            
                            # Make sure annotation timer is initialized and active for this day
                            annotation_timer.initialize_session_state()
                            annotation_timer.start_timer(selected_doy)
                            
                            # Set the selected day for viewing
                            st.session_state.historical_view_ready = True
                    else:
                        st.info(f"No days with status {', '.join(status_filter)} found for this month")
                else:
                    st.info("No annotation status data available for the selected month")
            
            # Display selected day's images if a day is selected
            if st.session_state.get('historical_view_ready', False) and st.session_state.get('historical_day'):
                # Get selected day information
                hist_day = st.session_state.historical_day
                hist_year = st.session_state.historical_year
                hist_filepaths = st.session_state.get('historical_filepaths', [])
                
                # Show header
                date_obj = datetime.datetime.strptime(f"{hist_year}-{hist_day}", "%Y-%j")
                readable_date = date_obj.strftime("%Y-%m-%d")
                st.subheader(f"Viewing annotations for {readable_date} (DOY: {hist_day})")
                
                # Display image list and selected image
                if hist_filepaths:
                    # Create two columns with the specified ratio [2,5]
                    left_col, main_col = st.columns([2, 5])
                    
                    with left_col:
                        # Create image list
                        from phenotag.ui.components.image_display import display_image_list
                        hist_event = display_image_list(hist_filepaths)
                        
                        # Show file count
                        st.write(f"{len(hist_filepaths)} images available for day {hist_day}")
                    
                    with main_col:
                        # Display selected image
                        from phenotag.ui.components.image_display import display_selected_image
                        displayed_hist_filepath = display_selected_image(hist_event, hist_filepaths)
                        
                        # Update current filepath for annotation panel
                        if displayed_hist_filepath:
                            st.session_state.current_filepath = displayed_hist_filepath
                else:
                    st.warning(f"No image files found for day {hist_day} in year {hist_year}")
        
        with hist_bottom_container:
            # Display annotation panel for the historical image
            if 'current_filepath' in st.session_state and st.session_state.current_filepath:
                # Mark this day as in_progress in the annotation status cache
                if 'historical_day' in st.session_state and st.session_state.historical_day:
                    try:
                        if 'annotation_status_map' in st.session_state:
                            hist_status_key = f"{normalized_name}_{selected_instrument}_{st.session_state.historical_year}_{st.session_state.historical_month}"
                            
                            # Update cache entry
                            if hist_status_key not in st.session_state.annotation_status_map:
                                st.session_state.annotation_status_map[hist_status_key] = {}
                                
                            # Mark this day as in_progress in the cache
                            if st.session_state.historical_day in st.session_state.annotation_status_map[hist_status_key]:
                                current_status = st.session_state.annotation_status_map[hist_status_key][st.session_state.historical_day]
                                if current_status != 'completed':  # Don't downgrade from completed
                                    st.session_state.annotation_status_map[hist_status_key][st.session_state.historical_day] = 'in_progress'
                            else:
                                st.session_state.annotation_status_map[hist_status_key][st.session_state.historical_day] = 'in_progress'
                    except Exception as e:
                        print(f"Error updating historical status cache: {str(e)}")
                
                # Display the annotation panel
                display_annotation_panel(st.session_state.current_filepath)
                
                # Add a button to refresh the calendar view
                if st.button("Update Calendar View", key="refresh_calendar_view"):
                    # Force saving annotations
                    save_all_annotations()
                    st.session_state.historical_status_map_loaded = False
                    st.rerun()
    
    # Store important data in session state
    if selected_instrument:
        # Store instrument info in session state
        st.session_state.current_instrument = selected_instrument
        
        # Try to load ROIs if showing overlays but not yet loaded
        if (st.session_state.get('show_roi_overlays', False) and 
            ('instrument_rois' not in st.session_state or not st.session_state.instrument_rois)):
            with MemoryTracker("Load ROIs"):
                load_instrument_rois()
                
    # Save annotations before leaving the page
    if 'image_annotations' in st.session_state and st.session_state.image_annotations:
        save_all_annotations()
    
    # Check memory usage and reclaim if necessary
    if memory_manager.check_memory_threshold():
        memory_manager.clear_memory()
        
    # Memory information is now displayed in an expander at the bottom of the sidebar


if __name__ == "__main__":
    main()