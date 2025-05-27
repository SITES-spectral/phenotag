"""
Example implementation of image selection in data_editor for PhenoTag application

This shows how to implement row selection with thumbnails in a data_editor,
allowing users to click on a thumbnail to select and display an image.
"""

import streamlit as st
import pandas as pd
import numpy as np
import cv2
import base64
from pathlib import Path
import os
from typing import Optional, Tuple

class ImageProcessor:
    """Simplified version of ImageProcessor for demonstrating thumbnail generation"""
    
    def __init__(self):
        self.image = None
        self.file_path = None
    
    def load_image(self, file_path: str) -> bool:
        """Load an image from file path"""
        try:
            self.image = cv2.imread(file_path)
            self.file_path = file_path
            return self.image is not None
        except Exception as e:
            st.error(f"Error loading image: {e}")
            return False
    
    def create_thumbnail(self, max_size: Tuple[int, int] = (100, 100)) -> Optional[str]:
        """
        Create a thumbnail of the loaded image and return it as a base64-encoded string.
        
        Args:
            max_size: Maximum width and height of the thumbnail (width, height)
            
        Returns:
            str: Base64-encoded string representing the thumbnail image, or None if creation fails
        """
        if self.image is None:
            st.error("Error: No image loaded")
            return None
            
        try:
            # Use the current image
            img = self.image
                
            # Calculate the thumbnail size while maintaining aspect ratio
            h, w = img.shape[:2]
            max_w, max_h = max_size
            
            # Calculate new dimensions
            if h > w:
                new_h = max_h
                new_w = int(w * (max_h / h))
            else:
                new_w = max_w
                new_h = int(h * (max_w / w))
                
            # Resize the image
            thumbnail = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Convert from BGR to RGB
            thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', thumbnail)
            return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        except Exception as e:
            st.error(f"Error creating thumbnail: {str(e)}")
            return None


def demonstrate_data_editor_row_selection():
    """Demonstrate row selection in a data_editor with thumbnails"""
    
    st.title("PhenoTag Data Editor Row Selection")
    
    # Create a sample dataframe to simulate image data
    # In real app, this would come from your image scanning logic
    df = pd.DataFrame({
        "file_path": [f"sample_image_{i}.jpg" for i in range(1, 6)],
        "filename": [f"sample_image_{i}.jpg" for i in range(1, 6)],
        "discard_file": [False, False, False, False, False],
        "snow_presence": [False, True, False, False, True],
    })
    
    # Initialize session state for selected image
    session_key = "selected_image"
    if session_key not in st.session_state:
        # Set the first image as default if there are any images
        if not df.empty:
            st.session_state[session_key] = df.iloc[0]['file_path']
        else:
            st.session_state[session_key] = None
    
    # Create a key for the data editor
    editor_key = "image_data_editor"
    
    # Create a container for the image display
    with st.container():
        # Display selected image
        st.subheader("Image Preview", divider=True)
        current_image_path = st.session_state[session_key]
        
        # In a real app, you would use ImageProcessor to load and display the actual image
        # For this demo, we'll simulate image display
        st.info(f"Displaying image: {current_image_path}")
        
        # Simulate image display with a placeholder
        st.markdown("#### Image would appear here")
        st.code(f"# Code to display {current_image_path}")
    
    # Add a spacing between image preview and data editor
    st.write("")
    
    # Add navigation buttons above the data editor
    st.subheader("Image Navigation", divider=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    
    # Find current index in the dataframe
    current_index = 0
    if current_image_path in df['file_path'].values:
        current_index = df[df['file_path'] == current_image_path].index[0]
    
    with nav_col1:
        if st.button("⬅️ Previous Image", 
                   disabled=current_index <= 0,
                   use_container_width=True):
            # Get the previous image path
            prev_index = max(0, current_index - 1)
            prev_image_path = df.iloc[prev_index]['file_path']
            # Update session state
            st.session_state[session_key] = prev_image_path
            st.rerun()
                            
    with nav_col2:
        # Display current position
        st.markdown(f"**Image {current_index + 1} of {len(df)}**", 
                   help="Current image position")
        
    with nav_col3:
        if st.button("Next Image ➡️", 
                   disabled=current_index >= len(df) - 1,
                   use_container_width=True):
            # Get the next image path
            next_index = min(len(df) - 1, current_index + 1)
            next_image_path = df.iloc[next_index]['file_path']
            # Update session state
            st.session_state[session_key] = next_image_path
            st.rerun()
    
    # Add a spacing before the data editor
    st.write("")
    
    # Subheader for image selection
    st.subheader("Image Selection", divider=True)
    
    # Create a selectbox for selecting an image by filename
    filenames = df['filename'].tolist()
    file_paths = df['file_path'].tolist()
    file_dict = dict(zip(filenames, file_paths))
    
    # Find current filename
    current_filename = os.path.basename(current_image_path) if current_image_path else filenames[0] if filenames else ""
    
    selected_filename = st.selectbox(
        "Select image by filename",
        options=filenames,
        index=filenames.index(current_filename) if current_filename in filenames else 0,
        key="filename_selector"
    )
    
    # Update the selected image path if the filename changed
    if selected_filename in file_dict and file_dict[selected_filename] != current_image_path:
        st.session_state[session_key] = file_dict[selected_filename]
        st.rerun()
    
    # Add a spacing before the data editor
    st.write("")
    
    # Subheader for data editor section
    st.subheader("Image Selection with Thumbnails", divider=True)
    
    # Add instructions for using thumbnails
    st.info("👉 Click on a thumbnail to select that image for viewing.")
    
    # Simulate adding thumbnails to the dataframe
    # In a real app, you'd use ImageProcessor to create actual thumbnails
    df["thumbnail"] = ["data:image/png;base64,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"] * len(df)
    
    # Configure column settings for data editor with thumbnails
    column_config = {
        "thumbnail": st.column_config.ImageColumn(
            "Preview", help="Click to select this image", width="medium"),
        "filename": st.column_config.TextColumn("Filename", width="medium"),
        "file_path": st.column_config.TextColumn("File Path", width="medium"),
        "discard_file": st.column_config.CheckboxColumn("Discard File", width="small"),
        "snow_presence": st.column_config.CheckboxColumn("Snow Presence", width="small"),
    }
    
    # Create the data editor with thumbnails
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        num_rows="fixed",
        hide_index=False,  # Show index for easier selection
        column_order=["thumbnail", "filename", "file_path", "discard_file", "snow_presence"],
        key=editor_key
    )
    
    # Store the last edited data in session_state to prevent infinite loops
    if "last_edited_data" not in st.session_state:
        st.session_state.last_edited_data = None
    
    # Check if an image was clicked by detecting changes in edited dataframe
    if edited_df is not None and 'thumbnail' in edited_df.columns:
        # Convert current dataframe to a hashable representation for comparison
        current_df_state = tuple(row['file_path'] for i, row in edited_df.iterrows())
        
        # Only update if this is a new edit (prevents infinite loops)
        if st.session_state.last_edited_data != current_df_state:
            # Store current state to avoid repeating
            st.session_state.last_edited_data = current_df_state
            
            # Make sure we can identify which row was clicked
            for i, row in edited_df.iterrows():
                if row['file_path'] != current_image_path:
                    # Different thumbnail clicked, update selection
                    st.session_state[session_key] = row['file_path']
                    st.rerun()
                    break
    
    # Explain how to implement this in the actual application
    st.divider()
    st.subheader("Implementation Notes")
    st.write("""
    To implement this functionality in your PhenoTag application:
    
    1. **Thumbnail Generation**: Use the `ImageProcessor.create_thumbnail()` method to generate base64-encoded thumbnails for each image.
    
    2. **Row Selection Callback**: Use the approach shown above to detect when a user clicks on a thumbnail:
       - Store the currently selected image path in session state
       - When iterating through the dataframe, check if any row's file_path differs from the current selection
       - If a change is detected, update the session state and rerun the app
    
    3. **Multiple Selection Methods**: Provide different ways to select images:
       - Thumbnail clicks in the data_editor
       - Filename dropdown selection
       - Next/Previous navigation buttons
    
    4. **Display Selected Image**: Load and display the selected image using the ImageProcessor
    
    5. **Avoid Experimental API**: Remember to use `st.rerun()` instead of the deprecated `st.experimental_rerun()`
    """)


if __name__ == "__main__":
    demonstrate_data_editor_row_selection()