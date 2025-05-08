# st.session_state

## Overview

`st.session_state` is a key feature in Streamlit that provides a way to preserve state between reruns of your app. It allows you to store and access data across different interactions and sessions.

## How It Works

- **Session-specific:** Data is tied to each user session
- **Persistent during session:** Values retain across reruns of the app
- **Dictionary-like access:** Use it like a Python dictionary
- **Attribute-based access:** Also supports attribute notation

## Syntax

Session state can be accessed and modified directly using either dictionary-like or attribute-based syntax:

```python
# Dictionary-like syntax
st.session_state["key"] = value
value = st.session_state["key"]

# Attribute-based syntax
st.session_state.key = value
value = st.session_state.key

# Check if a key exists
if "key" in st.session_state:
    # Do something
```

## Common Operations

### Initializing Values

```python
# Check if key exists before initializing
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Or in one line using dictionary-like syntax
if "counter" not in st.session_state:
    st.session_state["counter"] = 0
```

### Updating Values

```python
# Increment a counter
st.session_state.counter += 1

# Update a list
if "my_list" not in st.session_state:
    st.session_state.my_list = []
st.session_state.my_list.append(new_item)
```

### Deleting Values

```python
# Delete a specific key
if "temp_data" in st.session_state:
    del st.session_state.temp_data

# Clear all keys
st.session_state.clear()
```

### Displaying Session State

```python
# Display the entire session state (useful for debugging)
st.write("Session State:", st.session_state)

# Display a specific value
st.write("Counter:", st.session_state.counter)
```

## Examples

### Simple Counter App

```python
import streamlit as st

# Initialize counter
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Display current count
st.write(f"Count: {st.session_state.counter}")

# Button to increment
if st.button("Increment"):
    st.session_state.counter += 1
    st.rerun()  # Rerun to update the displayed count

# Button to reset
if st.button("Reset"):
    st.session_state.counter = 0
    st.rerun()  # Rerun to update the displayed count
```

### Form Input Memory

```python
import streamlit as st

# Initialize session state for form fields
if "name" not in st.session_state:
    st.session_state.name = ""
if "email" not in st.session_state:
    st.session_state.email = ""

# Show current stored values
st.write("Current stored values:")
st.write(f"Name: {st.session_state.name}")
st.write(f"Email: {st.session_state.email}")

# Create a form
with st.form("user_form"):
    # Get user input with current session state as default
    name_input = st.text_input("Name", value=st.session_state.name)
    email_input = st.text_input("Email", value=st.session_state.email)
    submitted = st.form_submit_button("Submit")

# Update session state when form is submitted
if submitted:
    st.session_state.name = name_input
    st.session_state.email = email_input
    st.success("Form submitted successfully!")
```

### Multi-page App State

```python
import streamlit as st

# Function to change the page
def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# Initialize the current page if not already set
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Initialize user data if not already set
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# Display different pages based on current_page
if st.session_state.current_page == "home":
    st.title("Home Page")
    st.write("Welcome to the home page!")
    if st.button("Go to Form"):
        navigate_to("form")
    if st.button("Go to Results"):
        navigate_to("results")

elif st.session_state.current_page == "form":
    st.title("Data Entry Form")
    
    # Form
    with st.form("data_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        submitted = st.form_submit_button("Submit")
    
    if submitted:
        st.session_state.user_data["name"] = name
        st.session_state.user_data["age"] = age
        st.success("Data saved successfully!")
    
    if st.button("Go to Home"):
        navigate_to("home")
    if st.button("Go to Results"):
        navigate_to("results")

elif st.session_state.current_page == "results":
    st.title("Results Page")
    
    if st.session_state.user_data:
        st.write("User Data:")
        for key, value in st.session_state.user_data.items():
            st.write(f"{key}: {value}")
    else:
        st.warning("No data has been entered yet.")
    
    if st.button("Go to Home"):
        navigate_to("home")
    if st.button("Go to Form"):
        navigate_to("form")
```

### Widget State Callbacks

```python
import streamlit as st

# Define callback functions
def increment_counter():
    st.session_state.counter += 1

def reset_counter():
    st.session_state.counter = 0

# Initialize counter
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Display current count
st.write(f"Count: {st.session_state.counter}")

# Buttons with callbacks
st.button("Increment", on_click=increment_counter)
st.button("Reset", on_click=reset_counter)

# Alternative with direct callback
if st.button("Increment (Alternative)"):
    st.session_state.counter += 1
```

### Widget Key-Based State

```python
import streamlit as st

# Using widget keys to track state
st.text_input("Enter your name", key="name")
st.number_input("Enter your age", key="age", min_value=0, max_value=120)
st.selectbox("Select your country", 
             options=["USA", "Canada", "UK", "Australia", "Other"],
             key="country")

# Display the values from session state
st.write("Name:", st.session_state.name)
st.write("Age:", st.session_state.age)
st.write("Country:", st.session_state.country)

# Clear inputs button
if st.button("Clear Inputs"):
    st.session_state.name = ""
    st.session_state.age = 0
    st.session_state.country = "USA"
    st.rerun()
```

## Advanced Usage

### Managing Complex State

```python
import streamlit as st
import pandas as pd
import numpy as np

# Initialize complex state
if "dataframe" not in st.session_state:
    # Create a sample DataFrame
    st.session_state.dataframe = pd.DataFrame(
        np.random.randn(5, 3),
        columns=['A', 'B', 'C']
    )

if "settings" not in st.session_state:
    # Create a nested dictionary for app settings
    st.session_state.settings = {
        "theme": "light",
        "display": {
            "show_sidebar": True,
            "wide_mode": False
        },
        "filters": []
    }

# Display and interact with complex state
st.write("DataFrame:", st.session_state.dataframe)

# Modify dataframe
if st.button("Add Row"):
    new_row = pd.DataFrame(
        [np.random.randn(3)],
        columns=['A', 'B', 'C']
    )
    st.session_state.dataframe = pd.concat([st.session_state.dataframe, new_row], ignore_index=True)

# Modify settings
theme = st.radio("Theme", ["light", "dark"], index=0 if st.session_state.settings["theme"] == "light" else 1)
show_sidebar = st.checkbox("Show Sidebar", st.session_state.settings["display"]["show_sidebar"])
wide_mode = st.checkbox("Wide Mode", st.session_state.settings["display"]["wide_mode"])

# Update settings
if st.button("Apply Settings"):
    st.session_state.settings["theme"] = theme
    st.session_state.settings["display"]["show_sidebar"] = show_sidebar
    st.session_state.settings["display"]["wide_mode"] = wide_mode
    st.success("Settings updated!")
```

### Using Session State with Forms

```python
import streamlit as st

# Initialize session state
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "name": "",
        "email": "",
        "message": ""
    }
if "submissions" not in st.session_state:
    st.session_state.submissions = []

# Function to handle form submission
def handle_submit():
    # Make a copy of the current form data
    submission = st.session_state.form_data.copy()
    # Add it to the submissions list
    st.session_state.submissions.append(submission)
    # Clear the form
    st.session_state.form_data = {
        "name": "",
        "email": "",
        "message": ""
    }

# Display form
with st.form("contact_form"):
    st.write("Contact Form")
    
    # Form fields with default values from session state
    name = st.text_input("Name", value=st.session_state.form_data["name"])
    email = st.text_input("Email", value=st.session_state.form_data["email"])
    message = st.text_area("Message", value=st.session_state.form_data["message"])
    
    # Submit button
    submitted = st.form_submit_button("Submit")

# Update form data in session state (whether submitted or not)
st.session_state.form_data["name"] = name
st.session_state.form_data["email"] = email
st.session_state.form_data["message"] = message

# Handle form submission
if submitted:
    handle_submit()
    st.success("Form submitted successfully!")

# Display submissions
if st.session_state.submissions:
    st.write("Submissions:")
    for i, submission in enumerate(st.session_state.submissions):
        st.write(f"Submission {i+1}:")
        st.write(f"Name: {submission['name']}")
        st.write(f"Email: {submission['email']}")
        st.write(f"Message: {submission['message']}")
        st.write("---")
```

## Best Practices

1. **Initialize Early**: Always initialize session state variables at the beginning of your app
   ```python
   if "key" not in st.session_state:
       st.session_state.key = default_value
   ```

2. **Use Descriptive Keys**: Use clear, descriptive names for your keys
   ```python
   # Good
   st.session_state.user_settings = {...}
   
   # Not as clear
   st.session_state.u_s = {...}
   ```

3. **Organize Related Data**: Group related data within dictionaries
   ```python
   if "form_data" not in st.session_state:
       st.session_state.form_data = {
           "name": "",
           "email": "",
           "age": 0
       }
   ```

4. **Be Cautious with Mutable Objects**: When using mutable objects like lists or dictionaries, be aware of reference issues
   ```python
   # Make a copy when needed to avoid unwanted references
   new_list = st.session_state.my_list.copy()
   ```

5. **Use Session State with Widget Keys**: For simple widget state, use the widget key approach
   ```python
   st.text_input("Input", key="my_input")
   # Access with st.session_state.my_input
   ```

6. **Debug with st.write**: Easily debug your session state by displaying it
   ```python
   st.write(st.session_state)  # Display all session state
   ```

## Limitations

1. **Session Expiry**: Session state is cleared when the Streamlit server restarts or after periods of inactivity

2. **Not for Persistent Storage**: Session state is not designed for long-term storage; use databases for that purpose

3. **Not Shared Between Users**: Each user gets their own separate session state

4. **Serialization Issues**: Not all Python objects can be properly stored in session state (e.g., file handles, database connections)

5. **Performance with Large Data**: Storing large datasets in session state can impact performance