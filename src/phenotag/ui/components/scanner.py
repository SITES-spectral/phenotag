"""
Scanner component for PhenoTag.

This module handles scanning for images and maintaining scan state.
"""
import os
import time
import streamlit as st

from phenotag.io_tools import (
    lazy_find_phenocam_images,
    get_available_days_in_year,
    get_available_years
)
from phenotag.ui.components.session_state import save_session_config


def handle_scan(normalized_name, selected_instrument):
    """
    Handle image scanning process for the selected station and instrument.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        
    Returns:
        bool: True if scan was performed, False otherwise
    """
    # Only proceed if scan is requested
    if not hasattr(st.session_state, 'scan_requested') or not st.session_state.scan_requested:
        return False
        
    scan_container = st.container()
    with scan_container:
        # Check if this is an automatic scan
        is_auto_scan = hasattr(st.session_state, 'auto_scan') and st.session_state.auto_scan
        
        # Display appropriate heading based on scan type
        if is_auto_scan:
            st.subheader("Loading images from saved configuration...")
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

            # Save session config (UI state and settings, not annotations)
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
        
    return True


def should_auto_scan(normalized_name, selected_instrument):
    """
    Check if auto-scanning should be performed based on the current state.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
        
    Returns:
        bool: True if auto-scan should be performed, False otherwise
    """
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
            key = f"{normalized_name}_{selected_instrument}"

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

        # Return the result
        return should_scan
    
    # Default to false
    return False


def setup_auto_scan(normalized_name, selected_instrument):
    """
    Set up auto-scanning flags in the session state.
    
    Args:
        normalized_name (str): Normalized station name
        selected_instrument (str): Selected instrument ID
    """
    st.session_state.scan_requested = True
    st.session_state.scan_station = normalized_name
    st.session_state.scan_instrument = selected_instrument
    st.session_state.auto_scan = True  # Flag to indicate this is an automatic scan