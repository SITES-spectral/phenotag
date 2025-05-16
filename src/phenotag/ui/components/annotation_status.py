"""
Annotation status tracking component for PhenoTag.

This module provides functions to check and track the status of annotations
for different days, instruments, and stations.
"""
import os
import yaml
import streamlit as st
from pathlib import Path


def check_day_annotation_status(base_dir, station_name, instrument_id, year, day):
    """
    Check the annotation status for a specific day.
    
    Args:
        base_dir (str): Base directory for data
        station_name (str): Station name
        instrument_id (str): Instrument ID
        year (str): Year
        day (str): Day of year
        
    Returns:
        str: Status - 'not_annotated', 'in_progress', or 'completed'
    """
    # Get the normalized station name for consistent directory paths
    from phenotag.ui.components.annotation_status_manager import get_normalized_station_name
    normalized_name = get_normalized_station_name(station_name)
    
    # Check if we have this in our status cache
    if 'annotation_status_map' in st.session_state:
        # Create a key for this month (extract month from day number)
        try:
            from datetime import datetime
            date = datetime.strptime(f"{year}-{day}", "%Y-%j")
            month = date.month
            # Use the normalized station name for cache key consistency
            status_key = f"{normalized_name}_{instrument_id}_{year}_{month}"
            
            # Check if we have this month in our cache
            if status_key in st.session_state.annotation_status_map:
                # Try to get status from cache
                day_status = st.session_state.annotation_status_map[status_key].get(day)
                if day_status:
                    # Always check if currently being annotated (overrides cache)
                    if 'annotation_timer_current_day' in st.session_state and st.session_state.annotation_timer_current_day == day:
                        return 'in_progress'
                    return day_status
        except Exception as e:
            print(f"Error accessing status cache: {str(e)}")
    
    # Path to the annotation file
    day_dir = os.path.join(
        base_dir, 
        normalized_name,  # Use normalized station name for path
        "phenocams", 
        "products", 
        instrument_id, 
        "L1", 
        str(year), 
        str(day)
    )
    
    annotations_file = os.path.join(day_dir, f"annotations_{day}.yaml")
    
    # Check if currently being annotated (highest priority)
    if 'annotation_timer_current_day' in st.session_state and st.session_state.annotation_timer_current_day == day:
        return 'in_progress'
    
    # Check if file exists
    if os.path.exists(annotations_file):
        try:
            # Verify contents to make sure it's complete
            with open(annotations_file, 'r') as f:
                data = yaml.safe_load(f)
                # Check if it has annotations
                if data and 'annotations' in data and data['annotations']:
                    return 'completed'
        except:
            # If we can't read the file or it's empty, consider it not annotated
            return 'not_annotated'
    
    return 'not_annotated'


def get_status_icon(status):
    """
    Get an icon for the annotation status.
    
    Args:
        status (str): Status - 'not_annotated', 'in_progress', or 'completed'
        
    Returns:
        str: Icon character
    """
    if status == 'completed':
        return "✅"  # Green check mark
    elif status == 'in_progress':
        return "🔶"  # Orange diamond
    else:
        return ""  # No icon for not annotated


def get_status_color(status):
    """
    Get color for the annotation status.
    
    Args:
        status (str): Status - 'not_annotated', 'in_progress', or 'completed'
        
    Returns:
        str: CSS color
    """
    if status == 'completed':
        return "#E8F5E9"  # Light green
    elif status == 'in_progress':
        return "#FFF3E0"  # Light orange
    else:
        return "#FFFFFF"  # White