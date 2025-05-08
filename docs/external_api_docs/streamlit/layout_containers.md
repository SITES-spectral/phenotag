# Streamlit Layout and Containers

This document provides comprehensive documentation on Streamlit's layout components and containers that allow you to organize the UI of your applications.

## Table of Contents
- [Columns](#columns)
- [Containers](#containers)
- [Expanders](#expanders)
- [Tabs](#tabs)
- [Sidebar](#sidebar)
- [Popover](#popover)
- [Status](#status)
- [Chat Message](#chat-message)
- [Configure Page](#configure-page)
- [Best Practices](#best-practices)

## Columns

The `st.columns` function creates columns that enable side-by-side placement of elements.

```python
col1, col2 = st.columns(2)
col1.write("This content appears in the left column")
col2.write("This content appears in the right column")
```

**Parameters:**
- `spec`: Number of columns or list of relative widths
- `gap`: Gap size between columns ("small", "medium", "large")
- `vertical_align`: Vertical alignment of columns ("top", "center", "bottom")

**Examples:**

```python
import streamlit as st
import numpy as np
import pandas as pd

# Basic columns with equal width
col1, col2 = st.columns(2)
col1.write("Column 1")
col2.write("Column 2")

# Columns with custom relative widths
col1, col2, col3 = st.columns([1, 2, 1])  # Center column is twice as wide
col1.write("25% width")
col2.write("50% width")
col3.write("25% width")

# Columns with gap
col1, col2 = st.columns(2, gap="large")
col1.write("Column 1")
col2.write("Column 2")

# Columns with different content types
left_col, right_col = st.columns(2)
left_col.subheader("A dataframe")
df = pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
})
left_col.dataframe(df)

right_col.subheader("A chart")
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
right_col.line_chart(chart_data)

# Using columns with 'with' statement
col1, col2 = st.columns(2)
with col1:
    st.header("Column 1")
    st.image("https://static.streamlit.io/examples/cat.jpg")
    st.button("Click me!")

with col2:
    st.header("Column 2")
    st.write("This is column 2")
    option = st.selectbox("Select an option", ["Option 1", "Option 2", "Option 3"])
    st.write(f"You selected: {option}")

# Nested columns
col1, col2 = st.columns(2)
with col1:
    st.header("Main Column 1")
    nested_col1, nested_col2 = st.columns(2)
    with nested_col1:
        st.write("Nested Column 1")
    with nested_col2:
        st.write("Nested Column 2")

with col2:
    st.header("Main Column 2")
```

## Containers

Containers are used to group elements together and control their layout.

### st.container

Creates a container that can hold multiple elements.

```python
container = st.container()
container.write("This is inside the container")
st.write("This is outside the container")
container.write("This is also inside the container")
```

**Parameters:**
- `border`: If True, displays a border around the container (default: False)
- `height`: Height of the container in pixels

**Examples:**

```python
import streamlit as st
import pandas as pd
import numpy as np

# Basic container
container = st.container()
container.write("This is inside the container")
container.write("This is also inside the container")
st.write("This is outside the container")

# Container with border
bordered_container = st.container(border=True)
bordered_container.header("Container with border")
bordered_container.write("This container has a visible border around it.")

# Container with fixed height
scrollable_container = st.container(height=200)
scrollable_container.header("Fixed Height Container")
scrollable_container.write("This container has a fixed height and becomes scrollable when content exceeds it.")
for i in range(20):
    scrollable_container.write(f"Line {i+1}")

# Using containers with 'with' statement
with st.container():
    st.write("This is inside a container")
    st.write("These elements are grouped together")
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    st.line_chart(chart_data)

# Ordering content with containers
latest_container = st.container()
st.write("This content appears in the middle")
earliest_container = st.container()

# Now populate the containers
latest_container.write("This content appears at the bottom")
earliest_container.write("This content appears at the top")

# Nested containers
outer = st.container()
with outer:
    st.write("This is the outer container")
    inner = st.container()
    inner.write("This is the inner container")
```

### st.empty

Creates an empty single-element container that can be replaced.

```python
placeholder = st.empty()
placeholder.text("Hello world!")
placeholder.text("This text replaces the previous text")
```

**Examples:**

```python
import streamlit as st
import time
import numpy as np

# Basic empty container
placeholder = st.empty()
placeholder.text("This will be replaced after 2 seconds")
time.sleep(2)
placeholder.text("This text has replaced the previous text")

# Using empty for dynamic content
chart_placeholder = st.empty()
data_placeholder = st.empty()

# Progress bar example
progress_placeholder = st.empty()
for i in range(100):
    progress_placeholder.progress(i + 1)
    time.sleep(0.05)
progress_placeholder.success("Done!")

# Animated chart example
chart_data = pd.DataFrame(np.random.randn(1, 3), columns=['a', 'b', 'c'])
chart_placeholder = st.empty()

for i in range(50):
    # Add new data
    new_data = pd.DataFrame(np.random.randn(1, 3), columns=['a', 'b', 'c'])
    chart_data = pd.concat([chart_data, new_data], ignore_index=True)
    
    # Update the chart
    chart_placeholder.line_chart(chart_data)
    time.sleep(0.1)

# Multiple placeholders for a form-like interface
name_placeholder = st.empty()
email_placeholder = st.empty()
submit_placeholder = st.empty()
result_placeholder = st.empty()

name = name_placeholder.text_input("Name")
email = email_placeholder.text_input("Email")
submit = submit_placeholder.button("Submit")

if submit:
    result_placeholder.success(f"Form submitted for {name} ({email})")
    # Clear the form
    name_placeholder.empty()
    email_placeholder.empty()
    submit_placeholder.empty()
```

## Expanders

Expanders are collapsible containers that can hide or show content.

### st.expander

Creates an expandable container that can be collapsed/expanded by the user.

```python
with st.expander("See explanation"):
    st.write("This content is hidden by default and expands when clicked.")
    st.image("https://static.streamlit.io/examples/cat.jpg")
```

**Parameters:**
- `label`: Label to display as the expander trigger
- `expanded`: If True, the expander is expanded by default (default: False)
- `icon`: Icon to display next to the expander label

**Examples:**

```python
import streamlit as st
import pandas as pd
import numpy as np

# Basic expander
with st.expander("Click to expand"):
    st.write("This content is hidden by default")
    st.image("https://static.streamlit.io/examples/cat.jpg")

# Expander that's open by default
with st.expander("Details (expanded by default)", expanded=True):
    st.write("This content is visible by default")
    st.write("The user can collapse it by clicking the header")

# Expander with complex content
with st.expander("View Data Analysis"):
    st.subheader("Data Summary")
    
    # Create some sample data
    df = pd.DataFrame(
        np.random.randn(50, 5),
        columns=('col %d' % i for i in range(5))
    )
    
    st.dataframe(df)
    st.write("Description:")
    st.write(df.describe())
    
    # Add a chart
    st.subheader("Data Visualization")
    st.line_chart(df)

# Multiple expanders for FAQ-like interface
st.title("Frequently Asked Questions")

with st.expander("What is Streamlit?"):
    st.write("Streamlit is an open-source app framework for Machine Learning and Data Science teams.")
    
with st.expander("How do I install Streamlit?"):
    st.code("pip install streamlit")
    
with st.expander("How do I run a Streamlit app?"):
    st.code("streamlit run app.py")

# Expander with form
with st.expander("Contact Form"):
    with st.form("contact_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        message = st.text_area("Message")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            st.success("Form submitted successfully!")
```

## Tabs

Tabs allow organizing content into separate tabbed sections.

### st.tabs

Creates a tabbed container to display content.

```python
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
tab1.write("This is tab 1")
tab2.write("This is tab 2")
```

**Examples:**

```python
import streamlit as st
import pandas as pd
import numpy as np

# Basic tabs
tab1, tab2, tab3 = st.tabs(["Home", "Data", "Visualization"])

with tab1:
    st.header("Home Tab")
    st.write("Welcome to the Home tab!")
    st.write("Use the tabs above to navigate to different sections.")

with tab2:
    st.header("Data Tab")
    df = pd.DataFrame({
        'First Column': [1, 2, 3, 4],
        'Second Column': [10, 20, 30, 40]
    })
    st.write("Sample data:")
    st.dataframe(df)

with tab3:
    st.header("Visualization Tab")
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    st.line_chart(chart_data)

# Tabs with more complex layouts
analysis_tab, settings_tab = st.tabs(["Analysis", "Settings"])

with analysis_tab:
    st.subheader("Data Analysis")
    
    # Add columns within the tab
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Column 1 within Analysis tab")
        st.metric("Accuracy", "92%", "4%")
        
    with col2:
        st.write("Column 2 within Analysis tab")
        st.metric("Loss", "0.08", "-0.02")

with settings_tab:
    st.subheader("Settings")
    st.write("Configure application settings")
    
    # Add a form within the tab
    with st.form("settings_form"):
        st.write("Model Settings")
        learning_rate = st.slider("Learning Rate", min_value=0.001, max_value=0.1, value=0.01, step=0.001)
        epochs = st.number_input("Epochs", min_value=1, max_value=100, value=10)
        st.form_submit_button("Save Settings")

# Nested tabs within tabs
main_tab1, main_tab2 = st.tabs(["Main Tab 1", "Main Tab 2"])

with main_tab1:
    st.write("This is the main tab 1")
    
    # Create nested tabs
    nested_tab1, nested_tab2 = st.tabs(["Nested Tab 1", "Nested Tab 2"])
    
    with nested_tab1:
        st.write("This is a tab within a tab")
        
    with nested_tab2:
        st.write("This is another nested tab")

with main_tab2:
    st.write("This is the main tab 2")
```

## Sidebar

The sidebar provides a fixed location for navigation and controls.

### st.sidebar

Adds an element to the sidebar.

```python
st.sidebar.title("Sidebar Title")
st.sidebar.button("Click me!")
```

**Examples:**

```python
import streamlit as st
import pandas as pd
import numpy as np

# Basic sidebar elements
st.sidebar.title("Navigation")
st.sidebar.text_input("Search")
selected_page = st.sidebar.radio("Go to", ["Home", "Data", "Analytics", "Settings"])

# Main content based on selection
if selected_page == "Home":
    st.title("Home Page")
    st.write("Welcome to the Home page!")
elif selected_page == "Data":
    st.title("Data Page")
    df = pd.DataFrame({
        'First Column': [1, 2, 3, 4],
        'Second Column': [10, 20, 30, 40]
    })
    st.dataframe(df)
elif selected_page == "Analytics":
    st.title("Analytics Page")
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    st.line_chart(chart_data)
elif selected_page == "Settings":
    st.title("Settings Page")
    st.write("Configure application settings here.")

# Sidebar with form
st.sidebar.header("Filters")
with st.sidebar.form("filter_form"):
    st.write("Apply filters")
    min_value = st.slider("Minimum Value", 0, 100, 25)
    max_value = st.slider("Maximum Value", 0, 100, 75)
    categories = st.multiselect("Categories", ["A", "B", "C", "D"])
    apply_filter = st.form_submit_button("Apply")

if apply_filter:
    st.write(f"Filters applied: Min={min_value}, Max={max_value}, Categories={categories}")

# Sidebar with expander
with st.sidebar.expander("Advanced Options"):
    st.write("These are advanced options")
    option1 = st.checkbox("Enable feature 1")
    option2 = st.checkbox("Enable feature 2")
    
    if option1:
        st.write("Feature 1 enabled")
    if option2:
        st.write("Feature 2 enabled")

# Sidebar with columns
sidebar_col1, sidebar_col2 = st.sidebar.columns(2)
sidebar_col1.button("Button 1")
sidebar_col2.button("Button 2")

# Using container in sidebar
with st.sidebar:
    st.header("Container in Sidebar")
    st.write("This is an alternative way to add elements to the sidebar")
    
    # Tabs in sidebar
    tab1, tab2 = st.tabs(["Info", "Help"])
    with tab1:
        st.write("Information tab")
    with tab2:
        st.write("Help tab")
```

## Popover

Popovers create floating containers that appear when triggered.

### st.popover

Creates a popover that shows content when clicked.

```python
with st.popover("Open popover"):
    st.write("This content appears in a popover")
    st.image("https://static.streamlit.io/examples/cat.jpg")
```

**Parameters:**
- `label`: Label to display as the popover trigger

**Examples:**

```python
import streamlit as st
import pandas as pd

# Basic popover
with st.popover("Open popover"):
    st.write("This content appears in a popover")
    st.write("Popovers are useful for additional information or settings")

# Popover with more complex content
with st.popover("View Details"):
    st.header("Product Details")
    st.write("Product ID: ABC123")
    st.write("In stock: Yes")
    st.write("Shipping: 2-3 business days")
    
    # Add an image
    st.image("https://static.streamlit.io/examples/cat.jpg", width=200)

# Popover with form
with st.popover("Quick Settings"):
    with st.form("quick_settings"):
        st.write("Adjust settings")
        theme = st.selectbox("Theme", ["Light", "Dark", "System"])
        notifications = st.checkbox("Enable notifications")
        st.form_submit_button("Save")

# Popover with data
with st.popover("Show Data"):
    st.subheader("Sample Data")
    df = pd.DataFrame({
        'Name': ['John', 'Emily', 'Sarah', 'Mike'],
        'Age': [28, 35, 42, 24],
        'City': ['New York', 'Boston', 'Chicago', 'San Francisco']
    })
    st.dataframe(df)

# Multiple popovers in a row
col1, col2, col3 = st.columns(3)

with col1:
    with st.popover("Profile"):
        st.write("User Profile")
        st.write("Name: John Doe")
        st.write("Email: john@example.com")

with col2:
    with st.popover("Settings"):
        st.write("App Settings")
        st.toggle("Dark Mode")
        st.selectbox("Language", ["English", "Spanish", "French"])

with col3:
    with st.popover("Help"):
        st.write("Need help?")
        st.write("Contact support at support@example.com")
        st.button("Contact Support")
```

## Status

The status container displays a status indicator with content.

### st.status

Creates a status indicator for long-running operations.

```python
with st.status("Processing data..."):
    st.write("Fetching data...")
    time.sleep(2)
    st.write("Cleaning data...")
    time.sleep(2)
    st.write("Data processing complete!")
```

**Parameters:**
- `label`: Status message to display
- `expanded`: If True, the status details are expanded by default (default: True)
- `state`: State of the status indicator ("running", "complete", "error")

**Examples:**

```python
import streamlit as st
import time

# Basic status indicator
with st.status("Processing data...") as status:
    st.write("Fetching data...")
    time.sleep(2)
    
    st.write("Cleaning data...")
    time.sleep(2)
    
    st.write("Analyzing data...")
    time.sleep(2)
    
    status.update(label="Data processing complete!", state="complete")

# Status with error state
with st.status("Connecting to database...") as status:
    st.write("Establishing connection...")
    time.sleep(2)
    
    st.write("Authenticating...")
    time.sleep(2)
    
    # Simulate an error
    status.update(label="Connection failed!", state="error")
    st.error("Could not connect to the database. Please check your credentials.")

# Status with collapsed details
with st.status("Initializing...", expanded=False) as status:
    # The details will be hidden by default
    st.write("Loading models...")
    time.sleep(1)
    
    st.write("Configuring environment...")
    time.sleep(1)
    
    status.update(label="Ready!", state="complete")

# Using status with a progress bar
with st.status("Training model...") as status:
    progress_bar = st.progress(0)
    
    for i in range(100):
        time.sleep(0.05)
        progress_bar.progress(i + 1)
        
        if i == 25:
            st.write("25% - Loading data")
        elif i == 50:
            st.write("50% - Calculating features")
        elif i == 75:
            st.write("75% - Optimizing parameters")
    
    status.update(label="Model training complete!", state="complete")

# Status with user interaction
status = st.status("Waiting to start...", expanded=True)

if st.button("Start Process"):
    status.update(label="Process running...", state="running")
    status.write("Step 1: Initialization")
    time.sleep(2)
    
    status.write("Step 2: Processing")
    time.sleep(2)
    
    status.write("Step 3: Finalization")
    time.sleep(2)
    
    status.update(label="Process complete!", state="complete")
```

## Chat Message

Creates a chat message container styled like a chat UI.

### st.chat_message

Creates a chat message container.

```python
with st.chat_message("user"):
    st.write("Hello! How can I help you today?")
```

**Parameters:**
- `name`: Name of the sender ("user", "assistant", or custom name)
- `avatar`: URL or image to display as the avatar

**Examples:**

```python
import streamlit as st
import numpy as np

# Basic chat messages
with st.chat_message("user"):
    st.write("Hello! Can you help me understand my data?")

with st.chat_message("assistant"):
    st.write("Of course! I'd be happy to help analyze your data.")

# Chat message with custom avatar
with st.chat_message("user", avatar="🧑‍💻"):
    st.write("How do I create a line chart in Streamlit?")

with st.chat_message("assistant", avatar="🤖"):
    st.write("You can use `st.line_chart()` to create a line chart.")
    
    # Example code
    st.code("""
    import streamlit as st
    import numpy as np
    import pandas as pd
    
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    st.line_chart(chart_data)
    """)

# Chat message with rich content
with st.chat_message("user"):
    st.write("Can you show me some sample data and visualization?")

with st.chat_message("assistant"):
    st.write("Here's a sample dataframe and a chart:")
    
    # Add a dataframe
    df = pd.DataFrame({
        'Name': ['John', 'Emily', 'Sarah', 'Mike'],
        'Age': [28, 35, 42, 24],
        'City': ['New York', 'Boston', 'Chicago', 'San Francisco']
    })
    st.dataframe(df)
    
    # Add a chart
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    st.line_chart(chart_data)

# Simulating a chat conversation
messages = [
    {"role": "user", "content": "Hi there! I'm looking for insights on my sales data."},
    {"role": "assistant", "content": "I'd be happy to help! Do you have specific questions about your sales data?"},
    {"role": "user", "content": "Yes, I want to know which product category performed best last quarter."}
]

for message in messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat message with custom styling
with st.chat_message("custom", avatar="👨‍⚕️"):
    st.write("This is a message from a custom role (doctor)")
    st.info("Patient information is confidential")
```

## Configure Page

### st.set_page_config

Configures the default settings of the page.

```python
st.set_page_config(
    page_title="My App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

**Parameters:**
- `page_title`: Title of the page, shown in the browser tab
- `page_icon`: Icon shown in the browser tab
- `layout`: Page layout ("centered" or "wide")
- `initial_sidebar_state`: Initial state of the sidebar ("auto", "expanded", "collapsed")
- `menu_items`: Dictionary of menu items to override the default menu

**Examples:**

```python
import streamlit as st

# Basic page configuration
st.set_page_config(
    page_title="My Streamlit App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("This is my app with custom page configuration")

# Custom menu items
st.set_page_config(
    page_title="App with Custom Menu",
    page_icon="🔍",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': "# My Custom App\nThis is a custom Streamlit app."
    }
)

# Centered layout
st.set_page_config(
    page_title="Centered Layout",
    page_icon="🎯",
    layout="centered"
)

# Collapsed sidebar
st.set_page_config(
    page_title="Collapsed Sidebar",
    page_icon="📌",
    initial_sidebar_state="collapsed"
)
```

## Best Practices

1. **Use Columns for Side-by-Side Content**: Columns are ideal for displaying related information side by side or creating dashboard-like layouts.

2. **Use Containers for Logical Grouping**: Group related elements together in containers to maintain a clear UI organization.

3. **Use Expanders for Optional Details**: Use expanders to hide complex details or additional information that might otherwise clutter the UI.

4. **Use Tabs for Different Sections**: Organize different sections of your app into separate tabs to make navigation easier.

5. **Keep the Sidebar Focused**: Use the sidebar for navigation and global controls, keeping it focused and uncluttered.

6. **Use Empty Containers for Dynamic Content**: Use empty containers when you need to replace content based on user interaction or data updates.

7. **Consistent Layout**: Maintain a consistent layout across your app to provide a better user experience.

8. **Responsive Design**: Test your app at different screen sizes to ensure it remains usable on various devices.

9. **Progressive Disclosure**: Use containers, expanders, and tabs to implement progressive disclosure, showing only the necessary information at each step.

10. **Combine Layout Components**: Combine different layout components (e.g., columns inside tabs, expanders inside containers) to create sophisticated UIs.

## Related Components

- **[Input Widgets](input_widgets.md)**: UI elements for user input
- **[Session State](session_state.md)**: State management for your app
- **[Data Elements](data_elements.md)**: Components for displaying data