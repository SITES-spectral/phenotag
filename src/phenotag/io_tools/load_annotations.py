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
    Supports both per-image annotation files and legacy day-level annotation files.
    
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
        
        # Construct the path to the directory
        annotations_dir = Path(base_dir) / normalized_name / 'phenocams' / 'products' / instrument_id / 'L1' / str(year) / str(day)
        
        # First check for day status file (most recent format)
        day_status_file = annotations_dir / f'day_status_{day}.yaml'
        if day_status_file.exists():
            print(f"Found day status file: {day_status_file}")
            day_status = load_yaml(day_status_file)
            
            # If day status exists, look for individual image annotation files
            per_image_annotations = {}
            for image_filename in day_status.get('image_annotations', []):
                # Get base name without extension
                base_name = image_filename.rsplit('.', 1)[0]
                img_annotation_file = annotations_dir / f"{base_name}_annotations.yaml"
                
                if img_annotation_file.exists():
                    try:
                        img_data = load_yaml(img_annotation_file)
                        if 'annotations' in img_data:
                            per_image_annotations[image_filename] = img_data['annotations']
                    except Exception as img_err:
                        print(f"Error loading per-image annotation file {img_annotation_file}: {img_err}")
            
            # Return per-image annotations if found
            if per_image_annotations:
                return {'annotations': per_image_annotations}
        
        # Then check for individual image annotation files even without day status
        # This scans all image annotation files in the directory
        per_image_annotations = {}
        for img_annotation_file in annotations_dir.glob("*_annotations.yaml"):
            try:
                # Skip day status files
                if img_annotation_file.name.startswith('day_status_'):
                    continue
                    
                img_data = load_yaml(img_annotation_file)
                if 'annotations' in img_data and 'filename' in img_data:
                    per_image_annotations[img_data['filename']] = img_data['annotations']
            except Exception as img_err:
                print(f"Error loading per-image annotation file {img_annotation_file}: {img_err}")
        
        # Return per-image annotations if found
        if per_image_annotations:
            print(f"Loaded {len(per_image_annotations)} per-image annotation files from {annotations_dir}")
            return {'annotations': per_image_annotations}
            
        # Finally fallback to the old day-level annotation file
        old_annotation_file = annotations_dir / f'annotations_{day}.yaml'
        if old_annotation_file.exists():
            print(f"Using legacy day-level annotation file: {old_annotation_file}")
            return load_yaml(old_annotation_file)
            
        # No annotation files found
        print(f"No annotation files found in {annotations_dir}")
        return {}
    except Exception as e:
        print(f"Error loading annotations: {e}")
        return {}