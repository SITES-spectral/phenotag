"""
Lazy, memory-efficient scanner for phenocam images

This module provides functions for efficient, targeted scanning of phenocam images 
by year, month, or day without loading all images into memory at once.
"""

from pathlib import Path
from typing import Union, Dict, List, Any, Optional, Tuple, Set
import os
import calendar
import datetime
from collections import defaultdict
import logging

from .load_annotations import load_annotations
from .defaults import get_default_quality_data, get_default_roi_data


def get_available_years(base_dir: Union[str, Path], station_name: str, instrument_id: str) -> List[str]:
    """
    Get a list of available years for a given station and instrument.
    This is very fast as it only lists directories without scanning image files.
    
    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        
    Returns:
        List[str]: A list of available years as strings
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Construct the path to the L1 directory
    l1_dir = base_dir / station_name / "phenocams" / "products" / instrument_id / "L1"
    
    if not l1_dir.exists() or not l1_dir.is_dir():
        return []
    
    # Get all year directories
    years = []
    for year_dir in l1_dir.iterdir():
        if year_dir.is_dir() and year_dir.name.isdigit():
            years.append(year_dir.name)
    
    # Sort years in descending order (newest first)
    years.sort(reverse=True)
    return years


def get_available_days_in_year(base_dir: Union[str, Path], station_name: str,
                             instrument_id: str, year: str, force_refresh: bool = False,
                             month: Optional[int] = None) -> List[str]:
    """
    Get a list of available days for a given year, station and instrument.
    This is fast as it only lists directories without scanning image files.

    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str): The year to search in
        force_refresh (bool): Whether to force a refresh instead of using cache
        month (int, optional): Specific month to filter days (1-12)

    Returns:
        List[str]: A list of available days (DOY) as strings
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Construct the path to the year directory
    year_dir = base_dir / station_name / "phenocams" / "products" / instrument_id / "L1" / year
    
    if not year_dir.exists() or not year_dir.is_dir():
        return []
    
    # Get all day directories
    days = []
    for day_dir in year_dir.iterdir():
        if day_dir.is_dir() and day_dir.name.isdigit():
            days.append(day_dir.name.zfill(3))  # Ensure 3-digit format
    
    # Sort days
    days.sort()

    # Filter by month if specified
    if month is not None:
        # Convert month to set of days of year
        year_int = int(year)
        month_days = get_days_in_month(year_int, month)

        # Filter days to only include those in the specified month
        days = [day for day in days if int(day) in month_days]

    return days


def get_days_in_month(year: Union[str, int], month: Union[str, int]) -> Set[int]:
    """
    Get a set of days of year (DOY) that correspond to a given month.
    
    Parameters:
        year (str or int): The year
        month (str or int): The month (1-12)
        
    Returns:
        Set[int]: A set of DOY values for the month
    """
    year = int(year)
    month = int(month)
    
    # Get the number of days in the month
    days_in_month = calendar.monthrange(year, month)[1]
    
    # Calculate DOY for each day in the month
    doys = set()
    for day in range(1, days_in_month + 1):
        date = datetime.date(year, month, day)
        doy = date.timetuple().tm_yday
        doys.add(doy)
    
    return doys


def scan_month_data(base_dir: Union[str, Path], station_name: str, 
                   instrument_id: str, year: str, month: int) -> Dict[str, Dict[str, Dict]]:
    """
    Efficiently scan image data for a specific month without loading all years/days.
    
    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str): The year to scan
        month (int): The month to scan (1-12)
        
    Returns:
        Dict: A nested dictionary with image data for the specified month only
    """
    # Get the DOYs that correspond to the requested month
    target_doys = get_days_in_month(year, month)
    
    # Get the available days for this year
    available_days = get_available_days_in_year(base_dir, station_name, instrument_id, year)
    
    # Filter to only include days in the target month
    days_to_scan = [day for day in available_days if int(day) in target_doys]
    
    # Initialize result structure
    result = defaultdict(dict)
    
    # Scan only the filtered days
    for day in days_to_scan:
        # Try both with and without leading zeros to handle filesystem differences
        day_with_zeros = day
        day_without_zeros = day.lstrip('0') if day else '0'

        # First try with the original format
        day_dir = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / year / day_with_zeros

        # If that doesn't exist, try without leading zeros
        if not day_dir.exists() or not day_dir.is_dir():
            day_dir = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / year / day_without_zeros

            # If that still doesn't exist, skip this day
            if not day_dir.exists() or not day_dir.is_dir():
                continue
        
        # Load existing annotations if available
        existing_annotations = load_annotations(base_dir, station_name, instrument_id, year, day)
        
        # Find all JPEG files in this directory
        file_paths = list(day_dir.glob("*.jp*g"))
        
        if not file_paths:
            continue
        
        # Create day entry
        day_data = {}
        
        # Add file entries
        for file_path in file_paths:
            str_path = str(file_path)
            
            # If annotations exist for this file, use them
            if existing_annotations and str_path in existing_annotations:
                day_data[str_path] = existing_annotations[str_path]
            else:
                # Otherwise use default values
                day_data[str_path] = {
                    'quality': get_default_quality_data(),
                    'rois': get_default_roi_data()
                }
        
        # Add day to result if it has files
        if day_data:
            result[day] = day_data
    
    return {year: dict(result)} if result else {}


def scan_selected_days(base_dir: Union[str, Path], station_name: str, 
                      instrument_id: str, year: str, days: List[str]) -> Dict[str, Dict[str, Dict]]:
    """
    Efficiently scan image data for specific days without loading all data.
    
    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str): The year to scan
        days (List[str]): List of days (DOY) to scan
        
    Returns:
        Dict: A nested dictionary with image data for the specified days only
    """
    # Initialize result structure
    result = defaultdict(dict)
    
    # Scan only the specified days
    for day in days:
        # Ensure day is properly formatted (3 digits with leading zeros)
        day = day.zfill(3) if isinstance(day, str) else str(day).zfill(3)
        
        # Try both with and without leading zeros to handle filesystem differences
        day_with_zeros = day
        day_without_zeros = day.lstrip('0') if day else '0'

        # First try with the original format
        day_dir = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / year / day_with_zeros

        # If that doesn't exist, try without leading zeros
        if not day_dir.exists() or not day_dir.is_dir():
            day_dir = Path(base_dir) / station_name / "phenocams" / "products" / instrument_id / "L1" / year / day_without_zeros

            # If that still doesn't exist, skip this day
            if not day_dir.exists() or not day_dir.is_dir():
                continue
        
        # Load existing annotations if available
        existing_annotations = load_annotations(base_dir, station_name, instrument_id, year, day)
        
        # Find all JPEG files in this directory
        file_paths = list(day_dir.glob("*.jp*g"))
        
        if not file_paths:
            continue
        
        # Create day entry
        day_data = {}
        
        # Add file entries
        for file_path in file_paths:
            str_path = str(file_path)
            
            # If annotations exist for this file, use them
            if existing_annotations and str_path in existing_annotations:
                day_data[str_path] = existing_annotations[str_path]
            else:
                # Otherwise use default values
                day_data[str_path] = {
                    'quality': get_default_quality_data(),
                    'rois': get_default_roi_data()
                }
        
        # Add day to result if it has files
        if day_data:
            result[day] = day_data
    
    return {year: dict(result)} if result else {}


def lazy_find_phenocam_images(
    base_dir: Union[str, Path], 
    station_name: str,
    instrument_id: str,
    year: Optional[str] = None,
    month: Optional[int] = None,
    days: Optional[List[str]] = None
) -> Dict[str, Dict]:
    """
    Lazily find phenocam images without loading all data at once.
    
    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str, optional): Specific year to scan
        month (int, optional): Specific month to scan (1-12)
        days (List[str], optional): Specific days to scan
        
    Returns:
        Dict: A nested dictionary with image data for the specified parameters
    """
    # Convert to Path if it's a string
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Check if base directory exists
    if not base_dir.exists() or not base_dir.is_dir():
        return {}
    
    # Case 1: Get only available years (very fast, no image scanning)
    if not year:
        years = get_available_years(base_dir, station_name, instrument_id)
        return {y: {} for y in years}  # Return empty placeholders for each year
    
    # Case 2: Scan a specific month
    if year and month and not days:
        return scan_month_data(base_dir, station_name, instrument_id, year, month)
    
    # Case 3: Scan specific days
    if year and days:
        return scan_selected_days(base_dir, station_name, instrument_id, year, days)
    
    # Case 4: Scan all days in a year (still more efficient than loading everything)
    if year and not month and not days:
        available_days = get_available_days_in_year(base_dir, station_name, instrument_id, year)
        return scan_selected_days(base_dir, station_name, instrument_id, year, available_days)
    
    # Fallback: empty result
    return {}