"""
Memory-efficient directory scanner for phenocam data

This module provides functions for scanning the phenocam directory structure
without loading the actual image data to minimize memory usage.
"""

from pathlib import Path
import os
import datetime
from typing import List, Dict, Set, Optional, Union, Tuple
import calendar


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
    Get available years by scanning L1 directories without loading any image data.
    
    Args:
        base_dir: Base data directory
        station_name: Station name
        instrument_id: Instrument ID
        
    Returns:
        List of year strings sorted in descending order (newest first)
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)
    
    # Construct path to L1 directory
    l1_path = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1"
    
    if not l1_path.exists() or not l1_path.is_dir():
        return []
    
    # Get directory names that are digit-only (years)
    years = []
    for item in l1_path.iterdir():
        if item.is_dir() and item.name.isdigit():
            years.append(item.name)
    
    # Sort in descending order (newest first)
    years.sort(reverse=True)
    return years


def get_days_in_year(base_dir: Union[str, Path], station_name: str, 
                   instrument_id: str, year: str) -> List[str]:
    """
    Get available days of year by scanning directories without loading image data.
    
    Args:
        base_dir: Base data directory
        station_name: Station name
        instrument_id: Instrument ID
        year: Year to scan
        
    Returns:
        List of day of year strings (padded to 3 digits, e.g., "001")
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)
    
    # Construct path to year directory
    year_path = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year
    
    if not year_path.exists() or not year_path.is_dir():
        return []
    
    # Get directory names that are digit-only (days of year)
    days = []
    for item in year_path.iterdir():
        if item.is_dir() and item.name.isdigit():
            # Ensure 3-digit format with leading zeros
            days.append(item.name.zfill(3))
    
    # Sort in ascending order
    days.sort()
    # Debug output
    print(f"Found {len(days)} days in year {year}: {days[:5]}...")
    return days


def get_days_by_month(year: Union[str, int], days: List[str]) -> Dict[int, List[str]]:
    """
    Organize days of year by month.
    
    Args:
        year: Year 
        days: List of day of year strings
        
    Returns:
        Dictionary mapping month number (1-12) to list of day of year strings
    """
    year_int = int(year)
    month_to_days = {month: [] for month in range(1, 13)}
    
    for day_str in days:
        try:
            # Convert day of year to date
            day_int = int(day_str)
            date = datetime.datetime(year_int, 1, 1) + datetime.timedelta(days=day_int-1)
            
            # Add to appropriate month
            month = date.month
            month_to_days[month].append(day_str)
        except (ValueError, TypeError, OverflowError):
            # Skip invalid days
            continue
    
    return month_to_days


def count_images_in_days(base_dir: Union[str, Path], station_name: str,
                       instrument_id: str, year: str, days: List[str]) -> Dict[str, int]:
    """
    Count images in each day directory without loading image data.

    Args:
        base_dir: Base data directory
        station_name: Station name
        instrument_id: Instrument ID
        year: Year to scan
        days: List of day of year strings

    Returns:
        Dictionary mapping day of year to image count
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
    
    # Get the normalized station name for consistent directory paths
    normalized_name = get_normalized_station_name(station_name)
    
    counts = {}

    # Add debug output for tracing
    print(f"Counting images for {len(days)} days in {base_dir}/{normalized_name}/phenocams/products/{instrument_id}/L1/{year}")

    for day in days:
        # Try both with and without leading zeros to handle filesystem differences
        day_with_zeros = day
        day_without_zeros = day.lstrip('0') if day else '0'
        
        # Also try with integer format (some systems might store as integer)
        day_as_int = str(int(day))

        # First try with the original format
        day_path = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year / day_with_zeros

        # If that doesn't exist, try without leading zeros
        if not day_path.exists() or not day_path.is_dir():
            day_path = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year / day_without_zeros

            # If that still doesn't exist, try with integer format
            if not day_path.exists() or not day_path.is_dir():
                day_path = base_dir / normalized_name / "phenocams" / "products" / instrument_id / "L1" / year / day_as_int
                
                # If that still doesn't exist, mark as having zero images
                if not day_path.exists() or not day_path.is_dir():
                    counts[day] = 0
                    continue

        # Count image files
        image_count = 0
        image_files = []
        for item in day_path.iterdir():
            if item.is_file() and item.name.lower().endswith(('.jpg', '.jpeg')):
                image_count += 1
                if len(image_files) < 3:  # Keep track of first few files for debugging
                    image_files.append(item.name)

        counts[day] = image_count
        
        # Add debugging output
        if image_count > 0:
            print(f"Day {day}: Found {image_count} images in {day_path} - Examples: {image_files}")
        else:
            print(f"Day {day}: No images found in {day_path}")

    return counts


def get_month_info(year: Union[str, int], month: int) -> Tuple[int, List[int]]:
    """
    Get information about a month: days in month and corresponding days of year.
    
    Args:
        year: Year
        month: Month number (1-12)
        
    Returns:
        Tuple of (days in month, list of day of year numbers)
    """
    year_int = int(year)
    
    # Get days in the month
    days_in_month = calendar.monthrange(year_int, month)[1]
    
    # Convert to days of year
    days_of_year = []
    for day in range(1, days_in_month + 1):
        date = datetime.date(year_int, month, day)
        doy = date.timetuple().tm_yday
        days_of_year.append(doy)
    
    return days_in_month, days_of_year


def get_days_in_month(year: Union[str, int], month: int, days: List[str]) -> List[str]:
    """
    Filter days to get only those in a specific month.

    Args:
        year: Year
        month: Month number (1-12)
        days: List of all day of year strings

    Returns:
        List of day of year strings in the specified month
    """
    year_int = int(year)

    # Get days of year for the month
    _, month_days = get_month_info(year_int, month)
    month_days_set = set(month_days)

    # Add debug output
    print(f"Month {month} contains DOYs: {sorted(month_days_set)}")
    print(f"Available days (before filtering): {days[:10]}...")

    # Filter days list
    result = []
    for day_str in days:
        try:
            # Handle both padded (e.g., "001") and unpadded (e.g., "1") day strings
            day_int = int(day_str)
            if day_int in month_days_set:
                # Preserve the original format of the day string
                result.append(day_str)
        except (ValueError, TypeError):
            continue

    # Add debug output for result
    print(f"Days in month {month} after filtering: {result}")
    return result


def get_date_from_doy(year: Union[str, int], doy: Union[str, int]) -> datetime.date:
    """
    Convert year and day of year to a date object.
    
    Args:
        year: Year
        doy: Day of year
        
    Returns:
        Date object
    """
    year_int = int(year)
    doy_int = int(doy)
    
    date = datetime.date(year_int, 1, 1) + datetime.timedelta(days=doy_int-1)
    return date


def get_month_with_most_images(base_dir: Union[str, Path], station_name: str, 
                            instrument_id: str, year: str) -> int:
    """
    Find the month with the most images.
    
    Args:
        base_dir: Base data directory
        station_name: Station name
        instrument_id: Instrument ID
        year: Year to scan
        
    Returns:
        Month number (1-12) with the most images, or 1 if no images found
    """
    # Get all days with images
    days = get_days_in_year(base_dir, station_name, instrument_id, year)
    
    if not days:
        return 1  # Default to January if no days found
    
    # Organize by month
    month_to_days = get_days_by_month(year, days)
    
    # Count images in each day
    image_counts = count_images_in_days(base_dir, station_name, instrument_id, year, days)
    
    # Calculate total images per month
    month_totals = {}
    for month, month_days in month_to_days.items():
        month_totals[month] = sum(image_counts.get(day, 0) for day in month_days)
    
    # Add debug output
    print(f"Images per month: {month_totals}")
    
    # Find month with most images
    if any(month_totals.values()):
        best_month = max(month_totals.items(), key=lambda x: x[1])[0]
        print(f"Month with most images: {calendar.month_name[best_month]} ({best_month}) with {month_totals[best_month]} images")
        return best_month
    
    return 1  # Default to January if no images found


def format_month_year(year: Union[str, int], month: int) -> str:
    """
    Format month and year as a string.
    
    Args:
        year: Year
        month: Month number (1-12)
        
    Returns:
        Formatted string (e.g., "January 2022")
    """
    return f"{calendar.month_name[month]} {year}"


def create_placeholder_data(year: str, days: List[str]) -> Dict:
    """
    Create placeholder data structure with the given days.

    Args:
        year: Year
        days: List of day of year strings

    Returns:
        Nested dictionary for image data structure
    """
    # Ensure consistent day of year formatting with leading zeros
    formatted_days = {}
    for day in days:
        # Ensure day is properly padded with leading zeros
        day_int = int(day.lstrip('0') or '0')  # Handle '000' case
        day_padded = f"{day_int:03d}"          # Format with leading zeros (090)
        formatted_days[day_padded] = {"_placeholder": True}
    
    # Debug output for the first few days
    sample_days = list(formatted_days.keys())[:5]
    print(f"Created placeholder data for {len(formatted_days)} days in year {year}. Sample days: {sample_days}")
    
    return {
        year: formatted_days
    }