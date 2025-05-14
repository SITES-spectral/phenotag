"""
ROI utility functions for PhenoTag UI.

This module provides functions for working with Regions of Interest (ROIs),
including serialization, deserialization, and overlay on images.
"""
import cv2
import numpy as np


def serialize_polygons(phenocam_rois):
    """
    Converts a dictionary of polygons to be YAML-friendly by converting tuples to lists.

    Parameters:
        phenocam_rois (dict of dict): Dictionary where keys are ROI names and values are dictionaries representing polygons.

    Returns:
        yaml_friendly_rois (dict of dict): Dictionary with tuples converted to lists.
    """
    yaml_friendly_rois = {}
    for roi, polygon in phenocam_rois.items():
        yaml_friendly_polygon = {
            'points': [list(point) for point in polygon['points']],
            'color': list(polygon['color']),
            'thickness': polygon['thickness']
        }
        yaml_friendly_rois[roi] = yaml_friendly_polygon
    return yaml_friendly_rois


def deserialize_polygons(yaml_friendly_rois):
    """
    Converts YAML-friendly polygons back to their original format with tuples.
    Makes the ROI format compatible with ImageProcessor.overlay_polygons_from_dict.

    Parameters:
        yaml_friendly_rois (dict of dict): Dictionary where keys are ROI names and values are dictionaries representing polygons in YAML-friendly format.

    Returns:
        original_rois (dict of dict): Dictionary with points and color as tuples.
    """
    original_rois = {}
    for roi_name, roi_data in yaml_friendly_rois.items():
        # Convert points to tuples and ensure they're in the correct format
        points = [tuple(point) for point in roi_data['points']]

        # Convert color to tuple
        color = tuple(roi_data['color'])

        # Get thickness (default to 2 if not present)
        thickness = roi_data.get('thickness', 2)

        # Set alpha to 0 to disable filling
        alpha = 0.0  # Disable filling

        # Store in the format expected by overlay_polygons_from_dict
        original_rois[roi_name] = {
            'points': points,
            'color': color,
            'thickness': thickness,
            'alpha': alpha
        }

    return original_rois


def overlay_polygons(image_path, phenocam_rois: dict, show_names: bool = True, font_scale: float = 2.0):
    """
    Overlays polygons on an image and optionally labels them with their respective ROI names.

    Parameters:
        image_path (str): Path to the image file.
        phenocam_rois (dict): Dictionary where keys are ROI names and values are dictionaries representing polygons.
        Each dictionary should have the following keys:
        - 'points' (list of tuple): List of (x, y) tuples representing the vertices of the polygon.
        - 'color' (tuple): (B, G, R) color of the polygon border.
        - 'thickness' (int): Thickness of the polygon border.
        show_names (bool): Whether to display the ROI names on the image. Default is True.
        font_scale (float): Scale factor for the font size of the ROI names. Default is 2.0.

    Returns:
        numpy.ndarray: The image with polygons overlaid, in RGB format.
    """
    # Read the image
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not found or path is incorrect")

    for roi_name, roi_data in phenocam_rois.items():
        try:
            # Extract points from the polygon dictionary
            points = roi_data['points']
            # Convert to numpy array for OpenCV
            points_array = np.array(points, dtype=np.int32)

            # Extract color - handle both RGB and BGR formats
            color = roi_data['color']
            # Convert RGB to BGR if needed (OpenCV uses BGR)
            if len(color) == 3:
                color = (color[2], color[1], color[0])  # Swap R and B

            # Extract thickness with default
            thickness = roi_data.get('thickness', 2)

            # Draw the polygon outline on the image (no filling)
            cv2.polylines(img, [points_array], isClosed=True, color=color, thickness=thickness)

            if show_names:
                # Calculate the centroid of the polygon for labeling
                M = cv2.moments(points_array)
                if M['m00'] != 0:
                    cX = int(M['m10'] / M['m00'])
                    cY = int(M['m01'] / M['m00'])
                else:
                    # In case of a degenerate polygon where area is zero
                    cX, cY = points_array[0][0], points_array[0][1]

                # Get text size for centering
                text = roi_name
                font = cv2.FONT_HERSHEY_SIMPLEX
                text_thickness = 2  # Appropriate thickness for a font scale of 2.0
                (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, text_thickness)

                # Adjust position to center text on centroid
                text_x = cX - (text_width // 2)
                text_y = cY + (text_height // 2)

                # Draw text with same color as polygon
                cv2.putText(img, text, (text_x, text_y), font, font_scale, color, text_thickness, cv2.LINE_AA)

        except Exception as e:
            print(f"Error processing ROI '{roi_name}': {str(e)}")
            # Continue with other ROIs even if one fails

    # Convert the image from BGR to RGB before returning
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img_rgb