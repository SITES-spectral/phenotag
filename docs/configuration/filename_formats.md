# Filename Formats in SITES Spectral

This document describes the standardized filename formats used throughout the SITES Spectral ecosystem, particularly for phenocam images.

## L0 Filename Format

L0 (raw) phenocam images follow this structured naming pattern:

```
{location}_{station_acronym}_{instrument_id}_{year}_{day_of_year}_{timestamp}.jpg
```

### Components

| Component | Description | Example |
|-----------|-------------|---------|
| `location` | The site name | `abisko` |
| `station_acronym` | Station identifier | `ANS` |
| `instrument_id` | Full instrument identifier | `FOR_BL01_PHE01` |
| `year` | 4-digit year | `2022` |
| `day_of_year` | 3-digit day of year with leading zeros | `181` |
| `timestamp` | Time format YYYYMMDD_HHMMSS | `20220630_113454` |

### Example

```
abisko_ANS_FOR_BL01_PHE01_2022_181_20220630_113454.jpg
```

This filename represents:
- Site: Abisko
- Station: ANS (Abisko Nature Station)
- Instrument: FOR_BL01_PHE01 (Forest site, Block 01, Phenocam 01)
- Captured on: June 30, 2022 (day 181 of 2022)
- At time: 11:34:54

## File Organization

L0 images are typically stored in a directory structure:

```
{data_dir}/{station}/phenocams/products/{instrument}/L0/{year}/{doy}/
```

For example:
```
/data/abisko/phenocams/products/ANS_FOR_BL01_PHE01/L0/2022/181/
```

## Programmatic Generation

To generate a filename in code:

```python
def generate_l0_filename(location, station_acronym, instrument_id, dt):
    """Generate standardized L0 filename for phenocam images.
    
    Args:
        location (str): Site location name
        station_acronym (str): Station identifier
        instrument_id (str): Instrument identifier
        dt (datetime): Capture datetime
        
    Returns:
        str: Formatted filename
    """
    year = dt.year
    day_of_year = dt.timetuple().tm_yday
    timestamp = dt.strftime("%Y%m%d_%H%M%S")
    
    return f"{location}_{station_acronym}_{instrument_id}_{year}_{day_of_year:03d}_{timestamp}.jpg"
```

## Notes

- The day of year is always a 3-digit number with leading zeros (001-366)
- Standardizing filenames ensures consistent processing across the platform
- The format allows for deterministic recreation of filenames when needed
- Parsing these filenames allows automatic extraction of temporal information