"""
Memory Manager for the PhenoTag application.

This module provides utilities to monitor and manage memory usage
in the application, particularly when dealing with large image datasets.
"""

import gc
import os
import psutil
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
import time
import weakref
import threading
import tracemalloc

# Configure logging
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitors system and process memory usage."""
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize the memory monitor.
        
        Args:
            log_level: Logging level (default: INFO)
        """
        self.process = psutil.Process(os.getpid())
        self.log_level = log_level
        self._monitoring = False
        self._monitor_thread = None
        self._monitor_interval = 5  # seconds
        
        # Configure tracemalloc for detailed memory tracking
        self.tracemalloc_enabled = False
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage information.
        
        Returns:
            Dict with memory usage information in MB:
                - process_rss: Resident Set Size (actual physical memory used)
                - process_vms: Virtual Memory Size (total memory allocated)
                - system_used: System memory used
                - system_total: Total system memory
                - system_percent: Percentage of system memory used
        """
        # Get process memory info
        process_info = self.process.memory_info()
        
        # Get system memory info
        system_info = psutil.virtual_memory()
        
        # Convert bytes to MB for easier reading
        return {
            'process_rss': process_info.rss / (1024 * 1024),  # MB
            'process_vms': process_info.vms / (1024 * 1024),  # MB
            'system_used': system_info.used / (1024 * 1024),  # MB
            'system_total': system_info.total / (1024 * 1024),  # MB
            'system_percent': system_info.percent  # %
        }
    
    def log_memory_usage(self, label: str = "") -> Dict[str, float]:
        """
        Log current memory usage with an optional label.
        
        Args:
            label: Optional label to identify this memory check
            
        Returns:
            Dict with memory usage information
        """
        memory_info = self.get_memory_usage()
        
        # Format the log message
        if label:
            message = f"{label} - "
        else:
            message = ""
            
        message += (
            f"Process: {memory_info['process_rss']:.1f}MB (RSS), "
            f"System: {memory_info['system_percent']:.1f}% of "
            f"{memory_info['system_total']:.1f}MB"
        )
        
        logger.log(self.log_level, message)
        return memory_info
    
    def start_monitoring(self, interval: float = 5.0, 
                        threshold_mb: float = 1000.0,
                        callback: Optional[Callable[[Dict[str, float]], None]] = None) -> None:
        """
        Start a background thread to monitor memory usage.
        
        Args:
            interval: Monitoring interval in seconds
            threshold_mb: Memory threshold in MB to trigger warnings
            callback: Optional callback function when threshold is exceeded
        """
        if self._monitoring:
            logger.warning("Memory monitoring is already active")
            return
            
        self._monitoring = True
        self._monitor_interval = interval
        
        def monitor_loop():
            """Background monitoring loop."""
            while self._monitoring:
                memory_info = self.get_memory_usage()
                
                # Check against threshold
                if memory_info['process_rss'] > threshold_mb:
                    logger.warning(
                        f"Memory usage exceeded threshold: "
                        f"{memory_info['process_rss']:.1f}MB > {threshold_mb:.1f}MB"
                    )
                    
                    if callback:
                        try:
                            callback(memory_info)
                        except Exception as e:
                            logger.error(f"Error in memory callback: {e}")
                
                # Sleep for the interval
                time.sleep(self._monitor_interval)
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=monitor_loop, 
            daemon=True,  # Allow app to exit even if thread is running
            name="MemoryMonitorThread"
        )
        self._monitor_thread.start()
        logger.info(f"Memory monitoring started (interval: {interval}s, threshold: {threshold_mb}MB)")
    
    def stop_monitoring(self) -> None:
        """Stop the background memory monitoring."""
        if not self._monitoring:
            return
            
        self._monitoring = False
        
        # Wait for thread to finish if it's running
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2*self._monitor_interval)
            
        logger.info("Memory monitoring stopped")
    
    def enable_tracemalloc(self) -> None:
        """Enable detailed memory tracking with tracemalloc."""
        if not self.tracemalloc_enabled:
            tracemalloc.start()
            self.tracemalloc_enabled = True
            logger.info("Tracemalloc started for detailed memory tracking")
    
    def disable_tracemalloc(self) -> None:
        """Disable tracemalloc to reduce overhead."""
        if self.tracemalloc_enabled:
            tracemalloc.stop()
            self.tracemalloc_enabled = False
            logger.info("Tracemalloc stopped")
    
    def get_top_allocations(self, limit: int = 10) -> List[Tuple[tracemalloc.Snapshot, int]]:
        """
        Get the top memory allocations if tracemalloc is enabled.
        
        Args:
            limit: Maximum number of allocations to return
            
        Returns:
            List of (trace, size) tuples for top allocations
        """
        if not self.tracemalloc_enabled:
            logger.warning("Tracemalloc is not enabled. Call enable_tracemalloc() first.")
            return []
            
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        return top_stats[:limit]
    
    def log_top_allocations(self, limit: int = 10) -> None:
        """Log the top memory allocations if tracemalloc is enabled."""
        if not self.tracemalloc_enabled:
            logger.warning("Tracemalloc is not enabled. Call enable_tracemalloc() first.")
            return
            
        logger.info(f"Top {limit} memory allocations:")
        
        for stat in self.get_top_allocations(limit):
            logger.info(f"{stat.count} allocations: {stat.size / 1024:.1f} KiB")
            logger.info(f"\tAt: {stat.traceback.format()[0]}")
    
    def log_memory_diff(self, label: str = "") -> None:
        """
        Log memory usage difference since tracemalloc was started.
        
        Args:
            label: Optional label to identify this check
        """
        if not self.tracemalloc_enabled:
            logger.warning("Tracemalloc is not enabled. Call enable_tracemalloc() first.")
            return
            
        current, peak = tracemalloc.get_traced_memory()
        
        if label:
            prefix = f"{label} - "
        else:
            prefix = ""
            
        logger.info(
            f"{prefix}Current traced memory: {current / 1024:.1f} KiB, "
            f"Peak: {peak / 1024:.1f} KiB"
        )


class MemoryManager:
    """
    Manages memory for the application by providing tools to track and release resources.
    Implements a simple cache with size limitation and automatic cleanup.
    """
    
    def __init__(self, max_cache_size_mb: float = 500.0):
        """
        Initialize the memory manager.
        
        Args:
            max_cache_size_mb: Maximum cache size in MB
        """
        self.monitor = MemoryMonitor()
        self.max_cache_size_mb = max_cache_size_mb
        self.current_cache_size_mb = 0.0
        
        # Cache mapping (key -> (weakref, size, last_access_time))
        self._cache = {}
        self._cache_lock = threading.RLock()
        
        # Register for low memory callback
        self._low_memory_callbacks = []
        
        # Object tracking for memory leaks
        self._tracked_objects = weakref.WeakValueDictionary()
        
        self._cache_log_interval = 300  # 5 minutes
        self._last_cache_log = 0
    
    def register_low_memory_callback(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to be called when memory is low.
        
        Args:
            callback: Function to call when memory is low
        """
        self._low_memory_callbacks.append(callback)
    
    def _on_low_memory(self, memory_info: Dict[str, float]) -> None:
        """
        Internal callback when memory is low.
        
        Args:
            memory_info: Memory usage information
        """
        logger.warning(
            f"Low memory condition detected. "
            f"Process using {memory_info['process_rss']:.1f}MB, "
            f"System at {memory_info['system_percent']:.1f}%"
        )
        
        # Force garbage collection
        self.force_garbage_collection()
        
        # Clear cache if still low
        if memory_info['process_rss'] > self.max_cache_size_mb * 1.5:
            logger.warning("Memory still high, clearing cache")
            self.clear_cache()
        
        # Call registered callbacks
        for callback in self._low_memory_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in low memory callback: {e}")
    
    def start_memory_monitoring(self, interval: float = 30.0, 
                               threshold_mb: float = 1000.0) -> None:
        """
        Start monitoring memory with automatic intervention when thresholds are exceeded.
        
        Args:
            interval: Check interval in seconds
            threshold_mb: Memory threshold in MB to trigger interventions
        """
        self.monitor.start_monitoring(
            interval=interval,
            threshold_mb=threshold_mb,
            callback=self._on_low_memory
        )
    
    def stop_memory_monitoring(self) -> None:
        """Stop memory monitoring."""
        self.monitor.stop_monitoring()
    
    def force_garbage_collection(self) -> int:
        """
        Force a garbage collection cycle and return number of objects collected.
        
        Returns:
            Number of unreachable objects found (collected)
        """
        # Disable automatic garbage collection during manual collection
        was_enabled = gc.isenabled()
        if was_enabled:
            gc.disable()
        
        # Perform collection and get stats
        gc.collect()  # First collection to break reference cycles
        collected = gc.collect()  # Second collection to clean up
        
        # Re-enable if it was enabled before
        if was_enabled:
            gc.enable()
            
        logger.info(f"Garbage collection: {collected} objects collected")
        return collected
    
    def track_object(self, obj: Any, name: str) -> None:
        """
        Track an object for potential memory leaks.
        
        Args:
            obj: Object to track
            name: Name for the object in logs
        """
        if obj is None:
            return
            
        self._tracked_objects[name] = obj
        logger.debug(f"Now tracking object: {name}")
    
    def get_tracked_object_count(self) -> int:
        """
        Get the number of tracked objects still alive.
        
        Returns:
            Number of tracked objects
        """
        return len(self._tracked_objects)
    
    def log_tracked_objects(self) -> None:
        """Log information about tracked objects."""
        logger.info(f"Currently tracking {len(self._tracked_objects)} objects")
        for name in self._tracked_objects:
            logger.debug(f"Tracked object still alive: {name}")
    
    def add_to_cache(self, key: str, value: Any, size_mb: float = None) -> None:
        """
        Add an item to the memory cache with automatic size management.
        
        Args:
            key: Cache key
            value: Object to cache
            size_mb: Estimated size in MB (will estimate if None)
        """
        if value is None:
            return
            
        # Estimate size if not provided
        if size_mb is None:
            if isinstance(value, np.ndarray):
                # Calculate numpy array size
                size_mb = value.nbytes / (1024 * 1024)
            else:
                # Rough estimate
                size_mb = 1.0  # Default 1MB
        
        # Create a weak reference to the value
        value_ref = weakref.ref(value)
        access_time = time.time()
        
        with self._cache_lock:
            # If we're adding a new item or replacing an existing one, 
            # first subtract old size if it exists
            if key in self._cache:
                old_item = self._cache[key]
                self.current_cache_size_mb -= old_item[1]  # Subtract old size
            
            # Add the new item
            self._cache[key] = (value_ref, size_mb, access_time)
            self.current_cache_size_mb += size_mb
            
            # Check if we need to clean up
            self._check_cache_size()
            
            # Periodically log cache stats
            current_time = time.time()
            if current_time - self._last_cache_log > self._cache_log_interval:
                logger.debug(
                    f"Cache status: {len(self._cache)} items, "
                    f"{self.current_cache_size_mb:.1f}/{self.max_cache_size_mb:.1f}MB used"
                )
                self._last_cache_log = current_time
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._cache_lock:
            if key not in self._cache:
                return None
            
            # Get the weak reference and resolve it
            value_ref, size_mb, _ = self._cache[key]
            value = value_ref()
            
            if value is None:
                # Object has been garbage collected
                del self._cache[key]
                self.current_cache_size_mb -= size_mb
                return None
            
            # Update the access time
            self._cache[key] = (value_ref, size_mb, time.time())
            return value
    
    def remove_from_cache(self, key: str) -> bool:
        """
        Remove an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if item was found and removed, False otherwise
        """
        with self._cache_lock:
            if key not in self._cache:
                return False
            
            # Get size to update current cache size
            _, size_mb, _ = self._cache[key]
            
            # Remove the item
            del self._cache[key]
            self.current_cache_size_mb -= size_mb
            return True
    
    def _check_cache_size(self) -> None:
        """Check cache size and remove oldest items if it exceeds the maximum size."""
        if self.current_cache_size_mb <= self.max_cache_size_mb:
            return
            
        # Sort by access time (oldest first)
        items = sorted(
            [(k, v[1], v[2]) for k, v in self._cache.items()],
            key=lambda x: x[2]
        )
        
        # Remove oldest items until we're under the size limit
        for key, size_mb, _ in items:
            if self.current_cache_size_mb <= self.max_cache_size_mb * 0.8:  # 20% buffer
                break
                
            if key in self._cache:
                del self._cache[key]
                self.current_cache_size_mb -= size_mb
                logger.debug(f"Removed {key} ({size_mb:.1f}MB) from cache due to size limits")
    
    def clear_cache(self) -> None:
        """Clear the entire cache."""
        with self._cache_lock:
            self._cache.clear()
            self.current_cache_size_mb = 0.0
            logger.info("Memory cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dict with cache statistics
        """
        with self._cache_lock:
            return {
                'item_count': len(self._cache),
                'size_mb': self.current_cache_size_mb,
                'max_size_mb': self.max_cache_size_mb,
                'usage_percent': (self.current_cache_size_mb / self.max_cache_size_mb * 100) 
                                 if self.max_cache_size_mb > 0 else 0
            }
    
    def log_memory_stats(self, label: str = "") -> None:
        """
        Log memory statistics including cache info.
        
        Args:
            label: Optional label for the log entry
        """
        # Get memory usage from the monitor
        memory_info = self.monitor.log_memory_usage(label)
        
        # Add cache stats
        cache_stats = self.get_cache_stats()
        logger.info(
            f"Cache status: {cache_stats['item_count']} items, "
            f"{cache_stats['size_mb']:.1f}/{cache_stats['max_size_mb']:.1f}MB "
            f"({cache_stats['usage_percent']:.1f}%)"
        )
        
        return memory_info


# Default instance for easy access
memory_manager = MemoryManager()


# Context manager for memory tracking
class MemoryTracker:
    """
    Context manager to track memory usage during a code block.
    
    Example:
        with MemoryTracker("Loading large file"):
            # Code that might use lots of memory
            data = load_large_file()
    """
    
    def __init__(self, label: str, manager: MemoryManager = None, 
                enable_tracemalloc: bool = False):
        """
        Initialize the memory tracker.
        
        Args:
            label: Label for this memory tracking session
            manager: Memory manager to use (or default)
            enable_tracemalloc: Whether to use tracemalloc for detailed tracking
        """
        self.label = label
        self.manager = manager or memory_manager
        self.enable_tracemalloc = enable_tracemalloc
        self.start_time = None
    
    def __enter__(self):
        """Start tracking memory when entering the context."""
        self.start_time = time.time()
        
        # Log starting memory
        self.manager.monitor.log_memory_usage(f"{self.label} (start)")
        
        # Enable tracemalloc if requested
        if self.enable_tracemalloc:
            self.manager.monitor.enable_tracemalloc()
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log memory when exiting the context."""
        duration = time.time() - self.start_time
        
        # Log ending memory
        self.manager.monitor.log_memory_usage(
            f"{self.label} (end after {duration:.2f}s)"
        )
        
        # Log tracemalloc differences if enabled
        if self.enable_tracemalloc:
            self.manager.monitor.log_memory_diff(self.label)
            self.manager.monitor.log_top_allocations(5)
            self.manager.monitor.disable_tracemalloc()
            
        # Force garbage collection
        collected = self.manager.force_garbage_collection()
        if collected > 0:
            logger.debug(f"{self.label}: GC collected {collected} objects")


# Decorator for memory tracking
def track_memory(label: str = None, enable_tracemalloc: bool = False):
    """
    Decorator to track memory usage of a function.
    
    Args:
        label: Label for the memory tracking (defaults to function name)
        enable_tracemalloc: Whether to use tracemalloc for detailed tracking
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Use function name if no label provided
            nonlocal label
            func_label = label or f"Function {func.__name__}"
            
            with MemoryTracker(func_label, enable_tracemalloc=enable_tracemalloc):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Function to estimate memory requirements
def estimate_memory_requirements(image_info: Dict[str, Any]) -> Dict[str, float]:
    """
    Estimate memory requirements for processing an image with given properties.
    
    Args:
        image_info: Dictionary with image properties:
            - width: Image width in pixels
            - height: Image height in pixels
            - channels: Number of color channels (3 for RGB)
            - dtype: Data type (e.g., 'uint8', 'float32')
            
    Returns:
        Dict with estimated memory requirements in MB
    """
    # Get image dimensions
    width = image_info.get('width', 0)
    height = image_info.get('height', 0)
    channels = image_info.get('channels', 3)
    dtype = image_info.get('dtype', 'uint8')
    
    # Calculate bytes per pixel
    if dtype == 'uint8':
        bytes_per_pixel = 1
    elif dtype == 'uint16':
        bytes_per_pixel = 2
    elif dtype in ('float32', 'int32'):
        bytes_per_pixel = 4
    elif dtype in ('float64', 'int64'):
        bytes_per_pixel = 8
    else:
        bytes_per_pixel = 1  # Default
    
    # Calculate base image size
    base_size_bytes = width * height * channels * bytes_per_pixel
    base_size_mb = base_size_bytes / (1024 * 1024)
    
    # Estimate for various operations (based on empirical observations)
    loaded_size_mb = base_size_mb  # Original image
    with_copy_mb = base_size_mb * 2  # Original + copy
    with_processing_mb = base_size_mb * 3  # Original + working copy + results
    with_masks_mb = base_size_mb * 4  # Original + working copy + results + masks
    
    return {
        'base_size_mb': base_size_mb,
        'loaded_size_mb': loaded_size_mb,
        'with_copy_mb': with_copy_mb,
        'with_processing_mb': with_processing_mb,
        'with_masks_mb': with_masks_mb,
        'recommended_min_mb': with_processing_mb * 1.5  # 50% safety margin
    }


def get_memory_manager() -> MemoryManager:
    """
    Get the global memory manager instance.
    
    Returns:
        The global memory manager
    """
    return memory_manager