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
    
    if not yaml_friendly_rois or not isinstance(yaml_friendly_rois, dict):
        print(f"Warning: Invalid ROI data format. Expected dict, got {type(yaml_friendly_rois)}")
        return original_rois
    
    for roi_name, roi_data in yaml_friendly_rois.items():
        try:
            # Validate roi_data
            if not isinstance(roi_data, dict):
                print(f"Warning: ROI data for {roi_name} is not a dictionary. Skipping.")
                continue
                
            # Check for required keys
            if 'points' not in roi_data:
                print(f"Warning: ROI data for {roi_name} has no 'points' key. Skipping.")
                continue
                
            if 'color' not in roi_data:
                print(f"Warning: ROI data for {roi_name} has no 'color' key. Using default.")
                roi_data['color'] = [0, 255, 0]  # Default to green
            
            # Convert points to tuples and ensure they're in the correct format
            points = []
            for point in roi_data['points']:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    # Convert to int to ensure proper coordinate handling
                    points.append((int(point[0]), int(point[1])))
                else:
                    print(f"Warning: Invalid point format in ROI {roi_name}: {point}. Skipping point.")
            
            # Skip ROIs with fewer than 3 points (can't form a polygon)
            if len(points) < 3:
                print(f"Warning: ROI {roi_name} has fewer than 3 valid points ({len(points)}). Skipping ROI.")
                continue
                
            # Convert color to tuple
            color = tuple(int(c) for c in roi_data['color'][:3])  # Take only first 3 values and convert to int

            # Get thickness (default to 2 if not present)
            thickness = int(roi_data.get('thickness', 2))

            # Set alpha to 0 to disable filling
            alpha = 0.0  # Disable filling

            # Store in the format expected by overlay_polygons_from_dict
            original_rois[roi_name] = {
                'points': points,
                'color': color,
                'thickness': thickness,
                'alpha': alpha
            }
            
            print(f"Successfully processed ROI '{roi_name}' with {len(points)} points")
        except Exception as e:
            print(f"Error processing ROI '{roi_name}': {str(e)}")
            # Continue with other ROIs even if one fails

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
        
    # Get image dimensions to check if ROIs are within bounds
    height, width = img.shape[:2]
    print(f"Image dimensions: {width} x {height}")
    
    # Count how many ROIs are successfully drawn
    successful_rois = 0
    total_rois = len(phenocam_rois) if phenocam_rois else 0

    for roi_name, roi_data in phenocam_rois.items():
        try:
            # Validate roi_data
            if not isinstance(roi_data, dict) or 'points' not in roi_data:
                print(f"ROI '{roi_name}' has invalid format. Skipping.")
                continue
                
            # Extract points from the polygon dictionary
            points = roi_data['points']
            
            # Check that we have enough points for a polygon
            if len(points) < 3:
                print(f"ROI '{roi_name}' has fewer than 3 points ({len(points)}). Skipping.")
                continue
                
            # Check if points are within image boundaries
            out_of_bounds_points = []
            for i, point in enumerate(points):
                x, y = point
                if x < 0 or x >= width or y < 0 or y >= height:
                    out_of_bounds_points.append((i, point))
            
            if out_of_bounds_points:
                print(f"ROI '{roi_name}' has {len(out_of_bounds_points)} points outside image boundaries:")
                for idx, point in out_of_bounds_points[:3]:  # Show up to 3 examples
                    print(f"  - Point {idx}: {point} is outside {width}x{height}")
                if len(out_of_bounds_points) > 3:
                    print(f"  - ... and {len(out_of_bounds_points) - 3} more")
                    
                # Clip points to stay within image boundaries
                clipped_points = []
                for point in points:
                    x, y = point
                    clipped_points.append((max(0, min(x, width-1)), max(0, min(y, height-1))))
                points = clipped_points
                print(f"Clipped points to stay within image boundaries for ROI '{roi_name}'")
                
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
                
                # Ensure text remains within image boundaries
                text_x = max(0, min(text_x, width - text_width))
                text_y = max(text_height, min(text_y, height - baseline))

                # Draw text with same color as polygon
                cv2.putText(img, text, (text_x, text_y), font, font_scale, color, text_thickness, cv2.LINE_AA)
                
            successful_rois += 1

        except Exception as e:
            print(f"Error processing ROI '{roi_name}': {str(e)}")
            # Continue with other ROIs even if one fails
    
    print(f"Successfully overlaid {successful_rois} out of {total_rois} ROIs")

    # Convert the image from BGR to RGB before returning
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img_rgb