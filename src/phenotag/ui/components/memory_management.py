"""
Memory management component for PhenoTag UI.

This module provides utilities to manage memory usage in the application.
"""
import streamlit as st
import gc
import os
import psutil
import time
from typing import Optional, Dict, Any, Callable

# Try to import memory_profiler if available
try:
    import memory_profiler
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False


class MemoryManager:
    """Memory manager for tracking and optimizing memory usage."""
    
    def __init__(self):
        """Initialize the memory manager."""
        self.memory_usage_history = []
        self.memory_threshold_mb = 1000  # Default 1GB
        self.monitoring_active = False
        self.monitor_interval = 30.0  # seconds
        self.last_check_time = 0
        self.process = psutil.Process(os.getpid())
        self.cache = {}
        
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        if HAS_MEMORY_PROFILER:
            return memory_profiler.memory_usage()[0]
        else:
            # Fallback to psutil
            return self.process.memory_info().rss / (1024 * 1024)
        
    def log_memory_usage(self, label: str) -> None:
        """Log memory usage with a label."""
        memory_mb = self.get_memory_usage_mb()
        timestamp = time.time()
        self.memory_usage_history.append({
            'timestamp': timestamp,
            'memory_mb': memory_mb,
            'label': label
        })
        
        # Keep only the last 100 entries to avoid memory growth
        if len(self.memory_usage_history) > 100:
            self.memory_usage_history = self.memory_usage_history[-100:]
            
        # Print debug info
        print(f"[MEMORY] {label}: {memory_mb:.2f} MB")
        
    def check_memory_threshold(self) -> bool:
        """
        Check if memory usage is above threshold.
        
        Returns:
            bool: True if memory usage is above threshold, False otherwise
        """
        memory_mb = self.get_memory_usage_mb()
        return memory_mb > self.memory_threshold_mb
        
    def clear_memory(self) -> None:
        """Force garbage collection to free memory."""
        gc.collect()
        self.log_memory_usage("After garbage collection")
        
    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self.cache.clear()
        self.clear_memory()
        self.log_memory_usage("After cache clear")
        
    def start_memory_monitoring(self, interval: float = 30.0, threshold_mb: int = 1000) -> None:
        """
        Start monitoring memory usage in the background.
        
        Args:
            interval (float): Check interval in seconds
            threshold_mb (int): Memory threshold in MB
        """
        self.monitoring_active = True
        self.monitor_interval = interval
        self.memory_threshold_mb = threshold_mb
        self.last_check_time = time.time()
        
        # Log initial memory usage
        self.log_memory_usage("Monitoring started")
        
    def stop_memory_monitoring(self) -> None:
        """Stop memory monitoring."""
        self.monitoring_active = False
        
    def get_memory_status(self) -> Dict[str, Any]:
        """
        Get current memory status information.
        
        Returns:
            dict: Memory status information
        """
        memory_mb = self.get_memory_usage_mb()
        percent = (memory_mb / self.memory_threshold_mb) * 100
        
        return {
            'current_mb': memory_mb,
            'threshold_mb': self.memory_threshold_mb,
            'percent': percent,
            'is_high': memory_mb > self.memory_threshold_mb
        }
        
    def monitor_check(self) -> None:
        """Perform a memory monitoring check if due."""
        if not self.monitoring_active:
            return
            
        current_time = time.time()
        if current_time - self.last_check_time >= self.monitor_interval:
            self.last_check_time = current_time
            memory_status = self.get_memory_status()
            
            # Log memory status
            self.log_memory_usage(f"Monitoring check: {memory_status['current_mb']:.2f} MB")
            
            # If memory usage is high, try to free memory
            if memory_status['is_high']:
                print(f"[MEMORY WARNING] Memory usage is high: {memory_status['current_mb']:.2f} MB")
                self.clear_memory()


class MemoryTracker:
    """Context manager for tracking memory usage of code blocks."""
    
    def __init__(self, label: str, 
                 memory_manager: Optional[MemoryManager] = None,
                 threshold_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize memory tracker.
        
        Args:
            label (str): Label for the tracked code block
            memory_manager (MemoryManager, optional): Memory manager to use
            threshold_callback (Callable, optional): Callback function when threshold is exceeded
        """
        self.label = label
        self.start_memory = 0
        self.memory_manager = memory_manager
        self.threshold_callback = threshold_callback
        
        # Get or create memory manager
        if self.memory_manager is None:
            if 'memory_manager' in st.session_state:
                self.memory_manager = st.session_state.memory_manager
            else:
                self.memory_manager = memory_manager
                
    def __enter__(self):
        """Enter the context manager."""
        if self.memory_manager:
            self.start_memory = self.memory_manager.get_memory_usage_mb()
            self.memory_manager.log_memory_usage(f"Start {self.label}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if self.memory_manager:
            end_memory = self.memory_manager.get_memory_usage_mb()
            delta = end_memory - self.start_memory
            self.memory_manager.log_memory_usage(f"End {self.label} (delta: {delta:.2f} MB)")
            
            # Check if memory usage is above threshold
            if self.threshold_callback and self.memory_manager.check_memory_threshold():
                self.threshold_callback(end_memory)


class MemoryDashboard:
    """Streamlit dashboard for displaying memory usage."""
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize memory dashboard.
        
        Args:
            memory_manager (MemoryManager, optional): Memory manager to use
        """
        self.memory_manager = memory_manager
        
        # Get or create memory manager
        if self.memory_manager is None:
            if 'memory_manager' in st.session_state:
                self.memory_manager = st.session_state.memory_manager
            else:
                self.memory_manager = MemoryManager()
                st.session_state.memory_manager = self.memory_manager
                
    def render_mini_dashboard(self):
        """Render a mini memory dashboard in the sidebar."""
        # Show memory usage in the sidebar
        with st.sidebar:
            memory_status = self.memory_manager.get_memory_status()
            
            # Create columns for metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Memory Usage",
                    f"{memory_status['current_mb']:.1f} MB",
                    f"{memory_status['percent']:.1f}% of limit",
                    delta_color="inverse"
                )
                
            with col2:
                # Add a button to clear memory
                if st.button("Clear Memory"):
                    self.memory_manager.clear_memory()
                    st.success("Memory cleared")
                    
    def render_dashboard(self, location="sidebar"):
        """
        Render the full memory dashboard.
        
        Args:
            location (str): Where to display the dashboard ('sidebar' or 'main')
        """
        dashboard_container = st.sidebar if location == "sidebar" else st
        
        with dashboard_container:
            st.subheader("Memory Management")
            
            # Show memory metrics
            memory_status = self.memory_manager.get_memory_status()
            st.progress(min(memory_status['percent'] / 100, 1.0))
            
            # Color based on status
            color = "normal"
            if memory_status['percent'] > 80:
                color = "red"
            elif memory_status['percent'] > 60:
                color = "orange"
                
            st.markdown(
                f"<span style='color:{color}'>Current: {memory_status['current_mb']:.1f} MB "
                f"({memory_status['percent']:.1f}% of threshold)</span>",
                unsafe_allow_html=True
            )
            
            # Memory management actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Force GC"):
                    self.memory_manager.clear_memory()
                    st.success("Memory cleared")
                    
            with col2:
                if st.button("Clear Cache"):
                    self.memory_manager.clear_cache()
                    st.success("Cache cleared")
                    
            # Display memory monitoring settings
            st.subheader("Monitoring Settings")
            
            # Toggle for memory monitoring
            monitoring = st.toggle(
                "Enable monitoring",
                value=self.memory_manager.monitoring_active
            )
            
            if monitoring != self.memory_manager.monitoring_active:
                if monitoring:
                    self.memory_manager.start_memory_monitoring()
                else:
                    self.memory_manager.stop_memory_monitoring()
                    
            # Settings if monitoring is enabled
            if monitoring:
                col1, col2 = st.columns(2)
                with col1:
                    interval = st.number_input(
                        "Check interval (s)",
                        min_value=5.0,
                        max_value=300.0,
                        value=self.memory_manager.monitor_interval,
                        step=5.0
                    )
                    if interval != self.memory_manager.monitor_interval:
                        self.memory_manager.monitor_interval = interval
                        
                with col2:
                    threshold = st.number_input(
                        "Threshold (MB)",
                        min_value=100,
                        max_value=10000,
                        value=self.memory_manager.memory_threshold_mb,
                        step=100
                    )
                    if threshold != self.memory_manager.memory_threshold_mb:
                        self.memory_manager.memory_threshold_mb = threshold
                        
            # Show memory history
            if self.memory_manager.memory_usage_history:
                st.subheader("Memory History")
                
                # Extract data for chart
                timestamps = [entry['timestamp'] for entry in self.memory_manager.memory_usage_history]
                memory_values = [entry['memory_mb'] for entry in self.memory_manager.memory_usage_history]
                
                # Create a dataframe for the chart
                import pandas as pd
                import numpy as np
                
                # Calculate relative timestamps
                base_time = timestamps[0]
                relative_timestamps = [(t - base_time) / 60 for t in timestamps]  # minutes
                
                # Create df for line chart
                df = pd.DataFrame({
                    'Minutes': relative_timestamps,
                    'Memory (MB)': memory_values
                })
                
                # Add threshold line
                chart_df = pd.DataFrame({
                    'Minutes': [relative_timestamps[0], relative_timestamps[-1]],
                    'Memory (MB)': [self.memory_manager.memory_threshold_mb, self.memory_manager.memory_threshold_mb],
                    'Threshold': ['Threshold', 'Threshold']
                })
                
                st.line_chart(df, x='Minutes', y='Memory (MB)')
                
    def add_memory_metrics_to_status_bar(self):
        """Add memory metrics to the status bar."""
        memory_status = self.memory_manager.get_memory_status()
        
        # Create a status message
        status_color = "green"
        if memory_status['percent'] > 80:
            status_color = "red"
        elif memory_status['percent'] > 60:
            status_color = "orange"
            
        st.markdown(
            f"<div style='position: fixed; bottom: 0; right: 0; padding: 5px; "
            f"background-color: #f0f0f0; color: {status_color}; font-size: 0.8em;'>"
            f"Memory: {memory_status['current_mb']:.1f} MB "
            f"({memory_status['percent']:.1f}%)</div>",
            unsafe_allow_html=True
        )


# Create global instances
memory_manager = MemoryManager()
memory_dashboard = MemoryDashboard(memory_manager)