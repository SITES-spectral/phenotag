"""
Image Index Cache Module for PhenoTag

This module provides a cached index of L1 images organized by DOY and timestamp.
Instead of re-scanning directories multiple times, it builds an index once and
caches it for fast lookups.

The index structure:
{
    "station_instrument_year": {
        "091": {
            "20250401_080949": "/path/to/abisko_ANS_FOR_BL01_PHE01_2025_091_20250401_080949.jpg",
            "20250401_100949": "/path/to/abisko_ANS_FOR_BL01_PHE01_2025_091_20250401_100949.jpg",
            ...
        },
        "092": {...},
        ...
    }
}
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict
from datetime import datetime
import threading


# Module-level cache with thread safety
_image_index_cache: Dict[str, Dict[str, Dict[str, str]]] = {}
_cache_lock = threading.Lock()


def get_cache_key(station_name: str, instrument_id: str, year: str) -> str:
    """Generate a unique cache key for station/instrument/year combination."""
    return f"{station_name}_{instrument_id}_{year}"


def parse_filename(filename: str) -> Optional[Dict[str, str]]:
    """
    Parse a phenocam filename to extract metadata.

    Expected filename pattern: station_instrument_year_doy_datestring_timestring.jpg
    Example: abisko_ANS_FOR_BL01_PHE01_2025_091_20250401_080949.jpg

    Args:
        filename: Filename to parse

    Returns:
        Dictionary with keys: 'station', 'instrument', 'year', 'doy', 'date', 'time', 'timestamp'
        or None if parsing fails
    """
    # Pattern: station_instrument_year_doy_YYYYMMDD_HHMMSS.jpg
    # instrument can have underscores like ANS_FOR_BL01_PHE01
    pattern = r'^([a-z]+)_([A-Z0-9_]+)_(\d{4})_(\d{1,3})_(\d{8})_(\d{6})\.jpe?g$'
    match = re.match(pattern, filename, re.IGNORECASE)

    if match:
        station, instrument, year, doy, date_str, time_str = match.groups()
        return {
            'station': station,
            'instrument': instrument,
            'year': year,
            'doy': doy.zfill(3),  # Ensure 3-digit format
            'date': date_str,
            'time': time_str,
            'timestamp': f"{date_str}_{time_str}"
        }
    return None


def extract_doy_from_filename(filename: str) -> Optional[str]:
    """
    Extract day of year (DOY) from a phenocam filename.

    Args:
        filename: Filename to parse

    Returns:
        DOY as 3-digit string (e.g., "091") or None if not found
    """
    parsed = parse_filename(filename)
    return parsed['doy'] if parsed else None


def extract_timestamp_from_filename(filename: str) -> Optional[str]:
    """
    Extract timestamp from a phenocam filename.

    Args:
        filename: Filename to parse

    Returns:
        Timestamp string (e.g., "20250401_080949") or None if not found
    """
    parsed = parse_filename(filename)
    return parsed['timestamp'] if parsed else None


def extract_time_from_filename(filename: str) -> Optional[str]:
    """
    Extract time (HHMMSS) from a phenocam filename.

    Args:
        filename: Filename to parse

    Returns:
        Time string (e.g., "080949") or None if not found
    """
    parsed = parse_filename(filename)
    return parsed['time'] if parsed else None


def build_year_index(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str
) -> Dict[str, Dict[str, str]]:
    """
    Build an index of all L1 images for a specific station/instrument/year.

    Supports both:
    1. Flat structure: /L1/year/*.jpg
    2. Nested structure: /L1/year/doy/*.jpg

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to index

    Returns:
        Dictionary mapping DOY -> {timestamp: filepath}
    """
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

    # Construct path to year directory
    year_dir = base_dir / station_name / "phenocams" / "products" / instrument_id / "L1" / year

    if not year_dir.exists() or not year_dir.is_dir():
        return {}

    index: Dict[str, Dict[str, str]] = defaultdict(dict)

    # Check if this year has DOY subdirectories or flat files
    has_doy_dirs = any(item.is_dir() and item.name.isdigit() for item in year_dir.iterdir())

    if has_doy_dirs:
        # Nested structure: /L1/year/doy/*.jpg
        for doy_dir in year_dir.iterdir():
            if doy_dir.is_dir() and doy_dir.name.isdigit():
                doy = doy_dir.name.zfill(3)
                for file_path in doy_dir.iterdir():
                    if file_path.is_file() and file_path.name.lower().endswith(('.jpg', '.jpeg')):
                        timestamp = extract_timestamp_from_filename(file_path.name)
                        if timestamp:
                            index[doy][timestamp] = str(file_path)
                        else:
                            # Fallback: use filename as timestamp
                            index[doy][file_path.stem] = str(file_path)
    else:
        # Flat structure: /L1/year/*.jpg
        for file_path in year_dir.iterdir():
            if file_path.is_file() and file_path.name.lower().endswith(('.jpg', '.jpeg')):
                parsed = parse_filename(file_path.name)
                if parsed:
                    index[parsed['doy']][parsed['timestamp']] = str(file_path)

    # Convert defaultdict to regular dict and sort timestamps within each DOY
    return {doy: dict(sorted(timestamps.items())) for doy, timestamps in sorted(index.items())}


def get_year_index(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str,
    force_refresh: bool = False
) -> Dict[str, Dict[str, str]]:
    """
    Get the image index for a year, using cache if available.

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to get index for
        force_refresh: If True, rebuild the index even if cached

    Returns:
        Dictionary mapping DOY -> {timestamp: filepath}
    """
    cache_key = get_cache_key(station_name, instrument_id, year)

    with _cache_lock:
        if not force_refresh and cache_key in _image_index_cache:
            return _image_index_cache[cache_key]

        # Build the index
        index = build_year_index(base_dir, station_name, instrument_id, year)

        # Cache it
        _image_index_cache[cache_key] = index

        return index


def get_available_doys(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str,
    force_refresh: bool = False
) -> List[str]:
    """
    Get list of available DOYs for a year using the cached index.

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to query
        force_refresh: If True, rebuild the index

    Returns:
        Sorted list of DOY strings (e.g., ["091", "092", "093"])
    """
    index = get_year_index(base_dir, station_name, instrument_id, year, force_refresh)
    return sorted(index.keys())


def get_day_files(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str,
    doy: str,
    force_refresh: bool = False
) -> Dict[str, str]:
    """
    Get all files for a specific DOY using the cached index.

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to query
        doy: Day of year (will be normalized to 3 digits)
        force_refresh: If True, rebuild the index

    Returns:
        Dictionary mapping timestamp -> filepath, sorted by timestamp
    """
    index = get_year_index(base_dir, station_name, instrument_id, year, force_refresh)
    doy_normalized = doy.zfill(3)
    return index.get(doy_normalized, {})


def get_day_filepaths(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str,
    doy: str,
    force_refresh: bool = False
) -> List[str]:
    """
    Get list of filepaths for a specific DOY, sorted by timestamp.

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to query
        doy: Day of year
        force_refresh: If True, rebuild the index

    Returns:
        List of filepaths sorted by timestamp
    """
    files = get_day_files(base_dir, station_name, instrument_id, year, doy, force_refresh)
    return list(files.values())


def get_image_count(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str,
    doy: Optional[str] = None,
    force_refresh: bool = False
) -> int:
    """
    Get count of images for a year or specific DOY.

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to query
        doy: Optional DOY to count (if None, counts all images in year)
        force_refresh: If True, rebuild the index

    Returns:
        Number of images
    """
    index = get_year_index(base_dir, station_name, instrument_id, year, force_refresh)

    if doy:
        return len(index.get(doy.zfill(3), {}))
    else:
        return sum(len(timestamps) for timestamps in index.values())


def get_doy_image_counts(
    base_dir: Union[str, Path],
    station_name: str,
    instrument_id: str,
    year: str,
    force_refresh: bool = False
) -> Dict[str, int]:
    """
    Get image counts for each DOY in a year.

    Args:
        base_dir: Base data directory
        station_name: Normalized station name
        instrument_id: Instrument ID
        year: Year to query
        force_refresh: If True, rebuild the index

    Returns:
        Dictionary mapping DOY -> image count
    """
    index = get_year_index(base_dir, station_name, instrument_id, year, force_refresh)
    return {doy: len(timestamps) for doy, timestamps in index.items()}


def invalidate_cache(
    station_name: Optional[str] = None,
    instrument_id: Optional[str] = None,
    year: Optional[str] = None
) -> int:
    """
    Invalidate cached index entries.

    Args:
        station_name: If provided with instrument_id and year, invalidate specific entry
                      If only station_name, invalidate all entries for that station
        instrument_id: Instrument ID (requires station_name)
        year: Year (requires station_name and instrument_id)

    Returns:
        Number of cache entries invalidated
    """
    with _cache_lock:
        if station_name and instrument_id and year:
            # Invalidate specific entry
            cache_key = get_cache_key(station_name, instrument_id, year)
            if cache_key in _image_index_cache:
                del _image_index_cache[cache_key]
                return 1
            return 0
        elif station_name:
            # Invalidate all entries for station
            keys_to_delete = [k for k in _image_index_cache if k.startswith(f"{station_name}_")]
            for key in keys_to_delete:
                del _image_index_cache[key]
            return len(keys_to_delete)
        else:
            # Invalidate all entries
            count = len(_image_index_cache)
            _image_index_cache.clear()
            return count


def get_cache_stats() -> Dict[str, any]:
    """
    Get statistics about the current cache state.

    Returns:
        Dictionary with cache statistics
    """
    with _cache_lock:
        total_doys = sum(len(index) for index in _image_index_cache.values())
        total_images = sum(
            sum(len(timestamps) for timestamps in index.values())
            for index in _image_index_cache.values()
        )

        return {
            'cached_entries': len(_image_index_cache),
            'total_doys': total_doys,
            'total_images': total_images,
            'cache_keys': list(_image_index_cache.keys())
        }
