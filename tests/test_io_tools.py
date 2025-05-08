#!/usr/bin/env python3
import unittest
from pathlib import Path
import tempfile
import yaml
import requests
from unittest.mock import patch, mock_open
from phenotag.io_tools import load_yaml


class TestLoadYaml(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_yaml_content = {
            'test_key': 'test_value',
            'nested': {
                'key': 'value'
            }
        }
        self.yaml_string = yaml.dump(self.test_yaml_content)

    def test_load_yaml_from_local_file(self):
        """Test loading YAML from a local file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(self.test_yaml_content, temp_file)
            temp_file_path = temp_file.name

        try:
            result = load_yaml(temp_file_path)
            self.assertEqual(result, self.test_yaml_content)
        finally:
            Path(temp_file_path).unlink()

    def test_load_yaml_from_path_object(self):
        """Test loading YAML using a Path object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(self.test_yaml_content, temp_file)
            temp_file_path = Path(temp_file.name)

        try:
            result = load_yaml(temp_file_path)
            self.assertEqual(result, self.test_yaml_content)
        finally:
            temp_file_path.unlink()

    @patch('requests.get')
    def test_load_yaml_from_url(self, mock_get):
        """Test loading YAML from a URL."""
        mock_response = mock_get.return_value
        mock_response.text = self.yaml_string
        mock_response.raise_for_status.return_value = None

        result = load_yaml('http://example.com/test.yaml')
        self.assertEqual(result, self.test_yaml_content)
        mock_get.assert_called_once_with('http://example.com/test.yaml')

    def test_load_yaml_file_not_found(self):
        """Test loading YAML from a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_yaml('nonexistent_file.yaml')

    @patch('requests.get')
    def test_load_yaml_url_not_found(self, mock_get):
        """Test loading YAML from a non-existent URL."""
        mock_get.side_effect = requests.RequestException('404 Not Found')
        
        with self.assertRaises(requests.RequestException):
            load_yaml('http://example.com/nonexistent.yaml')

    def test_load_yaml_invalid_yaml(self):
        """Test loading invalid YAML content."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write(invalid_yaml)
            temp_file_path = temp_file.name

        try:
            with self.assertRaises(yaml.YAMLError):
                load_yaml(temp_file_path)
        finally:
            Path(temp_file_path).unlink()

    @patch('requests.get')
    def test_load_yaml_invalid_yaml_from_url(self, mock_get):
        """Test loading invalid YAML content from URL."""
        mock_response = mock_get.return_value
        mock_response.text = "invalid: yaml: content: ["
        mock_response.raise_for_status.return_value = None

        with self.assertRaises(yaml.YAMLError):
            load_yaml('http://example.com/invalid.yaml')


if __name__ == '__main__':
    unittest.main() 