# st.sidebar

## Overview

The sidebar in Streamlit provides a convenient way to organize widgets and controls that the user can access without affecting the main content area of your app. It creates a vertical column on the left side of the screen that remains accessible as users scroll through the main content.

## Basic Usage

There are two ways to add elements to the sidebar:

### 1. Using st.sidebar as an object

```python
import streamlit as st

# Add elements to the sidebar
st.sidebar.title("Sidebar Title")
st.sidebar.write("This is a sidebar")
value = st.sidebar.slider("Select a value", 0, 100, 50)
option = st.sidebar.selectbox("Select an option", ["Option 1", "Option 2", "Option 3"])

# Main content area
st.title("Main Content")
st.write(f"You selected value: {value}")
st.write(f"You selected option: {option}")
```

### 2. Using 'with' notation

```python
import streamlit as st

# Use 'with' notation to add elements to the sidebar
with st.sidebar:
    st.title("Sidebar Title")
    st.write("This is a sidebar")
    value = st.slider("Select a value", 0, 100, 50)
    option = st.selectbox("Select an option", ["Option 1", "Option 2", "Option 3"])

# Main content area
st.title("Main Content")
st.write(f"You selected value: {value}")
st.write(f"You selected option: {option}")
```

## Features and Capabilities

The sidebar supports virtually all Streamlit elements, including:

- Text elements (title, header, write, markdown)
- Input widgets (sliders, buttons, selectboxes)
- Media elements (images, videos)
- Charts and data display
- Layout elements (columns, expanders)

### Example with Various Elements

```python
import streamlit as st
import pandas as pd
import numpy as np

# Create a rich sidebar
with st.sidebar:
    st.title("Navigation")
    
    # Add a profile section
    st.image("https://via.placeholder.com/150", width=100)
    st.write("Welcome, User!")
    
    # Add a navigation section
    page = st.radio("Go to", ["Home", "Dashboard", "Settings"])
    
    # Add filters section
    st.header("Filters")
    
    date_range = st.date_input("Select date range", [])
    categories = st.multiselect("Categories", ["A", "B", "C", "D"])
    
    # Add an expander for advanced options
    with st.expander("Advanced Options"):
        st.checkbox("Include inactive items")
        st.slider("Confidence threshold", 0.0, 1.0, 0.5)
    
    # Add a footer
    st.write("---")
    st.caption("App version 1.0.0")

# Main content based on selected page
if page == "Home":
    st.title("Home Page")
    st.write("Welcome to the home page!")
    
elif page == "Dashboard":
    st.title("Dashboard")
    
    # Create a sample chart
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
    st.line_chart(chart_data)
    
    # Show filtered data based on sidebar selections
    st.write("Selected categories:", categories)
    
elif page == "Settings":
    st.title("Settings")
    st.write("Configure your application settings here.")
    
    # Add some settings options
    st.checkbox("Dark mode")
    st.selectbox("Theme", ["Default", "Light", "Dark", "Blue"])
    st.number_input("Items per page", 5, 100, 20)
```

## Sidebar Configuration

### Initial State

You can set the initial state of the sidebar using the `st.set_page_config` function:

```python
import streamlit as st

# Set the initial sidebar state
st.set_page_config(
    page_title="App with Sidebar",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # or "collapsed"
)

# Add content to sidebar
with st.sidebar:
    st.title("Sidebar")
    st.write("This sidebar starts expanded")

# Main content
st.title("Main Content")
```

The `initial_sidebar_state` parameter can be:

- `"auto"`: Show the sidebar if there's content in it (default)
- `"expanded"`: Always show the sidebar
- `"collapsed"`: Start with the sidebar collapsed

### Controlling Sidebar Visibility Programmatically

```python
import streamlit as st

# Set the initial sidebar state
st.set_page_config(initial_sidebar_state="collapsed")

# Add sidebar content
with st.sidebar:
    st.title("Navigation")
    page = st.radio("Go to", ["Home", "About", "Contact"])

# Add a button to show/hide sidebar
if st.button("Toggle Sidebar"):
    # Get the current state from query params
    query_params = st.experimental_get_query_params()
    current_state = query_params.get("sidebar", ["visible"])[0]
    
    # Toggle the state
    new_state = "collapsed" if current_state == "visible" else "visible"
    
    # Set the new state in query params
    st.experimental_set_query_params(sidebar=new_state)
    
    # Need to rerun the script to apply the change
    st.rerun()
```

## Advanced Usage

### Sidebar with Forms

```python
import streamlit as st

# Add a form to the sidebar
with st.sidebar:
    st.title("Filter Data")
    
    with st.form("filter_form"):
        st.date_input("Date Range")
        st.multiselect("Categories", ["A", "B", "C", "D"])
        st.slider("Price Range", 0, 1000, (200, 800))
        
        # Add form submit button
        submitted = st.form_submit_button("Apply Filters")
    
    if submitted:
        st.success("Filters applied!")
```

### Multi-Level Navigation

```python
import streamlit as st

# Set up multi-level navigation
with st.sidebar:
    st.title("Navigation")
    
    # Main sections
    main_section = st.radio("Section", ["Dashboard", "Data", "Reports", "Settings"])
    
    # Sub-sections based on main selection
    if main_section == "Dashboard":
        sub_section = st.radio("Dashboard View", ["Overview", "Performance", "Analytics"])
    
    elif main_section == "Data":
        sub_section = st.radio("Data Options", ["Browse", "Import", "Export", "Clean"])
    
    elif main_section == "Reports":
        sub_section = st.radio("Report Type", ["Summary", "Detailed", "Custom"])
    
    elif main_section == "Settings":
        sub_section = st.radio("Settings", ["Profile", "Preferences", "API Keys", "Users"])

# Display content based on navigation
st.title(f"{main_section} - {sub_section}")

# Example content for Dashboard > Overview
if main_section == "Dashboard" and sub_section == "Overview":
    st.write("This is the dashboard overview page.")
    st.metric("Users", "1,204", "+12%")
    st.metric("Revenue", "$12,938", "+2.4%")
```

### Conditionally Showing Sidebar Elements

```python
import streamlit as st

# Initialize state
if "show_advanced" not in st.session_state:
    st.session_state.show_advanced = False

# Sidebar with conditional elements
with st.sidebar:
    st.title("Filters")
    
    # Basic filters always shown
    st.date_input("Date")
    st.multiselect("Categories", ["A", "B", "C"])
    
    # Toggle for advanced options
    if st.checkbox("Show Advanced Options", value=st.session_state.show_advanced):
        st.session_state.show_advanced = True
        
        # Advanced filters
        st.slider("Price Range", 0, 1000, (200, 800))
        st.selectbox("Sort By", ["Relevance", "Price: Low to High", "Price: High to Low"])
        st.number_input("Minimum Rating", 1, 5, 3)
    else:
        st.session_state.show_advanced = False

# Main content
st.title("Products")
st.write("Product list would appear here, filtered according to the sidebar options.")
```

### Sidebar with Custom Styling

```python
import streamlit as st

# Apply custom CSS to style the sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        padding: 1rem;
        border-right: 1px solid #eee;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #0066cc;
    }
    
    [data-testid="stSidebar"] hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 0;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .sidebar-section {
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Add content to styled sidebar
with st.sidebar:
    st.title("Navigation")
    
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.write("### Menu")
    page = st.radio("", ["Home", "Dashboard", "Settings"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.write("### Filters")
    st.date_input("Date")
    st.multiselect("Categories", ["A", "B", "C", "D"])
    st.markdown('</div>', unsafe_allow_html=True)

# Main content
st.title(f"{page} Page")
st.write("This is the main content area.")
```

## Best Practices

1. **Organize Related Controls**: Group related controls together in the sidebar to make the UI intuitive.

2. **Keep the Sidebar Clean**: Avoid overcrowding the sidebar; use expanders for less frequently used options.

3. **Responsive Design**: Remember that on mobile devices, the sidebar appears as a collapsible menu, so prioritize the most important controls.

4. **Use Forms for Multiple Inputs**: When multiple sidebar inputs should be processed together, use a form to collect all inputs before triggering updates.

5. **Provide Clear Navigation**: If using the sidebar for navigation, make the current selection obvious.

6. **Remember Session State**: Use session state to maintain sidebar values between app reruns and page navigations.

7. **Consider UI Balance**: Ensure there's a good balance between sidebar controls and main content; overly complex sidebars can overwhelm users.

## Common Issues and Solutions

1. **Sidebar Becomes Scrollable**:
   - If you add too many elements to the sidebar, it becomes scrollable
   - Solution: Use expanders to group related controls

2. **Sidebar Resets on Interaction**:
   - Without session state, sidebar values may reset when other parts of the app change
   - Solution: Use session state to persist values

3. **Mobile Display Issues**:
   - The sidebar collapses to a menu on mobile devices
   - Solution: Test your app on mobile and ensure critical controls are accessible

4. **Sidebar Activation in Multi-Page Apps**:
   - In multi-page apps, the sidebar may not highlight the current page
   - Solution: Use query parameters or session state to track the current page

5. **Performance with Many Elements**:
   - Large numbers of sidebar elements can affect app performance
   - Solution: Simplify the sidebar and use expanders to group related elements