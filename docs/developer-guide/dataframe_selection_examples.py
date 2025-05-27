"""
Example implementations of data_editor row selection with callbacks

This file contains examples of how to track changes in a Streamlit data_editor
and implement row click detection.
"""

import streamlit as st
import pandas as pd
import numpy as np


def method1_on_select_rerun():
    """
    Method 1: Using on_select="rerun" (Streamlit version >= 1.25.0)
    
    This method uses the on_select parameter to automatically rerun the app
    when a row is selected, along with selection_mode to allow selecting rows.
    """
    st.header("Method 1: Using on_select='rerun'")
    
    # Create sample data
    df = pd.DataFrame({
        "File": [f"image_{i}.jpg" for i in range(1, 6)],
        "Width": [800, 1024, 640, 1280, 800],
        "Height": [600, 768, 480, 720, 600],
        "Size (KB)": [150, 220, 100, 350, 180],
    })
    
    st.write("Click on any row to select it:")
    
    # Display data_editor with row selection enabled
    selection = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",           # Rerun app when row is selected
        selection_mode="single-row", # Allow single row selection
    )
    
    # Get the selected rows
    selected_rows = selection.selection.rows
    
    # Display the selection
    if selected_rows:
        st.success(f"Row selected: {selected_rows[0]}")
        selected_file = df.iloc[selected_rows[0]]["File"]
        st.write(f"Selected file: {selected_file}")
        
        # You can now do something with the selected file, like display it
        st.write(f"Displaying {selected_file}...")
        
        # Example: simulating image display
        st.code(f"# Code to display {selected_file}")
    else:
        st.info("No row selected yet. Click on a row to select it.")


def method2_session_state():
    """
    Method 2: Using Session State to track changes
    
    This method works with any Streamlit version. It uses session state to track
    which row was selected by comparing current data with previous state.
    """
    st.header("Method 2: Using Session State")
    
    # Create sample data
    df = pd.DataFrame({
        "File": [f"image_{i}.jpg" for i in range(1, 6)],
        "Width": [800, 1024, 640, 1280, 800],
        "Height": [600, 768, 480, 720, 600],
        "Size (KB)": [150, 220, 100, 350, 180],
    })
    
    # Add a column for row selection
    df_with_selection = df.copy()
    df_with_selection.insert(0, "Select", False)
    
    # Initialize session state for selection
    if "previous_selection" not in st.session_state:
        st.session_state.previous_selection = None
    
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None

    st.write("Click on the checkbox to select a row:")
    
    # Display data_editor with selection column
    edited_df = st.data_editor(
        df_with_selection,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select a row",
                required=False
            )
        },
        disabled=df.columns,  # Make all other columns readonly
        key="editor"  # Important: use a key to track changes
    )
    
    # Check for changes in selection
    selected_rows = edited_df[edited_df["Select"]].index.tolist()
    
    # If selection changed, update the state
    if selected_rows and st.session_state.previous_selection != selected_rows:
        st.session_state.previous_selection = selected_rows
        if len(selected_rows) > 0:
            selected_index = selected_rows[0]
            st.session_state.selected_file = df.iloc[selected_index]["File"]
            st.rerun()  # Rerun to update UI with new selection
    
    # Display the selection
    if st.session_state.selected_file:
        st.success(f"Selected file: {st.session_state.selected_file}")
        
        # You can now do something with the selected file
        st.write(f"Displaying {st.session_state.selected_file}...")
        
        # Example: simulating image display
        st.code(f"# Code to display {st.session_state.selected_file}")
    else:
        st.info("No row selected yet. Use the checkbox to select a row.")


def method3_direct_click_detection():
    """
    Method 3: Direct click detection using edited dataframe values
    
    This method is more flexible but requires tracking the edited dataframe
    and detecting changes using Session State.
    """
    st.header("Method 3: Direct Click Detection")
    
    # Create sample data with a thumbnail column
    df = pd.DataFrame({
        "File": [f"image_{i}.jpg" for i in range(1, 6)],
        "Thumbnail": ["🖼️", "🖼️", "🖼️", "🖼️", "🖼️"],  # Simulated thumbnails
        "Width": [800, 1024, 640, 1280, 800],
        "Height": [600, 768, 480, 720, 600],
    })
    
    # Initialize session state
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = "image_editor_1"
    
    if "selected_image" not in st.session_state:
        st.session_state.selected_image = None
    
    # Display instruction
    st.write("Click on a thumbnail to select an image:")
    
    # Configure columns for data_editor
    column_config = {
        "File": st.column_config.TextColumn("Filename", width="medium"),
        "Thumbnail": st.column_config.TextColumn("Preview", width="small"),
        "Width": st.column_config.NumberColumn("Width (px)", width="small"),
        "Height": st.column_config.NumberColumn("Height (px)", width="small"),
    }
    
    # Display the data editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=st.session_state.editor_key
    )
    
    # Check if the user clicked on a row (would be better with real thumbnails)
    if st.button("Simulate Row Click for image_2.jpg"):
        st.session_state.selected_image = "image_2.jpg"
        st.rerun()
    
    # Display the selected image
    if st.session_state.selected_image:
        st.success(f"Selected image: {st.session_state.selected_image}")
        
        # Do something with the selected image
        st.write(f"Displaying {st.session_state.selected_image}...")
        
        # Example: simulating image display
        st.code(f"# Code to display {st.session_state.selected_image}")
    else:
        st.info("No image selected yet. Click on a thumbnail to select it.")


def main():
    """Main function to demonstrate different methods."""
    st.title("Data Editor Row Selection Examples")
    st.write("""
    This app demonstrates different methods for detecting row clicks and 
    implementing row selection in Streamlit data_editor.
    """)
    
    # Create tabs for different methods
    tab1, tab2, tab3 = st.tabs([
        "Method 1: on_select='rerun'", 
        "Method 2: Session State",
        "Method 3: Direct Click Detection"
    ])
    
    with tab1:
        method1_on_select_rerun()
    
    with tab2:
        method2_session_state()
    
    with tab3:
        method3_direct_click_detection()


if __name__ == "__main__":
    main()