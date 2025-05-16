"""
Session state management module for PhenoTag.

This module handles initialization and management of Streamlit session state,
providing functions to load and save session configuration.
"""
import os
import time
from pathlib import Path
import streamlit as st

from phenotag.io_tools import save_yaml, load_session_config


def initialize_session_state(session_config=None):
    """
    Initialize the session state variables from config or with defaults.
    
    Args:
        session_config (dict, optional): Configuration loaded from previous session.
    """
    # Initialize basic session state variables
    if 'data_directory' not in st.session_state:
        st.session_state.data_directory = session_config.get('data_directory', "") if session_config else ""
    if 'selected_station' not in st.session_state:
        st.session_state.selected_station = session_config.get('selected_station') if session_config else None
    if 'selected_instrument' not in st.session_state:
        st.session_state.selected_instrument = session_config.get('selected_instrument') if session_config else None
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = session_config.get('selected_year') if session_config else None
    if 'selected_day' not in st.session_state:
        st.session_state.selected_day = session_config.get('selected_day') if session_config else None
    if 'selected_days' not in st.session_state:
        st.session_state.selected_days = session_config.get('selected_days', []) if session_config else []
    if 'selected_month' not in st.session_state:
        st.session_state.selected_month = session_config.get('selected_month') if session_config else None
    if 'image_data' not in st.session_state:
        st.session_state.image_data = {}
    if 'current_filepath' not in st.session_state:
        st.session_state.current_filepath = None
    if 'selected_image_index' not in st.session_state:
        st.session_state.selected_image_index = 0  # Initialize with default of first image
    
    # Initialize ROI-related state
    if 'show_roi_overlays' not in st.session_state:
        st.session_state.show_roi_overlays = False
    
    # Initialize ROI toggle tracking flag
    if 'roi_toggle_changed' not in st.session_state:
        st.session_state.roi_toggle_changed = False


def save_session_config():
    """Save the current session configuration to a YAML file."""
    # Define the configuration file path
    config_dir = Path(os.path.expanduser("~/.phenotag"))
    config_file = config_dir / "sites_spectral_phenocams_session_config.yaml"
    
    # Create the configuration data
    config_data = {
        "data_directory": st.session_state.data_directory,
        "selected_station": st.session_state.selected_station if 'selected_station' in st.session_state else None,
        "selected_instrument": st.session_state.selected_instrument if 'selected_instrument' in st.session_state else None,
        "selected_year": st.session_state.selected_year,
        "selected_day": st.session_state.selected_day,
        "selected_days": st.session_state.selected_days if 'selected_days' in st.session_state else [],
        "selected_month": st.session_state.selected_month if 'selected_month' in st.session_state else None,
        "last_saved": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save the configuration
    success = save_yaml(config_data, config_file)
    return success


def load_config():
    """
    Load session configuration from the config file.
    
    Returns:
        dict: The loaded session configuration.
    """
    # Define the configuration file path
    config_dir = Path(os.path.expanduser("~/.phenotag"))
    config_file = config_dir / "sites_spectral_phenocams_session_config.yaml"
    
    # Load previous session configuration if available
    return load_session_config(config_file)


def reset_session():
    """Reset session state variables to their default values."""
    # Clear session state without using status container
    for key in ['data_directory', 'selected_station', 'selected_instrument',
                'selected_year', 'selected_day', 'selected_days', 'selected_month',
                'image_data', 'ready_notified']:
        if key in st.session_state:
            if key == 'image_data':
                st.session_state[key] = {}
            elif key == 'selected_days':
                st.session_state[key] = []
            else:
                st.session_state[key] = None
    
    st.session_state.data_directory = ""