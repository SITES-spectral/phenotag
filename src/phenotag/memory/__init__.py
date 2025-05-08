"""
Memory management package for the PhenoTag application.

This package provides tools for tracking and optimizing memory usage,
particularly when working with large image datasets.
"""

from .memory_manager import (
    MemoryMonitor,
    MemoryManager,
    MemoryTracker,
    track_memory,
    estimate_memory_requirements,
    get_memory_manager,
    memory_manager,
)

__all__ = [
    'MemoryMonitor',
    'MemoryManager',
    'MemoryTracker',
    'track_memory',
    'estimate_memory_requirements',
    'get_memory_manager',
    'memory_manager',
]