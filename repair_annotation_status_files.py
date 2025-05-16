#!/usr/bin/env python3
"""
Repair Script for Annotation Status Files

This script finds and repairs annotation status files that were incorrectly named or placed
using the non-normalized station name. It identifies misnamed files and moves them to the
correct location with the correct filename using the normalized station name.

Usage:
    python repair_annotation_status_files.py [--dry-run] [--base-dir PATH]

Options:
    --dry-run   Print what would be done without actually moving files
    --base-dir  Base directory for data (default: /home/jobelund/lu2024-12-46/SITES/Spectral/data)
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import yaml

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phenotag.config import load_config_files
from phenotag.ui.components.annotation_status_manager import (
    get_normalized_station_name,
    get_l1_parent_path,
    get_status_filename
)

def find_and_repair_annotation_files(base_dir, dry_run=False):
    """
    Find and repair annotation status files with incorrect names or locations.
    
    Args:
        base_dir (str): Base directory for data
        dry_run (bool): If True, only print what would be done without moving files
    """
    print(f"Scanning for annotation status files in {base_dir}...")
    base_dir = Path(base_dir)
    
    # Load station configuration to get normalized names
    config = load_config_files()
    stations_data = config.get('stations', {}).get('stations', {})
    
    # Track counts for reporting
    found_files = 0
    need_repair = 0
    repaired = 0
    errors = 0
    
    # Process each station
    for normalized_name, station_info in stations_data.items():
        station_name = station_info.get('name')
        print(f"\nChecking station: {station_name} (normalized: {normalized_name})")
        
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
        
        # Check each instrument
        for instrument_id in instruments:
            print(f"  Checking instrument: {instrument_id}")
            
            # Correct path and filename
            correct_path = get_l1_parent_path(base_dir, normalized_name, instrument_id)
            correct_filename = get_status_filename(normalized_name, instrument_id)
            correct_file_path = correct_path / correct_filename
            
            # Incorrect path with non-normalized name
            incorrect_path = base_dir / station_name / "phenocams" / "products" / instrument_id / "L1"
            incorrect_filename = f"L1_annotation_status_{station_name}_{instrument_id}.yaml"
            incorrect_file_path = incorrect_path / incorrect_filename
            
            if incorrect_path.exists():
                # Check if incorrect filename exists
                if incorrect_file_path.exists() and incorrect_file_path != correct_file_path:
                    found_files += 1
                    need_repair += 1
                    print(f"    Found incorrect file: {incorrect_file_path}")
                    print(f"    Should be: {correct_file_path}")
                    
                    if not dry_run:
                        try:
                            # Create destination directory if it doesn't exist
                            os.makedirs(correct_path, exist_ok=True)
                            
                            # Move file to correct location
                            shutil.move(str(incorrect_file_path), str(correct_file_path))
                            print(f"    ✅ Moved file to correct location")
                            repaired += 1
                        except Exception as e:
                            print(f"    ❌ Error moving file: {e}")
                            errors += 1
                    else:
                        print(f"    [DRY RUN] Would move file to correct location")
            
            # Check if correct file exists
            if correct_file_path.exists():
                found_files += 1
                print(f"    Found correct file: {correct_file_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"  Total annotation status files found: {found_files}")
    print(f"  Files needing repair: {need_repair}")
    if not dry_run:
        print(f"  Files successfully repaired: {repaired}")
        print(f"  Errors encountered: {errors}")
    else:
        print(f"  [DRY RUN] No files were actually modified")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Repair annotation status files with incorrect names or locations")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without actually moving files")
    parser.add_argument("--base-dir", default="/home/jobelund/lu2024-12-46/SITES/Spectral/data", 
                        help="Base directory for data")
    
    args = parser.parse_args()
    
    print("PhenoTag Annotation Status File Repair Tool")
    print("=" * 80)
    if args.dry_run:
        print("DRY RUN MODE: No files will be modified")
    
    find_and_repair_annotation_files(args.base_dir, args.dry_run)

if __name__ == "__main__":
    main()