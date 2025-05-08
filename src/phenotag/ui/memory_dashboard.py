"""
Memory monitoring dashboard for the Streamlit UI.

This module provides components for monitoring and controlling memory usage
that can be embedded in the Streamlit sidebar or main UI.
"""

import streamlit as st
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import threading
import logging
from typing import Dict, List, Optional, Union

from phenotag.memory.memory_manager import memory_manager, MemoryTracker

# Configure logging
logger = logging.getLogger(__name__)


class MemoryDashboard:
    """
    Memory monitoring dashboard for Streamlit.
    
    Provides widgets for monitoring memory usage and managing cache.
    """
    
    def __init__(self):
        """Initialize the memory dashboard."""
        # Initialize session state for memory monitoring
        if 'memory_history' not in st.session_state:
            st.session_state.memory_history = []
        
        if 'memory_monitor_active' not in st.session_state:
            st.session_state.memory_monitor_active = False
            
        if 'memory_last_update' not in st.session_state:
            st.session_state.memory_last_update = time.time()
            
        if 'memory_update_interval' not in st.session_state:
            st.session_state.memory_update_interval = 10  # seconds
    
    def toggle_monitoring(self) -> bool:
        """
        Toggle memory monitoring on/off.
        
        Returns:
            bool: New monitoring state
        """
        st.session_state.memory_monitor_active = not st.session_state.memory_monitor_active
        
        if st.session_state.memory_monitor_active:
            # Start monitoring
            memory_manager.start_memory_monitoring(
                interval=st.session_state.memory_update_interval,
                threshold_mb=2000  # Default 2GB threshold
            )
            logger.info("Memory monitoring started")
        else:
            # Stop monitoring
            memory_manager.stop_memory_monitoring()
            logger.info("Memory monitoring stopped")
            
        return st.session_state.memory_monitor_active
    
    def update_memory_history(self) -> None:
        """Update the memory history for the chart."""
        # Check if it's time to update
        current_time = time.time()
        elapsed = current_time - st.session_state.memory_last_update
        
        if elapsed < st.session_state.memory_update_interval:
            return
            
        # Get current memory usage
        memory_info = memory_manager.monitor.get_memory_usage()
        cache_stats = memory_manager.get_cache_stats()
        
        # Add to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.memory_history.append({
            'timestamp': timestamp,
            'process_mb': memory_info['process_rss'],
            'system_percent': memory_info['system_percent'],
            'cache_mb': cache_stats['size_mb']
        })
        
        # Keep only the most recent data points (e.g., last 30)
        if len(st.session_state.memory_history) > 30:
            st.session_state.memory_history = st.session_state.memory_history[-30:]
            
        # Update last update time
        st.session_state.memory_last_update = current_time
    
    def render_memory_chart(self) -> None:
        """Render a chart showing memory usage over time."""
        if not st.session_state.memory_history:
            st.info("No memory data collected yet. Start monitoring to collect data.")
            return
            
        # Convert history to DataFrame
        df = pd.DataFrame(st.session_state.memory_history)
        
        # Create a multi-line chart
        fig = go.Figure()
        
        # Process memory line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['process_mb'],
            mode='lines+markers',
            name='Process (MB)',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=5)
        ))
        
        # System memory percentage line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['system_percent'],
            mode='lines+markers',
            name='System (%)',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=5),
            yaxis='y2'
        ))
        
        # Cache size line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cache_mb'],
            mode='lines+markers',
            name='Cache (MB)',
            line=dict(color='#2ca02c', width=2),
            marker=dict(size=5)
        ))
        
        # Set layout with dual y-axes
        fig.update_layout(
            title='Memory Usage Over Time',
            xaxis=dict(title='Time'),
            yaxis=dict(
                title='Memory (MB)',
                side='left'
            ),
            yaxis2=dict(
                title='System Memory (%)',
                side='right',
                overlaying='y',
                range=[0, 100]
            ),
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation='h', y=1.1),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_dashboard(self, location: str = "sidebar") -> None:
        """
        Render the memory monitoring dashboard in the specified location.
        
        Args:
            location: Where to render the dashboard ("sidebar" or "main")
        """
        # Update memory history
        self.update_memory_history()
        
        # Choose the streamlit container based on location
        if location == "sidebar":
            container = st.sidebar
        else:
            container = st
        
        # Create the dashboard
        with container.expander("🧠 Memory Monitor", expanded=False):
            # Current memory usage metrics
            col1, col2 = st.columns(2)
            
            with col1:
                memory_info = memory_manager.monitor.get_memory_usage()
                st.metric(
                    "Process Memory",
                    f"{memory_info['process_rss']:.1f} MB",
                    delta=None,
                    delta_color="inverse"
                )
                
            with col2:
                st.metric(
                    "System Memory",
                    f"{memory_info['system_percent']:.1f} %",
                    delta=None,
                    delta_color="inverse"
                )
            
            # Cache usage
            cache_stats = memory_manager.get_cache_stats()
            st.progress(cache_stats['usage_percent'] / 100)
            st.caption(
                f"Cache: {cache_stats['size_mb']:.1f}/{cache_stats['max_size_mb']:.1f} MB "
                f"({cache_stats['usage_percent']:.1f}%) - {cache_stats['item_count']} items"
            )
            
            # Control buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(
                    "Start Monitoring" if not st.session_state.memory_monitor_active else "Stop Monitoring",
                    key="toggle_monitor"
                ):
                    new_state = self.toggle_monitoring()
                    st.success(f"Memory monitoring {'started' if new_state else 'stopped'}")
            
            with col2:
                if st.button("Clear Cache", key="clear_cache"):
                    with st.spinner("Clearing cache..."):
                        memory_manager.clear_cache()
                        memory_manager.force_garbage_collection()
                    st.success("Memory cache cleared!")
            
            # Update interval setting
            st.slider(
                "Update interval (seconds)",
                min_value=5,
                max_value=60,
                value=st.session_state.memory_update_interval,
                step=5,
                key="memory_update_interval"
            )
            
            # Memory usage chart
            self.render_memory_chart()
    
    def render_mini_dashboard(self) -> None:
        """Render a minimal version of the memory dashboard for the sidebar."""
        # Update memory history
        self.update_memory_history()
        
        # Create a mini dashboard
        with st.sidebar:
            st.markdown("### 🧠 Memory")
            
            # Current memory usage
            memory_info = memory_manager.monitor.get_memory_usage()
            st.progress(memory_info['system_percent'] / 100)
            st.caption(
                f"Process: {memory_info['process_rss']:.1f} MB | "
                f"System: {memory_info['system_percent']:.1f}%"
            )
            
            # Cache info and clear button in one row
            col1, col2 = st.columns([3, 1])
            with col1:
                cache_stats = memory_manager.get_cache_stats()
                st.caption(
                    f"Cache: {cache_stats['size_mb']:.1f} MB "
                    f"({cache_stats['usage_percent']:.1f}%)"
                )
            
            with col2:
                if st.button("🗑️", key="mini_clear_cache", help="Clear memory cache"):
                    memory_manager.clear_cache()
                    memory_manager.force_garbage_collection()
                    st.success("Cache cleared!")
    
    @staticmethod
    def add_memory_metrics_to_status_bar() -> None:
        """Add memory metrics to the application status bar."""
        memory_info = memory_manager.monitor.get_memory_usage()
        cache_stats = memory_manager.get_cache_stats()
        
        st.markdown(
            f"""
            <div style="position: fixed; bottom: 0; right: 0; padding: 5px; 
                       background-color: rgba(0,0,0,0.1); font-size: 12px; 
                       border-top-left-radius: 5px; z-index: 1000;">
                Process: {memory_info['process_rss']:.1f} MB | 
                System: {memory_info['system_percent']:.1f}% | 
                Cache: {cache_stats['size_mb']:.1f} MB
            </div>
            """,
            unsafe_allow_html=True
        )


# Create a global instance for easy access
memory_dashboard = MemoryDashboard()


def get_memory_dashboard() -> MemoryDashboard:
    """
    Get the global memory dashboard instance.
    
    Returns:
        The global memory dashboard instance
    """
    return memory_dashboard