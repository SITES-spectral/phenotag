"""
Memory-optimized image processor extending the base ImageProcessor.

This module integrates with the memory manager to provide better
memory usage tracking and optimization when processing large images.
"""

import cv2
import numpy as np
import yaml
from typing import Dict, List, Tuple, Optional, Union, Any
import os
import gc
import time
import logging
from pathlib import Path

from phenotag.processors.image_processor import ImageProcessor
from phenotag.memory.memory_manager import (
    memory_manager, 
    MemoryTracker, 
    track_memory,
    estimate_memory_requirements
)

# Configure logging
logger = logging.getLogger(__name__)


class MemoryOptimizedProcessor(ImageProcessor):
    """
    Memory-optimized version of ImageProcessor that integrates with the 
    MemoryManager for better tracking and optimization of memory usage.
    """
    
    def __init__(self, image_path: str = None, downscale_factor: float = 1.0, 
                 memory_threshold_mb: float = 1000.0):
        """
        Initialize the memory-optimized image processor.
        
        Args:
            image_path: Optional path to an image file
            downscale_factor: Factor to downscale images (1.0 = original size, 0.5 = half size)
                              Use this to reduce memory usage for large images
            memory_threshold_mb: Memory threshold in MB for automatic downscaling
        """
        # Initialize the base class
        super().__init__(image_path=None, downscale_factor=downscale_factor)
        
        # Memory management settings
        self.memory_threshold_mb = memory_threshold_mb
        self._image_cache_key = None
        self._auto_downscale = True
        
        # Register with memory manager for tracking
        memory_manager.track_object(self, f"ImageProcessor-{id(self)}")
        
        # Load image if provided (using our memory-optimized version)
        if image_path:
            self.load_image(image_path)
    
    @track_memory("ImageProcessor.load_image")
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
            logger.error(f"File {image_path} not found")
            return False
            
        try:
            # Check if the image is already in memory cache
            cache_key = f"image:{image_path}:{self.downscale_factor}"
            self._image_cache_key = cache_key
            
            cached_img = memory_manager.get_from_cache(cache_key)
            if cached_img is not None:
                logger.debug(f"Using cached image for {image_path}")
                self.image = cached_img
                
                if keep_original:
                    self.original_image = self.image.copy()
                else:
                    self.original_image = None
                    self._image_shape = self.image.shape[:2]
                    
                # Reset derived bands
                self._reset_band_data()
                return True
            
            # Not cached, load the image
            logger.debug(f"Loading image from {image_path}")
            
            # First get image dimensions without loading full image
            img_header = cv2.imread(image_path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_REDUCED_GRAYSCALE_8)
            if img_header is None:
                logger.error(f"Could not read image header from {image_path}")
                return False
            
            original_height, original_width = img_header.shape[:2]
            estimated_channels = 3  # Assume RGB
            
            # Estimate memory requirements
            mem_estimate = estimate_memory_requirements({
                'width': original_width,
                'height': original_height,
                'channels': estimated_channels,
                'dtype': 'uint8'
            })
            
            logger.debug(
                f"Estimated memory for {image_path}: {mem_estimate['with_processing_mb']:.1f}MB"
            )
            
            # Check if we need to adjust downscale factor based on memory threshold
            current_memory = memory_manager.monitor.get_memory_usage()
            available_memory_mb = (
                current_memory['system_total'] * (1 - current_memory['system_percent'] / 100)
            )
            
            effective_downscale = self.downscale_factor
            
            # Auto-downscale if enabled and memory requirements are high
            if (self._auto_downscale and 
                mem_estimate['with_processing_mb'] > self.memory_threshold_mb and
                mem_estimate['with_processing_mb'] > available_memory_mb * 0.5):
                
                # Calculate required downscale factor
                target_memory_mb = min(self.memory_threshold_mb, available_memory_mb * 0.5)
                required_downscale = (
                    target_memory_mb / mem_estimate['with_processing_mb']
                ) ** 0.5  # Square root for 2D image
                
                # Limit to reasonable values (0.1 to 1.0)
                effective_downscale = max(0.1, min(self.downscale_factor, required_downscale))
                
                if effective_downscale < self.downscale_factor:
                    logger.warning(
                        f"Auto-downscaling image to {effective_downscale:.2f} "
                        f"(from {self.downscale_factor:.2f}) to fit memory constraints"
                    )
            
            # Now load the full image
            with MemoryTracker(f"Reading image {Path(image_path).name}"):
                # Use reduced reading for very large images
                if effective_downscale < 0.25:
                    # Use reduced flag for significant downscaling
                    flags = cv2.IMREAD_COLOR
                    if effective_downscale < 0.125:
                        flags |= cv2.IMREAD_REDUCED_COLOR_8
                    elif effective_downscale < 0.25:
                        flags |= cv2.IMREAD_REDUCED_COLOR_4
                        
                    img = cv2.imread(image_path, flags)
                    if img is None:
                        logger.error(f"Could not read image from {image_path}")
                        return False
                    
                    # May need additional resizing
                    height, width = img.shape[:2]
                    target_height = int(original_height * effective_downscale)
                    target_width = int(original_width * effective_downscale)
                    
                    # Only resize if significantly different from target
                    if (abs(height - target_height) > 10 or 
                        abs(width - target_width) > 10):
                        self.image = cv2.resize(
                            img, (target_width, target_height),
                            interpolation=cv2.INTER_AREA
                        )
                    else:
                        self.image = img
                else:
                    # Normal loading for modest downscaling
                    img = cv2.imread(image_path)
                    if img is None:
                        logger.error(f"Could not read image from {image_path}")
                        return False
                    
                    # Apply downscaling if needed
                    if effective_downscale < 1.0:
                        height, width = img.shape[:2]
                        new_height = int(height * effective_downscale)
                        new_width = int(width * effective_downscale)
                        self.image = cv2.resize(
                            img, (new_width, new_height),
                            interpolation=cv2.INTER_AREA
                        )
                    else:
                        self.image = img
            
            # Store original dimensions
            self._image_shape = (original_height, original_width)
            
            # Store effective downscale factor
            self.downscale_factor = effective_downscale
            
            # Track how much memory this image uses
            image_size_mb = (
                self.image.shape[0] * self.image.shape[1] * 
                self.image.shape[2] * self.image.itemsize / (1024 * 1024)
            )
            
            # Add to cache
            memory_manager.add_to_cache(cache_key, self.image, image_size_mb)
            
            # Only keep original if explicitly requested
            if keep_original:
                self.original_image = self.image.copy()
            else:
                self.original_image = None
                self._image_shape = self.image.shape[:2]
            
            # Reset derived bands
            self._reset_band_data()
            
            # Force garbage collection
            gc.collect()
            return True
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return False
    
    def _reset_band_data(self) -> None:
        """Reset all derived band data."""
        for key in self.chromatic_coords:
            self.chromatic_coords[key] = None
        for key in self.rgb_bands:
            self.rgb_bands[key] = None
    
    @track_memory("ImageProcessor.release_original")
    def release_original(self) -> None:
        """
        Release the original image from memory to save RAM.
        Use this after applying all ROIs if you no longer need to reset.
        """
        if self.original_image is not None:
            self._image_shape = self.original_image.shape[:2]
            self.original_image = None
            gc.collect()
            logger.debug("Released original image to save memory")
    
    @track_memory("ImageProcessor.compute_chromatic_coordinates")
    def compute_chromatic_coordinates(self, force_recompute: bool = False) -> Dict[str, np.ndarray]:
        """
        Compute chromatic coordinates r, g, b from RGB values with memory tracking.
        
        Memory-optimized version that:
        1. Processes images in chunks
        2. Tracks memory usage during computation
        3. Caches results for reuse
        
        Args:
            force_recompute: Whether to force recomputation even if already available
            
        Returns:
            Dict: Dictionary containing 'r', 'g', 'b' bands and 'composite' (BGR)
        """
        # First try the base implementation
        result = super().compute_chromatic_coordinates(force_recompute)
        
        # Cache the results if successful
        if result and all(result.values()):
            for band_name, band_data in result.items():
                if band_data is None:
                    continue
                    
                # Only cache the individual bands (r, g, b), not the composite
                if band_name != 'composite' and self._image_cache_key:
                    cache_key = f"{self._image_cache_key}:chromatic:{band_name}"
                    
                    # Estimate size
                    size_mb = (
                        band_data.shape[0] * band_data.shape[1] * 
                        band_data.itemsize / (1024 * 1024)
                    )
                    
                    # Add to cache
                    memory_manager.add_to_cache(cache_key, band_data, size_mb)
        
        return result
    
    @track_memory("ImageProcessor.get_rgb_bands")
    def get_rgb_bands(self, force_recompute: bool = False) -> Dict[str, np.ndarray]:
        """
        Extract individual RGB bands from the image with memory tracking.
        
        Args:
            force_recompute: Whether to force recomputation even if already available
            
        Returns:
            Dict: Dictionary containing 'r', 'g', 'b' bands
        """
        # First try to use cached values
        if not force_recompute and self._image_cache_key:
            bands_cached = True
            
            for band_name in ['r', 'g', 'b']:
                cache_key = f"{self._image_cache_key}:rgb:{band_name}"
                band_data = memory_manager.get_from_cache(cache_key)
                
                if band_data is not None:
                    self.rgb_bands[band_name] = band_data
                else:
                    bands_cached = False
                    break
            
            if bands_cached:
                logger.debug("Using cached RGB bands")
                return self.rgb_bands
        
        # Fall back to base implementation
        result = super().get_rgb_bands(force_recompute)
        
        # Cache the results
        if result:
            for band_name, band_data in result.items():
                if band_data is None:
                    continue
                    
                if self._image_cache_key:
                    cache_key = f"{self._image_cache_key}:rgb:{band_name}"
                    
                    # Estimate size
                    size_mb = (
                        band_data.shape[0] * band_data.shape[1] * 
                        band_data.itemsize / (1024 * 1024)
                    )
                    
                    # Add to cache
                    memory_manager.add_to_cache(cache_key, band_data, size_mb)
        
        return result
    
    @track_memory("ImageProcessor.analyze_roi_bands")
    def analyze_roi_bands(self, roi_name: str, 
                         skip_chromatic: bool = False, 
                         skip_rgb: bool = False) -> Dict[str, Any]:
        """
        Analyze RGB and chromatic coordinates for an ROI with memory tracking.
        
        Args:
            roi_name: Name of the ROI to analyze
            skip_chromatic: Whether to skip chromatic coordinate analysis
            skip_rgb: Whether to skip RGB band analysis
            
        Returns:
            Dict: Analysis results with statistics for each band
        """
        # Use cache for results if available
        cache_key = f"{self._image_cache_key}:roi_stats:{roi_name}"
        cached_result = memory_manager.get_from_cache(cache_key)
        
        if cached_result is not None:
            logger.debug(f"Using cached ROI analysis for {roi_name}")
            return cached_result
        
        # Get result from base implementation
        result = super().analyze_roi_bands(roi_name, skip_chromatic, skip_rgb)
        
        # Cache the result
        if result and self._image_cache_key:
            memory_manager.add_to_cache(cache_key, result)
            
        return result
    
    @track_memory("ImageProcessor.process_batch")
    def process_batch(self, images_list: List[str], yaml_path: Optional[str] = None,
                     output_dir: str = None, enable_overlay: bool = True,
                     export_bands: bool = False, band_types: List[str] = None,
                     analyze_rois: bool = False, skip_list: List[str] = None) -> None:
        """
        Process multiple images in a memory-efficient way with tracking.
        
        Args:
            images_list: List of image paths to process
            yaml_path: Optional path to YAML file with ROI definitions
            output_dir: Directory to save processed images
            enable_overlay: Whether to draw ROI overlays
            export_bands: Whether to export band images
            band_types: List of band types to export (e.g. ['rgb-r', 'chromatic-b'])
            analyze_rois: Whether to analyze ROIs and export statistics
            skip_list: List of ROI names to skip analysis
        """
        # Start memory monitoring before batch processing
        memory_manager.start_memory_monitoring(
            interval=30.0,
            threshold_mb=self.memory_threshold_mb
        )
        
        try:
            # Use base implementation with memory tracking
            super().process_batch(
                images_list, yaml_path, output_dir, enable_overlay,
                export_bands, band_types, analyze_rois, skip_list
            )
        finally:
            # Stop monitoring when done
            memory_manager.stop_memory_monitoring()
            
            # Log memory stats
            memory_manager.log_memory_stats("Batch processing complete")
            
            # Clear cache after batch processing
            memory_manager.clear_cache()
    
    def __del__(self):
        """
        Destructor to clean up resources.
        """
        # Clear cache keys
        if self._image_cache_key:
            memory_manager.remove_from_cache(self._image_cache_key)
            
        # Call base destructor
        super().__del__()