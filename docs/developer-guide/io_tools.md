# IO Tools Module Documentation

The `io_tools` module provides utility functions for handling input/output operations in the PhenoTag application, with a particular focus on YAML file handling.

## Functions

### `load_yaml(filepath: Union[str, Path]) -> dict`

Loads and parses a YAML file from either a local path or a URL.

#### Parameters

- `filepath` (Union[str, Path]): The path to the YAML file or a URL pointing to a YAML file.
  - Can be a local file path (e.g., `/path/to/file.yaml`)
  - Can be a URL (e.g., `http://example.com/config.yaml`)

#### Returns

- `dict`: The parsed contents of the YAML file as a Python dictionary.

#### Raises

- `FileNotFoundError`: If the specified local file does not exist.
- `yaml.YAMLError`: If there is an error parsing the YAML content.
- `requests.RequestException`: If there is an error fetching the YAML file from a URL.

#### Usage Examples

```python
from phenotag.io_tools import load_yaml

# Load from local file
config = load_yaml("/path/to/config.yaml")

# Load from URL
remote_config = load_yaml("http://example.com/config.yaml")
```

#### Error Handling

The function includes comprehensive error handling for various scenarios:

1. Local file errors:
   - File not found
   - Invalid YAML format

2. URL-based errors:
   - Network connectivity issues
   - Invalid HTTP responses
   - Invalid YAML format in remote content

## Dependencies

The module requires the following Python packages:
- `pathlib`: For path manipulation
- `requests`: For HTTP requests
- `yaml`: For YAML parsing

## Notes

- The function automatically detects whether the input is a URL or a local file path.
- All file operations use UTF-8 encoding.
- The function uses `yaml.safe_load()` for secure YAML parsing. 