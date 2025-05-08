import cv2
import numpy as np
import yaml
import base64
from typing import Dict, List, Tuple, Optional, Union, Any
import os
from io import BytesIO
import gc  # Garbage collector for explicit memory management

class ImageProcessor:
    def __init__(self, image_path: str = None, downscale_factor: float = 1.0):
        """
        Initialize the image processor with memory efficiency in mind.
        
        Args:
            image_path: Optional path to an image file
            downscale_factor: Factor to downscale images (1.0 = original size, 0.5 = half size)
                              Use this to reduce memory usage for large images
        """
        self.image = None
        self.original_image = None
        self.rois = {}  # Store ROIs for later use
        self.roi_masks = {}  # Store masks for each ROI
        self.downscale_factor = max(0.1, min(1.0, downscale_factor))  # Clamp between 0.1 and 1.0
        self._image_shape = None  # Store shape without keeping the image in memory
        
        # Store derived bands/indices
        self.chromatic_coords = {
            'r': None,
            'g': None,
            'b': None,
            'composite': None
        }
        self.rgb_bands = {
            'r': None,
            'g': None,
            'b': None
        }
        
        # Store ROI band statistics
        self.roi_band_stats = {}
        
        if image_path:
            self.load_image(image_path)
    
    def load_image(self, image_path: str, keep_original: bool = True) -> bool:
        """
        Load an image from the given file path with memory optimization.
        
        Args:
            image_path: Path to the image file
            keep_original: Whether to keep the original image in memory
                          Set to False for maximum memory efficiency
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(image_path):
            print(f"Error: File {image_path} not found")
            return False
            
        try:
            # Use IMREAD_REDUCED flags for initial memory saving on very large images
            if self.downscale_factor < 1.0:
                img = cv2.imread(image_path)
                if img is None:
                    print(f"Error: Could not read image from {image_path}")
                    return False
                
                # Resize for memory efficiency if downscale_factor is set
                height, width = img.shape[:2]
                new_height = int(height * self.downscale_factor)
                new_width = int(width * self.downscale_factor)
                self.image = cv2.resize(img, (new_width, new_height), 
                                      interpolation=cv2.INTER_AREA)
                
                # Store original dimensions for reference
                self._image_shape = (height, width)
                
                # Only keep original if explicitly requested
                if keep_original:
                    self.original_image = self.image.copy()
                else:
                    self.original_image = None
                    # Store shape before releasing image reference
                    self._image_shape = self.image.shape[:2]
            else:
                # Standard loading at full resolution
                self.image = cv2.imread(image_path)
                if self.image is None:
                    print(f"Error: Could not read image from {image_path}")
                    return False
                
                self._image_shape = self.image.shape[:2]
                
                if keep_original:
                    self.original_image = self.image.copy()
                else:
                    self.original_image = None
            
            # Reset derived bands
            for key in self.chromatic_coords:
                self.chromatic_coords[key] = None
            for key in self.rgb_bands:
                self.rgb_bands[key] = None
            
            # Force garbage collection
            gc.collect()
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def release_original(self) -> None:
        """
        Release the original image from memory to save RAM.
        Use this after applying all ROIs if you no longer need to reset.
        """
        if self.original_image is not None:
            self._image_shape = self.original_image.shape[:2]
            self.original_image = None
            gc.collect()
    
    def get_image(self, with_overlays: bool = True) -> Optional[np.ndarray]:
        """
        Get the current image, with memory-efficient handling.
        
        Args:
            with_overlays: Whether to include ROI overlays
            
        Returns:
            np.ndarray: Image with or without overlays, or None if no image loaded
        """
        if self.image is None:
            print("Error: No image loaded")
            return None
        
        if with_overlays:
            # Return without creating unnecessary copy
            return self.image
        else:
            if self.original_image is not None:
                return self.original_image
            else:
                print("Warning: Original image was released to save memory. Returning current image.")
                return self.image
    
    def create_thumbnail(self, max_size: Tuple[int, int] = (100, 100)) -> Optional[str]:
        """
        Create a thumbnail of the loaded image and return it as a base64-encoded string.
        
        Args:
            max_size: Maximum width and height of the thumbnail (width, height)
            
        Returns:
            str: Base64-encoded string representing the thumbnail image, or None if creation fails
        """
        if self.image is None:
            print("Error: No image loaded")
            return None
            
        try:
            # Use the current image (with or without overlays)
            img = self.image
                
            # Calculate the thumbnail size while maintaining aspect ratio
            h, w = img.shape[:2]
            max_w, max_h = max_size
            
            # Calculate new dimensions
            if h > w:
                new_h = max_h
                new_w = int(w * (max_h / h))
            else:
                new_w = max_w
                new_h = int(h * (max_w / w))
                
            # Resize the image
            thumbnail = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Convert from BGR to RGB
            thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', thumbnail)
            return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        except Exception as e:
            print(f"Error creating thumbnail: {str(e)}")
            return None
    
    def create_default_roi(self) -> None:
        """
        Create a default ROI (ROI_00) that covers the entire image or excludes the sky,
        with memory-efficient implementation.
        """
        if self.image is None:
            print("Error: No image loaded")
            return
        
        height, width = self.image.shape[:2]
        
        # Try to detect and exclude sky
        try:
            # Convert to HSV for better color segmentation
            hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
            
            # Process in smaller chunks to reduce memory usage
            chunk_height = min(500, height)  # Process 500 rows at a time
            top_third_height = height // 3
            sky_line = top_third_height  # Default if no sky found
            
            # First pass: quick check of top area for sky
            for start_y in range(0, top_third_height, chunk_height):
                end_y = min(start_y + chunk_height, top_third_height)
                hsv_chunk = hsv[start_y:end_y, :]
                
                # Blue sky: high hue, moderate-high saturation, high value
                sky_mask_blue = cv2.inRange(
                    hsv_chunk, 
                    np.array([90, 50, 150]), 
                    np.array([140, 255, 255])
                )
                
                # White/cloudy sky: low saturation, high value
                sky_mask_white = cv2.inRange(
                    hsv_chunk, 
                    np.array([0, 0, 180]), 
                    np.array([180, 50, 255])
                )
                
                # Combine masks
                sky_mask_chunk = cv2.bitwise_or(sky_mask_blue, sky_mask_white)
                
                # Check each row in the chunk
                for y_offset in range(0, end_y - start_y, 5):  # Check every 5 rows
                    y = start_y + y_offset
                    row_sum = np.sum(sky_mask_chunk[y_offset, :]) / 255
                    if row_sum > width * 0.3:  # If >30% of row is detected as sky
                        sky_line = y
                
                # Release chunk memory
                del hsv_chunk, sky_mask_blue, sky_mask_white, sky_mask_chunk
                gc.collect()
            
            # Add a buffer of 10% to avoid cutting off important features
            sky_line = int(min(sky_line * 1.1, height))
            
            # Create a rectangle that excludes the detected sky
            points = [[0, sky_line], [width-1, sky_line], [width-1, height-1], [0, height-1]]
            
        except Exception as e:
            print(f"Sky detection failed: {e}. Using full frame as default ROI.")
            # Fallback: use the entire image
            points = [[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]]
        
        # Create the default ROI
        self.overlay_polygon(
            points=points,
            color=[0, 255, 255],  # Yellow
            thickness=3,
            roi_name="ROI_00",
            alpha=0.2
        )
        
        # Force garbage collection
        gc.collect()
        
        print(f"Created default ROI_00 with points: {points}")
    
    def overlay_polygon(self, points: List[List[int]], 
                       color: List[int] = [0, 255, 0], 
                       thickness: int = 2,
                       closed: bool = True,
                       roi_name: Optional[str] = None,
                       alpha: float = 0.3) -> None:
        """
        Overlay a single polygon on the current image.
        Memory-efficient implementation.
        
        Args:
            points: List of [x, y] coordinates defining the polygon
            color: BGR color tuple (default: green)
            thickness: Line thickness (default: 2)
            closed: Whether to close the polygon (default: True)
            roi_name: Optional name to identify this ROI
            alpha: Transparency for filled regions (0-1)
        """
        if self.image is None:
            print("Error: No image loaded")
            return
            
        points_array = np.array(points, dtype=np.int32)
        
        # Store ROI if name provided - just store the data, not the mask yet
        if roi_name:
            self.rois[roi_name] = {
                'points': points,
                'color': color,
                'thickness': thickness,
                'closed': closed,
                'alpha': alpha
            }
            
            # Create mask when needed (lazily)
            if alpha > 0:
                # For filled polygons, we need the mask right away
                mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [points_array], 255)
                self.roi_masks[roi_name] = mask
        
        # Draw the polygon outline directly on the image
        cv2.polylines(self.image, [points_array], closed, color, thickness)
        
        # Optional: fill polygon with semi-transparent color
        if alpha > 0:
            # Use a more memory-efficient blending approach
            # Get the mask (created above if roi_name is provided)
            if roi_name and roi_name in self.roi_masks:
                mask = self.roi_masks[roi_name]
            else:
                mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [points_array], 255)
                if roi_name:
                    self.roi_masks[roi_name] = mask
            
            # Apply color to the masked region
            colored_region = np.zeros_like(self.image)
            colored_region[mask > 0] = color
            
            # Blend using weighted addition
            # This avoids creating a full copy of the image
            cv2.addWeighted(
                colored_region, alpha,
                self.image, 1 - alpha,
                0, self.image
            )
            
            # Clean up temporary arrays
            del colored_region
            
            # If we don't need the mask for later, release it
            if not roi_name:
                del mask
                gc.collect()
    
    def _create_roi_mask(self, roi_name: str) -> Optional[np.ndarray]:
        """
        Create mask for an ROI on-demand if it doesn't exist.
        This is to avoid storing masks for ROIs that aren't analyzed.
        
        Args:
            roi_name: Name of the ROI
            
        Returns:
            np.ndarray: The mask or None if ROI not found
        """
        if roi_name not in self.rois:
            return None
            
        if roi_name in self.roi_masks:
            return self.roi_masks[roi_name]
            
        # Create the mask since it doesn't exist
        points = self.rois[roi_name]['points']
        points_array = np.array(points, dtype=np.int32)
        
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points_array], 255)
        
        # Cache it for future use
        self.roi_masks[roi_name] = mask
        return mask
    
    def overlay_polygons_from_dict(self, rois_dict: Dict = None, enable_overlay: bool = True) -> None:
        """
        Overlay multiple polygons from a dictionary of ROIs.
        If no ROIs are provided, create a default one.
        
        Args:
            rois_dict: Dictionary containing ROI definitions
            enable_overlay: Whether to actually draw the overlays
        """
        if self.image is None:
            print("Error: No image loaded")
            return
            
        # Reset image to original state
        self.reset_image()
        
        # Clear previous ROI data
        self.rois.clear()
        self.roi_masks.clear()
        self.roi_band_stats.clear()
        gc.collect()
        
        if not enable_overlay:
            return
        
        # If no ROIs provided or empty dict, create default ROI
        if not rois_dict or len(rois_dict) == 0:
            self.create_default_roi()
            return
            
        for roi_name, roi_data in rois_dict.items():
            points = roi_data.get('points', [])
            color = roi_data.get('color', [0, 255, 0])
            thickness = roi_data.get('thickness', 2)
            alpha = roi_data.get('alpha', 0.3)
            self.overlay_polygon(points, color, thickness, True, roi_name, alpha)
    
    def overlay_polygons_from_yaml(self, yaml_path: Optional[str] = None, enable_overlay: bool = True) -> bool:
        """
        Load ROIs from a YAML file and overlay them on the image.
        If no YAML file is provided or it contains no ROIs, create a default one.
        
        Args:
            yaml_path: Path to the YAML file containing ROI definitions
            enable_overlay: Whether to actually draw the overlays
            
        Returns:
            bool: True if successful, False otherwise
        """
        # If no YAML file provided, create default ROI
        if not yaml_path:
            if enable_overlay:
                self.create_default_roi()
            return True
            
        if not os.path.exists(yaml_path):
            print(f"Error: YAML file {yaml_path} not found")
            if enable_overlay:
                self.create_default_roi()
            return False
            
        try:
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
                
            if 'rois' not in data or not data['rois']:
                print("No ROIs found in YAML file, creating default ROI")
                if enable_overlay:
                    self.create_default_roi()
                return True
                
            self.overlay_polygons_from_dict(data['rois'], enable_overlay)
            return True
        except Exception as e:
            print(f"Error loading ROIs from YAML: {e}")
            if enable_overlay:
                self.create_default_roi()
            return False
    
    def reset_image(self) -> None:
        """Reset the image to its original state without overlays."""
        if self.original_image is not None:
            # Use direct assignment instead of copy() to avoid memory spike
            if self.image is not None:
                del self.image
            self.image = self.original_image.copy()
            gc.collect()
        else:
            print("Warning: Original image was released to save memory. Cannot reset.")
    
    def show(self, window_name: str = "Image", wait: bool = True) -> None:
        """
        Display the current image.
        
        Args:
            window_name: Name of the display window
            wait: Whether to wait for a key press
        """
        if self.image is None:
            print("Error: No image loaded")
            return
            
        cv2.imshow(window_name, self.image)
        if wait:
            cv2.waitKey(0)
            cv2.destroyWindow(window_name)
    
    def save(self, output_path: str, quality: int = 95) -> bool:
        """
        Save the current image to a file.
        
        Args:
            output_path: Path where the image should be saved
            quality: JPEG quality (0-100) if saving as JPEG
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.image is None:
            print("Error: No image loaded")
            return False
            
        try:
            # Get file extension
            _, ext = os.path.splitext(output_path)
            ext = ext.lower()
            
            if ext == '.jpg' or ext == '.jpeg':
                # Use compression params for JPEG
                params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                success = cv2.imwrite(output_path, self.image, params)
            else:
                success = cv2.imwrite(output_path, self.image)
                
            return success
        except Exception as e:
            print(f"Error saving image: {e}")
            return False
    
    def compute_chromatic_coordinates(self, force_recompute: bool = False) -> Dict[str, np.ndarray]:
        """
        Compute chromatic coordinates r, g, b from RGB values.
        
        Chromatic coordinates are defined as:
        r = R / (R + G + B)
        g = G / (R + G + B)
        b = B / (R + G + B)
        
        Args:
            force_recompute: Whether to force recomputation even if already available
            
        Returns:
            Dict: Dictionary containing 'r', 'g', 'b' bands and 'composite' (BGR)
        """
        # Return cached version if available and not forcing recompute
        if not force_recompute and all(self.chromatic_coords.values()):
            return self.chromatic_coords
            
        if self.image is None:
            print("Error: No image loaded")
            return None
            
        # Get RGB channels from BGR image
        img_to_use = self.original_image if self.original_image is not None else self.image
        
        # Process in chunks to save memory for large images
        height, width = img_to_use.shape[:2]
        r_chrom = np.zeros((height, width), dtype=np.float32)
        g_chrom = np.zeros((height, width), dtype=np.float32)
        b_chrom = np.zeros((height, width), dtype=np.float32)
        
        chunk_size = min(500, height)  # Process 500 rows at a time
        for start_y in range(0, height, chunk_size):
            end_y = min(start_y + chunk_size, height)
            
            # Get chunk
            chunk = img_to_use[start_y:end_y, :]
            
            # Split BGR channels
            b, g, r = cv2.split(chunk)
            
            # Convert to float32 for calculations
            b = b.astype(np.float32)
            g = g.astype(np.float32)
            r = r.astype(np.float32)
            
            # Calculate RGB sum
            rgb_sum = r + g + b
            
            # Avoid division by zero
            rgb_sum[rgb_sum == 0] = 1.0
            
            # Calculate chromatic coordinates
            r_chrom[start_y:end_y, :] = r / rgb_sum
            g_chrom[start_y:end_y, :] = g / rgb_sum
            b_chrom[start_y:end_y, :] = b / rgb_sum
            
            # Clean up
            del chunk, b, g, r, rgb_sum
            gc.collect()
        
        # Store results
        self.chromatic_coords['r'] = r_chrom
        self.chromatic_coords['g'] = g_chrom
        self.chromatic_coords['b'] = b_chrom
        
        # Create a composite image (BGR for visualization)
        # Scale to 0-255
        r_vis = np.zeros((height, width), dtype=np.uint8)
        g_vis = np.zeros((height, width), dtype=np.uint8)
        b_vis = np.zeros((height, width), dtype=np.uint8)
        
        # Scale each band to 0-255
        cv2.normalize(r_chrom, r_vis, 0, 255, cv2.NORM_MINMAX)
        cv2.normalize(g_chrom, g_vis, 0, 255, cv2.NORM_MINMAX)
        cv2.normalize(b_chrom, b_vis, 0, 255, cv2.NORM_MINMAX)
        
        # Create BGR composite
        self.chromatic_coords['composite'] = cv2.merge([b_vis, g_vis, r_vis])
        
        return self.chromatic_coords
    
    def get_rgb_bands(self, force_recompute: bool = False) -> Dict[str, np.ndarray]:
        """
        Extract individual RGB bands from the image.
        
        Args:
            force_recompute: Whether to force recomputation even if already available
            
        Returns:
            Dict: Dictionary containing 'r', 'g', 'b' bands
        """
        # Return cached version if available and not forcing recompute
        if not force_recompute and all(self.rgb_bands.values()):
            return self.rgb_bands
            
        if self.image is None:
            print("Error: No image loaded")
            return None
            
        # Get RGB channels from BGR image
        img_to_use = self.original_image if self.original_image is not None else self.image
        
        # Split BGR channels
        b, g, r = cv2.split(img_to_use)
        
        # Store results
        self.rgb_bands['r'] = r
        self.rgb_bands['g'] = g
        self.rgb_bands['b'] = b
        
        return self.rgb_bands
    
    def get_band_image(self, band_type: str, band_name: str) -> Optional[np.ndarray]:
        """
        Get a specific band as an image.
        
        Args:
            band_type: Type of band - 'rgb' or 'chromatic'
            band_name: Name of the band - 'r', 'g', 'b', or 'composite' (for chromatic)
            
        Returns:
            np.ndarray: Image representing the band or None if not available
        """
        if band_type == 'rgb':
            if not all(self.rgb_bands.values()):
                self.get_rgb_bands()
                
            if band_name in self.rgb_bands:
                # Return as grayscale image
                return self.rgb_bands[band_name]
            else:
                print(f"Error: Invalid RGB band name '{band_name}'")
                return None
                
        elif band_type == 'chromatic':
            if not all(self.chromatic_coords.values()):
                self.compute_chromatic_coordinates()
                
            if band_name in self.chromatic_coords:
                if band_name == 'composite':
                    # Return as color image
                    return self.chromatic_coords[band_name]
                else:
                    # Create a normalized visualization of the chromatic band
                    band = self.chromatic_coords[band_name]
                    vis = np.zeros(band.shape, dtype=np.uint8)
                    cv2.normalize(band, vis, 0, 255, cv2.NORM_MINMAX)
                    return vis
            else:
                print(f"Error: Invalid chromatic band name '{band_name}'")
                return None
        else:
            print(f"Error: Invalid band type '{band_type}'")
            return None
    
    def save_band_image(self, band_type: str, band_name: str, output_path: str) -> bool:
        """
        Save a specific band as an image file.
        
        Args:
            band_type: Type of band - 'rgb' or 'chromatic'
            band_name: Name of the band - 'r', 'g', 'b', or 'composite' (for chromatic)
            output_path: Path to save the image
            
        Returns:
            bool: True if successful, False otherwise
        """
        band_image = self.get_band_image(band_type, band_name)
        if band_image is None:
            return False
            
        try:
            cv2.imwrite(output_path, band_image)
            return True
        except Exception as e:
            print(f"Error saving band image: {e}")
            return False
    
    def analyze_roi_bands(self, roi_name: str, 
                         skip_chromatic: bool = False, 
                         skip_rgb: bool = False) -> Dict[str, Any]:
        """
        Analyze RGB and chromatic coordinates for an ROI.
        
        Args:
            roi_name: Name of the ROI to analyze
            skip_chromatic: Whether to skip chromatic coordinate analysis
            skip_rgb: Whether to skip RGB band analysis
            
        Returns:
            Dict: Analysis results with statistics for each band
        """
        # Create mask if needed
        mask = self._create_roi_mask(roi_name)
        if mask is None:
            print(f"Error: ROI '{roi_name}' not found")
            return {}
        
        result = {}
        
        # Get band data
        if not skip_rgb:
            if not all(self.rgb_bands.values()):
                self.get_rgb_bands()
            
            # Analyze RGB bands
            rgb_result = {}
            for band_name, band in self.rgb_bands.items():
                # Get only pixels within the ROI
                roi_pixels = band[mask > 0]
                
                if len(roi_pixels) == 0:
                    rgb_result[band_name] = {
                        'mean': 0, 'std': 0, 'min': 0, 'max': 0,
                        'sum': 0, 'pixels': 0
                    }
                    continue
                
                rgb_result[band_name] = {
                    'mean': float(np.mean(roi_pixels)),
                    'std': float(np.std(roi_pixels)),
                    'min': float(np.min(roi_pixels)),
                    'max': float(np.max(roi_pixels)),
                    'sum': float(np.sum(roi_pixels)),  # Added sum of all pixel values
                    'pixels': len(roi_pixels)
                }
                
                # Clean up
                del roi_pixels
                gc.collect()
                
            result['rgb'] = rgb_result
        
        # Analyze chromatic coordinates
        if not skip_chromatic:
            if not all(v is not None for v in self.chromatic_coords.values() 
                      if v != self.chromatic_coords['composite']):
                self.compute_chromatic_coordinates()
            
            chrom_result = {}
            for band_name, band in self.chromatic_coords.items():
                if band_name == 'composite':
                    continue  # Skip composite image
                
                # Get only pixels within the ROI
                roi_pixels = band[mask > 0]
                
                if len(roi_pixels) == 0:
                    chrom_result[band_name] = {
                        'mean': 0, 'std': 0, 'min': 0, 'max': 0,
                        'sum': 0, 'pixels': 0
                    }
                    continue
                
                chrom_result[band_name] = {
                    'mean': float(np.mean(roi_pixels)),
                    'std': float(np.std(roi_pixels)),
                    'min': float(np.min(roi_pixels)),
                    'max': float(np.max(roi_pixels)),
                    'sum': float(np.sum(roi_pixels)),  # Added sum of all pixel values
                    'pixels': len(roi_pixels)
                }
                
                # Clean up
                del roi_pixels
                gc.collect()
                
            result['chromatic'] = chrom_result
        
        # Store results for this ROI
        self.roi_band_stats[roi_name] = result
        
        return result
    
    def analyze_all_roi_bands(self, 
                            skip_list: List[str] = None, 
                            skip_chromatic: bool = False, 
                            skip_rgb: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Analyze RGB and chromatic coordinates for all ROIs.
        
        Args:
            skip_list: List of ROI names to skip (e.g., poor quality flags)
            skip_chromatic: Whether to skip chromatic coordinate analysis
            skip_rgb: Whether to skip RGB band analysis
            
        Returns:
            Dict: Analysis results for all ROIs
        """
        if not self.rois:
            print("No ROIs defined")
            return {}
        
        # Clear previous results
        self.roi_band_stats.clear()
        
        # Create skip set for faster lookup
        skip_set = set(skip_list) if skip_list else set()
        
        # Calculate bands once for efficiency
        if not skip_rgb:
            self.get_rgb_bands()
        if not skip_chromatic:
            self.compute_chromatic_coordinates()
        
        # Analyze each ROI
        for roi_name in self.rois.keys():
            if roi_name in skip_set:
                print(f"Skipping ROI '{roi_name}' as requested")
                continue
                
            self.analyze_roi_bands(roi_name, skip_chromatic, skip_rgb)
        
        return self.roi_band_stats
    
    def analyze_roi(self, roi_name: str, 
                   compute_histograms: bool = True,
                   compute_vegetation: bool = True) -> Dict[str, Any]:
        """
        Analyze a specific ROI to extract useful information.
        Memory-efficient implementation with selectable features.
        
        Args:
            roi_name: Name of the ROI to analyze
            compute_histograms: Whether to compute channel histograms (memory intensive)
            compute_vegetation: Whether to compute vegetation indices
            
        Returns:
            Dict: Analysis results including mean color, histograms, etc.
        """
        # Create mask if needed
        mask = self._create_roi_mask(roi_name)
        if mask is None:
            print(f"Error: ROI '{roi_name}' not found")
            return {}
        
        result = {}
        
        # Reference the original or current image
        img_to_analyze = self.original_image if self.original_image is not None else self.image
        
        # Calculate mean color within ROI (low memory usage)
        mean_val = cv2.mean(img_to_analyze, mask=mask)
        result['mean_color'] = mean_val[:3]  # BGR
        
        # Calculate sum of pixel values
        # Process in chunks to save memory
        height, width = img_to_analyze.shape[:2]
        chunk_size = min(500, height)
        
        # Initialize sums for each channel
        pixel_sums = [0, 0, 0]  # BGR order
        pixel_count = 0
        
        for start_y in range(0, height, chunk_size):
            end_y = min(start_y + chunk_size, height)
            
            # Extract mask for this chunk
            mask_chunk = mask[start_y:end_y, :]
            
            # Skip if no pixels in this chunk
            if cv2.countNonZero(mask_chunk) == 0:
                continue
                
            # Get image chunk
            img_chunk = img_to_analyze[start_y:end_y, :]
            
            # Apply mask
            masked_chunk = cv2.bitwise_and(img_chunk, img_chunk, mask=mask_chunk)
            
            # Split channels
            b, g, r = cv2.split(masked_chunk)
            
            # Sum pixel values
            pixel_sums[0] += np.sum(b)
            pixel_sums[1] += np.sum(g)
            pixel_sums[2] += np.sum(r)
            
            # Count pixels in this chunk
            pixel_count += cv2.countNonZero(mask_chunk)
            
            # Clean up
            del mask_chunk, img_chunk, masked_chunk, b, g, r
            gc.collect()
        
        result['pixel_sum'] = {
            'blue': float(pixel_sums[0]),
            'green': float(pixel_sums[1]),
            'red': float(pixel_sums[2]),
            'total': float(sum(pixel_sums)),
            'pixel_count': pixel_count
        }
        
        # Calculate histograms if requested (higher memory usage)
        if compute_histograms:
            # Calculate histograms for each channel
            channels = cv2.split(img_to_analyze)  # Split channels
            histograms = {}
            
            for i, channel_name in enumerate(['blue', 'green', 'red']):
                hist = cv2.calcHist([channels[i]], [0], mask, [256], [0, 256])
                histograms[channel_name] = hist.flatten().tolist()
                
            result['histograms'] = histograms
            
            # Clean up
            del channels
            gc.collect()
        
        # Calculate ROI area (low memory usage)
        result['area_pixels'] = cv2.countNonZero(mask)
        
        # Get ROI bounding rectangle (low memory usage)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = cv2.boundingRect(contours[0])
            result['bounding_rect'] = {
                'x': x, 'y': y, 'width': w, 'height': h,
                'aspect_ratio': w / h if h > 0 else 0
            }
        
        # Calculate vegetation indices if requested
        if compute_vegetation:
            try:
                # Process in chunks if the image is large
                height, width = mask.shape
                chunk_size = min(500, height)  # Process 500 rows at a time
                veg_values = []
                
                # Extract BGR channels only for masked regions to save memory
                for start_y in range(0, height, chunk_size):
                    end_y = min(start_y + chunk_size, height)
                    
                    # Extract only the part of the mask for this chunk
                    mask_chunk = mask[start_y:end_y, :]
                    
                    # Skip chunks with no mask pixels
                    if cv2.countNonZero(mask_chunk) == 0:
                        continue
                    
                    # Extract only the image chunk we need
                    img_chunk = img_to_analyze[start_y:end_y, :]
                    
                    # Apply mask to image chunk
                    masked_chunk = cv2.bitwise_and(img_chunk, img_chunk, mask=mask_chunk)
                    
                    # Extract BGR channels
                    b, g, r = cv2.split(masked_chunk)
                    
                    # Convert to float for calculations
                    b = b.astype(float)
                    g = g.astype(float)
                    r = r.astype(float)
                    
                    # Simple vegetation index (Green - Red) / (Green + Red)
                    epsilon = 1e-10  # To avoid division by zero
                    denominator = g + r
                    
                    # Only calculate where denominator is not zero and mask is applied
                    valid_pixels = (denominator > epsilon) & (mask_chunk > 0)
                    
                    if np.any(valid_pixels):
                        chunk_veg_values = (g[valid_pixels] - r[valid_pixels]) / (denominator[valid_pixels])
                        veg_values.extend(chunk_veg_values)
                    
                    # Clean up chunk data
                    del mask_chunk, img_chunk, masked_chunk, b, g, r, denominator, valid_pixels
                    gc.collect()
                
                # Calculate statistics if we have values
                if veg_values:
                    veg_values = np.array(veg_values)
                    result['vegetation_index'] = {
                        'mean': float(np.mean(veg_values)),
                        'min': float(np.min(veg_values)),
                        'max': float(np.max(veg_values)),
                        'std': float(np.std(veg_values)),
                        'sum': float(np.sum(veg_values))  # Added sum of vegetation index values
                    }
                    
                    # Clean up
                    del veg_values
                    gc.collect()
            except Exception as e:
                print(f"Error calculating vegetation indices: {e}")
        
        return result
    
    def extract_roi(self, roi_name: str) -> Optional[np.ndarray]:
        """
        Extract a specific ROI as a separate image.
        Memory-efficient implementation.
        
        Args:
            roi_name: Name of the ROI to extract
            
        Returns:
            np.ndarray: Extracted ROI image, or None if ROI not found
        """
        # Create mask if needed
        mask = self._create_roi_mask(roi_name)
        if mask is None:
            print(f"Error: ROI '{roi_name}' not found")
            return None
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(mask)
        
        # Extract the masked region directly without creating intermediate copies
        img_to_extract = self.original_image if self.original_image is not None else self.image
        
        # Create mask subset for the bounding rectangle
        mask_roi = mask[y:y+h, x:x+w]
        
        # Extract image region
        img_roi = img_to_extract[y:y+h, x:x+w].copy()
        
        # Apply mask (set non-mask pixels to zero)
        img_roi[mask_roi == 0] = 0
        
        return img_roi
    
    def export_roi_band_stats(self, output_path: str) -> bool:
        """
        Export ROI band statistics to a YAML file.
        
        Args:
            output_path: Path to save the YAML file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.roi_band_stats:
            print("No ROI band statistics available. Run analyze_all_roi_bands() first.")
            return False
            
        try:
            with open(output_path, 'w') as file:
                yaml.dump({'roi_band_stats': self.roi_band_stats}, file, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error exporting ROI band statistics: {e}")
            return False
    
    def process_batch(self, images_list: List[str], yaml_path: Optional[str] = None,
                     output_dir: str = None, enable_overlay: bool = True,
                     export_bands: bool = False, band_types: List[str] = None,
                     analyze_rois: bool = False, skip_list: List[str] = None) -> None:
        """
        Process multiple images in a memory-efficient way.
        
        Args:
            images_list: List of image paths to process
            yaml_path: Optional path to YAML file with ROI definitions
            output_dir: Directory to save processed images
            enable_overlay: Whether to draw ROI overlays
            export_bands: Whether to export band images
            band_types: List of band types to export (e.g. ['rgb-r', 'chromatic-b', 'chromatic-composite'])
            analyze_rois: Whether to analyze ROIs and export statistics
            skip_list: List of ROI names to skip analysis
        """
        # Create output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Load ROI definitions once
        rois_dict = None
        if yaml_path and os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r') as file:
                    data = yaml.safe_load(file)
                if 'rois' in data:
                    rois_dict = data['rois']
            except Exception as e:
                print(f"Error loading ROIs from YAML: {e}")
        
        # Process each image
        for img_path in images_list:
            try:
                # Get base filename without extension
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                
                # Clear any previous state
                self.image = None
                self.original_image = None
                self.rois.clear()
                self.roi_masks.clear()
                self.roi_band_stats.clear()
                for key in self.chromatic_coords:
                    self.chromatic_coords[key] = None
                for key in self.rgb_bands:
                    self.rgb_bands[key] = None
                gc.collect()
                
                print(f"Processing {img_path}...")
                
                # Load image (keep original since we need it for band calculations)
                if not self.load_image(img_path, keep_original=True):
                    continue
                
                # Apply ROIs
                if rois_dict:
                    self.overlay_polygons_from_dict(rois_dict, enable_overlay)
                else:
                    if enable_overlay:
                        self.create_default_roi()
                
                # Export band images if requested
                if export_bands and output_dir:
                    band_dir = os.path.join(output_dir, "bands")
                    if not os.path.exists(band_dir):
                        os.makedirs(band_dir)
                        
                    # Process requested band types
                    if not band_types:
                        # Default: export all bands
                        band_types = [
                            'rgb-r', 'rgb-g', 'rgb-b', 
                            'chromatic-r', 'chromatic-g', 'chromatic-b', 'chromatic-composite'
                        ]
                    
                    for band_type in band_types:
                        try:
                            band_parts = band_type.split('-')
                            if len(band_parts) != 2:
                                print(f"Invalid band type format: {band_type}")
                                continue
                                
                            type_name, band_name = band_parts
                            
                            # Calculate bands if not already done
                            if type_name == 'rgb' and not all(self.rgb_bands.values()):
                                self.get_rgb_bands()
                            elif type_name == 'chromatic' and not all(v is not None for v in self.chromatic_coords.values() 
                                                                 if v != self.chromatic_coords['composite']):
                                self.compute_chromatic_coordinates()
                            
                            # Save band image
                            band_path = os.path.join(band_dir, f"{base_name}_{band_type}.png")
                            self.save_band_image(type_name, band_name, band_path)
                            print(f"Saved band image: {band_path}")
                        except Exception as e:
                            print(f"Error exporting band {band_type}: {e}")
                
                # Analyze ROIs if requested
                if analyze_rois and output_dir:
                    self.analyze_all_roi_bands(skip_list=skip_list)
                    
                    # Export ROI band statistics
                    stats_dir = os.path.join(output_dir, "statistics")
                    if not os.path.exists(stats_dir):
                        os.makedirs(stats_dir)
                        
                    stats_path = os.path.join(stats_dir, f"{base_name}_roi_stats.yaml")
                    self.export_roi_band_stats(stats_path)
                    print(f"Saved ROI statistics: {stats_path}")
                
                # Save the processed image with overlays
                if output_dir:
                    output_path = os.path.join(output_dir, f"{base_name}_processed.jpg")
                    self.save(output_path)
                    print(f"Saved processed image: {output_path}")
                    
                # Force cleanup
                gc.collect()
                
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
    
    def __del__(self):
        """
        Destructor to clean up resources.
        """
        # Release all image references
        self.image = None
        self.original_image = None
        self.rois.clear()
        self.roi_masks.clear()
        
        # Clear band data
        for key in self.chromatic_coords:
            self.chromatic_coords[key] = None
        for key in self.rgb_bands:
            self.rgb_bands[key] = None
            
        self.roi_band_stats.clear()
        gc.collect()


# Memory-efficient standalone function
def process_image_with_rois(image_path: str, 
                           yaml_path: Optional[str] = None,
                           rois_dict: Optional[Dict] = None,
                           output_path: Optional[str] = None,
                           show_image: bool = False,
                           enable_overlay: bool = True,
                           downscale_factor: float = 1.0,
                           keep_original: bool = False,
                           export_bands: bool = False,
                           band_types: List[str] = None,
                           output_dir: Optional[str] = None,
                           analyze_rois: bool = False,
                           skip_list: List[str] = None) -> Optional[np.ndarray]:
    """
    Process an image with optional ROI overlays and band analysis.
    Memory-efficient implementation.
    
    Args:
        image_path: Path to the image file
        yaml_path: Optional path to a YAML file containing ROI definitions
        rois_dict: Optional dictionary of ROIs to overlay
        output_path: Optional path to save the resulting image
        show_image: Whether to display the image
        enable_overlay: Whether to draw ROI overlays
        downscale_factor: Factor to reduce image size for memory savings
        keep_original: Whether to keep the original image in memory
        export_bands: Whether to export band images
        band_types: List of band types to export (e.g. ['rgb-r', 'chromatic-b'])
        output_dir: Directory to save band images and statistics
        analyze_rois: Whether to analyze ROIs and export statistics
        skip_list: List of ROI names to skip analysis
        
    Returns:
        np.ndarray: The processed image, or None if loading fails
    """
    processor = ImageProcessor(downscale_factor=downscale_factor)
    
    # We need to keep the original for band calculations
    need_original = export_bands or analyze_rois
    
    if not processor.load_image(image_path, keep_original=need_original or keep_original):
        return None
        
    # Load ROIs or create default if none provided
    if yaml_path:
        processor.overlay_polygons_from_yaml(yaml_path, enable_overlay)
    elif rois_dict:
        processor.overlay_polygons_from_dict(rois_dict, enable_overlay)
    else:
        # No ROIs provided - create default
        if enable_overlay:
            processor.create_default_roi()
    
    # Export band images if requested
    if export_bands and output_dir:
        band_dir = os.path.join(output_dir, "bands")
        if not os.path.exists(band_dir):
            os.makedirs(band_dir)
            
        # Process requested band types
        if not band_types:
            # Default: export all bands
            band_types = [
                'rgb-r', 'rgb-g', 'rgb-b', 
                'chromatic-r', 'chromatic-g', 'chromatic-b', 'chromatic-composite'
            ]
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        for band_type in band_types:
            try:
                band_parts = band_type.split('-')
                if len(band_parts) != 2:
                    print(f"Invalid band type format: {band_type}")
                    continue
                    
                type_name, band_name = band_parts
                
                # Calculate bands if not already done
                if type_name == 'rgb' and not all(processor.rgb_bands.values()):
                    processor.get_rgb_bands()
                elif type_name == 'chromatic' and not all(processor.chromatic_coords.values()):
                    processor.compute_chromatic_coordinates()
                
                # Save band image
                band_path = os.path.join(band_dir, f"{base_name}_{band_type}.png")
                processor.save_band_image(type_name, band_name, band_path)
                print(f"Saved band image: {band_path}")
            except Exception as e:
                print(f"Error exporting band {band_type}: {e}")
    
    # Analyze ROIs if requested
    if analyze_rois and output_dir:
        processor.analyze_all_roi_bands(skip_list=skip_list)
        
        # Export ROI band statistics
        stats_dir = os.path.join(output_dir, "statistics")
        if not os.path.exists(stats_dir):
            os.makedirs(stats_dir)
            
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        stats_path = os.path.join(stats_dir, f"{base_name}_roi_stats.yaml")
        processor.export_roi_band_stats(stats_path)
        print(f"Saved ROI statistics: {stats_path}")
    
    if show_image:
        processor.show()
        
    if output_path:
        processor.save(output_path)
    
    # Get the image and then clean up
    result_image = processor.get_image(with_overlays=enable_overlay).copy()
    
    # Clean up
    del processor
    gc.collect()
    
    return result_image