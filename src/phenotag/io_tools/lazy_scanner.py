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
from .directory_scanner import extract_doy_from_filename
from .image_index_cache import get_day_filepaths, get_available_doys


def get_normalized_station_name(station_name: str) -> str:
    """
    Get the normalized station name for consistent directory paths.
    
    Args:
        station_name: Station name (either normalized or display name)
        
    Returns:
        Normalized station name
    """
    # Import here to avoid circular imports
    from phenotag.ui.components.annotation_status_manager import get_normalized_station_name as get_name
    return get_name(station_name)


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
    
    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)
    
    # Construct the path to the L1 directory
    l1_dir = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1"
    
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
                             month: Optional[int] = None, use_cache: bool = True) -> List[str]:
    """
    Get a list of available days for a given year, station and instrument.

    Supports two directory structures:
    1. Flat structure: /L1/year/*.jpg (DOY extracted from filename)
    2. Nested structure: /L1/year/doy/*.jpg (DOY from directory name)

    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str): The year to search in
        force_refresh (bool): Whether to force a refresh instead of using cache
        month (int, optional): Specific month to filter days (1-12)
        use_cache (bool): If True, use the image index cache for faster lookups

    Returns:
        List[str]: A list of available days (DOY) as strings
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)

    # Use cache if requested (faster for repeated lookups)
    if use_cache:
        days = get_available_doys(base_dir, normalized_name, instrument_id, year, force_refresh)
    else:
        # Fallback: direct directory scan
        year_dir = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year

        if not year_dir.exists() or not year_dir.is_dir():
            return []

        days_set = set()

        # First, check for DOY subdirectories (original nested structure)
        has_doy_dirs = False
        for item in year_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                has_doy_dirs = True
                days_set.add(item.name.zfill(3))

        # If no DOY directories found, scan for flat files and extract DOY from filenames
        if not has_doy_dirs:
            for item in year_dir.iterdir():
                if item.is_file() and item.name.lower().endswith(('.jpg', '.jpeg')):
                    doy = extract_doy_from_filename(item.name)
                    if doy:
                        days_set.add(doy)

        days = sorted(list(days_set))

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

    Supports two directory structures:
    1. Flat structure: /L1/year/*.jpg (DOY extracted from filename)
    2. Nested structure: /L1/year/doy/*.jpg (files in DOY subdirectories)

    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str): The year to scan
        month (int): The month to scan (1-12)

    Returns:
        Dict: A nested dictionary with image data for the specified month only
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)

    # Get the DOYs that correspond to the requested month
    target_doys = get_days_in_month(year, month)

    # Get the available days for this year
    available_days = get_available_days_in_year(base_dir, station_name, instrument_id, year)

    # Filter to only include days in the target month
    days_to_scan = [day for day in available_days if int(day) in target_doys]

    # Initialize result structure
    result = defaultdict(dict)

    # Construct path to year directory
    year_dir = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year

    if not year_dir.exists() or not year_dir.is_dir():
        return {}

    # Determine if we have DOY subdirectories or flat structure
    has_doy_dirs = any(item.is_dir() and item.name.isdigit() for item in year_dir.iterdir())

    if has_doy_dirs:
        # Original nested structure: /L1/year/doy/*.jpg
        for day in days_to_scan:
            day_with_zeros = day.zfill(3)
            day_without_zeros = day.lstrip('0') or '0'

            day_dir = None
            for day_format in [day_with_zeros, day_without_zeros]:
                candidate = year_dir / day_format
                if candidate.exists() and candidate.is_dir():
                    day_dir = candidate
                    break

            if day_dir is None:
                continue

            # Load existing annotations if available
            existing_annotations = load_annotations(base_dir, normalized_name, instrument_id, year, day)

            # Find all JPEG files in this directory
            file_paths = list(day_dir.glob("*.jp*g"))

            if not file_paths:
                continue

            # Create day entry
            day_data = {}
            for file_path in file_paths:
                str_path = str(file_path)
                if existing_annotations and str_path in existing_annotations:
                    day_data[str_path] = existing_annotations[str_path]
                else:
                    day_data[str_path] = {
                        'quality': get_default_quality_data(),
                        'rois': get_default_roi_data()
                    }

            if day_data:
                result[day] = day_data

    else:
        # Flat structure: /L1/year/*.jpg (DOY in filename)
        # Group files by DOY
        files_by_doy = defaultdict(list)
        for item in year_dir.iterdir():
            if item.is_file() and item.name.lower().endswith(('.jpg', '.jpeg')):
                doy = extract_doy_from_filename(item.name)
                if doy and doy in days_to_scan:
                    files_by_doy[doy].append(item)

        # Process each day
        for day, file_paths in files_by_doy.items():
            # Load existing annotations if available
            existing_annotations = load_annotations(base_dir, normalized_name, instrument_id, year, day)

            day_data = {}
            for file_path in file_paths:
                str_path = str(file_path)
                if existing_annotations and str_path in existing_annotations:
                    day_data[str_path] = existing_annotations[str_path]
                else:
                    day_data[str_path] = {
                        'quality': get_default_quality_data(),
                        'rois': get_default_roi_data()
                    }

            if day_data:
                result[day] = day_data

    return {year: dict(result)} if result else {}


def scan_selected_days(base_dir: Union[str, Path], station_name: str,
                      instrument_id: str, year: str, days: List[str],
                      use_cache: bool = True) -> Dict[str, Dict[str, Dict]]:
    """
    Efficiently scan image data for specific days without loading all data.

    Supports two directory structures:
    1. Flat structure: /L1/year/*.jpg (DOY extracted from filename)
    2. Nested structure: /L1/year/doy/*.jpg (files in DOY subdirectories)

    Parameters:
        base_dir (str or Path): The base directory to search in
        station_name (str): The normalized station name
        instrument_id (str): The instrument ID
        year (str): The year to scan
        days (List[str]): List of days (DOY) to scan
        use_cache (bool): If True, use the image index cache for faster lookups

    Returns:
        Dict: A nested dictionary with image data for the specified days only
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

    # Initialize result structure
    result = defaultdict(dict)

    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)

    # Normalize days to 3-digit format
    days_normalized = set()
    for day in days:
        day_padded = day.zfill(3) if isinstance(day, str) else str(day).zfill(3)
        days_normalized.add(day_padded)

    # Use cache if requested (faster for repeated lookups)
    if use_cache:
        for day in days_normalized:
            # Get file paths from cache
            file_paths = get_day_filepaths(base_dir, normalized_name, instrument_id, year, day)

            if not file_paths:
                continue

            # Load existing annotations if available
            existing_annotations = load_annotations(base_dir, normalized_name, instrument_id, year, day)

            day_data = {}
            for str_path in file_paths:
                if existing_annotations and str_path in existing_annotations:
                    day_data[str_path] = existing_annotations[str_path]
                else:
                    day_data[str_path] = {
                        'quality': get_default_quality_data(),
                        'rois': get_default_roi_data()
                    }

            if day_data:
                result[day] = day_data

        return {year: dict(result)} if result else {}

    # Fallback: direct directory scan
    year_dir = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year

    if not year_dir.exists() or not year_dir.is_dir():
        return {}

    # Determine if we have DOY subdirectories or flat structure
    has_doy_dirs = any(item.is_dir() and item.name.isdigit() for item in year_dir.iterdir())

    if has_doy_dirs:
        # Original nested structure: /L1/year/doy/*.jpg
        for day in days_normalized:
            day_with_zeros = day
            day_without_zeros = day.lstrip('0') or '0'

            day_dir = None
            for day_format in [day_with_zeros, day_without_zeros]:
                candidate = year_dir / day_format
                if candidate.exists() and candidate.is_dir():
                    day_dir = candidate
                    break

            if day_dir is None:
                continue

            # Load existing annotations if available
            existing_annotations = load_annotations(base_dir, normalized_name, instrument_id, year, day)

            # Find all JPEG files in this directory
            file_paths = list(day_dir.glob("*.jp*g"))

            if not file_paths:
                continue

            day_data = {}
            for file_path in file_paths:
                str_path = str(file_path)
                if existing_annotations and str_path in existing_annotations:
                    day_data[str_path] = existing_annotations[str_path]
                else:
                    day_data[str_path] = {
                        'quality': get_default_quality_data(),
                        'rois': get_default_roi_data()
                    }

            if day_data:
                result[day] = day_data

    else:
        # Flat structure: /L1/year/*.jpg (DOY in filename)
        # Group files by DOY
        files_by_doy = defaultdict(list)
        for item in year_dir.iterdir():
            if item.is_file() and item.name.lower().endswith(('.jpg', '.jpeg')):
                doy = extract_doy_from_filename(item.name)
                if doy and doy in days_normalized:
                    files_by_doy[doy].append(item)

        # Process each day
        for day, file_paths in files_by_doy.items():
            # Load existing annotations if available
            existing_annotations = load_annotations(base_dir, normalized_name, instrument_id, year, day)

            day_data = {}
            for file_path in file_paths:
                str_path = str(file_path)
                if existing_annotations and str_path in existing_annotations:
                    day_data[str_path] = existing_annotations[str_path]
                else:
                    day_data[str_path] = {
                        'quality': get_default_quality_data(),
                        'rois': get_default_roi_data()
                    }

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