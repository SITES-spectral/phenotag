# Streamlit Execution Flow

This document provides comprehensive documentation on Streamlit's execution flow, including how scripts run, rerun triggers, caching, and fragments.

## Table of Contents
- [Script Execution](#script-execution)
- [Reruns](#reruns)
- [Fragments](#fragments)
- [Callbacks](#callbacks)
- [Forms](#forms)
- [Caching](#caching)
- [Best Practices](#best-practices)

## Script Execution

Streamlit executes scripts from top to bottom in a reactive programming model.

### Basic Execution Model

When a Streamlit app is launched:

1. The entire script runs from top to bottom.
2. UI elements are displayed in the order they're created during script execution.
3. When a user interacts with a widget (button, slider, etc.), the entire script reruns.
4. During rerun, widget values are preserved through Session State.

```python
import streamlit as st

st.title("Basic Execution Flow")

# This runs on every script execution
st.write("This code always runs")

# Widget values are preserved between reruns
name = st.text_input("Your name")

# Code after a widget executes on every script run
if name:
    st.write(f"Hello, {name}!")

# This code runs even if name is empty
st.write("This code always runs too")
```

### Execution Order

Streamlit adds UI elements to the app in the order they're created in your code:

```python
import streamlit as st

# First element
st.title("Execution Order")

# Second element
st.write("This appears second")

# Third element using a container
container = st.container()

# Fourth element (outside the container)
st.write("This appears fourth")

# This will actually be the third element
container.write("This appears third")
```

## Reruns

Streamlit reruns the script when:

1. A user interacts with a widget.
2. The app is explicitly told to rerun with `st.rerun()`.
3. A session's source code is modified.

### Widget-Triggered Reruns

Every time a user interacts with a widget, the script reruns:

```python
import streamlit as st

st.title("Widget-Triggered Reruns")

# Display the current timestamp to show when the script reruns
from datetime import datetime
st.write(f"Current time: {datetime.now().strftime('%H:%M:%S')}")

# The script reruns when this slider is moved
value = st.slider("Move this slider to trigger a rerun", 0, 100, 50)
st.write(f"Slider value: {value}")

# The script reruns when this button is clicked
if st.button("Click me to trigger a rerun"):
    st.write("Button was clicked!")
```

### Explicit Reruns

You can explicitly trigger a rerun using `st.rerun()`:

```python
import streamlit as st
import time

st.title("Explicit Rerun")

if "counter" not in st.session_state:
    st.session_state.counter = 0

st.write(f"Counter: {st.session_state.counter}")

# Trigger rerun with a button
if st.button("Increment and rerun"):
    st.session_state.counter += 1
    st.rerun()  # Explicitly rerun the script

# Automatic rerun every 5 seconds
if st.checkbox("Enable auto-rerun"):
    st.write("This page will rerun automatically in 5 seconds")
    time.sleep(5)
    st.session_state.counter += 1
    st.rerun()  # Trigger rerun after sleep
```

## Fragments

Fragments are sections of your app that can be rerun independently from the rest of the app. They were introduced in Streamlit 1.19.0.

### Basic Fragment

Create a fragment using the `@st.fragment` decorator:

```python
import streamlit as st
import time

st.title("Fragments Example")

# This code runs on every app rerun
st.write("This code is outside the fragment and runs on every rerun")

# Define a fragment
@st.fragment
def my_fragment():
    st.write(f"Fragment last ran at: {time.strftime('%H:%M:%S')}")
    
    # This button only reruns the fragment, not the entire app
    if st.button("Rerun fragment"):
        st.write("Fragment button was clicked!")

# Code after the fragment still runs on every app rerun
my_fragment()  # Execute the fragment
st.write("This code runs on every app rerun too")
```

### Fragments with Arguments

Fragments can accept arguments:

```python
import streamlit as st
import numpy as np
import time

st.title("Fragments with Arguments")

# Create some data
data = np.random.randn(100, 2)

# Fragment that receives data as an argument
@st.fragment
def data_visualization(data, title):
    st.subheader(title)
    st.write(f"Fragment ran at: {time.strftime('%H:%M:%S')}")
    
    chart_type = st.selectbox("Select chart type", ["Scatter", "Line", "Bar"], key="chart_type")
    
    if chart_type == "Scatter":
        st.scatter_chart(data)
    elif chart_type == "Line":
        st.line_chart(data)
    else:
        st.bar_chart(data)
        
    if st.button("Regenerate Data", key="regen"):
        # This triggers only a fragment rerun
        st.write("Regenerating data...")

# Call the fragment with different arguments
data_visualization(data, "First Dataset")
data_visualization(np.random.randn(50, 3), "Second Dataset")
```

### Passing Containers to Fragments

Fragments can work with containers:

```python
import streamlit as st
import time

st.title("Fragments with Containers")

# Create containers
container1 = st.container()
container2 = st.container()

# Fragment that updates containers
@st.fragment
def update_containers(container_a, container_b):
    st.write(f"Fragment ran at: {time.strftime('%H:%M:%S')}")
    
    update_a = st.button("Update Container A")
    update_b = st.button("Update Container B")
    
    if update_a:
        with container_a:
            st.write(f"Container A updated at {time.strftime('%H:%M:%S')}")
            st.metric("Value A", np.random.randint(1, 100))
    
    if update_b:
        with container_b:
            st.write(f"Container B updated at {time.strftime('%H:%M:%S')}")
            st.metric("Value B", np.random.randint(1, 100))

# Execute the fragment with containers
update_containers(container1, container2)

# This runs on every full app rerun
st.write("This code is outside the fragment")
```

### Auto-Rerunning Fragments

Create a fragment that automatically reruns:

```python
import streamlit as st
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.title("Auto-Rerunning Fragment")

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(
        np.random.randn(20, 3), 
        columns=["A", "B", "C"],
        index=pd.date_range(start=datetime.now() - timedelta(minutes=20), periods=20, freq="min")
    )

if "stream" not in st.session_state:
    st.session_state.stream = False

# Function to toggle streaming state
def toggle_streaming():
    st.session_state.stream = not st.session_state.stream

# Function to generate recent data
def get_recent_data(last_timestamp):
    now = datetime.now()
    if now - last_timestamp > timedelta(seconds=60):
        last_timestamp = now - timedelta(seconds=60)
    
    sample_time = timedelta(seconds=1)
    next_timestamp = last_timestamp + sample_time
    timestamps = pd.date_range(start=next_timestamp, end=now, freq=sample_time)
    
    if len(timestamps) == 0:
        return pd.DataFrame()
    
    sample_values = np.random.randn(len(timestamps), 3)
    data = pd.DataFrame(sample_values, index=timestamps, columns=["A", "B", "C"])
    return data

# Create the auto-rerunning fragment
@st.fragment
def streaming_data_fragment():
    st.subheader("Live Data Stream")
    
    # UI controls
    st.sidebar.button("Start streaming", disabled=st.session_state.stream, on_click=toggle_streaming)
    st.sidebar.button("Stop streaming", disabled=not st.session_state.stream, on_click=toggle_streaming)
    
    # Placeholder for chart
    chart = st.line_chart(st.session_state.data)
    
    # Auto-rerun when streaming is enabled
    if st.session_state.stream:
        last_timestamp = st.session_state.data.index[-1]
        new_data = get_recent_data(last_timestamp)
        
        if not new_data.empty:
            # Update session state data
            st.session_state.data = pd.concat([st.session_state.data, new_data]).iloc[-100:]
            
            # Update chart
            chart.line_chart(st.session_state.data)
            
            # Artificially add a small delay
            time.sleep(0.5)
            
            # Rerun this fragment (not the entire app)
            st.rerun()

# Execute the fragment
streaming_data_fragment()

# This only runs on full app reruns
st.write("This text is outside the fragment and only updates on full app reruns")
```

### Triggering Full Reruns from Fragments

Sometimes you need to trigger a full app rerun from within a fragment:

```python
import streamlit as st
import time
from datetime import date

st.title("Full Rerun from Fragment")

# Fragment for date selection
@st.fragment
def date_selector():
    selected_date = st.date_input("Select a date", date.today())
    
    if "previous_date" not in st.session_state:
        st.session_state.previous_date = selected_date
    
    # Check if month has changed
    previous_date = st.session_state.previous_date
    st.session_state.previous_date = selected_date
    
    month_changed = selected_date.month != previous_date.month
    
    if month_changed:
        st.write("Month changed! Triggering full app rerun...")
        time.sleep(1)
        st.rerun()  # Triggers full app rerun
    
    st.write(f"Selected date: {selected_date}")
    st.write(f"Previous date: {previous_date}")

# Run the fragment
date_selector()

# This code depends on the selected date's month
st.subheader(f"Data for {date.today().strftime('%B %Y')}")
st.write("This section requires a full rerun when the month changes")
```

## Callbacks

Callbacks are functions that execute when widgets are triggered.

### Basic Callbacks

```python
import streamlit as st

st.title("Callbacks Example")

def on_button_click():
    st.session_state.clicked = True

if "clicked" not in st.session_state:
    st.session_state.clicked = False

# Button with callback
st.button("Click me", on_click=on_button_click)

# Display result based on session state
if st.session_state.clicked:
    st.write("Button was clicked!")
else:
    st.write("Button has not been clicked yet")
```

### Callbacks with Arguments

```python
import streamlit as st

st.title("Callbacks with Arguments")

def process_name(prefix):
    st.session_state.processed_name = prefix + " " + st.session_state.name

# Text input
st.text_input("Enter your name", key="name")

# Buttons with different callbacks
st.button("Add Mr.", on_click=process_name, args=("Mr.",))
st.button("Add Ms.", on_click=process_name, args=("Ms.",))
st.button("Add Dr.", on_click=process_name, args=("Dr.",))

# Display processed name
if "processed_name" in st.session_state:
    st.write(f"Processed name: {st.session_state.processed_name}")
```

### Callbacks for Multiple Widgets

```python
import streamlit as st

st.title("Multiple Widget Callbacks")

def update_total():
    st.session_state.total = st.session_state.quantity * st.session_state.price

# Initialize session state
if "quantity" not in st.session_state:
    st.session_state.quantity = 1
if "price" not in st.session_state:
    st.session_state.price = 10.0
if "total" not in st.session_state:
    st.session_state.total = st.session_state.quantity * st.session_state.price

# Widgets with callbacks
st.number_input("Quantity", min_value=1, value=st.session_state.quantity, key="quantity", on_change=update_total)
st.number_input("Price", min_value=0.0, value=st.session_state.price, key="price", on_change=update_total)

# Display total
st.write(f"Total: ${st.session_state.total:.2f}")
```

## Forms

Forms allow bundling multiple widgets together and submitting them as a single unit.

### Basic Form

```python
import streamlit as st

st.title("Forms Example")

with st.form("my_form"):
    st.write("Inside the form")
    name = st.text_input("Name")
    age = st.slider("Age", 0, 120, 30)
    submitted = st.form_submit_button("Submit")

if submitted:
    st.write(f"Form submitted with name: {name} and age: {age}")
```

### Form with Callback

```python
import streamlit as st

st.title("Form with Callback")

def handle_form_submission():
    st.session_state.form_submitted = True
    st.session_state.submitted_name = st.session_state.form_name
    st.session_state.submitted_age = st.session_state.form_age

# Initialize session state
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

with st.form("callback_form"):
    st.text_input("Name", key="form_name")
    st.slider("Age", 0, 120, 30, key="form_age")
    st.form_submit_button("Submit", on_click=handle_form_submission)

if st.session_state.form_submitted:
    st.write(f"Submitted Name: {st.session_state.submitted_name}")
    st.write(f"Submitted Age: {st.session_state.submitted_age}")
```

### Multiple Forms

```python
import streamlit as st

st.title("Multiple Forms")

# First form
with st.form("personal_info"):
    st.subheader("Personal Information")
    name = st.text_input("Name")
    email = st.text_input("Email")
    personal_submitted = st.form_submit_button("Save Personal Info")

if personal_submitted:
    st.success(f"Personal information saved for {name}")

# Second form
with st.form("preferences"):
    st.subheader("Preferences")
    color = st.selectbox("Favorite Color", ["Red", "Green", "Blue"])
    hobby = st.text_input("Favorite Hobby")
    pref_submitted = st.form_submit_button("Save Preferences")

if pref_submitted:
    st.success(f"Preferences saved: Color - {color}, Hobby - {hobby}")
```

## Caching

Streamlit provides caching mechanisms to optimize performance.

### st.cache_data

Caches the return value of a function:

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("Caching with st.cache_data")

# Function with cache_data
@st.cache_data
def expensive_computation(n):
    st.write(f"Cache miss: expensive_computation({n}) called")
    time.sleep(2)  # Simulate expensive computation
    return pd.DataFrame(np.random.randn(n, 5), columns=list('abcde'))

# Demonstrate caching behavior
n = st.slider("Select data size", 10, 1000, 100)

st.write("Calling expensive_computation()...")
start_time = time.time()
data = expensive_computation(n)
end_time = time.time()

st.write(f"Execution time: {end_time - start_time:.4f} seconds")
st.dataframe(data)

# This will use the cached value if the input (n) hasn't changed
st.write("Calling expensive_computation() again...")
start_time = time.time()
data_again = expensive_computation(n)
end_time = time.time()

st.write(f"Execution time: {end_time - start_time:.4f} seconds")
```

### st.cache_resource

Caches a single resource object:

```python
import streamlit as st
import pandas as pd
import numpy as np
import time
import sqlite3

st.title("Caching with st.cache_resource")

# Initialize a database connection with cache_resource
@st.cache_resource
def get_database_connection():
    st.write("Cache miss: Creating new database connection")
    time.sleep(2)  # Simulate connection delay
    conn = sqlite3.connect(":memory:")
    
    # Create a sample table
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER, value REAL)")
    
    # Insert some data
    for i in range(10):
        c.execute("INSERT INTO data VALUES (?, ?)", (i, np.random.rand()))
    
    conn.commit()
    return conn

st.write("Getting database connection...")
start_time = time.time()
conn = get_database_connection()
end_time = time.time()

st.write(f"Connection time: {end_time - start_time:.4f} seconds")

# Query the database
query = st.text_input("Enter SQL query", "SELECT * FROM data")
if query:
    try:
        df = pd.read_sql_query(query, conn)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error executing query: {e}")

# This will use the cached connection
st.write("Getting database connection again...")
start_time = time.time()
conn_again = get_database_connection()
end_time = time.time()

st.write(f"Connection time: {end_time - start_time:.4f} seconds")
```

### Cache Invalidation

Controlling cache invalidation:

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("Cache Invalidation")

# Cache with TTL (Time To Live)
@st.cache_data(ttl=10)  # Cache invalidates after 10 seconds
def get_data_with_ttl():
    st.write(f"Cache miss: get_data_with_ttl() called at {time.strftime('%H:%M:%S')}")
    return pd.DataFrame(np.random.randn(5, 3), columns=['A', 'B', 'C'])

# Cache with max_entries
@st.cache_data(max_entries=2)  # Only keep the 2 most recent results
def get_data_with_max_entries(n):
    st.write(f"Cache miss: get_data_with_max_entries({n}) called")
    return pd.DataFrame(np.random.randn(n, 3), columns=['A', 'B', 'C'])

# Demonstrate TTL
st.subheader("Cache with TTL (10 seconds)")
st.write("This data will refresh automatically after 10 seconds")
data_ttl = get_data_with_ttl()
st.dataframe(data_ttl)

# Demonstrate max_entries
st.subheader("Cache with max_entries (2)")
option = st.selectbox("Select size", [10, 20, 30, 40, 50])
data_max = get_data_with_max_entries(option)
st.dataframe(data_max)
st.write("Try selecting different values. Only the 2 most recent will be cached.")

# Manual cache clearing
st.subheader("Manual Cache Clearing")

# Define a function with normal caching
@st.cache_data
def get_random_data():
    st.write(f"Cache miss: get_random_data() called at {time.strftime('%H:%M:%S')}")
    return pd.DataFrame(np.random.randn(5, 3), columns=['A', 'B', 'C'])

data = get_random_data()
st.dataframe(data)

if st.button("Clear Cache"):
    # Clear this function's cache
    get_random_data.clear()
    st.write("Cache cleared!")

if st.button("Clear All Caches"):
    # Clear all st.cache_data caches
    st.cache_data.clear()
    st.write("All caches cleared!")
```

## Best Practices

### 1. Optimize Script Structure

```python
import streamlit as st
import pandas as pd
import numpy as np

# 1. Always place imports at the top
# 2. Place expensive operations in cached functions

# 3. Initialize session state variables at the top
if "counter" not in st.session_state:
    st.session_state.counter = 0

# 4. Define cached functions near the top
@st.cache_data
def load_data():
    df = pd.DataFrame(np.random.randn(1000, 5), columns=list('abcde'))
    return df

# 5. Use fragments for parts that need independent reruns
@st.fragment
def interactive_visualization():
    data = load_data()
    chart_type = st.selectbox("Select chart type", ["Line", "Bar", "Scatter"])
    
    if chart_type == "Line":
        st.line_chart(data)
    elif chart_type == "Bar":
        st.bar_chart(data)
    else:
        st.scatter_chart(data, x='a', y='b')

# 6. Main app logic
st.title("Optimized App Structure")

# 7. Call cached functions and fragments
data = load_data()
st.write("Data sample:", data.head())

interactive_visualization()

# 8. Minimize operations after user inputs
if st.button("Increment Counter"):
    st.session_state.counter += 1

st.write(f"Counter: {st.session_state.counter}")
```

### 2. Use Fragments Effectively

```python
import streamlit as st
import time

st.title("Effective Fragment Usage")

# 1. Use fragments for independent parts of the UI
@st.fragment
def settings_panel():
    st.subheader("Settings")
    theme = st.selectbox("Theme", ["Light", "Dark", "System"])
    font_size = st.slider("Font Size", 8, 24, 14)
    
    return theme, font_size

@st.fragment
def content_area(theme, font_size):
    st.subheader("Content")
    st.write(f"Current theme: {theme}")
    st.write(f"Font size: {font_size}px")
    
    content = st.text_area("Enter content")
    
    if content:
        st.markdown(f"<div style='font-size:{font_size}px'>{content}</div>", unsafe_allow_html=True)

# 2. Fragment for features that need frequent updates
@st.fragment
def live_stats():
    st.subheader("Live Statistics")
    
    if st.button("Refresh Stats"):
        with st.status("Refreshing..."):
            time.sleep(1)  # Simulate API call
            st.write("Data updated!")
            
            # Only this fragment reruns, not the entire app
            st.metric("Users", f"{np.random.randint(1000, 5000)}", f"{np.random.randint(-100, 100)}")
            st.metric("Revenue", f"${np.random.randint(10000, 50000)}", f"${np.random.randint(-1000, 1000)}")
            st.metric("Conversion", f"{np.random.uniform(1, 5):.2f}%", f"{np.random.uniform(-1, 1):.2f}%")

# Main app execution
col1, col2 = st.columns([1, 3])

with col1:
    theme, font_size = settings_panel()
    live_stats()

with col2:
    content_area(theme, font_size)

# This code still runs on every full app rerun
st.write("Last full app rerun:", time.strftime("%H:%M:%S"))
```

### 3. Manage Session State Properly

```python
import streamlit as st

st.title("Session State Best Practices")

# 1. Initialize all session state variables at the top
if "user_settings" not in st.session_state:
    st.session_state.user_settings = {
        "name": "",
        "theme": "Light",
        "notifications": True
    }

if "page" not in st.session_state:
    st.session_state.page = "home"

# 2. Create functions to manage state transitions
def go_to_page(page_name):
    st.session_state.page = page_name

def update_settings(key, value):
    st.session_state.user_settings[key] = value
    st.success(f"{key} updated to {value}")

# 3. Create a navigation system
st.sidebar.title("Navigation")
st.sidebar.button("Home", on_click=go_to_page, args=("home",))
st.sidebar.button("Settings", on_click=go_to_page, args=("settings",))
st.sidebar.button("Profile", on_click=go_to_page, args=("profile",))

# 4. Display content based on state
if st.session_state.page == "home":
    st.header("Home Page")
    st.write(f"Welcome, {st.session_state.user_settings['name'] or 'Guest'}!")
    st.write("This is the home page of the application.")
    
elif st.session_state.page == "settings":
    st.header("Settings")
    
    # Use current values from session state as defaults
    name = st.text_input("Name", st.session_state.user_settings["name"])
    theme = st.selectbox("Theme", ["Light", "Dark", "System"], 
                        index=["Light", "Dark", "System"].index(st.session_state.user_settings["theme"]))
    notifications = st.checkbox("Enable Notifications", st.session_state.user_settings["notifications"])
    
    if st.button("Save Settings"):
        update_settings("name", name)
        update_settings("theme", theme)
        update_settings("notifications", notifications)
        
elif st.session_state.page == "profile":
    st.header("User Profile")
    if st.session_state.user_settings["name"]:
        st.write(f"Name: {st.session_state.user_settings['name']}")
        st.write(f"Theme: {st.session_state.user_settings['theme']}")
        st.write(f"Notifications: {'Enabled' if st.session_state.user_settings['notifications'] else 'Disabled'}")
    else:
        st.warning("Please set your name in Settings first")
        st.button("Go to Settings", on_click=go_to_page, args=("settings",))

# 5. Display current state (for debugging)
if st.checkbox("Show session state"):
    st.write(st.session_state)
```

### 4. Optimize for Performance

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("Performance Optimization")

# 1. Cache data loading operations
@st.cache_data
def load_large_dataset():
    st.write("Cache miss: Loading large dataset...")
    time.sleep(2)  # Simulate loading time
    return pd.DataFrame(np.random.randn(10000, 10))

# 2. Cache resource initialization
@st.cache_resource
def initialize_model():
    st.write("Cache miss: Initializing model...")
    time.sleep(3)  # Simulate model initialization
    # This would be a machine learning model in a real app
    return {"model_name": "SampleModel", "version": "1.0", "accuracy": 0.92}

# 3. Use fragments for expensive UI sections
@st.fragment
def data_explorer():
    st.subheader("Data Explorer")
    
    # Load data through cache
    data = load_large_dataset()
    
    # Allow exploring without rerunning the entire app
    num_rows = st.slider("Number of rows", 5, 100, 10)
    columns = st.multiselect("Select columns", data.columns.tolist(), data.columns.tolist()[:3])
    
    # Show filtered data
    st.dataframe(data.loc[:num_rows-1, columns])
    
    # Compute statistics without triggering full reruns
    if st.button("Compute Statistics"):
        with st.status("Computing..."):
            time.sleep(1)  # Simulate computation
            st.write("Statistics:", data[columns].describe())

# 4. Lazy loading with expanders
with st.expander("Model Information"):
    # Only initialized when the expander is opened
    model = initialize_model()
    st.json(model)

# 5. Main app components
data_explorer()

# 6. Avoid unnecessary computations
show_charts = st.checkbox("Show Charts")

if show_charts:
    chart_data = load_large_dataset().iloc[:100, :3]  # Reuse cached data
    
    tab1, tab2 = st.tabs(["Line Chart", "Bar Chart"])
    
    with tab1:
        st.line_chart(chart_data)
    
    with tab2:
        st.bar_chart(chart_data)
```

## Related Components

- **[Session State](session_state.md)**: State management across reruns
- **[Caching](state_caching.md)**: Detailed information on caching
- **[Layouts and Containers](layout_containers.md)**: Organizing UI elements