"""
Annotation Status Manager Module

This module provides functionality for managing annotation status files at the L1 parent level.
"""

import os
from pathlib import Path
import yaml
from datetime import datetime

def get_l1_parent_path(base_dir, station_name, instrument_id):
    """Generate the path to the L1 parent directory."""
    return Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1"

def get_status_filename(station_name, instrument_id):
    """Generate the filename for the annotation status file."""
    return f"L1_annotation_status_{station_name}_{instrument_id}.yaml"

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
        
        # Generate the status filename
        status_filename = f"L1_annotation_status_{station_name}_{instrument_id}.yaml"
        status_file_path = l1_parent_path / status_filename
        
        # Create or load existing status data
        if os.path.exists(status_file_path):
            with open(status_file_path, "r") as f:
                status_data = yaml.safe_load(f) or {}
        else:
            status_data = {
                "metadata": {
                    "station": station_name,
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
        
        if day not in status_data["annotations"][str(year)]:
            status_data["annotations"][str(year)][day] = {}
            
        status_data["annotations"][str(year)][day] = {
            "status": status,
            "last_updated": datetime.now().isoformat()
        }
        
        # Update last modified timestamp
        status_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Create the directory if it doesn't exist
        os.makedirs(l1_parent_path, exist_ok=True)
        
        # Save the status file
        with open(status_file_path, "w") as f:
            yaml.dump(status_data, f, default_flow_style=False)
        
        return True
    
    except Exception as e:
        print(f"Error saving annotation status: {e}")
        return False