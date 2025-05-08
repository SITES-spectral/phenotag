# Streamlit State Management

This document provides comprehensive documentation on state management in Streamlit applications, focusing on Session State and other state-related features.

## Table of Contents
- [Session State Overview](#session-state-overview)
- [Working with Session State](#working-with-session-state)
- [State Persistence](#state-persistence)
- [Widget State](#widget-state)
- [State vs. Caching](#state-vs-caching)
- [Best Practices](#best-practices)

## Session State Overview

Streamlit's Session State provides a way to share variables between reruns for each user session. It persists across Streamlit script reruns and acts as a "memory" for your application.

### Why Session State is Needed

Due to Streamlit's execution model (running from top to bottom on each interaction), any variables defined in your script are recreated on each rerun. Session State provides a way to maintain state between runs.

```python
import streamlit as st

# Without Session State
count = 0
if st.button("Increment"):
    count += 1  # This will always be 0+1=1 on each click
st.write(f"Count: {count}")

# With Session State
if "count" not in st.session_state:
    st.session_state.count = 0
    
if st.button("Increment"):
    st.session_state.count += 1  # This persists between reruns
st.write(f"Count: {st.session_state.count}")
```

### Session State Anatomy

`st.session_state` is a dictionary-like object where:
- Keys are strings identifying the state variable
- Values can be almost any Python object (with some serialization considerations)

## Working with Session State

### Initialization

Always initialize session state values before use:

```python
import streamlit as st

# Check if the key exists before using it
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
    
# Initialize multiple values
if "initialized" not in st.session_state:
    st.session_state.update({
        "initialized": True,
        "counter": 0,
        "user_settings": {
            "theme": "light",
            "notifications": True
        }
    })
```

### Access Methods

There are two equivalent ways to access session state:

```python
# Dictionary-style access
value = st.session_state["key"]

# Attribute-style access
value = st.session_state.key
```

Choose the style that makes your code most readable. Attribute-style is often more concise, while dictionary-style is more explicit and handles keys with spaces or special characters.

### Updating Values

```python
# Direct assignment
st.session_state.counter = 42

# Dictionary-style update
st.session_state["counter"] = 42

# Update multiple values
st.session_state.update({
    "counter": 42,
    "name": "John Doe",
    "active": True
})
```

### Removing Values

```python
# Remove a single value
del st.session_state.counter

# Check before removing
if "counter" in st.session_state:
    del st.session_state.counter
    
# Clear all session state
for key in list(st.session_state.keys()):
    del st.session_state[key]
```

### Complex Data Types

Session State can store complex Python objects:

```python
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize with complex data
if "data" not in st.session_state:
    st.session_state.data = {
        "df": pd.DataFrame({
            "A": np.random.randn(10),
            "B": np.random.randn(10)
        }),
        "timestamp": datetime.now(),
        "nested": {
            "level1": {
                "level2": "value"
            }
        }
    }

# Accessing complex data
st.write(st.session_state.data["df"].head())
st.write(f"Timestamp: {st.session_state.data['timestamp']}")
st.write(f"Nested value: {st.session_state.data['nested']['level1']['level2']}")

# Updating complex data
if st.button("Update DataFrame"):
    # Create a copy to avoid reference issues
    new_df = st.session_state.data["df"].copy()
    new_df["C"] = np.random.randn(10)
    st.session_state.data["df"] = new_df
    st.session_state.data["timestamp"] = datetime.now()
```

### Serialization Considerations

By default, Session State can handle most Python objects. However, when deploying to Streamlit Cloud or other platforms, consider the following:

1. Some environments enforce serialization (using pickle) for Session State values
2. Unserializable objects (like database connections, file handles, or certain custom objects) may cause issues

For strict serialization enforcement:

```toml
# .streamlit/config.toml
[runner]
enforceSerializableSessionState = true
```

With this setting, attempting to store unserializable objects will raise an exception:

```python
import streamlit as st

def unserializable_function():
    return lambda x: x

# This will raise an exception with enforceSerializableSessionState=true
st.session_state.func = unserializable_function()
```

## State Persistence

### Session Duration

By default, session state persists until:
1. The browser tab is closed
2. The user's session times out due to inactivity
3. The Streamlit server is restarted

### Cross-Page State

Session State is shared across all pages in a multi-page Streamlit app:

```python
# page1.py
import streamlit as st

if "user" not in st.session_state:
    st.session_state.user = ""

username = st.text_input("Enter your name", st.session_state.user)
if username:
    st.session_state.user = username
    
# page2.py
import streamlit as st

if "user" in st.session_state and st.session_state.user:
    st.write(f"Welcome back, {st.session_state.user}!")
else:
    st.write("Please enter your name on the first page")
```

### Long-Term Persistence

For long-term storage beyond the user's session, consider:

1. Using databases or file storage
2. Implementing custom authentication
3. Using browser-side storage via components

Example with file-based persistence:

```python
import streamlit as st
import json
import os

# Function to load data from file
def load_user_data(user_id):
    file_path = f"user_data/{user_id}.json"
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    
    return {"user_id": user_id, "settings": {}, "saved_items": []}

# Function to save data to file
def save_user_data(data):
    user_id = data["user_id"]
    file_path = f"user_data/{user_id}.json"
    
    # Ensure directory exists
    os.makedirs("user_data", exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump(data, f)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"
    
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data(st.session_state.user_id)

# UI for changing user ID
user_id = st.text_input("User ID", st.session_state.user_id)
if user_id != st.session_state.user_id:
    st.session_state.user_id = user_id
    st.session_state.user_data = load_user_data(user_id)
    st.rerun()

# UI for updating user settings
st.subheader("Settings")
theme = st.selectbox(
    "Theme",
    ["Light", "Dark", "System"],
    index=["Light", "Dark", "System"].index(
        st.session_state.user_data.get("settings", {}).get("theme", "Light")
    )
)

# Save button
if st.button("Save Settings"):
    # Update session state
    if "settings" not in st.session_state.user_data:
        st.session_state.user_data["settings"] = {}
        
    st.session_state.user_data["settings"]["theme"] = theme
    
    # Save to file
    save_user_data(st.session_state.user_data)
    st.success("Settings saved!")
```

## Widget State

### Automatic State Management

Widgets automatically sync with session state when you provide a key:

```python
import streamlit as st

# Text input with state
name = st.text_input("Your name", key="name")

# Access the value
st.write(f"Hello, {st.session_state.name}!")

# Slider with default value
if "temperature" not in st.session_state:
    st.session_state.temperature = 70

temperature = st.slider(
    "Temperature",
    min_value=0,
    max_value=100,
    value=st.session_state.temperature,
    key="temperature"
)
```

### Callbacks for Widget State Changes

You can execute functions when widgets change using callbacks:

```python
import streamlit as st

def on_name_change():
    st.session_state.greeting = f"Hello, {st.session_state.name}!"

# Initialize
if "greeting" not in st.session_state:
    st.session_state.greeting = ""

# Widget with callback
name = st.text_input("Your name", key="name", on_change=on_name_change)

# Display greeting
st.write(st.session_state.greeting)
```

When a callback is triggered:
1. The widget's value is already updated in `st.session_state`
2. The callback function is executed
3. Then the script reruns from top to bottom

### Callbacks with Arguments

```python
import streamlit as st

def change_country(continent):
    if continent == "Europe":
        st.session_state.country_options = ["Germany", "France", "UK", "Spain"]
    elif continent == "Asia":
        st.session_state.country_options = ["China", "Japan", "India", "Thailand"]
    elif continent == "Americas":
        st.session_state.country_options = ["USA", "Canada", "Brazil", "Mexico"]
    else:
        st.session_state.country_options = []

# Initialize
if "country_options" not in st.session_state:
    st.session_state.country_options = []

# Continent selection with callback
continent = st.selectbox(
    "Select a continent",
    ["", "Europe", "Asia", "Americas"],
    on_change=change_country,
    args=(st.session_state.get("continent", ""),)
)

# Country selection based on continent
if st.session_state.country_options:
    country = st.selectbox("Select a country", st.session_state.country_options)
else:
    st.write("Please select a continent first")
```

### Forms and Session State

Forms bundle multiple widgets and only trigger callbacks on submission:

```python
import streamlit as st

# Initialize session state
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
    st.session_state.user_data = {
        "name": "",
        "email": "",
        "age": 0
    }

def handle_form_submit():
    st.session_state.form_submitted = True
    st.session_state.user_data = {
        "name": st.session_state.name,
        "email": st.session_state.email,
        "age": st.session_state.age
    }

# Create form
with st.form("user_form"):
    st.text_input("Name", key="name")
    st.text_input("Email", key="email")
    st.number_input("Age", key="age", min_value=0, max_value=120)
    
    # Submit button
    submitted = st.form_submit_button("Submit", on_click=handle_form_submit)

# Display results after submission
if st.session_state.form_submitted:
    st.success("Form submitted successfully!")
    
    st.write("Submitted data:")
    for key, value in st.session_state.user_data.items():
        st.write(f"{key}: {value}")
    
    # Reset button
    if st.button("Reset Form"):
        st.session_state.form_submitted = False
        st.session_state.name = ""
        st.session_state.email = ""
        st.session_state.age = 0
        st.rerun()
```

### Widget Key Conflicts

Each widget key must be unique within your app:

```python
import streamlit as st

# This will cause an error - both widgets use the same key
value1 = st.text_input("Input 1", key="shared_key")
value2 = st.number_input("Input 2", key="shared_key")  # Error!

# Instead, use unique keys
value1 = st.text_input("Input 1", key="text_key")
value2 = st.number_input("Input 2", key="number_key")
```

### Widget Value Manipulation Limitations

Certain widget types have limitations:

1. Button states (`st.button`) can't be directly set in Session State
2. Upload widgets (`st.file_uploader`) can't have their files set programmatically
3. Camera and microphone inputs can't be simulated

```python
import streamlit as st

# This will throw an error
if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = True  # State is set

st.button("Click me", key="button_clicked")  # Error!
```

## State vs. Caching

### Session State vs. Cache

Streamlit has two distinct mechanisms for persistence:

1. **Session State (`st.session_state`)**: 
   - Per-session, user-specific data
   - Mutable storage
   - Use for user inputs, UI state, temporary calculations
   
2. **Caching (`st.cache_data`, `st.cache_resource`)**:
   - Cross-session, global data
   - Immutable function results
   - Use for expensive computations, database connections, ML models

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

# Session State example
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = {
        "rows": 10,
        "columns": ["A", "B"]
    }

# Cache example
@st.cache_data
def load_large_dataset():
    # This will only execute once, then cache the result
    print("Loading large dataset...")
    time.sleep(2)  # Simulate loading time
    return pd.DataFrame(np.random.randn(1000, 5), columns=list("ABCDE"))

# UI to modify session state
rows = st.slider(
    "Number of rows",
    min_value=5,
    max_value=100,
    value=st.session_state.user_preferences["rows"]
)

available_columns = list("ABCDE")
columns = st.multiselect(
    "Select columns",
    available_columns,
    default=st.session_state.user_preferences["columns"]
)

# Update session state on change
if (rows != st.session_state.user_preferences["rows"] or 
    columns != st.session_state.user_preferences["columns"]):
    st.session_state.user_preferences["rows"] = rows
    st.session_state.user_preferences["columns"] = columns

# Use cached data, filtered by session state
data = load_large_dataset()
filtered_data = data.loc[:rows-1, columns]
st.dataframe(filtered_data)
```

### When to Use Each

- **Use Session State when**:
  - Tracking user-specific data
  - Managing UI state (current page, expanded sections)
  - Storing temporary calculations
  - Building multi-step forms or wizards
  - Implementing undo/redo functionality
  - Managing authentication states

- **Use Caching when**:
  - Performing expensive data loading operations
  - Running time-consuming calculations
  - Initializing ML models
  - Managing database connections
  - Processing large files
  - Fetching remote data

## Best Practices

### 1. Consistent Initialization

Always initialize all session state variables at the top of your script:

```python
import streamlit as st

# Initialize all session state variables at the top
if "initialized" not in st.session_state:
    st.session_state.update({
        "initialized": True,
        "page": "home",
        "user": None,
        "settings": {
            "theme": "light",
            "sidebar_collapsed": False
        },
        "data": None
    })

# Rest of your app
# ...
```

### 2. Use a State Management Pattern

Group related state in dictionaries and use functions to update state:

```python
import streamlit as st

# Initialize state
if "user" not in st.session_state:
    st.session_state.user = {
        "logged_in": False,
        "username": None,
        "preferences": {
            "theme": "light",
            "notifications": True
        }
    }

# State management functions
def login(username):
    st.session_state.user["logged_in"] = True
    st.session_state.user["username"] = username
    
def logout():
    st.session_state.user["logged_in"] = False
    st.session_state.user["username"] = None
    
def update_preference(key, value):
    st.session_state.user["preferences"][key] = value

# UI
if not st.session_state.user["logged_in"]:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username and password == "password":  # Demo only!
            login(username)
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    st.write(f"Welcome, {st.session_state.user['username']}!")
    
    # Preferences
    theme = st.selectbox(
        "Theme",
        ["light", "dark"],
        index=["light", "dark"].index(st.session_state.user["preferences"]["theme"])
    )
    
    notifications = st.checkbox(
        "Enable notifications",
        value=st.session_state.user["preferences"]["notifications"]
    )
    
    if st.button("Save Preferences"):
        update_preference("theme", theme)
        update_preference("notifications", notifications)
        st.success("Preferences saved!")
        
    if st.button("Logout"):
        logout()
        st.rerun()
```

### 3. Avoid Excessive State

Only store what you need in session state:

```python
import streamlit as st
import pandas as pd

# BAD: Storing entire DataFrame in session state
if "data" not in st.session_state:
    st.session_state.data = pd.read_csv("large_file.csv")  # Inefficient

# GOOD: Cache the data loading, store only filters in session state
@st.cache_data
def load_data():
    return pd.read_csv("large_file.csv")

if "filters" not in st.session_state:
    st.session_state.filters = {
        "min_value": 0,
        "max_value": 100,
        "categories": []
    }

# Load data through cache
data = load_data()

# UI for filters
min_value = st.slider("Min Value", 0, 100, st.session_state.filters["min_value"])
max_value = st.slider("Max Value", 0, 100, st.session_state.filters["max_value"])
categories = st.multiselect("Categories", data["category"].unique(), st.session_state.filters["categories"])

# Update filters in session state
st.session_state.filters["min_value"] = min_value
st.session_state.filters["max_value"] = max_value
st.session_state.filters["categories"] = categories

# Apply filters
filtered_data = data[
    (data["value"] >= min_value) &
    (data["value"] <= max_value) &
    (data["category"].isin(categories) if categories else True)
]

st.dataframe(filtered_data)
```

### 4. Handle Serialization

Be aware of serialization requirements, especially when deploying:

```python
import streamlit as st
import pickle
import base64
import io

# Test if an object is serializable
def is_serializable(obj):
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PickleError, TypeError):
        return False

# Safely store objects
def safe_store(key, obj):
    if is_serializable(obj):
        st.session_state[key] = obj
        return True
    else:
        st.warning(f"Object for key '{key}' is not serializable")
        return False

# Example usage
class SimpleClass:
    def __init__(self, value):
        self.value = value

# Serializable object
simple_obj = SimpleClass(42)
safe_store("simple_obj", simple_obj)

# Potentially unserializable object (files, connections)
buffer = io.StringIO("Hello World")

# For unserializable objects, consider serializing manually
if not safe_store("buffer", buffer):
    # Alternative: serialize to string
    buffer_contents = buffer.getvalue()
    st.session_state.buffer_contents = buffer_contents
    st.info("Stored buffer contents instead")
```

### 5. Structure Multi-Page Apps

For multi-page apps, organize session state consistently:

```python
import streamlit as st

# Common session state initialization for multi-page apps
def initialize_session_state():
    defaults = {
        "user": {
            "logged_in": False,
            "username": None,
            "role": "guest"
        },
        "navigation": {
            "current_page": "home",
            "history": ["home"]
        },
        "data": {
            "loaded": False,
            "filters": {}
        },
        "ui": {
            "theme": "light",
            "sidebar_expanded": True
        }
    }
    
    # Initialize with defaults for any missing keys
    for section, items in defaults.items():
        if section not in st.session_state:
            st.session_state[section] = {}
            
        for key, value in items.items():
            if key not in st.session_state[section]:
                st.session_state[section][key] = value

# Call at the start of each page
initialize_session_state()

# Navigation system
def navigate_to(page):
    st.session_state.navigation["current_page"] = page
    st.session_state.navigation["history"].append(page)

# Page management based on session state
current_page = st.session_state.navigation["current_page"]

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    
    for page in ["home", "dashboard", "settings", "about"]:
        if st.button(page.title(), key=f"nav_{page}"):
            navigate_to(page)
            st.rerun()
    
    # Authentication
    if st.session_state.user["logged_in"]:
        st.write(f"Logged in as: {st.session_state.user['username']}")
        if st.button("Logout"):
            st.session_state.user["logged_in"] = False
            st.session_state.user["username"] = None
            st.rerun()
    else:
        if st.button("Login"):
            navigate_to("login")
            st.rerun()

# Display current page
st.title(current_page.title())

if current_page == "home":
    st.write("Welcome to the home page!")
    
elif current_page == "dashboard":
    if not st.session_state.user["logged_in"]:
        st.warning("Please login to view the dashboard")
        navigate_to("login")
        st.rerun()
    else:
        st.write("Dashboard content here")
    
elif current_page == "settings":
    st.write("Settings page")
    
    theme = st.selectbox(
        "Theme",
        ["light", "dark"],
        index=["light", "dark"].index(st.session_state.ui["theme"])
    )
    
    if st.button("Save Settings"):
        st.session_state.ui["theme"] = theme
        st.success("Settings saved!")
    
elif current_page == "login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Demo login
        if username and password == "password":
            st.session_state.user["logged_in"] = True
            st.session_state.user["username"] = username
            navigate_to("home")
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")
```

## Related Components

- **[Execution Flow](execution_flow.md)**: How Streamlit scripts execute
- **[Caching](state_caching.md)**: Detailed information on caching
- **[Input Widgets](input_widgets.md)**: UI elements for user input