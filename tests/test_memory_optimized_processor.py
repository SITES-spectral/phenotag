"""
Tests for the memory-optimized image processor.
"""

import pytest
import numpy as np
import cv2
import tempfile
import os
import time
from pathlib import Path

from phenotag.processors.memory_optimized_processor import MemoryOptimizedProcessor
from phenotag.memory.memory_manager import memory_manager


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple test image: 500x300 with a red rectangle
        img = np.zeros((300, 500, 3), dtype=np.uint8)
        img[:, :] = [50, 100, 150]  # Blue-ish background
        
        # Draw a rectangle
        cv2.rectangle(img, (100, 50), (400, 250), [0, 0, 255], -1)  # Filled red rectangle
        
        # Save the image
        img_path = os.path.join(temp_dir, "test_image.jpg")
        cv2.imwrite(img_path, img)
        
        yield img_path


def test_memory_optimized_processor_creation():
    """Test that the memory-optimized processor can be created."""
    processor = MemoryOptimizedProcessor()
    assert processor is not None
    assert hasattr(processor, 'memory_threshold_mb')


def test_memory_optimized_processor_load_image(sample_image):
    """Test loading an image with the memory-optimized processor."""
    processor = MemoryOptimizedProcessor()
    
    # Test loading image
    success = processor.load_image(sample_image)
    assert success is True
    assert processor.image is not None
    
    # Image should have been cached
    assert processor._image_cache_key is not None
    
    # Verify cache has the image
    cached_image = memory_manager.get_from_cache(processor._image_cache_key)
    assert cached_image is not None


def test_memory_optimized_processor_auto_downscale(sample_image):
    """Test auto-downscaling with the memory-optimized processor."""
    # Set a very low threshold to force downscaling
    processor = MemoryOptimizedProcessor(memory_threshold_mb=0.01)
    
    # Load image (should auto-downscale)
    success = processor.load_image(sample_image)
    assert success is True
    
    # Downscale factor should have been adjusted
    assert processor.downscale_factor <= 1.0
    
    # Image dimensions should be reduced
    assert processor.image.shape[0] < 300 or processor.image.shape[1] < 500


def test_memory_optimized_processor_release_original(sample_image):
    """Test releasing the original image."""
    processor = MemoryOptimizedProcessor()
    
    # Load with original
    processor.load_image(sample_image, keep_original=True)
    assert processor.original_image is not None
    
    # Release original
    processor.release_original()
    assert processor.original_image is None


def test_memory_optimized_processor_rgb_bands(sample_image):
    """Test getting RGB bands with the memory-optimized processor."""
    processor = MemoryOptimizedProcessor()
    processor.load_image(sample_image)
    
    # Get RGB bands
    bands = processor.get_rgb_bands()
    assert bands is not None
    assert 'r' in bands
    assert 'g' in bands
    assert 'b' in bands
    
    # Check band dimensions
    height, width = processor.image.shape[:2]
    assert bands['r'].shape == (height, width)
    
    # Getting again should use cache
    processor.get_rgb_bands()  # This should use cache
    
    # Verify cache contains the bands
    cache_key = f"{processor._image_cache_key}:rgb:r"
    cached_band = memory_manager.get_from_cache(cache_key)
    assert cached_band is not None


def test_memory_optimized_processor_chromatic(sample_image):
    """Test computing chromatic coordinates with memory optimization."""
    processor = MemoryOptimizedProcessor()
    processor.load_image(sample_image)
    
    # Compute chromatic coordinates
    coords = processor.compute_chromatic_coordinates()
    assert coords is not None
    assert 'r' in coords
    assert 'g' in coords
    assert 'b' in coords
    assert 'composite' in coords
    
    # Check dimensions
    height, width = processor.image.shape[:2]
    assert coords['r'].shape == (height, width)
    
    # Getting again should use cache
    processor.compute_chromatic_coordinates()  # This should use cache


def test_memory_optimized_processor_roi(sample_image):
    """Test ROI functionality with memory optimization."""
    processor = MemoryOptimizedProcessor()
    processor.load_image(sample_image)
    
    # Create a simple ROI (rectangle in the center)
    height, width = processor.image.shape[:2]
    points = [
        [width//4, height//4], 
        [width*3//4, height//4], 
        [width*3//4, height*3//4], 
        [width//4, height*3//4]
    ]
    processor.overlay_polygon(points, roi_name="test_roi")
    
    # Verify ROI was created
    assert "test_roi" in processor.rois
    
    # Analyze ROI bands
    results = processor.analyze_roi_bands("test_roi")
    assert results is not None
    
    # Results should be cached
    cache_key = f"{processor._image_cache_key}:roi_stats:test_roi"
    cached_results = memory_manager.get_from_cache(cache_key)
    assert cached_results is not None


def test_cleanup():
    """Test cleanup of memory cache."""
    # Clear memory cache after tests
    memory_manager.clear_cache()
    
    # Verify cache is empty
    stats = memory_manager.get_cache_stats()
    assert stats['item_count'] == 0
    assert stats['size_mb'] == 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])