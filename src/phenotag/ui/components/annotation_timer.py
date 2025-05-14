"""
Annotation timer component for PhenoTag.

This module tracks the time spent on annotating images for a specific day,
pausing after inactivity and persisting timing data across sessions.
"""
import time
import datetime
import streamlit as st


class AnnotationTimer:
    """
    Tracks time spent on annotations with inactivity detection.
    
    The timer measures active annotation time and automatically pauses
    after a period of inactivity (default 3 minutes).
    """
    
    def __init__(self, inactivity_threshold_seconds=180):
        """
        Initialize the annotation timer.
        
        Args:
            inactivity_threshold_seconds (int): Seconds of inactivity before pausing timer
        """
        self.inactivity_threshold = inactivity_threshold_seconds
        self.initialized = False
        
    def initialize_session_state(self):
        """Initialize timer-related session state variables if not already present."""
        if not self.initialized:
            # Timer state variables
            if 'annotation_timer_active' not in st.session_state:
                st.session_state.annotation_timer_active = False
            
            if 'annotation_timer_start' not in st.session_state:
                st.session_state.annotation_timer_start = None
                
            if 'annotation_timer_accumulated' not in st.session_state:
                st.session_state.annotation_timer_accumulated = {}
                
            if 'annotation_timer_last_interaction' not in st.session_state:
                st.session_state.annotation_timer_last_interaction = time.time()
                
            if 'annotation_timer_current_day' not in st.session_state:
                st.session_state.annotation_timer_current_day = None
            
            self.initialized = True
    
    def start_timer(self, day):
        """
        Start or resume the annotation timer for a specific day.
        
        Args:
            day (str): Day of year being annotated
        """
        self.initialize_session_state()
        
        # Record the current day
        st.session_state.annotation_timer_current_day = day
        
        # Initialize accumulated time for this day if not exists
        if day not in st.session_state.annotation_timer_accumulated:
            st.session_state.annotation_timer_accumulated[day] = 0
            
        # If timer is not active, start it
        if not st.session_state.annotation_timer_active:
            st.session_state.annotation_timer_start = time.time()
            st.session_state.annotation_timer_active = True
            
        # Reset last interaction time to now
        st.session_state.annotation_timer_last_interaction = time.time()
    
    def record_interaction(self):
        """Record user interaction to keep timer active."""
        self.initialize_session_state()
        
        # Update last interaction time
        st.session_state.annotation_timer_last_interaction = time.time()
        
        # If timer is not active but we have a current day, restart it
        if not st.session_state.annotation_timer_active and st.session_state.annotation_timer_current_day:
            self.start_timer(st.session_state.annotation_timer_current_day)
    
    def check_inactivity(self):
        """
        Check for inactivity and pause timer if threshold exceeded.
        
        Returns:
            bool: True if timer is active, False otherwise
        """
        self.initialize_session_state()
        
        # Skip if timer is not active
        if not st.session_state.annotation_timer_active:
            return False
            
        # Calculate time since last interaction
        current_time = time.time()
        elapsed_since_interaction = current_time - st.session_state.annotation_timer_last_interaction
        
        # If inactive for too long, pause the timer
        if elapsed_since_interaction > self.inactivity_threshold:
            self.pause_timer()
            return False
            
        return True
    
    def pause_timer(self):
        """Pause the timer and accumulate elapsed time."""
        self.initialize_session_state()
        
        # Skip if timer is not active
        if not st.session_state.annotation_timer_active:
            return
            
        # Get current day
        day = st.session_state.annotation_timer_current_day
        if not day:
            return
            
        # Calculate elapsed time since timer started
        current_time = time.time()
        elapsed = current_time - st.session_state.annotation_timer_start
        
        # Add to accumulated time for this day
        if day in st.session_state.annotation_timer_accumulated:
            st.session_state.annotation_timer_accumulated[day] += elapsed
        else:
            st.session_state.annotation_timer_accumulated[day] = elapsed
            
        # Mark timer as inactive
        st.session_state.annotation_timer_active = False
        st.session_state.annotation_timer_start = None
    
    def get_elapsed_time(self, day):
        """
        Get total elapsed time for a specific day in seconds.
        
        Args:
            day (str): Day of year
            
        Returns:
            float: Total elapsed time in seconds
        """
        self.initialize_session_state()
        
        # Get accumulated time for this day
        accumulated = st.session_state.annotation_timer_accumulated.get(day, 0)
        
        # If timer is active and for this day, add current session time
        if (st.session_state.annotation_timer_active and 
            st.session_state.annotation_timer_current_day == day and
            st.session_state.annotation_timer_start):
            
            current_time = time.time()
            current_session = current_time - st.session_state.annotation_timer_start
            return accumulated + current_session
            
        return accumulated
    
    def get_elapsed_time_minutes(self, day):
        """
        Get total elapsed time for a specific day in minutes.
        
        Args:
            day (str): Day of year
            
        Returns:
            float: Total elapsed time in minutes
        """
        seconds = self.get_elapsed_time(day)
        return seconds / 60
    
    def get_formatted_time(self, day):
        """
        Get formatted time string (HH:MM:SS) for a specific day.
        
        Args:
            day (str): Day of year
            
        Returns:
            str: Formatted time string
        """
        seconds = int(self.get_elapsed_time(day))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def set_accumulated_time(self, day, minutes):
        """
        Set accumulated time for a specific day.
        
        Args:
            day (str): Day of year
            minutes (float): Time in minutes
        """
        self.initialize_session_state()
        
        # Convert minutes to seconds and store
        st.session_state.annotation_timer_accumulated[day] = minutes * 60


# Create a singleton instance
annotation_timer = AnnotationTimer()