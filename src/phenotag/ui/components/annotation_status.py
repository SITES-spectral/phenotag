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
    Supports both per-image annotation files and legacy day-level annotation files.
    
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
    
    # Check if currently being annotated (highest priority)
    if 'annotation_timer_current_day' in st.session_state and st.session_state.annotation_timer_current_day == day:
        return 'in_progress'
    
    # First check the new day status file format
    day_status_file = os.path.join(day_dir, f"day_status_{day}.yaml")
    if os.path.exists(day_status_file):
        try:
            with open(day_status_file, 'r') as f:
                status_data = yaml.safe_load(f)
                
            # Check if all images are annotated
            if status_data and 'completion_percentage' in status_data:
                # If 100% complete, mark as completed
                if status_data['completion_percentage'] == 100:
                    return 'completed'
                # If some images are annotated but not all, mark as in progress
                elif status_data['completion_percentage'] > 0:
                    return 'in_progress'
            
            # Check individual file status
            if status_data and 'file_status' in status_data:
                file_statuses = status_data['file_status']
                if file_statuses:
                    # If any file is completed, it's at least in progress
                    if any(status == 'completed' for status in file_statuses.values()):
                        # If all files are completed, it's completed
                        if all(status == 'completed' for status in file_statuses.values()):
                            return 'completed'
                        else:
                            return 'in_progress'
                    # If any file is in progress, it's in progress
                    elif any(status == 'in_progress' for status in file_statuses.values()):
                        return 'in_progress'
        except Exception as e:
            print(f"Error reading day status file: {e}")
    
    # Check for per-image annotation files
    per_image_files = [f for f in os.listdir(day_dir) 
                      if f.endswith('_annotations.yaml') and not f.startswith('day_status_')]
    
    if per_image_files:
        # At least one per-image file exists, so it's at least in progress
        return 'in_progress'
    
    # Check legacy day-level annotation file as last resort
    legacy_annotations_file = os.path.join(day_dir, f"annotations_{day}.yaml")
    if os.path.exists(legacy_annotations_file):
        try:
            # Verify contents to make sure it's complete
            with open(legacy_annotations_file, 'r') as f:
                data = yaml.safe_load(f)
                # Check if it has annotations
                if data and 'annotations' in data and data['annotations']:
                    return 'completed'
        except Exception as e:
            print(f"Error reading legacy annotation file: {e}")
            return 'not_annotated'
    
    # No annotation files found
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