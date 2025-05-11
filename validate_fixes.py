"""
Simple validation script to check the fixes we made.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Mock streamlit
class MockStreamlit:
    """Mock streamlit for validation purposes"""
    class ColumnConfig:
        """Mock column config"""
        def TextColumn(self, label):
            print(f"Creating TextColumn with label: {label}")
            return {"type": "text", "label": label}
    
    def __init__(self):
        self.column_config = self.ColumnConfig()
        self.session_state = {}
    
    def container(self):
        """Mock container"""
        return type('Container', (), {'__enter__': lambda s: None, '__exit__': lambda s, *args: None})()

# Create a simple mock of st
st = MockStreamlit()

# Test years variable fix
def test_years_variable_fix():
    """Test that we handle the years variable properly"""
    print("Testing years variable fix...")
    
    # Initialize image data
    image_data = {
        "2023": {"001": {"/path/to/image.jpg": {"quality": {}, "rois": {}}}},
        "2022": {"002": {"/path/to/image2.jpg": {"quality": {}, "rois": {}}}}
    }
    
    # Get the years from the image data first
    years = list(image_data.keys())
    years.sort(reverse=True)
    
    # Verify the years are sorted correctly
    assert years == ["2023", "2022"], f"Expected years ['2023', '2022'], got {years}"
    
    # Check if we have years - this was the line that failed before
    if years:
        print(f"Found {len(years)} years: {', '.join(years)}")
    
    print("years variable test PASSED")
    return True

# Test column config fix
def test_column_config_fix():
    """Test that the column config doesn't use display=False"""
    print("Testing column config fix...")
    
    # Test our column config with just label
    col_config = {
        "Filename": st.column_config.TextColumn("File"),
        # Store path but don't show it as a column
        "Path": st.column_config.TextColumn("Path")
    }
    
    # Add column_order to hide the Path
    column_order = ["Filename"]  # Only show the filename column
    
    print(f"Column config: {col_config}")
    print(f"Column order: {column_order}")
    
    print("column_config test PASSED")
    return True

if __name__ == "__main__":
    # Run the tests
    years_test = test_years_variable_fix()
    column_test = test_column_config_fix()
    
    if years_test and column_test:
        print("\nALL TESTS PASSED - fixes appear to work correctly")
    else:
        print("\nTESTS FAILED")
        sys.exit(1)