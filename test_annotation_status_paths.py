#!/usr/bin/env python3
"""
Test script to verify that annotation status file paths and names use normalized station names.
This test validates the fix for the issue where annotation status files were using the station name
instead of the normalized station name.

Usage:
    python test_annotation_status_paths.py
"""

import os
from pathlib import Path
from phenotag.config import load_config_files
from phenotag.ui.components.annotation_status_manager import (
    get_l1_parent_path,
    get_status_filename
)

def test_annotation_status_paths():
    """Test that annotation status paths use normalized station names."""
    # Load station configuration
    config = load_config_files()
    stations_data = config.get('stations', {}).get('stations', {})
    
    # Test base directory (doesn't need to exist for this test)
    base_dir = "/home/jobelund/lu2024-12-46/SITES/Spectral/data"
    
    print(f"Testing annotation status paths for {len(stations_data)} stations...")
    print("-" * 80)
    
    for normalized_name, station_info in stations_data.items():
        station_name = station_info.get('name')
        print(f"Station: {station_name} (normalized: {normalized_name})")
        
        # Find instruments for this station
        instruments = []
        if 'phenocams' in station_info and 'platforms' in station_info['phenocams']:
            for platform_type, platform_data in station_info['phenocams']['platforms'].items():
                if 'instruments' in platform_data:
                    for instr_id in platform_data['instruments'].keys():
                        instruments.append(instr_id)
        
        if not instruments:
            print(f"  No instruments found for {station_name}")
            continue
            
        # Test with the first instrument
        instr_id = instruments[0]
        print(f"  Testing with instrument: {instr_id}")
        
        # Test with the regular name to verify our fix works
        l1_parent_path = get_l1_parent_path(base_dir, station_name, instr_id)
        status_filename = get_status_filename(station_name, instr_id)
        
        # Expected values (should use normalized_name)
        expected_path = Path(base_dir) / normalized_name / "phenocams" / "products" / instr_id / "L1"
        expected_filename = f"L1_annotation_status_{normalized_name}_{instr_id}.yaml"
        
        # Verify paths
        path_correct = l1_parent_path == expected_path
        filename_correct = status_filename == expected_filename
        
        # Display results
        print(f"  Path test: {'✅ PASS' if path_correct else '❌ FAIL'}")
        print(f"    Actual: {l1_parent_path}")
        print(f"    Expected: {expected_path}")
        
        print(f"  Filename test: {'✅ PASS' if filename_correct else '❌ FAIL'}")
        print(f"    Actual: {status_filename}")
        print(f"    Expected: {expected_filename}")
        
        print("-" * 80)
    
    print("Test completed.")

if __name__ == "__main__":
    test_annotation_status_paths()