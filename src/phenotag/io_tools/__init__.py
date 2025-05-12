# -*- coding: utf-8 -*-

"""
PhenoTag IO Tools module
"""

from pathlib import Path
from typing import Union, Dict, List, Optional, Tuple, Any
import requests
import yaml
import os
import cv2
import numpy as np
from collections import defaultdict


def load_yaml(filepath: Union[str, Path]) -> dict:
    """
    Loads a YAML file.

    Can be used as stand-alone script by providing a command-line argument:
        python load_yaml.py --filepath /file/path/to/filename.yaml
        python load_yaml.py --filepath http://example.com/path/to/filename.yaml

    Parameters:
        filepath (str): The absolute path to the YAML file or a URL to the YAML file.

    Returns:
        dict: The contents of the YAML file as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If there is an error while loading the YAML file.
        requests.RequestException: If there is an error while making the HTTP request.
        yaml.YAMLError: If there is an error while loading the YAML file.
    """
    
    # Check if the filepath is an instance of Path and convert to string if necessary
    if isinstance(filepath, Path):
        filepath = str(filepath)    
    
    if filepath.startswith('http://') or filepath.startswith('https://'):
        try:
            response = requests.get(filepath)
            response.raise_for_status()  # Raises a HTTPError if the response status is 4xx, 5xx
            yaml_data = yaml.safe_load(response.text)
            return yaml_data
        except requests.RequestException as e:
            raise requests.RequestException(f"Error fetching the YAML file from {filepath}: {e}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing the YAML file from {filepath}: {e}")
    else:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"The file {filepath} does not exist.")
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"The file {filepath} was not found: {e}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing the YAML file from {filepath}: {e}")


def save_yaml(data: Dict[str, Any], filepath: Union[str, Path]) -> bool:
    """
    Saves data to a YAML file.
    
    Parameters:
        data (dict): The data to save.
        filepath (str or Path): The path to save the YAML file to.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Convert to Path if it's a string
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write YAML file
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)
        
        return True
    except Exception as e:
        print(f"Error saving YAML file to {filepath}: {e}")
        return False


def save_annotations(image_data: Dict[str, Any], base_dir: str, 
                  station_name: str, instrument_id: str, 
                  year: str, day: str) -> Tuple[bool, str]:
    """
    Save annotations to a YAML file in the specified directory.
    
    Parameters:
        image_data (dict): Dictionary containing annotation data for images
        base_dir (str): Base directory where data is stored
        station_name (str): Name of the station
        instrument_id (str): ID of the instrument
        year (str): Year the images were taken
        day (str): Day of year the images were taken
        
    Returns:
        Tuple[bool, str]: (Success status, Path to saved file or error message)
    """
    try:
        # Construct the path to the annotations file
        annotations_dir = Path(base_dir) / station_name / 'phenocams' / 'products' / instrument_id / 'L1' / str(year) / str(day)
        annotations_file = annotations_dir / 'annotations.yaml'
        
        # Extract just the annotations for this day
        if str(year) in image_data and str(day) in image_data[str(year)]:
            day_data = image_data[str(year)][str(day)]
            
            # Save to disk
            if save_yaml(day_data, annotations_file):
                return True, str(annotations_file)
            else:
                return False, f"Failed to save annotations to {annotations_file}"
        else:
            return False, f"No data found for year {year}, day {day}"
            
    except Exception as e:
        return False, f"Error saving annotations: {e}"


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
        # Construct the path to the annotations file
        annotations_dir = Path(base_dir) / station_name / 'phenocams' / 'products' / instrument_id / 'L1' / str(year) / str(day)
        annotations_file = annotations_dir / 'annotations.yaml'
        
        # Check if file exists
        if annotations_file.exists():
            return load_yaml(annotations_file)
        else:
            print(f"No annotations file found at {annotations_file}")
            return {}
    except Exception as e:
        print(f"Error loading annotations: {e}")
        return {}


def load_session_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load session configuration from a YAML file.
    
    Parameters:
        config_path (str or Path): Path to the configuration file
        
    Returns:
        dict: Session configuration or empty dict if file doesn't exist
    """
    try:
        return load_yaml(config_path)
    except FileNotFoundError:
        # Return empty configuration if file doesn't exist
        return {}
    except Exception as e:
        print(f"Error loading session configuration: {e}")
        return {}


from pydantic import BaseModel, DirectoryPath, field_validator
from typing import Optional

class PhenocamDataPath(BaseModel):
    """
    Model for validating and representing a phenocam data directory path.
    
    The expected directory structure is:
    {base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}
    
    Where:
    - station_name: Normalized station name
    - instrument_id: Instrument ID 
    - year: Year as a 4-digit string
    - day_of_year: Day of year as a 3-digit string padded with zeros
    """
    base_dir: DirectoryPath
    station_name: str
    instrument_id: str
    
    @field_validator('station_name')
    def station_name_must_be_valid(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Station name must be a non-empty string')
        return v
    
    @field_validator('instrument_id')
    def instrument_id_must_be_valid(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Instrument ID must be a non-empty string')
        return v
    
    def get_instrument_path(self) -> Path:
        """Get the path to the L1 directory for the instrument."""
        return self.base_dir / self.station_name / "phenocams" / "products" / self.instrument_id / "L1"
    
    def exists(self) -> bool:
        """Check if the instrument path exists."""
        return self.get_instrument_path().exists()


def find_phenocam_image_paths(
    base_dir: Union[str, Path], 
    station_name: str,
    instrument_id: str
) -> Dict[str, Dict[str, List[str]]]:
    """
    Find paths to phenocam image files organized in subdirectories by year and day of year.
    This is a memory-efficient version that only returns file paths, not their contents.
    
    The expected directory structure is:
    {base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/*.jpg
    
    Parameters:
        base_dir (str or Path): The base directory to search in (PHENOCAMS_DATA_DIR)
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID to find images for
    
    Returns:
        Dict: A nested dictionary of file paths:
        {
            'year1': {
                'doy1': [file_path1, file_path2, ...],
                'doy2': [file_path1, file_path2, ...],
                ...
            },
            'year2': {...},
            ...
        }
    """
    # Convert to Path if it's a string
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Check if base directory exists
    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Base directory {base_dir} does not exist")
        return {}
    
    try:
        # Validate the path using Pydantic
        data_path = PhenocamDataPath(
            base_dir=base_dir,
            station_name=station_name,
            instrument_id=instrument_id
        )
        
        # Get the instrument L1 directory
        instrument_dir = data_path.get_instrument_path()
        
        # Check if the directory exists
        if not data_path.exists():
            return {}
        
    except Exception as e:
        print(f"Error validating data path: {e}")
        return {}
    
    # Initialize the result dictionary
    result = defaultdict(lambda: defaultdict(list))
    
    # Walk through the directory structure
    for year_dir in instrument_dir.iterdir():
        if year_dir.is_dir() and year_dir.name.isdigit():
            year = year_dir.name
            
            for doy_dir in year_dir.iterdir():
                if doy_dir.is_dir() and doy_dir.name.isdigit():
                    # Format the day of year as a 3-digit string with leading zeros
                    doy = doy_dir.name.zfill(3)
                    
                    # Find all JPEG files in this directory
                    for file_path in doy_dir.glob("*.jp*g"):
                        if file_path.is_file():
                            result[year][doy].append(str(file_path))
    
    # Convert defaultdict to regular dict for better serialization
    return {year: dict(doys) for year, doys in result.items()}


def get_default_quality_data():
    """Return default quality data for an image."""
    return {'discard_file': False, 'snow_presence': False}


def get_default_roi_data():
    """Return default ROI data structure."""
    return {
        'ROI_01': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
        'ROI_02': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
        'ROI_03': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []}
    }


def load_image(image_path: Union[str, Path], resize: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """
    Lazily load an image from disk using OpenCV.
    
    Parameters:
        image_path (str or Path): Path to the image file
        resize (tuple, optional): Tuple of (width, height) to resize the image to
    
    Returns:
        numpy.ndarray: Image data as a NumPy array, or empty array if loading fails
    """
    try:
        # Load the image using OpenCV (with proper color conversion)
        img = cv2.imread(str(image_path))
        
        if img is None:
            print(f"Failed to load image: {image_path}")
            return np.array([])
        
        # Convert BGR to RGB (OpenCV loads as BGR, but we want RGB for display)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Resize if requested
        if resize is not None and isinstance(resize, tuple) and len(resize) == 2:
            img = cv2.resize(img, resize)
        
        return img
    
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return np.array([])


def find_phenocam_images(
    base_dir: Union[str, Path], 
    station_name: Optional[str] = None,
    instrument_id: Optional[str] = None
) -> Dict[str, Union[Dict, List]]:
    """
    Find phenocam image files organized in subdirectories by year and day of year.
    
    The expected directory structure is:
    {base_dir}/{station_name}/phenocams/products/{instrument_id}/L1/{year}/{day_of_year}/*.jpg
    
    If station_name and instrument_id are not provided, it will auto-discover all available stations 
    and instruments in the base directory.
    
    Parameters:
        base_dir (str or Path): The base directory to search in (PHENOCAMS_DATA_DIR)
        station_name (str, optional): The normalized station name
        instrument_id (str, optional): The instrument ID to find images for
    
    Returns:
        Dict: A nested dictionary with structure based on the parameters provided:
        
        If both station_name and instrument_id are provided:
        {
            'year1': {
                'doy1': {
                    'file_path1': {
                        'quality': {'discard_file': False, 'snow_presence': False},
                        'rois': {
                            'ROI_01': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
                            ...
                        }
                    },
                    'file_path2': {...},
                    ...
                },
                'doy2': {...},
                ...
            },
            'year2': {...},
            ...
        }
        
        If only station_name is provided:
        {
            'instrument_id1': {...},
            'instrument_id2': {...},
            ...
        }
        
        If neither station_name nor instrument_id are provided:
        {
            'station_name1': {
                'instrument_id1': {...},
                'instrument_id2': {...},
                ...
            },
            'station_name2': {...},
            ...
        }
    """
    # Convert to Path if it's a string
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Check if base directory exists
    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Base directory {base_dir} does not exist")
        return {}
    
    # If both station and instrument are provided, get images for that specific combination
    if station_name and instrument_id:
        # Get the file paths first (efficient)
        image_paths = find_phenocam_image_paths(base_dir, station_name, instrument_id)
        
        # Convert to the full structure with quality and ROI data
        result = defaultdict(lambda: defaultdict(dict))
        
        for year, doys in image_paths.items():
            for doy, file_paths in doys.items():
                # Try to load existing annotations for this day
                existing_annotations = load_annotations(
                    base_dir, station_name, instrument_id, year, doy
                )
                
                for file_path in file_paths:
                    # If annotations exist for this file, use them
                    if existing_annotations and file_path in existing_annotations:
                        result[year][doy][file_path] = existing_annotations[file_path]
                    else:
                        # Otherwise use default values
                        result[year][doy][file_path] = {
                            'quality': get_default_quality_data(),
                            'rois': get_default_roi_data()
                        }
        
        # Convert defaultdict to regular dict for better serialization
        return {year: dict(doys) for year, doys in result.items()}
    
    # If only station is provided, discover all instruments for that station
    elif station_name:
        station_dir = base_dir / station_name / "phenocams" / "products"
        
        if not station_dir.exists() or not station_dir.is_dir():
            return {}
        
        result = {}
        for instr_dir in station_dir.iterdir():
            if instr_dir.is_dir():
                instr_id = instr_dir.name
                # Get image paths only (don't load full data structure)
                instr_paths = find_phenocam_image_paths(base_dir, station_name, instr_id)
                if instr_paths:  # Only include instruments with data
                    result[instr_id] = instr_paths
        
        return result
    
    # If neither station nor instrument are provided, discover all stations
    else:
        result = {}
        for station_dir in base_dir.iterdir():
            if station_dir.is_dir():
                # Check if this looks like a station directory with phenocams
                phenocam_dir = station_dir / "phenocams" / "products"
                if phenocam_dir.exists() and phenocam_dir.is_dir():
                    station_name = station_dir.name
                    # Only get directory structure for discovery
                    station_data = {}
                    for instr_dir in phenocam_dir.iterdir():
                        if instr_dir.is_dir():
                            instr_id = instr_dir.name
                            l1_dir = instr_dir / "L1"
                            if l1_dir.exists() and l1_dir.is_dir():
                                has_data = False
                                for year_dir in l1_dir.iterdir():
                                    if year_dir.is_dir() and year_dir.name.isdigit():
                                        has_data = True
                                        break
                                if has_data:
                                    station_data[instr_id] = {}
                    
                    if station_data:  # Only include stations with data
                        result[station_name] = station_data
        
        return result
