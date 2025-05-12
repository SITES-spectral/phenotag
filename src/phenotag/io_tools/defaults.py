"""
Default values for image quality and ROI data
"""

def get_default_quality_data():
    """Return default quality data for an image."""
    return {'discard_file': False, 'snow_presence': False}


def get_default_roi_data():
    """Return default ROI data structure."""
    return {
        'ROI_01': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
        'ROI_02': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []},
        'ROI_03': {'discard_roi': False, 'snow_presence': False, 'annotated_flags': []}
    }