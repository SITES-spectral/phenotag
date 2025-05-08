# -*- coding: utf-8 -*-

"""
PhenoTag Config module
"""

from pathlib import Path
from typing import Dict, Optional
from phenotag.io_tools import load_yaml


def load_config_files(stations_path: Optional[str] = None, flags_path: Optional[str] = None) -> Dict:
    """
    Load configuration files for stations and phenocams.
    
    Args:
        stations_path: Optional path to stations.yaml. If not provided, will look in default locations.
        flags_path: Optional path to flags.yaml for phenocams. If not provided, will look in default locations.
        
    Returns:
        Dict containing the loaded configuration data with keys 'stations' and 'flags'
        
    Raises:
        FileNotFoundError: If the configuration files cannot be found
        yaml.YAMLError: If there is an error parsing the YAML files
    """
    
    if Path(__file__).exists():
        stations_path = Path(__file__).parent / "stations.yaml"
        flags_path = Path(__file__).parent / "flags.yaml"
    
    assert Path(stations_path).exists(), f"Stations file not found at {stations_path}"    
    assert Path(flags_path).exists(), f"Flags file not found at {flags_path}"
    
    # Load configurations
    config = {
        'stations': load_yaml(stations_path),
        'flags': load_yaml(flags_path)
    }
    
    return config

