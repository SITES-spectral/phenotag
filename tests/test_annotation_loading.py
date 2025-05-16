"""
Tests for the annotation loading and saving functionality.

These tests verify that annotation loading shows spinners, prevents
concurrent saves during loading, and works correctly with the new
save button implementation.
"""
import os
import pytest
import tempfile
import yaml
import datetime
from unittest.mock import patch, MagicMock, Mock

import streamlit as st
from phenotag.ui.components.annotation import load_day_annotations, save_all_annotations


def test_loading_state_flag():
    """Test that the loading flag is set and cleared properly."""
    # Setup mock session state with __getitem__ and __setitem__ to simulate dict-like behavior
    mock_session_state = Mock()
    mock_session_state.__getitem__ = lambda self, key: False if key == 'loading_annotations' else {}
    mock_session_state.__setitem__ = lambda self, key, value: None
    mock_session_state.get = lambda key, default=None: False
    
    # Mock the spinner to avoid actual UI rendering
    spinner_mock_context = MagicMock()
    spinner_mock_context.__enter__ = MagicMock(return_value=None)
    spinner_mock_context.__exit__ = MagicMock(return_value=None)
    mock_spinner = MagicMock(return_value=spinner_mock_context)
    
    with patch('streamlit.session_state', mock_session_state):
        with patch('streamlit.spinner', mock_spinner):
            # Mock open and yaml to avoid file operations
            with patch('builtins.open', MagicMock()):
                with patch('yaml.safe_load', return_value={'annotations': {}}):
                    # Create a temp directory structure for the test
                    with tempfile.TemporaryDirectory() as tmpdirname:
                        # Simulate daily filepaths
                        day_dir = os.path.join(tmpdirname, "123")
                        os.makedirs(day_dir, exist_ok=True)
                        daily_filepaths = [os.path.join(day_dir, f"test{i}.jpg") for i in range(3)]
                        
                        # Also patch the annotation timer
                        with patch('phenotag.ui.components.annotation_timer.annotation_timer') as mock_timer:
                            # Call load_day_annotations
                            load_day_annotations("123", daily_filepaths)
                            
                            # Verify the spinner was called
                            mock_spinner.assert_called()
                            
                            # Check that we tried to set the loading flag
                            assert mock_session_state.__setitem__.called


def test_prevent_save_during_load():
    """Test that save operations are prevented during loading."""
    # Setup session state with loading_annotations flag set to True
    with patch('streamlit.session_state', {'loading_annotations': True}) as mock_session_state:
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            # Call save_all_annotations
            save_all_annotations()
            
            # Verify that save was skipped
            mock_print.assert_called_with("Skipping annotation save: currently loading annotations")


def test_save_with_force_save():
    """Test that force_save overrides auto_save_enabled setting."""
    # Setup mock session state with auto_save disabled
    mock_session_state = {
        'auto_save_enabled': False,
        'immediate_save_enabled': False,
        'loading_annotations': False,
        'image_annotations': {}
    }
    
    with patch('streamlit.session_state', mock_session_state):
        # Mock other dependencies to prevent actual file operations
        with patch('builtins.print') as mock_print:
            with patch('phenotag.ui.components.annotation_timer.annotation_timer') as mock_timer:
                with patch('phenotag.io_tools.save_yaml') as mock_save:
                    with patch('streamlit.toast') as mock_toast:
                        # Call save_all_annotations with force_save=True
                        save_all_annotations(force_save=True)
                        
                        # Verify save was attempted (not skipped due to auto_save being disabled)
                        mock_toast.assert_called()


def test_save_skipped_when_auto_save_disabled():
    """Test that save is skipped when auto_save is disabled."""
    # Setup mock session state with auto_save disabled
    mock_session_state = {
        'auto_save_enabled': False,
        'immediate_save_enabled': False,
        'loading_annotations': False
    }
    
    with patch('streamlit.session_state', mock_session_state):
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            # Call save_all_annotations
            save_all_annotations()
            
            # Verify that save was skipped
            mock_print.assert_called_with("Skipping annotation save: auto-save is disabled and not forcing")


def test_load_marks_just_loaded_flag():
    """Test that load_day_annotations sets the annotations_just_loaded flag."""
    # Setup mock session state with __getitem__ and __setitem__ to simulate dict-like behavior
    mock_session_state = Mock()
    mock_session_state.__getitem__ = lambda self, key: {}
    mock_session_state.__setitem__ = lambda self, key, value: None
    mock_session_state.get = lambda key, default=None: default
    
    # Mock the spinner
    spinner_mock_context = MagicMock()
    spinner_mock_context.__enter__ = MagicMock(return_value=None)
    spinner_mock_context.__exit__ = MagicMock(return_value=None)
    mock_spinner = MagicMock(return_value=spinner_mock_context)
    
    with patch('streamlit.session_state', mock_session_state):
        with patch('streamlit.spinner', mock_spinner):
            # Mock os.path.exists to return True
            with patch('os.path.exists', return_value=True):
                # Mock open and yaml.safe_load
                mock_file = MagicMock()
                mock_file.__enter__.return_value = mock_file
                
                with patch('builtins.open', return_value=mock_file):
                    with patch('yaml.safe_load', return_value={'annotations': {'image.jpg': []}}):
                        # Mock success message
                        with patch('streamlit.success'):
                            # Create a temp directory structure for the test
                            with tempfile.TemporaryDirectory() as tmpdirname:
                                # Simulate daily filepaths
                                day_dir = os.path.join(tmpdirname, "123")
                                os.makedirs(day_dir, exist_ok=True)
                                daily_filepaths = [os.path.join(day_dir, "image.jpg")]
                                
                                # Also patch the annotation timer
                                with patch('phenotag.ui.components.annotation_timer.annotation_timer') as mock_timer:
                                    # Call load_day_annotations
                                    load_day_annotations("123", daily_filepaths)
                                    
                                    # Verify setting the annotations_just_loaded flag was attempted
                                    mock_session_state.__setitem__.assert_any_call('annotations_just_loaded', True)


if __name__ == "__main__":
    # Run the tests (uncomment to run standalone)
    # pytest.main(["-xvs", __file__])
    pass