# stations.yaml Schema Documentation

This document provides a detailed overview of the `stations.yaml` configuration file structure, which is a key component of the PhenoTag and SITES Spectral ecosystem.

## Overview

The `stations.yaml` file defines the monitoring stations, their platforms, instruments, and ROI (Region of Interest) configurations. It follows a hierarchical structure that allows for precise organization of monitoring assets.

## Schema Structure

### Top Level

```yaml
stations:
  station_normalized_name:
    # Station configuration
    normalized_name: string          # ASCII-friendly name for file paths (e.g., "abisko")
    name: string                     # Official station name (e.g., "Abisko")
    acronym: string                  # 3-4 uppercase letters, unique across stations (e.g., "ANS")
    phenocams:
      platforms:
        # Platform configurations
```

### Platform Level

Platforms are defined under each station's `phenocams.platforms` section:

```yaml
platforms:
  BL:  # Building
    instruments:
      # Instrument configurations
  PL:  # Pole/Mast/Tower
    instruments:
      # Instrument configurations
  GL:  # Ground Level
    instruments:
      # Instrument configurations
```

#### Platform Types

- **BL**: Building
- **PL**: Pole, Mast, Tower (height > 1.5m)
- **GL**: Ground Level (supporting platform below 1.5 meters)

### Instrument Level

Instruments are defined under each platform's `instruments` section:

```yaml
instruments:
  ABC_XYZ_PL01_PHE01:  # Instrument ID
    id: string                 # Full instrument ID (e.g., "ANS_FOR_BL01_PHE01")
    legacy_names:              # Optional array of previous IDs for backward compatibility
      - string
    type: string               # Instrument type (e.g., "phenocam")
    ecosystem: string          # Ecosystem acronym (e.g., "FOR" for Forest)
    location: string           # Location identifier (e.g., "BL01")
    instrument_number: string  # Instrument identifier (e.g., "PHE01")
    status: string             # "Active" or "Inactive"
    deployment_date: string    # Optional deployment date
    
    # Platform information
    platform_mounting_structure: string  # Type of mount (Building, Mast, etc.)
    platform_height_in_meters_above_ground: number
    
    # Geolocation
    geolocation:
      point:
        epsg: string           # Coordinate system (e.g., "epsg:4326")
        latitude_dd: number    # Latitude in decimal degrees
        longitude_dd: number   # Longitude in decimal degrees
    
    # Instrument positioning
    instrument_height_in_meters_above_ground: number
    instrument_viewing_direction: string       # Cardinal direction
    instrument_azimuth_in_degrees: number      # Azimuth angle
    instrument_degrees_from_nadir: number      # Angle from vertical
    
    # Legacy information
    legacy_acronym: string     # Optional previous ID for backward compatibility
    
    # ROI definitions
    rois:
      # ROI configurations
```

### Instrument ID Format

The instrument ID follows this format:
```
{LOCATION_ACRONYM}_{ECOSYSTEM_ACRONYM}_{PLATFORM_ACRONYM}{PLATFORM_NUMBER}_{INSTRUMENT_TYPE_ACRONYM}{INSTRUMENT_NUMBER}
```

Example: `ANS_FOR_PL01_PHE01` where:
- `ANS`: Location acronym (Abisko)
- `FOR`: Ecosystem acronym (Forest)
- `PL01`: Platform type and number (Pole/Mast/Tower #1)
- `PHE01`: Instrument type and number (PhenoCam #1)

### ROI Level

ROIs (Regions of Interest) are defined under each instrument's `rois` section:

```yaml
rois:
  ROI_01:
    points: [[x1, y1], [x2, y2], [x3, y3], ...]  # List of [x,y] coordinates
    color: [R, G, B]                             # RGB color for visualization
    thickness: number                            # Line thickness for visualization
    alpha: number                                # Optional transparency (0-1) for fill
    updated: string                              # Optional last update date
    comment: string                              # Optional notes about the ROI
```

### Legacy ROI Section

For historical ROI definitions that are no longer active:

```yaml
legacy_phenocam_rois:
  ROI_01:
    points: [[x1, y1], [x2, y2], [x3, y3], ...]
    color: [R, G, B]
    thickness: number
    updated: string
    comment: string
    legacy_platform: string  # Information about the original platform
```

## Ecosystem Acronyms

The ecosystem acronyms used in instrument IDs are:
- `FOR`: Forest
- `AGR`: Arable Land
- `MIR`: Mires
- `LAK`: Lake
- `WET`: Wetland
- `GRA`: Grassland
- `HEA`: Heathland
- `ALP`: Alpine Forest
- `CON`: Coniferous Forest
- `DEC`: Deciduous Forest
- `MAR`: Marshland
- `PEA`: Peatland

## Full Schema Example

```yaml
stations:
  abisko:
    normalized_name: abisko
    name: Abisko
    acronym: ANS
    phenocams:
      platforms:
        BL:
          instruments:
            ANS_FOR_BL01_PHE01:
              id: ANS_FOR_BL01_PHE01
              legacy_names:
                - ANS-FOR-P01
              type: phenocam
              ecosystem: FOR
              location: BL01
              instrument_number: PHE01
              status: Active
              deployment_date: 
              platform_mounting_structure: Building RoofTop
              platform_height_in_meters_above_ground: 4.5
              geolocation:
                point:
                  epsg: "epsg:4326"
                  latitude_dd: 68.353729
                  longitude_dd: 18.816522
              instrument_height_in_meters_above_ground: 4.5
              instrument_viewing_direction: West
              instrument_azimuth_in_degrees: 270
              instrument_degrees_from_nadir: 90
              rois:
                ROI_01: {'points': [[100, 1800], [2700, 1550], [2500, 2700], [100, 2700]], 'color': [0, 255, 0], 'thickness': 7}
                ROI_02: {'points': [[100, 930], [3700, 1050], [3700, 1150], [100, 1300]], 'color': [0, 0, 255], 'thickness': 7}
```

## Data Relationships

The hierarchical organization of the `stations.yaml` file follows this structure:

```
stations
  └── station (normalized_name)
       ├── station metadata (name, acronym)
       └── phenocams
            └── platforms
                 └── platform type (BL, PL, GL)
                      └── instruments
                           └── instrument (full ID)
                                ├── instrument metadata
                                ├── geolocation
                                └── rois
                                     └── ROI definitions
```

## File Interactions

The `stations.yaml` file is used by multiple components of the system:

1. **PhenoTag UI**: For station and instrument selection, ROI display, and configuration viewing
2. **Image Processing**: For applying ROIs to images during analysis
3. **Metadata Generation**: For attaching station and instrument metadata to processed data
4. **Data Organization**: For structuring the file system hierarchy

## Validation Rules

When updating the `stations.yaml` file, ensure:

1. **Unique Identifiers**: Each station normalized name and acronym must be unique
2. **Required Fields**: All required fields are provided for each level
3. **Consistent Formatting**: Follow the established patterns for IDs, acronyms, and structures
4. **Coordinate Systems**: Use consistent coordinate systems (typically EPSG:4326)
5. **ROI Consistency**: ROI points define valid polygons and color values are in RGB [0-255] range

## Best Practices

1. **Commenting**: Add comments to document changes and special cases
2. **Legacy Information**: Keep legacy information for backward compatibility
3. **ROI Updates**: When updating ROIs, keep the old definition in `legacy_phenocam_rois` and document the reason
4. **Hierarchy Consistency**: Maintain the hierarchical structure for all stations
5. **Validation**: Validate the YAML syntax after making changes
6. **Documentation**: Update this document when changing the schema structure

## Troubleshooting Common Issues

### ROI Display Problems
- Ensure ROI `points` are in the format `[[x1, y1], [x2, y2], ...]`
- Verify color values are in RGB order `[R, G, B]` with values from 0-255
- Check that ROI polygons are within image dimensions

### Station Not Found
- Verify the normalized name matches exactly with directory names
- Check case sensitivity in all identifiers

### Instruments Not Loading
- Ensure the platform type (BL, PL, GL) is correctly specified
- Verify the instrument ID follows the required format

## Extending the Schema

When adding new fields to the schema:

1. **Documentation**: Update this document to reflect the new fields
2. **Compatibility**: Ensure backward compatibility with existing code
3. **Validation**: Add validation for the new fields in loading functions
4. **Defaults**: Provide sensible defaults for optional new fields
5. **Testing**: Test the system with the new fields to ensure compatibility

## Tools for Working with stations.yaml

1. **PhenoTag UI**: Use the "Load Full Station Configuration" button to view the current configuration
2. **CLI Tools**: Use the `phenotag` CLI to validate and manage station configurations
3. **YAML Validators**: Use standard YAML validators to check syntax
4. **Version Control**: Keep stations.yaml under version control for tracking changes

## References

For more information on the concepts used in this schema:

1. **SITES Spectral Documentation**: Details on the stations and instrument network
2. **PhenoTag Documentation**: UI and interaction with stations.yaml
3. **ROI Documentation**: Details on defining and using Regions of Interest