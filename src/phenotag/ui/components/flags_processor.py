"""
Flag processing utilities for PhenoTag UI.

This module provides functionality for processing and accessing 
quality flags from configuration files.
"""
import re
from typing import List, Dict, Tuple, Any

class FlagsProcessor:
    """
    Process and manage flag data from flags.yaml configuration.
    
    This class loads the flags configuration and provides methods to
    retrieve formatted flag data for use in the UI components.
    """
    
    def __init__(self, flags_data: Dict):
        """
        Initialize the FlagsProcessor with flags data.
        
        Parameters:
        -----------
        flags_data : Dict
            The flags data loaded from flags.yaml
        """
        self.flags_data = flags_data
        # Process flags on initialization
        self.flag_names, self.flag_categories, self.flag_details = self._process_flags()
    
    def _process_flags(self) -> Tuple[List[str], Dict[str, List[str]], Dict[str, Dict[str, Any]]]:
        """
        Process flags data to extract names, categories, and details.
        
        Returns:
        --------
        Tuple[List[str], Dict[str, List[str]], Dict[str, Dict[str, Any]]]
            - List of flag names without 'iflag_' prefix
            - Dictionary mapping categories to lists of flag names
            - Dictionary mapping flag names to their details
        """
        # Extract flag names without 'iflag_' prefix
        flag_names = [re.sub(r'^iflag_', '', key) for key in self.flags_data.keys()]
        
        # Group flags by category
        flag_categories = {}
        flag_details = {}
        
        for flag_key, flag_info in self.flags_data.items():
            # Skip any non-flag entries
            if not isinstance(flag_info, dict) or 'category' not in flag_info:
                continue
                
            clean_name = re.sub(r'^iflag_', '', flag_key)
            category = flag_info.get('category', 'Uncategorized')
            
            # Store flag details
            flag_details[clean_name] = {
                'description': flag_info.get('description', ''),
                'category': category,
                'penalty_value': flag_info.get('penalty_value', 0),
                'dwc_mapping': flag_info.get('DwC_mapping', '')
            }
            
            # Group by category
            if category not in flag_categories:
                flag_categories[category] = []
            
            flag_categories[category].append(clean_name)
        
        # Sort flags within each category
        for category in flag_categories:
            flag_categories[category].sort()
        
        return flag_names, flag_categories, flag_details
    
    def get_flag_details(self, flag_name: str) -> Dict[str, Any]:
        """
        Get details for a specific flag.
        
        Parameters:
        -----------
        flag_name : str
            Name of the flag without 'iflag_' prefix
            
        Returns:
        --------
        Dict[str, Any]
            Dictionary with flag details
        """
        return self.flag_details.get(flag_name, {})
    
    def get_flag_options(self) -> List[Dict[str, Any]]:
        """
        Get formatted flag options for use in Streamlit UI components.
        
        Returns:
        --------
        List[Dict[str, Any]]
            List of dictionaries with flag options
        """
        flag_options = []
        
        # Sort categories
        sorted_categories = sorted(self.flag_categories.keys())
        
        # Add all flags in category order
        for category in sorted_categories:
            # Sort flags within each category
            category_flags = sorted(self.flag_categories[category])
            
            for flag_name in category_flags:
                details = self.flag_details[flag_name]
                
                flag_options.append({
                    "value": flag_name,  # Value used internally
                    "label": flag_name,  # Display text
                    "description": details.get('description', ''),  # Tooltip text
                    "penalty": details.get('penalty_value', 0),  # For sorting by importance
                    "category": category
                })
        
        return flag_options
        
    def get_flag_values(self) -> List[str]:
        """
        Get just the flag values (names) for simple list operations.
        
        Returns:
        --------
        List[str]
            List of flag names without additional metadata
        """
        # Get all flag names sorted alphabetically
        return sorted(self.flag_names)