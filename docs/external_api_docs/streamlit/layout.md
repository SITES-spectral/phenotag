# Streamlit Layout Elements

## Overview

Streamlit offers various layout elements to help organize and structure your app's UI. This document covers the most important layout mechanisms provided by Streamlit.

## Sidebar

The sidebar is a vertical panel that appears on the left side of your app, providing a convenient place for controls and navigation elements.

### Basic Sidebar

```python
import streamlit as st

# Add a title to the sidebar
st.sidebar.title("Sidebar Title")

# Add other elements to the sidebar
st.sidebar.write("This is the sidebar")
st.sidebar.slider("Select a value", 0, 100, 50)
```

### Using 'with' Notation for Sidebar

```python
import streamlit as st

# Use with notation to add elements to the sidebar
with st.sidebar:
    st.title("Sidebar Title")
    st.write("This is the sidebar")
    value = st.slider("Select a value", 0, 100, 50)
    option = st.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
```

## Columns

Columns allow you to display widgets or content side by side horizontally.

### Basic Columns

```python
import streamlit as st

# Create three columns
col1, col2, col3 = st.columns(3)

# Add content to each column
with col1:
    st.header("Column 1")
    st.image("https://via.placeholder.com/150")

with col2:
    st.header("Column 2")
    st.write("This is column 2")
    st.button("Click Me")

with col3:
    st.header("Column 3")
    st.metric(label="Temperature", value="70 °F", delta="1.2 °F")
```

### Columns with Specified Widths

```python
import streamlit as st

# Create columns with specified relative widths
col1, col2, col3 = st.columns([1, 2, 1])  # The middle column is twice as wide

# Add content to each column
with col1:
    st.header("Column 1")
    st.write("This is a narrow column")

with col2:
    st.header("Column 2")
    st.write("This is a wide column")
    st.image("https://via.placeholder.com/300x150")

with col3:
    st.header("Column 3")
    st.write("This is another narrow column")
```

### Nested Columns

```python
import streamlit as st

# Create main columns
col1, col2 = st.columns(2)

with col1:
    st.header("Main Column 1")
    
    # Create nested columns inside col1
    nested_col1, nested_col2 = st.columns(2)
    
    with nested_col1:
        st.subheader("Nested 1.1")
        st.write("Content in nested column 1.1")
    
    with nested_col2:
        st.subheader("Nested 1.2")
        st.write("Content in nested column 1.2")

with col2:
    st.header("Main Column 2")
    st.write("Content in main column 2")
```

## Containers

Containers group elements into logical sections with clear boundaries.

### Basic Container

```python
import streamlit as st

# Create a container
container = st.container()

# Add elements to the container (these will appear inside the container)
container.write("This is inside the container")
container.slider("Container slider", 0, 100, 50)

# Elements outside the container
st.write("This is outside the container")
```

### Containers with 'with' Notation

```python
import streamlit as st

# Using with notation
with st.container():
    st.write("This is inside the container")
    st.image("https://via.placeholder.com/200")
    
    # Nested container
    with st.container():
        st.write("This is inside a nested container")
        st.slider("Nested slider", 0, 100, 50)

# Outside the container
st.write("This is outside the containers")
```

## Expanders

Expanders create collapsible sections that conserve space and reduce clutter.

### Basic Expander

```python
import streamlit as st

# Create an expander
with st.expander("Click to expand"):
    st.write("This content is hidden until the expander is clicked.")
    st.image("https://via.placeholder.com/300x150")
```

### Expanded by Default

```python
import streamlit as st

# Create an expander that's expanded by default
with st.expander("Details", expanded=True):
    st.write("This content is visible by default because the expander is expanded.")
    st.line_chart({"data": [1, 5, 2, 6, 2, 1]})
```

### Multiple Expanders

```python
import streamlit as st

st.title("FAQ")

with st.expander("What is Streamlit?"):
    st.write("Streamlit is an open-source Python library that makes it easy to create and share custom web apps for machine learning and data science.")

with st.expander("How do I install Streamlit?"):
    st.code("pip install streamlit")
    st.write("For more details, check the [documentation](https://docs.streamlit.io).")

with st.expander("How do I run a Streamlit app?"):
    st.code("streamlit run app.py")
```

## Tabs

Tabs organize content into separate tabbed sections.

### Basic Tabs

```python
import streamlit as st
import pandas as pd
import numpy as np

# Create tabs
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

# Add content to each tab
with tab1:
    st.header("Tab 1")
    st.write("This is the content of the first tab")
    st.image("https://via.placeholder.com/300x150")

with tab2:
    st.header("Tab 2")
    df = pd.DataFrame(np.random.randn(5, 3), columns=["a", "b", "c"])
    st.dataframe(df)
    
with tab3:
    st.header("Tab 3")
    st.write("This is the content of the third tab")
    st.line_chart({"data": [1, 5, 2, 6, 2, 1]})
```

### Tabs with Icons

```python
import streamlit as st

# Create tabs with icons
tab1, tab2, tab3 = st.tabs(["📈 Data", "🗃 Files", "⚙️ Settings"])

# Add content to each tab
with tab1:
    st.header("Data Tab")
    st.write("This tab contains data visualizations")

with tab2:
    st.header("Files Tab")
    st.write("This tab contains file operations")
    
with tab3:
    st.header("Settings Tab")
    st.write("This tab contains application settings")
```

## Empty

The `st.empty` element creates a placeholder that can be replaced with other content later.

### Basic Empty Placeholder

```python
import streamlit as st
import time

# Create an empty placeholder
placeholder = st.empty()

# Display something in the placeholder
placeholder.text("This will disappear in 2 seconds")

# Wait for 2 seconds
time.sleep(2)

# Replace the content of the placeholder
placeholder.text("The content has changed!")

# Wait for 2 more seconds
time.sleep(2)

# Replace with something else
placeholder.markdown("# Now it's a heading!")
```

### Multiple Empty Placeholders

```python
import streamlit as st
import time
import numpy as np

# Create multiple empty placeholders
header = st.empty()
chart = st.empty()
metrics = st.empty()

# First state
header.header("Initial State")
chart.line_chart(np.random.randn(10, 1))
metrics.metric("Value", 100, 10)

# Wait for 2 seconds
time.sleep(2)

# Update to second state
header.header("Updated State")
chart.bar_chart(np.random.randn(10, 3))
metrics.metric("Value", 200, -5)
```

### Form with Empty Placeholders

```python
import streamlit as st

# Create placeholders
result_area = st.empty()
error_area = st.empty()

# Create a form
with st.form("my_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    submitted = st.form_submit_button("Submit")

# Process form submission
if submitted:
    if not name:
        # Show error in the error area
        error_area.error("Please enter your name")
        result_area.empty()  # Clear the result area
    else:
        # Clear the error area and show the result
        error_area.empty()
        result_area.success(f"Hello, {name}! You are {age} years old.")
```

## Custom Layouts with Columns and Containers

### Dashboard Layout

```python
import streamlit as st
import pandas as pd
import numpy as np

st.title("Dashboard Demo")

# Top metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue", "$12,345", "4.5%")
col2.metric("Users", "1,234", "10%")
col3.metric("Conversion", "4.5%", "-0.5%")
col4.metric("Avg. Time", "2m 45s", "0.1%")

# Main content with sidebar
with st.container():
    # Create 70/30 split
    main_content, sidebar_content = st.columns([0.7, 0.3])
    
    with main_content:
        st.header("Main Chart")
        chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
        st.line_chart(chart_data)
        
        # Create two tabs for different views
        tab1, tab2 = st.tabs(["Detailed View", "Summary View"])
        
        with tab1:
            st.subheader("Detailed Data")
            st.dataframe(chart_data)
            
        with tab2:
            st.subheader("Summary Statistics")
            st.write(chart_data.describe())
    
    with sidebar_content:
        st.header("Controls")
        with st.form("filter_form"):
            st.selectbox("Select Category", ["A", "B", "C"])
            st.date_input("Select Date")
            st.slider("Select Range", 0, 100, (25, 75))
            st.form_submit_button("Apply Filters")
        
        with st.expander("Help"):
            st.write("This dashboard shows key metrics and data visualization.")
            st.write("Use the controls to filter the data.")

# Bottom section
st.header("Recent Activities")
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Latest Events")
        st.write("1. System update completed")
        st.write("2. New user registration")
        st.write("3. Payment processed")
    
    with col2:
        st.subheader("Alerts")
        st.error("Server load high")
        st.warning("5 failed login attempts")
        st.success("Backup completed successfully")
```

### Multi-Page Layout with Tabs

```python
import streamlit as st
import pandas as pd
import numpy as np

st.title("Multi-Page Application")

# Navigation tabs
tab1, tab2, tab3, tab4 = st.tabs(["Home", "Data", "Visualization", "Settings"])

# Home page
with tab1:
    st.header("Welcome to the Application")
    
    # Two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("About")
        st.write("This is a demo of a multi-page application built with Streamlit.")
        st.write("Use the tabs above to navigate between different sections.")
    
    with col2:
        st.subheader("Quick Stats")
        st.metric("Users", "1,234", "10%")
        st.metric("Activities", "5,678", "2.3%")
    
    # Featured content
    with st.container():
        st.subheader("Featured Content")
        with st.expander("Learn More", expanded=True):
            st.write("This application demonstrates various layout elements in Streamlit.")
            st.code("st.tabs, st.columns, st.container, st.expander")

# Data page
with tab2:
    st.header("Data Section")
    
    # Controls in a sidebar-like column
    col1, col2 = st.columns([0.3, 0.7])
    
    with col1:
        st.subheader("Controls")
        with st.form("data_controls"):
            st.selectbox("Data Source", ["Source A", "Source B", "Source C"])
            st.date_input("Select Date Range")
            st.multiselect("Select Columns", ["Col 1", "Col 2", "Col 3", "Col 4"])
            st.form_submit_button("Load Data")
    
    with col2:
        st.subheader("Data Preview")
        data = pd.DataFrame(np.random.randn(10, 4), columns=["Col 1", "Col 2", "Col 3", "Col 4"])
        st.dataframe(data)
        
        # Export options
        with st.expander("Export Options"):
            col1, col2, col3 = st.columns(3)
            col1.download_button("CSV", data.to_csv(), "data.csv")
            col2.download_button("Excel", data.to_excel(), "data.xlsx")
            col3.download_button("JSON", data.to_json(), "data.json")

# Visualization page
with tab3:
    st.header("Visualization Section")
    
    # Visualization selection
    viz_type = st.radio("Select Visualization Type", ["Line Chart", "Bar Chart", "Scatter Plot"], horizontal=True)
    
    # Generate sample data
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
    
    # Display selected visualization
    if viz_type == "Line Chart":
        st.line_chart(chart_data)
    elif viz_type == "Bar Chart":
        st.bar_chart(chart_data)
    else:  # Scatter Plot
        st.scatter_chart(chart_data)
    
    # Additional options in an expander
    with st.expander("Chart Options"):
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Show Legend")
            st.checkbox("Show Grid")
        with col2:
            st.selectbox("Color Palette", ["Blues", "Greens", "Reds"])
            st.slider("Opacity", 0.0, 1.0, 0.7)

# Settings page
with tab4:
    st.header("Settings")
    
    # Organize settings into categories using expanders
    with st.expander("General Settings", expanded=True):
        st.selectbox("Theme", ["Light", "Dark", "System Default"])
        st.selectbox("Language", ["English", "Spanish", "French", "German"])
    
    with st.expander("Display Settings"):
        st.checkbox("Show Welcome Message on Startup")
        st.checkbox("Use Animations")
        st.slider("Default Chart Height", 200, 800, 400)
    
    with st.expander("Account Settings"):
        st.text_input("Username")
        st.text_input("Email")
        st.password("Password")
        
    # Save button
    st.button("Save Settings")
```

## st.popup

The `st.popup` element creates a popup window that appears over the main content.

### Basic Popup

```python
import streamlit as st

if st.button("Show popup"):
    with st.popup("My popup"):
        st.write("This is a popup")
        st.image("https://via.placeholder.com/150")
```

### Popup with Columns

```python
import streamlit as st

if st.button("Show details"):
    with st.popup("User details"):
        # Use columns inside the popup
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Info")
            st.write("Name: John Doe")
            st.write("Email: john@example.com")
        
        with col2:
            st.subheader("Account Info")
            st.write("Status: Active")
            st.write("Plan: Premium")
```

### Form in Popup

```python
import streamlit as st

if st.button("Edit profile"):
    with st.popup("Edit profile", "medium"):
        with st.form("profile_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            bio = st.text_area("Bio")
            submitted = st.form_submit_button("Save")
        
        if submitted:
            st.success("Profile updated successfully!")
```

## Best Practices

1. **Keep Layout Consistent**: Maintain a consistent layout throughout your app for better user experience.

2. **Use Appropriate Container Types**: Choose the right layout element based on your content's needs:
   - Tabs for different views of the same data or functionality
   - Expanders for detailed information that isn't always needed
   - Columns for placing elements side by side
   - Empty for dynamic content that needs to be updated

3. **Responsive Design Considerations**: Remember that Streamlit apps will be viewed on different devices:
   - Avoid using too many columns on small screens
   - Test your layout on different screen sizes
   - Use `use_container_width=True` for charts and tables to make them responsive

4. **Nesting Layout Elements**: You can nest layout elements, but don't overdo it:
   - Nested columns can become very narrow
   - Deeply nested containers can become confusing

5. **Balance Between Space and Information**:
   - Use expanders to hide details that aren't immediately necessary
   - Use tabs to separate different types of content
   - Keep the most important information at the top

6. **Mobile-Friendly Layouts**:
   - Use fewer columns for better mobile experience
   - Consider how the sidebar will affect mobile users (it becomes a collapsible menu)

7. **Performance Considerations**:
   - Avoid creating too many layout elements as it can slow down your app
   - Use st.empty() for content that changes frequently to avoid full page reruns