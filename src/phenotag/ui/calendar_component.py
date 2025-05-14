import streamlit as st
import pandas as pd
import numpy as np
import datetime
import calendar
from typing import Dict, List, Optional, Tuple, Union

def generate_month_calendar(year: int, month: int, image_counts: Dict[str, int] = None) -> pd.DataFrame:
    """
    Generate a calendar dataframe for the specified month with day of year and image counts.
    
    Args:
        year: The year
        month: The month (1-12)
        image_counts: Dictionary mapping day of year to image count
        
    Returns:
        DataFrame with calendar data
    """
    # Get the first day of the month and the number of days in the month
    first_day, num_days = calendar.monthrange(year, month)
    
    # Create a list for each week (row) in the calendar
    weeks = []
    week = [None] * first_day  # Padding for the first week
    
    for day in range(1, num_days + 1):
        week.append(day)
        
        # If we've filled a week (7 days) or this is the last day, append the week and start a new one
        if len(week) == 7 or day == num_days:
            # Pad the last week if needed
            if len(week) < 7:
                week.extend([None] * (7 - len(week)))
            
            weeks.append(week)
            week = []
    
    # Create dataframe with the calendar data
    df = pd.DataFrame(weeks, columns=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    
    # Add metadata for each day (DOY and image counts)
    day_metadata = {}
    
    # Process each day in the calendar
    for week_idx, week in enumerate(weeks):
        for day_idx, day in enumerate(week):
            if day is not None:
                # Calculate day of year
                date = datetime.date(year, month, day)
                doy = date.timetuple().tm_yday
                
                # Format day of year with padding to match the format in the data
                doy_padded = f"{doy:03d}"  # Format with leading zeros (e.g., 090)
                doy_unpadded = str(doy)    # Format without leading zeros (e.g., 90)
                doy_as_int = str(int(doy))  # Format as plain integer (e.g., 90)
                
                # Debug output for specific days (like day 90)
                if doy in [90]:
                    print(f"Calendar - Day {doy} search:")
                    print(f"  - Checking formats: {doy_padded}, {doy_unpadded}, {doy_as_int}")
                    if image_counts:
                        print(f"  - Available keys in image_counts: {list(image_counts.keys())[:10]}")

                # Try all formats to be more resilient
                img_count = 0
                if image_counts:
                    # Check in order: padded, unpadded, int format
                    if doy_padded in image_counts:
                        img_count = image_counts[doy_padded]
                        if doy in [90]:
                            print(f"  - Found in padded format: {img_count} images")
                    elif doy_unpadded in image_counts:
                        img_count = image_counts[doy_unpadded]
                        if doy in [90]:
                            print(f"  - Found in unpadded format: {img_count} images")
                    elif doy_as_int in image_counts:
                        img_count = image_counts[doy_as_int]
                        if doy in [90]:
                            print(f"  - Found in int format: {img_count} images")
                    else:
                        if doy in [90]:
                            print(f"  - Not found in any format")
                
                # Store metadata
                day_metadata[(week_idx, day_idx)] = {
                    "day": day,
                    "doy": doy,
                    "doy_padded": doy_padded,
                    "year": year,
                    "image_count": img_count
                }
    
    return df, day_metadata

def get_color_scale(value: int, max_value: int) -> str:
    """
    Generate a color based on the value within a range from light blue to dark blue.
    
    Args:
        value: The current value
        max_value: The maximum value in the range
        
    Returns:
        CSS color string
    """
    if value == 0:
        return "#f0f0f0"  # Light gray for zero
    
    # Normalize value between 0.1 and 1.0 (avoid completely white)
    normalized = 0.1 + (0.9 * (value / max_value)) if max_value > 0 else 0.1
    
    # Convert to a blue shade (darker = more images)
    intensity = int(255 * (1 - normalized))
    return f"rgb(200, 220, {intensity})"

def style_calendar_cell(day: Optional[int], metadata: Dict, max_images: int) -> Dict:
    """
    Create styling for a calendar cell based on metadata.
    
    Args:
        day: The day number or None for empty cells
        metadata: Metadata for the day including image count
        max_images: Maximum number of images for any day
        
    Returns:
        Dictionary of CSS styles
    """
    if day is None:
        return {
            "backgroundColor": "#f9f9f9",  # Light gray for empty cells
            "color": "transparent"
        }
    
    # Get day of year for annotation status
    doy = metadata.get("doy_padded", None)
    img_count = metadata.get("image_count", 0)
    color = get_color_scale(img_count, max_images)
    
    # Get annotation status if possible
    annotation_status = "not_annotated"
    try:
        from phenotag.ui.components.annotation_status import check_day_annotation_status, get_status_color
        
        # Get status if we have scan info
        if hasattr(st.session_state, 'scan_info') and doy:
            scan_info = st.session_state.scan_info
            base_dir = scan_info['base_dir']
            station_name = scan_info['station_name']
            instrument_id = scan_info['instrument_id']
            year = metadata.get("year", st.session_state.get('selected_year'))
            
            if year and base_dir and station_name and instrument_id:
                annotation_status = check_day_annotation_status(
                    base_dir, 
                    station_name, 
                    instrument_id, 
                    year, 
                    doy
                )
                
                # Use status-based color
                status_color = get_status_color(annotation_status)
                if status_color:
                    color = status_color
    except Exception as e:
        print(f"Error getting annotation status for styling: {str(e)}")
    
    style = {
        "backgroundColor": color,
        "color": "#000000",
        "textAlign": "center",
        "cursor": "pointer",
        "borderRadius": "4px",
        "padding": "8px",
        "fontWeight": "normal"
    }
    
    # Add a notification dot for days with images
    if img_count > 0:
        # Add background position and image count as text
        style["position"] = "relative"
    
    # Add borders for annotation status
    if annotation_status == 'completed':
        style["borderLeft"] = "3px solid #4CAF50"  # Green border
    elif annotation_status == 'in_progress':
        style["borderLeft"] = "3px solid #FF9800"  # Orange border
        
    return style

def create_calendar(year: int, month: int, image_data: Dict, on_select=None):
    """
    Create an interactive calendar for the given month showing image availability.
    
    Args:
        year: The calendar year
        month: The calendar month (1-12)
        image_data: Dictionary with image data by day of year
        on_select: Callback function when a day is selected
        
    Returns:
        The calendar component and selected day(s)
    """
    # Get image counts by day of year
    image_counts = {}
    
    if str(year) in image_data:
        # Debug output of raw data
        print(f"Calendar image data for year {year}, month {month}:")
        print(f"Available days in data: {list(image_data[str(year)].keys())[:10]}")

        for doy, files in image_data[str(year)].items():
            # Support both full file data and placeholder metadata
            if isinstance(files, dict) and "_placeholder" in files:
                # For lazy loading, check if we have a stored image count
                if "_image_count" in files:
                    # Use the stored count
                    img_count = files["_image_count"]
                    image_counts[doy] = img_count
                    print(f"Calendar: Found stored count for day {doy}: {img_count}")
                else:
                    # Default to 1 if no count is available
                    image_counts[doy] = 1
                    print(f"Calendar: Using default count for day {doy}: 1")
            else:
                # Normal case - count the actual files
                img_count = len(files)
                image_counts[doy] = img_count
                print(f"Calendar: Counted {img_count} files for day {doy}")
                
        # Double-check if we have data for days in March (specifically around day 90)
        month_3_days = [d for d in range(60, 92)]  # Days in March
        for d in month_3_days:
            d_padded = f"{d:03d}"
            if d_padded in image_counts:
                print(f"Calendar: Found day {d_padded} with {image_counts[d_padded]} images")
            elif str(d) in image_counts:
                print(f"Calendar: Found day {d} with {image_counts[str(d)]} images")
    
    # Generate calendar dataframe and metadata
    calendar_df, day_metadata = generate_month_calendar(year, month, image_counts)
    
    # Find the maximum image count for scaling colors
    max_images = max([metadata.get("image_count", 0) for metadata in day_metadata.values()]) if day_metadata else 1
    
    # Format the calendar for display - convert all values to strings first
    formatted_calendar = calendar_df.copy().astype(object)
    
    # Apply formatting to each cell
    for week_idx in range(len(calendar_df)):
        for day_idx in range(7):
            day = calendar_df.iloc[week_idx, day_idx]
            if day is not None and not pd.isna(day):  # Check for None and NaN values
                # Add image count to display
                img_count = day_metadata.get((week_idx, day_idx), {}).get("image_count", 0)
                if img_count > 0:
                    # Convert day to integer safely
                    day_int = int(day) if not pd.isna(day) else ""
                    formatted_calendar.iloc[week_idx, day_idx] = f"{day_int} ({img_count})"
                else:
                    # Convert day to integer safely
                    day_int = int(day) if not pd.isna(day) else ""
                    formatted_calendar.iloc[week_idx, day_idx] = str(day_int)
            else:
                formatted_calendar.iloc[week_idx, day_idx] = ""
    
    # Create calendar header
    st.write(f"### {calendar.month_name[month]} {year}")
    
    # Use session state to track selection
    # Create a unique key for this calendar's selection
    selection_key = f"calendar_selection_{year}_{month}"
    clicked_key = f"calendar_clicked_{year}_{month}"
    
    # Initialize the selection state if needed
    if selection_key not in st.session_state:
        st.session_state[selection_key] = []
        
    # Add clickable day cells
    st.write("**Select days with images:**")
    
    # Create a grid of buttons for day selection
    for week_idx in range(len(formatted_calendar)):
        cols = st.columns(7)  # 7 days in a week
        for day_idx in range(7):
            with cols[day_idx]:
                day = calendar_df.iloc[week_idx, day_idx]
                if day is not None and not pd.isna(day):
                    # Get metadata for this day
                    meta = day_metadata.get((week_idx, day_idx), {})
                    doy = meta.get("doy", None)
                    img_count = meta.get("image_count", 0)

                    # Create a button for this day
                    if doy:
                        # Check if this day is already selected
                        is_selected = doy in st.session_state.get(selection_key, [])

                        # Determine button style based on selection and image count
                        # Convert day to integer for display safely
                        try:
                            day_int = int(day)
                            button_text = f"{day_int}"
                            # Image count removed as requested
                        except (ValueError, TypeError):
                            # Handle conversion errors
                            button_text = "?"
                            # Image count removed as requested
                            
                        # Get annotation status
                        try:
                            from phenotag.ui.components.annotation_status import check_day_annotation_status, get_status_icon
                            
                            # Get status if we have scan info
                            annotation_status = "not_annotated"
                            if hasattr(st.session_state, 'scan_info'):
                                scan_info = st.session_state.scan_info
                                base_dir = scan_info['base_dir']
                                station_name = scan_info['station_name']
                                instrument_id = scan_info['instrument_id']
                                
                                # Check if we have padded format
                                doy_padded = meta.get("doy_padded", doy)
                                
                                # Try to get from cache first
                                if 'annotation_status_map' in st.session_state:
                                    # Extract month from day number
                                    try:
                                        from datetime import datetime
                                        date = datetime.strptime(f"{year}-{doy_padded}", "%Y-%j")
                                        month = date.month
                                        status_key = f"{station_name}_{instrument_id}_{year}_{month}"
                                        
                                        # Get from cache if available
                                        if status_key in st.session_state.annotation_status_map:
                                            cached_status = st.session_state.annotation_status_map[status_key].get(doy_padded)
                                            if cached_status:
                                                annotation_status = cached_status
                                    except:
                                        # Fall back to direct check
                                        pass
                                
                                # If not in cache, check directly
                                if annotation_status == "not_annotated":
                                    annotation_status = check_day_annotation_status(
                                        base_dir, 
                                        station_name, 
                                        instrument_id, 
                                        year, 
                                        doy_padded
                                    )
                            
                            # Add status icon to button text
                            status_icon = get_status_icon(annotation_status)
                            if status_icon:
                                button_text = f"{button_text} {status_icon}"
                        except Exception as e:
                            print(f"Error getting annotation status: {str(e)}")
                            
                        # Current selected day (single selection)
                        is_selected = st.session_state.get('selected_day') == str(doy)
                        button_type = "primary" if is_selected else "secondary"
                        
                        # Disable days with no images
                        disabled = img_count == 0
                        
                        if st.button(button_text, key=f"day_{year}_{month}_{doy}", 
                                     type=button_type, disabled=disabled):
                            # Save annotations before changing day
                            if 'image_annotations' in st.session_state and st.session_state.image_annotations:
                                from phenotag.ui.components.annotation import save_all_annotations
                                save_all_annotations(force_save=True)
                                print(f"Saved annotations when changing day to {doy}")
                            
                            # Set this day as the selected day (single selection)
                            st.session_state.selected_day = str(doy)
                            
                            # Store a list with just this day for backward compatibility
                            if selection_key not in st.session_state:
                                st.session_state[selection_key] = []
                            st.session_state[selection_key] = [doy]
                            
                            # Rerun to update UI
                            st.rerun()
    
    # Process calendar selection
    selected_days = []
    selected_week = None
    
    # Use session state for selections
    if selection_key in st.session_state:
        selected_days = st.session_state[selection_key]
    
    if clicked_key in st.session_state:
        selected_week = st.session_state[clicked_key]
        
    # Add a legend for annotation status
    st.markdown("##### Annotation Status")
    st.markdown("✅ - Completed | 🔶 - In Progress | No icon - Not started")
    
    # Add a clear selection button
    if st.button("Clear Selection", key=f"clear_{year}_{month}"):
        # Save annotations before clearing selection
        if 'image_annotations' in st.session_state and st.session_state.image_annotations:
            from phenotag.ui.components.annotation import save_all_annotations
            save_all_annotations(force_save=True)
            print("Saved annotations when clearing day selection")
            
        # Clear both single selection and multi-selection for backward compatibility
        st.session_state.selected_day = None
        st.session_state[selection_key] = []
        if clicked_key in st.session_state:
            del st.session_state[clicked_key]
        st.rerun()
    
    return selected_days, selected_week

def get_month_with_most_images(year: str, image_data: Dict) -> int:
    """
    Find the month with the most images for a given year.
    
    Args:
        year: The year to check
        image_data: Image data dictionary
        
    Returns:
        Month number (1-12) with the most images
    """
    if year not in image_data:
        return 1  # Default to January if no data
    
    # Count images by month
    month_counts = {}
    for doy, files in image_data[year].items():
        # Convert day of year to month
        try:
            # Handle different formats of day
            if isinstance(doy, str):
                doy_int = int(doy.lstrip('0') or '0')  # Handle '000' case
            else:
                doy_int = int(doy)
                
            date = datetime.datetime(int(year), 1, 1) + datetime.timedelta(days=doy_int-1)
            month = date.month
            
            # Add image count to month total
            if month not in month_counts:
                month_counts[month] = 0
                
            # Count images - handle both actual files and placeholder data
            if isinstance(files, dict) and "_placeholder" in files:
                # For placeholder data, use stored count if available
                if "_image_count" in files:
                    month_counts[month] += files["_image_count"]
                else:
                    month_counts[month] += 1  # Default to 1 if no count
            else:
                # Normal case - count actual files
                month_counts[month] += len(files)
        except (ValueError, TypeError, OverflowError):
            continue
    
    # Find month with most images
    if month_counts:
        return max(month_counts, key=month_counts.get)
    return 1  # Default to January if no data

def format_day_range(selected_days: List[int], year: int) -> str:
    """
    Format selected days as a human-readable range.
    
    Args:
        selected_days: List of day of year numbers
        year: The year
        
    Returns:
        Formatted string describing the selection
    """
    if not selected_days:
        return "No days selected"
    
    # Sort days
    sorted_days = sorted(selected_days)
    
    # Convert to dates
    dates = [datetime.datetime(year, 1, 1) + datetime.timedelta(days=doy-1) for doy in sorted_days]
    
    # Check if this is a consecutive range (week)
    is_consecutive = all(dates[i+1].toordinal() - dates[i].toordinal() == 1 
                        for i in range(len(dates)-1))
    
    if is_consecutive and len(dates) > 1:
        # Format as range
        start, end = dates[0], dates[-1]
        return f"{start.strftime('%B %d')} - {end.strftime('%B %d, %Y')} (DoY {sorted_days[0]}-{sorted_days[-1]})"
    elif len(dates) == 1:
        # Single date
        return f"{dates[0].strftime('%B %d, %Y')} (DoY {sorted_days[0]})"
    else:
        # Multiple non-consecutive dates
        return f"{len(dates)} days selected (DoY {', '.join(map(str, sorted_days[:3]))}{'...' if len(sorted_days) > 3 else ''})"