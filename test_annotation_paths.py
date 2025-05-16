#!/usr/bin/env python3
"""
Test script to verify that annotation paths correctly use normalized station names.
This test validates the fix for the issue where annotation files were using 
the station name instead of the normalized station name.
"""

import os
from pathlib import Path
import yaml
from phenotag.config import load_config_files
from phenotag.ui.components.annotation_status_manager import (
    get_normalized_station_name, 
    get_l1_parent_path,
    get_status_filename
)
from phenotag.io_tools.load_annotations import load_annotations
from phenotag.io_tools.directory_scanner import get_available_years
from phenotag.io_tools.lazy_scanner import scan_selected_days

def test_station_name_normalization():
    """Test station name normalization function."""
    config = load_config_files()
    stations_data = config.get('stations', {}).get('stations', {})
    
    print("Testing station name normalization...")
    print("-" * 80)
    
    for normalized_name, station_info in stations_data.items():
        station_name = station_info.get('name')
        
        # Test normalized_name -> normalized_name (identity)
        result1 = get_normalized_station_name(normalized_name)
        
        # Test station_name -> normalized_name (conversion)
        result2 = get_normalized_station_name(station_name)
        
        print(f"Station: {station_name} (normalized: {normalized_name})")
        print(f"  Testing normalization of normalized name: {result1 == normalized_name}")
        print(f"  Testing normalization of display name: {result2 == normalized_name}")
        
        if result2 != normalized_name:
            print(f"  ERROR: Expected {normalized_name}, got {result2}")
        
        print("-" * 80)

def test_directory_paths():
    """Test directory path generation with normalized station names."""
    config = load_config_files()
    stations_data = config.get('stations', {}).get('stations', {})
    
    # Test base directory (doesn't need to exist for this test)
    base_dir = "/home/jobelund/lu2024-12-46/SITES/Spectral/data"
    
    print("Testing directory path generation...")
    print("-" * 80)
    
    for normalized_name, station_info in stations_data.items():
        station_name = station_info.get('name')
        print(f"Station: {station_name} (normalized: {normalized_name})")
        
        # Find an instrument for this station
        instruments = []
        if 'phenocams' in station_info and 'platforms' in station_info['phenocams']:
            for platform_type, platform_data in station_info['phenocams']['platforms'].items():
                if 'instruments' in platform_data:
                    for instr_id in platform_data['instruments'].keys():
                        instruments.append(instr_id)
                        break  # Just need one for testing
                    if instruments:
                        break
        
        if not instruments:
            print(f"  No instruments found for {station_name}")
            continue
            
        # Test with the first instrument
        instr_id = instruments[0]
        print(f"  Testing with instrument: {instr_id}")
        
        # Test path generation with both station name formats
        l1_path1 = get_l1_parent_path(base_dir, normalized_name, instr_id)
        l1_path2 = get_l1_parent_path(base_dir, station_name, instr_id)
        
        # Verify both paths are the same and use the normalized name
        expected_path = Path(base_dir) / normalized_name / "phenocams" / "products" / instr_id / "L1"
        
        print(f"  Path test 1 (normalized name): {'✅ PASS' if l1_path1 == expected_path else '❌ FAIL'}")
        print(f"    {l1_path1}")
        
        print(f"  Path test 2 (display name): {'✅ PASS' if l1_path2 == expected_path else '❌ FAIL'}")
        print(f"    {l1_path2}")
        
        # Test filename generation with both station name formats
        filename1 = get_status_filename(normalized_name, instr_id)
        filename2 = get_status_filename(station_name, instr_id)
        
        # Expected filename uses normalized name
        expected_filename = f"L1_annotation_status_{normalized_name}_{instr_id}.yaml"
        
        print(f"  Filename test 1 (normalized name): {'✅ PASS' if filename1 == expected_filename else '❌ FAIL'}")
        print(f"    {filename1}")
        
        print(f"  Filename test 2 (display name): {'✅ PASS' if filename2 == expected_filename else '❌ FAIL'}")
        print(f"    {filename2}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_station_name_normalization()
    print("\n")
    test_directory_paths()