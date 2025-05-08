# Memory Management in PhenoTag

This document explains how to use the memory management features in the PhenoTag application to optimize memory usage when working with large image datasets.

## Overview

PhenoTag's memory management system provides tools for:

1. Monitoring memory usage in real-time
2. Automatically optimizing memory usage through caching, downscaling, and cleanup
3. Tracking memory-intensive operations
4. Automatically responding to low memory conditions

## Key Components

### MemoryManager

The central component that provides:

- Memory usage monitoring 
- Caching of expensive computations
- Automatic cleanup when memory runs low
- Object tracking for memory leak detection

### MemoryOptimizedProcessor

A specialized image processor that extends the base ImageProcessor with:

- Memory usage tracking
- Automatic image downscaling when memory is limited
- Caching of band computations and ROI analyses

## Basic Usage

### Using the MemoryOptimizedProcessor

```python
from phenotag.processors.memory_optimized_processor import MemoryOptimizedProcessor

# Create with automatic memory management
processor = MemoryOptimizedProcessor(
    downscale_factor=1.0,  # Start with full resolution
    memory_threshold_mb=1000  # Automatically downscale if memory usage exceeds this
)

# Load an image (will automatically optimize memory usage)
processor.load_image("path/to/large_image.jpg")

# Process the image as normal
processor.compute_chromatic_coordinates()
processor.get_rgb_bands()

# Memory-intensive operations will be automatically tracked and optimized
```

### Batch Processing with Memory Optimization

```python
from phenotag.processors.memory_optimized_processor import MemoryOptimizedProcessor

# Define image paths
image_paths = [
    "path/to/image1.jpg",
    "path/to/image2.jpg",
    "path/to/image3.jpg",
    # ...more images
]

processor = MemoryOptimizedProcessor(memory_threshold_mb=1500)

# Process all images with memory monitoring
processor.process_batch(
    images_list=image_paths,
    output_dir="path/to/output",
    export_bands=True,
    analyze_rois=True
)
```

### Memory Tracking in Custom Functions

```python
from phenotag.memory.memory_manager import track_memory, MemoryTracker

# Method 1: Use decorator
@track_memory("Loading phenocam data")
def load_phenocam_data(path):
    # Memory-intensive loading code
    pass

# Method 2: Use context manager
def process_large_dataset(dataset_path):
    with MemoryTracker("Processing dataset", enable_tracemalloc=True):
        # Memory-intensive processing
        pass
```

## Integrating with Streamlit UI

```python
import streamlit as st
from phenotag.memory.memory_manager import memory_manager, MemoryTracker
from phenotag.processors.memory_optimized_processor import MemoryOptimizedProcessor

def main():
    # Start memory monitoring at app initialization
    memory_manager.start_memory_monitoring(
        interval=30.0,  # Check every 30 seconds
        threshold_mb=2000  # Alert if we exceed 2GB
    )
    
    # Add memory stats to sidebar
    with st.sidebar.expander("Memory Usage"):
        if st.button("Check Memory"):
            memory_info = memory_manager.monitor.get_memory_usage()
            st.write(f"Process memory: {memory_info['process_rss']:.1f} MB")
            st.write(f"System memory: {memory_info['system_percent']:.1f}%")
            
            # Show cache stats
            cache_stats = memory_manager.get_cache_stats()
            st.write(f"Cache usage: {cache_stats['size_mb']:.1f} MB " +
                    f"({cache_stats['usage_percent']:.1f}%)")
            
            # Add a cleanup button
            if st.button("Clear Memory Cache"):
                memory_manager.clear_cache()
                memory_manager.force_garbage_collection()
                st.success("Memory cache cleared!")
    
    # Use memory-optimized processor for image operations
    processor = MemoryOptimizedProcessor(memory_threshold_mb=1500)
    
    # Rest of the Streamlit app...
```

## Advanced Configuration

### Configuring Memory Thresholds

```python
from phenotag.memory.memory_manager import memory_manager

# Configure memory thresholds
memory_manager.max_cache_size_mb = 1000  # 1GB cache limit

# Register a custom callback for low memory conditions
def on_low_memory():
    # Custom handling for low memory
    print("Memory is running low, taking action...")
    
memory_manager.register_low_memory_callback(on_low_memory)
```

### Monitoring Specific Memory-Intensive Operations

```python
from phenotag.memory.memory_manager import memory_manager, MemoryTracker

# Enable detailed memory tracking for a specific operation
memory_manager.monitor.enable_tracemalloc()

with MemoryTracker("Loading large dataset"):
    # Load data
    pass

# Log the top memory allocations
memory_manager.monitor.log_top_allocations(limit=10)

# Disable detailed tracking when done
memory_manager.monitor.disable_tracemalloc()
```

## Best Practices

1. **Use MemoryOptimizedProcessor** instead of the base ImageProcessor when working with large images or batches

2. **Enable memory monitoring** at application startup:
   ```python
   from phenotag.memory.memory_manager import memory_manager
   memory_manager.start_memory_monitoring()
   ```

3. **Track memory-intensive operations** with the MemoryTracker context manager or @track_memory decorator

4. **Add memory statistics** to the UI to help users monitor resource usage

5. **Clear caches** when switching between different datasets or operations:
   ```python
   memory_manager.clear_cache()
   ```

6. **Explicitly release resources** when no longer needed:
   ```python
   processor.release_original()  # Release original image after processing
   ```