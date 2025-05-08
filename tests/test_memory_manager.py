"""
Tests for the memory manager module.
"""

import pytest
import numpy as np
import time
import gc
import psutil
import os
from pathlib import Path

from phenotag.memory.memory_manager import (
    MemoryMonitor,
    MemoryManager,
    MemoryTracker,
    track_memory,
    estimate_memory_requirements,
    get_memory_manager
)


def test_memory_monitor_creation():
    """Test that the memory monitor can be created."""
    monitor = MemoryMonitor()
    assert monitor is not None


def test_memory_monitor_usage():
    """Test that the memory monitor can get memory usage."""
    monitor = MemoryMonitor()
    memory_usage = monitor.get_memory_usage()
    
    # Check that we get the expected keys
    assert 'process_rss' in memory_usage
    assert 'process_vms' in memory_usage
    assert 'system_used' in memory_usage
    assert 'system_total' in memory_usage
    assert 'system_percent' in memory_usage
    
    # Check that values are reasonable
    assert memory_usage['process_rss'] > 0
    assert memory_usage['process_vms'] > 0
    assert memory_usage['system_used'] > 0
    assert memory_usage['system_total'] > 0
    assert 0 <= memory_usage['system_percent'] <= 100


def test_memory_monitoring():
    """Test starting and stopping memory monitoring."""
    monitor = MemoryMonitor()
    
    # Test starting monitoring
    monitor.start_monitoring(interval=0.1)
    assert monitor._monitoring is True
    assert monitor._monitor_thread is not None
    assert monitor._monitor_thread.is_alive()
    
    # Test stopping monitoring
    monitor.stop_monitoring()
    assert monitor._monitoring is False
    
    # Give thread time to stop
    time.sleep(0.3)
    assert not monitor._monitor_thread.is_alive()


def test_memory_manager_creation():
    """Test that the memory manager can be created."""
    manager = MemoryManager()
    assert manager is not None
    assert manager.monitor is not None


def test_memory_manager_global_instance():
    """Test that the global memory manager instance is available."""
    manager = get_memory_manager()
    assert manager is not None
    
    # Should be the same instance each time
    manager2 = get_memory_manager()
    assert manager is manager2


def test_memory_manager_garbage_collection():
    """Test forcing garbage collection."""
    manager = MemoryManager()
    
    # Create some garbage
    for _ in range(1000):
        _ = [1, 2, 3, 4, 5]
    
    # Force collection
    collected = manager.force_garbage_collection()
    
    # Should have collected something (but not guaranteed)
    # This is more of a smoke test since GC behavior can vary
    assert isinstance(collected, int)


def test_memory_manager_cache():
    """Test the memory manager's cache functionality."""
    manager = MemoryManager(max_cache_size_mb=10.0)
    
    # Add an item to the cache
    test_array = np.ones((100, 100), dtype=np.float32)
    manager.add_to_cache("test_key", test_array)
    
    # Retrieve the item
    retrieved = manager.get_from_cache("test_key")
    assert retrieved is not None
    assert np.array_equal(retrieved, test_array)
    
    # Get cache stats
    stats = manager.get_cache_stats()
    assert stats['item_count'] == 1
    assert stats['size_mb'] > 0
    
    # Remove the item
    result = manager.remove_from_cache("test_key")
    assert result is True
    
    # Verify it's gone
    retrieved = manager.get_from_cache("test_key")
    assert retrieved is None
    
    # Updated stats
    stats = manager.get_cache_stats()
    assert stats['item_count'] == 0


def test_memory_manager_cache_size_limit():
    """Test that the cache respects size limits."""
    # Small cache size
    manager = MemoryManager(max_cache_size_mb=2.0)
    
    # Add items to exceed the cache size
    # Each array is about 1MB
    arrays = []
    for i in range(5):
        # Create array and keep reference to prevent GC
        arr = np.ones((250, 1000), dtype=np.float32)
        arrays.append(arr)
        manager.add_to_cache(f"test_key_{i}", arr)
    
    # Cache should have auto-removed some items to stay under the limit
    stats = manager.get_cache_stats()
    assert stats['size_mb'] <= manager.max_cache_size_mb * 1.2  # Allow some leeway
    
    # Only the most recently added items should remain
    # The exact number depends on the implementation, but we know
    # at least the oldest items should be gone
    assert manager.get_from_cache("test_key_0") is None
    
    # Clear cache
    manager.clear_cache()
    stats = manager.get_cache_stats()
    assert stats['item_count'] == 0
    assert stats['size_mb'] == 0


def test_memory_tracker_context_manager():
    """Test the MemoryTracker context manager."""
    # This is mostly a smoke test to ensure it doesn't raise exceptions
    with MemoryTracker("Test tracking"):
        # Do something that uses memory
        arr = np.ones((100, 100))
        _ = arr * 2
    
    # If we get here, the context manager worked without error


@track_memory("Test decorator")
def decorated_function():
    """Function decorated with memory tracking."""
    # Do something that uses memory
    arr = np.ones((100, 100))
    return arr * 2


def test_memory_tracking_decorator():
    """Test the memory tracking decorator."""
    # This is mostly a smoke test to ensure it doesn't raise exceptions
    result = decorated_function()
    assert result.shape == (100, 100)
    assert result[0, 0] == 2


def test_estimate_memory_requirements():
    """Test estimating memory requirements for different image sizes."""
    # Test a small image
    small_image = {
        'width': 640,
        'height': 480,
        'channels': 3,
        'dtype': 'uint8'
    }
    small_estimate = estimate_memory_requirements(small_image)
    
    # Example assertion (adjust based on expected values)
    assert small_estimate['base_size_mb'] < 1  # Should be less than 1MB
    
    # Test a large image
    large_image = {
        'width': 4000,
        'height': 3000,
        'channels': 3,
        'dtype': 'float32'
    }
    large_estimate = estimate_memory_requirements(large_image)
    
    # Large float32 image should require significant memory
    assert large_estimate['base_size_mb'] > 100  # Should be well over 100MB
    
    # Verify that float32 requires more memory than uint8
    uint8_image = large_image.copy()
    uint8_image['dtype'] = 'uint8'
    uint8_estimate = estimate_memory_requirements(uint8_image)
    
    assert large_estimate['base_size_mb'] > uint8_estimate['base_size_mb']


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])