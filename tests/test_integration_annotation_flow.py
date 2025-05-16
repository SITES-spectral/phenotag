"""
Integration tests for the annotation loading and saving workflow.

These tests verify the full annotation flow including:
- Loading annotations with the spinner
- Preventing concurrent saves during loading
- Manual saving with the save button
- Auto-save behavior based on settings
"""
import os
import pytest
import tempfile
import yaml
import time
import datetime
from unittest.mock import patch, MagicMock, Mock, call

import streamlit as st
from phenotag.ui.components.annotation import load_day_annotations, save_all_annotations, display_annotation_panel


class TestAnnotationIntegrationFlow:
    """Test class for verifying the full annotation flow."""
    
    @pytest.fixture
    def setup_test_environment(self):
        """Fixture to set up the test environment with mock session state and dependencies."""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a structure mimicking the expected directory structure
            station_dir = os.path.join(tmpdirname, "teststation")
            instrument_dir = os.path.join(station_dir, "phenocams", "products", "testcam")
            l1_dir = os.path.join(instrument_dir, "L1")
            day_dir = os.path.join(l1_dir, "123")
            
            # Create the directories
            os.makedirs(day_dir, exist_ok=True)
            
            # Create test image paths
            test_image_paths = [os.path.join(day_dir, f"image_{i}.jpg") for i in range(3)]
            
            # Set up a test annotation file
            test_annotations = {
                "created": datetime.datetime.now().isoformat(),
                "day_of_year": "123",
                "station": "teststation",
                "instrument": "testcam",
                "annotation_time_minutes": 10.5,
                "annotations": {
                    f"image_{i}.jpg": [
                        {
                            "roi_name": "ROI_00",
                            "discard": False,
                            "snow_presence": False,
                            "flags": ["test_flag1", "test_flag2"]
                        },
                        {
                            "roi_name": "ROI_01",
                            "discard": True,
                            "snow_presence": True,
                            "flags": ["test_flag3"]
                        }
                    ] for i in range(3)
                }
            }
            
            # Write the test annotation file
            annotations_file = os.path.join(day_dir, "annotations_123.yaml")
            with open(annotations_file, 'w') as f:
                yaml.dump(test_annotations, f)
            
            # Set up a mock session state
            mock_session_state = {
                'selected_station': 'teststation',
                'selected_instrument': 'testcam',
                'selected_year': datetime.datetime.now().year,
                'scan_info': {'base_dir': tmpdirname},
                'instrument_rois': {'ROI_01': {}}  # Mock ROI definition
            }
            
            # Return the test data
            yield {
                'base_dir': tmpdirname,
                'l1_dir': l1_dir,
                'day_dir': day_dir,
                'test_image_paths': test_image_paths,
                'annotations_file': annotations_file,
                'mock_session_state': mock_session_state,
                'test_annotations': test_annotations
            }
    
    def test_full_annotation_flow(self, setup_test_environment):
        """Test the full annotation loading and saving flow."""
        env = setup_test_environment
        
        # Create a better mock session state with dict-like behavior
        mock_session_state = Mock()
        mock_data = {'image_annotations': {}}
        for key, value in env['mock_session_state'].items():
            mock_data[key] = value
        
        # Configure the mock to act like a dict
        mock_session_state.__getitem__ = lambda self, key: mock_data.get(key, {})
        mock_session_state.__setitem__ = lambda self, key, value: mock_data.update({key: value})
        mock_session_state.get = lambda key, default=None: mock_data.get(key, default)
        
        # Create patches for all external dependencies
        with patch('streamlit.session_state', mock_session_state):
            # Mock the spinner
            spinner_context = MagicMock()
            spinner_context.__enter__ = MagicMock(return_value=None)
            spinner_context.__exit__ = MagicMock(return_value=None)
            mock_spinner = MagicMock(return_value=spinner_context)
            
            # Mock other streamlit components
            mock_success = MagicMock()
            mock_error = MagicMock()
            mock_rerun = MagicMock()
            mock_button = MagicMock(return_value=True)  # Simulate button press
            mock_toast = MagicMock()
            
            # Mock the annotation timer
            mock_timer = MagicMock()
            mock_timer.get_elapsed_time_minutes.return_value = 5.0
            mock_timer.get_formatted_time.return_value = "00:05:00"
            
            with patch('streamlit.spinner', mock_spinner):
                with patch('streamlit.success', mock_success):
                    with patch('streamlit.error', mock_error):
                        with patch('os.path.exists', return_value=True):
                            with patch('builtins.open', MagicMock()):
                                with patch('yaml.safe_load', return_value={'annotations': {'image_0.jpg': []}}):
                                    with patch('phenotag.ui.components.annotation_timer.annotation_timer', mock_timer):
                                        # Step 1: Load annotations for the test day
                                        load_day_annotations("123", env['test_image_paths'])
                                        
                                        # Verify spinner was called with the correct day
                                        mock_spinner.assert_called_with(f"Loading annotations for day 123...")
                                        
                                        # Verify we set the loading_annotations flag
                                        mock_session_state.__setitem__.assert_any_call('loading_annotations', True)
                                        
                                        # Verify success message was shown
                                        mock_success.assert_called_with(f"Loaded annotations for day 123", icon="✅")
                                        
                                        # Step 2: Test that we skip saving during loading
                                        with patch('builtins.print') as mock_print:
                                            # Set loading flag to true
                                            mock_data['loading_annotations'] = True
                                            
                                            # Try to save
                                            save_all_annotations()
                                            
                                            # Verify save was skipped with correct message
                                            mock_print.assert_called_with("Skipping annotation save: currently loading annotations")
                                            
                                            # Reset loading flag for next tests
                                            mock_data['loading_annotations'] = False
                                        
                                        # Step 3: Test manual save with button press
                                        with patch('phenotag.io_tools.save_yaml') as mock_save_yaml:
                                            # Set up session state for saving
                                            mock_data['unsaved_changes'] = True
                                            mock_data['auto_save_enabled'] = False
                                            mock_data['immediate_save_enabled'] = False
                                            
                                            with patch('streamlit.toast', mock_toast):
                                                # Simulate manual save button press by calling with force_save=True
                                                save_all_annotations(force_save=True)
                                                
                                                # Verify toast notification was shown
                                                assert mock_toast.called, "Toast notification should be shown after save"
                                                
                                                # Verify we tried to update session state
                                                mock_session_state.__setitem__.assert_any_call('unsaved_changes', False)
                                                mock_keys = [args[0] for args, _ in mock_session_state.__setitem__.call_args_list]
                                                assert 'last_save_time' in mock_keys, "last_save_time should be set after save"
                                                
                                                # Verify save_yaml was called (actual saving attempted)
                                                assert mock_save_yaml.called, "save_yaml should be called during save"


if __name__ == "__main__":
    # Run the tests (uncomment to run standalone)
    # pytest.main(["-xvs", __file__])
    pass