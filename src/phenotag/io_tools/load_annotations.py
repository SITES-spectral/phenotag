"""
Functions for loading annotations
"""

from pathlib import Path
from typing import Union, Dict, Any
import yaml


def load_yaml(filepath: Union[str, Path]) -> dict:
    """
    Loads a YAML file.
    
    Parameters:
        filepath (str or Path): The absolute path to the YAML file
        
    Returns:
        dict: The contents of the YAML file as a dictionary
        
    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If there is an error while loading the YAML file
    """
    path = Path(filepath) if isinstance(filepath, str) else filepath
    if not path.exists():
        raise FileNotFoundError(f"The file {filepath} does not exist.")
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing the YAML file from {filepath}: {e}")


def load_annotations(base_dir: str, station_name: str, 
                    instrument_id: str, year: str, day: str) -> Dict[str, Any]:
    """
    Load annotations from a YAML file in the specified directory.
    
    Parameters:
        base_dir (str): Base directory where data is stored
        station_name (str): Name of the station
        instrument_id (str): ID of the instrument
        year (str): Year the images were taken
        day (str): Day of year the images were taken
        
    Returns:
        dict: Annotation data if file exists, empty dict otherwise
    """
    try:
        # Get the normalized station name for consistent directory paths
        from phenotag.ui.components.annotation_status_manager import get_normalized_station_name
        normalized_name = get_normalized_station_name(station_name)
        
        # Construct the path to the annotations file
        annotations_dir = Path(base_dir) / normalized_name / 'phenocams' / 'products' / instrument_id / 'L1' / str(year) / str(day)
        annotations_file = annotations_dir / 'annotations.yaml'
        
        # Check if file exists
        if annotations_file.exists():
            return load_yaml(annotations_file)
        else:
            return {}
    except Exception as e:
        print(f"Error loading annotations: {e}")
        return {}