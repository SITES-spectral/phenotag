#!/usr/bin/env python3
import unittest
import tempfile
import yaml
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from phenotag.io_tools import load_yaml


class YAMLRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that serves YAML content."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/valid.yaml':
            self.send_response(200)
            self.send_header('Content-type', 'text/yaml')
            self.end_headers()
            yaml_content = yaml.dump({'test': 'value'})
            self.wfile.write(yaml_content.encode())
        elif self.path == '/invalid.yaml':
            self.send_response(200)
            self.send_header('Content-type', 'text/yaml')
            self.end_headers()
            self.wfile.write(b'invalid: yaml: content: [')
        elif self.path == '/not_found.yaml':
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(500)
            self.end_headers()


class TestLoadYamlIntegration(unittest.TestCase):
    """Integration tests for load_yaml function using a real HTTP server."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test HTTP server."""
        cls.server = HTTPServer(('localhost', 0), YAMLRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        # Give the server a moment to start
        time.sleep(0.1)
        cls.server_url = f'http://localhost:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        """Shut down the test HTTP server."""
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    def test_load_valid_yaml_from_server(self):
        """Test loading valid YAML from the test server."""
        url = f'{self.server_url}/valid.yaml'
        result = load_yaml(url)
        self.assertEqual(result, {'test': 'value'})

    def test_load_invalid_yaml_from_server(self):
        """Test loading invalid YAML from the test server."""
        url = f'{self.server_url}/invalid.yaml'
        with self.assertRaises(yaml.YAMLError):
            load_yaml(url)

    def test_load_nonexistent_yaml_from_server(self):
        """Test loading non-existent YAML from the test server."""
        url = f'{self.server_url}/not_found.yaml'
        with self.assertRaises(requests.RequestException):
            load_yaml(url)

    def test_load_yaml_with_network_timeout(self):
        """Test loading YAML with network timeout."""
        # Use a non-existent port to simulate timeout
        url = 'http://localhost:99999/test.yaml'
        with self.assertRaises(requests.RequestException):
            load_yaml(url)

    def test_load_yaml_with_ssl_error(self):
        """Test loading YAML with SSL error."""
        # Use HTTPS with invalid certificate
        url = 'https://self-signed.badssl.com/test.yaml'
        with self.assertRaises(requests.RequestException):
            load_yaml(url)


if __name__ == '__main__':
    unittest.main() 