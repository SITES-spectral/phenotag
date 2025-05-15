"""
Annotation Status Manager Module

This module provides functionality for managing annotation status files at the L1 parent level.
"""

import os
from pathlib import Path
import yaml
from datetime import datetime

def get_normalized_station_name(station_name):
    """
    Get the normalized version of a station name by looking it up in the stations.yaml config.
    This handles cases where the station name has Swedish characters that need proper normalization.
    
    Args:
        station_name (str): Station name (either normalized or display name)
        
    Returns:
        str: Normalized station name
    """
    from phenotag.config import load_config_files
    
    # Load config data and get stations
    config = load_config_files()
    stations_data = config.get('stations', {}).get('stations', {})
    
    # Check if it's already a normalized name
    if station_name in stations_data:
        return station_name
    
    # Otherwise, try to find the normalized name for this display name
    for norm_name, station_info in stations_data.items():
        if station_info.get('name') == station_name:
            return norm_name
    
    # If all else fails, just return lowercase (backwards compatibility)
    return station_name.lower()

def get_l1_parent_path(base_dir, station_name, instrument_id):
    """Generate the path to the L1 parent directory."""
    # Get properly normalized station name that handles Swedish characters
    normalized_name = get_normalized_station_name(station_name)
    return Path(base_dir) / normalized_name / "phenocams" / "products" / instrument_id / "L1"

def get_status_filename(station_name, instrument_id):
    """Generate the filename for the annotation status file."""
    # Get properly normalized station name that handles Swedish characters
    normalized_name = get_normalized_station_name(station_name)
    return f"L1_annotation_status_{normalized_name}_{instrument_id}.yaml"

def save_status_to_l1_parent(base_dir, station_name, instrument_id, year, month, day, status):
    """
    Save the annotation status to the L1 parent directory.
    
    Args:
        base_dir (str): Base directory for PHENOCAMS_DATA
        station_name (str): Normalized station name
        instrument_id (str): Instrument ID
        year (int): Year
        month (int): Month
        day (str): Day of year
        status (str): Annotation status ('not_annotated', 'in_progress', or 'completed')
    """
    try:
        # Get the L1 parent path
        l1_parent_path = get_l1_parent_path(base_dir, station_name, instrument_id)
        
        # Generate the status filename using the get_status_filename function for consistency
        status_filename = get_status_filename(station_name, instrument_id)
        status_file_path = l1_parent_path / status_filename
        
        # Create or load existing status data
        if os.path.exists(status_file_path):
            with open(status_file_path, "r") as f:
                status_data = yaml.safe_load(f) or {}
        else:
            # Get the normalized station name for metadata
            normalized_name = get_normalized_station_name(station_name)
            status_data = {
                "metadata": {
                    "station": normalized_name,  # Use properly normalized station name
                    "instrument_id": instrument_id,
                    "created": datetime.now().isoformat()
                },
                "annotations": {}
            }
        
        # Ensure the annotations section exists
        if "annotations" not in status_data:
            status_data["annotations"] = {}
        
        # Update the status for this day
        if str(year) not in status_data["annotations"]:
            status_data["annotations"][str(year)] = {}
        
        # Get existing day data or create new
        if day in status_data["annotations"][str(year)]:
            # Preserve existing data and just update what's needed
            day_data = status_data["annotations"][str(year)][day]
            
            # Only update the status field and last_updated
            day_data["status"] = status
            day_data["last_updated"] = datetime.now().isoformat()
        else:
            # Create new day entry
            status_data["annotations"][str(year)][day] = {
                "status": status,
                "last_updated": datetime.now().isoformat()
            }
        
        # Update last modified timestamp in metadata
        status_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Preserve other metadata fields
        if "metadata" in status_data:
            # Ensure these fields are always set correctly
            normalized_name = get_normalized_station_name(station_name)
            status_data["metadata"]["station"] = normalized_name  # Use properly normalized station name
            status_data["metadata"]["instrument_id"] = instrument_id
            
            # Keep all other metadata fields
        
        # Create the directory if it doesn't exist
        os.makedirs(l1_parent_path, exist_ok=True)
        
        # Save the status file
        with open(status_file_path, "w") as f:
            yaml.dump(status_data, f, default_flow_style=False)
        
        return True
    
    except Exception as e:
        print(f"Error saving annotation status: {e}")
        return False