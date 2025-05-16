"""
Calendar view component for PhenoTag UI.

This module handles displaying and managing the calendar for day selection.
"""
import os
import time
import calendar
import streamlit as st
from pathlib import Path

from phenotag.io_tools import (
    get_available_years,
    get_days_in_year,
    get_days_in_month, 
    format_month_year,
    create_placeholder_data
)
from phenotag.ui.calendar_component import create_calendar, format_day_range
from phenotag.ui.components.session_state import save_session_config


def render_year_month_selectors(normalized_name, selected_instrument, image_data):
    """
    Render year and month selectors.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        image_data (dict): Image data dictionary
        
    Returns:
        tuple: (selected_year, selected_month) containing current selection
    """
    # Get years from image data
    key = f"{normalized_name}_{selected_instrument}"
    
    # For no L1 data case
    if (key in st.session_state.image_data and
        len(st.session_state.image_data[key]) == 1 and
        "_no_l1_data" in st.session_state.image_data[key]):
        # Show a reminder message about missing L1 data
        st.warning(f"No L1 data found for {selected_instrument}. Process L0 images to L1 before annotation.")
        st.info("Click 'Scan for Images' again after processing images to refresh.")
        return None, None
    
    # Normal case with image data
    years = list(image_data.keys())
    years.sort(reverse=True)  # Sort in descending order (newest first)
    
    if not years:
        return None, None
        
    # Default to the latest year if none selected
    if ('selected_year' not in st.session_state or 
        st.session_state.selected_year not in years):
        st.session_state.selected_year = years[0]
    
    # Create a container with two columns for year and month selectors
    year_month_cols = st.columns(2)

    # Year selector in the left column
    with year_month_cols[0]:
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
        # Reset image_annotations to ensure we reload them for the new year
        if 'image_annotations' in st.session_state:
            # No auto-save when changing year
            if hasattr(st.session_state, 'image_annotations') and st.session_state.image_annotations:
                print(f"No auto-save when changing year to {selected_year}")
                
            # Pause the annotation timer when changing years
            if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
                from phenotag.ui.components.annotation_timer import annotation_timer
                annotation_timer.pause_timer()
                
            # Now clear the annotations
            st.session_state.image_annotations = {}
            
            # Clear annotation status cache when changing year
            if 'annotation_status_map' in st.session_state:
                st.session_state.annotation_status_map = {}
                print("Cleared annotation status cache due to year change")
        # Save session config when selection changes (UI state, not annotations)
        save_session_config()
        # Trigger a rerun to update the UI
        st.rerun()

    # Set default month if not selected
    if st.session_state.selected_month is None:
        # Default to the current month or January if not specified
        import datetime
        current_month = datetime.datetime.now().month
        st.session_state.selected_month = current_month

    # Month selector in the right column
    with year_month_cols[1]:
        month_names = [calendar.month_name[m] for m in range(1, 13)]
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
        # Reset selected day
        st.session_state.selected_day = None
        
        # Clear annotations without auto-saving when changing months
        if 'image_annotations' in st.session_state and st.session_state.image_annotations:
            # No auto-save when changing month
            print(f"No auto-save when changing month to {selected_month_idx}")
            # Clear annotations 
            st.session_state.image_annotations = {}
            
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
        
    return selected_year, selected_month_idx


def render_calendar(normalized_name, selected_instrument, selected_year, selected_month):
    """
    Render calendar view for day selection.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        selected_year (str): Selected year
        selected_month (int): Selected month
        
    Returns:
        list: List of selected days
    """
    # Preload annotation status for all days in this month
    try:
        from phenotag.ui.components.annotation_status import check_day_annotation_status
        
        # Only check if we have scan info
        if hasattr(st.session_state, 'scan_info'):
            scan_info = st.session_state.scan_info
            base_dir = scan_info['base_dir']
            station_name = scan_info['station_name']
            instrument_id = scan_info['instrument_id']
            
            # If we don't have a cached annotation status map, create it
            if 'annotation_status_map' not in st.session_state:
                st.session_state.annotation_status_map = {}
                
            # Create a key for this combination
            status_key = f"{normalized_name}_{selected_instrument}_{selected_year}_{selected_month}"
            
            # Check if we need to load status
            if status_key not in st.session_state.annotation_status_map:
                # First, try to load from L1 parent directory
                try:
                    from phenotag.ui.components.annotation_status_manager import get_l1_parent_path, get_status_filename
                    l1_parent_path = get_l1_parent_path(base_dir, station_name, instrument_id)
                    status_filename = get_status_filename(station_name, instrument_id)
                    status_file_path = l1_parent_path / status_filename
                    
                    # Check if the status file exists
                    if os.path.exists(status_file_path):
                        import yaml
                        with open(status_file_path, "r") as f:
                            status_data = yaml.safe_load(f) or {}
                        
                        # Extract statuses for this year/month
                        status_map = {}
                        if ("annotations" in status_data and
                            str(selected_year) in status_data["annotations"]):
                            
                            year_data = status_data["annotations"][str(selected_year)]
                            
                            # Get days in this month (basic calculation)
                            import datetime
                            _, num_days = calendar.monthrange(int(selected_year), selected_month)
                            month_start = datetime.datetime(int(selected_year), selected_month, 1)
                            
                            # Process each day in the month
                            for day in range(1, num_days + 1):
                                # Calculate day of year
                                this_date = month_start + datetime.timedelta(days=day-1)
                                doy = this_date.timetuple().tm_yday
                                padded_doy = f"{doy:03d}"
                                
                                # Get status from L1 parent file if available
                                if padded_doy in year_data:
                                    day_status = year_data[padded_doy].get("status", "not_annotated")
                                    status_map[padded_doy] = day_status
                                else:
                                    # Fallback to checking individual files
                                    status = check_day_annotation_status(
                                        base_dir,
                                        station_name,
                                        instrument_id,
                                        selected_year,
                                        padded_doy
                                    )
                                    status_map[padded_doy] = status
                        
                        # If we found statuses, use them
                        if status_map:
                            st.session_state.annotation_status_map[status_key] = status_map
                            print(f"Loaded annotation status from L1 parent for {len(status_map)} days in {selected_month}/{selected_year}")
                            # No need to check individual files
                            return
                
                except Exception as parent_error:
                    print(f"Error loading from L1 parent: {str(parent_error)}")
                    # Continue with individual file checking
                
                # Create a new status map for this month
                status_map = {}
                
                # Get days in this month (basic calculation)
                _, num_days = calendar.monthrange(int(selected_year), selected_month)
                
                # Check each day in the month
                import datetime
                month_start = datetime.datetime(int(selected_year), selected_month, 1)
                for day in range(1, num_days + 1):
                    # Calculate day of year
                    this_date = month_start + datetime.timedelta(days=day-1)
                    doy = this_date.timetuple().tm_yday
                    padded_doy = f"{doy:03d}"
                    
                    # Check status
                    status = check_day_annotation_status(
                        base_dir, 
                        station_name, 
                        instrument_id, 
                        selected_year, 
                        padded_doy
                    )
                    
                    # Store in map
                    status_map[padded_doy] = status
                
                # Store the map
                st.session_state.annotation_status_map[status_key] = status_map
                print(f"Preloaded annotation status for {len(status_map)} days in {selected_month}/{selected_year}")
    except Exception as e:
        print(f"Error preloading annotation status: {str(e)}")
    if not selected_year or not selected_month:
        return []
        
    # Get the key for this station+instrument combo
    key = f"{normalized_name}_{selected_instrument}"
    
    # Add calendar directly (no expander when in sidebar)
    # Key to track if we've already scanned for this month
    calendar_scan_key = f"calendar_scanned_{selected_year}_{selected_month}"

    # Determine if we need to scan based on:
    # 1. We haven't scanned this month/year yet
    # 2. User explicitly requested a refresh
    # 3. We changed months or years
    month_changed = st.session_state.get('last_month', None) != selected_month
    year_changed = st.session_state.get('last_year', None) != selected_year

    need_scan = (not st.session_state.get(calendar_scan_key, False) or
                st.session_state.get('refresh_mode', False) or
                month_changed or year_changed)

    # Update last month/year tracking
    st.session_state['last_month'] = selected_month
    st.session_state['last_year'] = selected_year

    # Reset the refresh flag after checking
    if st.session_state.get('refresh_mode', False):
        st.session_state.refresh_mode = False

    # Check if we need to scan days for this month
    if need_scan and hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
        with st.spinner(f"Scanning for days in {calendar.month_name[selected_month]} {selected_year}..."):
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
                selected_month,
                all_days
            )

            # Log available days after filtering
            print(f"Calendar - Days in month {selected_month}: {month_filtered_days}")

            available_days = month_filtered_days

            # Update progress
            calendar_progress.progress(70)

            # Create placeholder data structure for the calendar
            calendar_image_data = create_placeholder_data(selected_year, available_days)

            # Store the data in session state
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
                st.success(f"Found {len(available_days)} days with images in {calendar.month_name[selected_month]} {selected_year}")
            else:
                st.info(f"No images found for {calendar.month_name[selected_month]} {selected_year}")

    # Check if we're using lazy loading and have data
    if hasattr(st.session_state, 'scan_info') and st.session_state.scan_info.get('lazy_loaded'):
        # See if we have data for this year/month
        if ('image_data' in st.session_state and
            key in st.session_state.image_data and
            selected_year in st.session_state.image_data[key]):

            # Create calendar with existing data
            calendar_data = {selected_year: st.session_state.image_data[key][selected_year]}

            # Use data for the calendar
            selected_days, selected_week = create_calendar(
                int(selected_year),
                selected_month,
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
            selected_month,
            st.session_state.image_data[key]
        )
        
    # Add a refresh button
    if st.button("🔄 Refresh Days", key="refresh_days_button",
              help="Refresh available days for the current month"):
        # Request a refresh for this month/year combination
        st.session_state.refresh_mode = True
        st.session_state[calendar_scan_key] = False  # Reset the scan flag
        st.rerun()
        
    return selected_days


def display_calendar_view(normalized_name, selected_instrument):
    """
    Display calendar view component for day selection.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        
    Returns:
        tuple: (selected_year, selected_days) containing current selection
    """
    # Check if we have image data to display
    key = f"{normalized_name}_{selected_instrument}" if normalized_name and selected_instrument else None
    image_data = st.session_state.image_data.get(key, {}) if key and 'image_data' in st.session_state else {}
    
    # No data scenario
    if not image_data:
        st.info("No image data available. Please scan for images first.")
        return None, []
    
    # Special no_l1_data case
    if (key in st.session_state.image_data and
        len(st.session_state.image_data[key]) == 1 and
        "_no_l1_data" in st.session_state.image_data[key]):
        st.warning(f"No L1 data found for {selected_instrument}. Process L0 images to L1 before annotation.")
        return None, []
    
    # Render year and month selectors
    selected_year, selected_month = render_year_month_selectors(normalized_name, selected_instrument, image_data)
    
    if not selected_year or not selected_month:
        return None, []
    
    # Render calendar for the selected year and month
    selected_days = render_calendar(normalized_name, selected_instrument, selected_year, selected_month)
    
    # Check if day selection has changed
    day_changed = False
    
    # Check if current day is different from selected day
    current_day = st.session_state.get('selected_day')
    
    # Handle case where we have days selected in multi-select but no single day
    if selected_days and not current_day:
        # Select the first day in the list
        current_day = str(selected_days[0])
        st.session_state.selected_day = current_day
        day_changed = True
        
    # If we have a single day selected but it's not in selected_days (compatibility)
    if current_day and selected_days and current_day not in [str(day) for day in selected_days]:
        # Update selected_days to match single selection
        selected_days = [int(current_day)]
        st.session_state.selected_days = selected_days
        day_changed = True
    
    # For backward compatibility, ensure selected_days always has at least the current day
    if current_day and (not selected_days or int(current_day) not in selected_days):
        selected_days = [int(current_day)]
        st.session_state.selected_days = selected_days
        day_changed = True
        
    # Save any changes to the configuration
    if day_changed:
        save_session_config()
            
    # If days changed, clear image annotations to ensure we load fresh annotations
    if day_changed and 'image_annotations' in st.session_state:
        # No auto-save when changing day selection
        if hasattr(st.session_state, 'image_annotations') and st.session_state.image_annotations:
            print(f"No auto-save when changing day selection")
            
        # Pause the annotation timer when changing days
        if hasattr(st.session_state, 'annotation_timer_current_day') and st.session_state.annotation_timer_current_day:
            from phenotag.ui.components.annotation_timer import annotation_timer
            annotation_timer.pause_timer()
            
        # Clear the annotations to force reloading
        st.session_state.image_annotations = {}
            
    # Display selected day range if available
    if selected_days:
        selection_text = format_day_range(selected_days, int(selected_year))
        st.write(f"**Selected: {selection_text}**")
        
    return selected_year, selected_days