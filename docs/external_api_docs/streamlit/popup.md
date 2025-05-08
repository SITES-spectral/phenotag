# st.popup

## Overview

`st.popup` is a Streamlit component that creates a modal overlay containing UI elements. Popups are useful for displaying additional information, forms, or details without navigating away from the current view or cluttering the main UI.

## Syntax

```python
st.popup(title, size=None, triggered=True)
```

## Parameters

- **title** (str):
  - The title of the popup. This appears at the top of the popup window.

- **size** (str or None, optional):
  - Controls the size of the popup window. Valid values:
    - "small"
    - "medium" (default)
    - "large"
  - Default: None (uses "medium" size)

- **triggered** (bool, optional):
  - Controls whether the popup is shown:
    - True: The popup will be displayed
    - False: The popup will not be displayed
  - Default: True

## Usage

The `st.popup` is used with a `with` statement to define the content that should appear inside the popup:

```python
with st.popup(title):
    # Content to display inside the popup
```

## Examples

### Basic Popup

```python
import streamlit as st

if st.button("Show popup"):
    with st.popup("Simple Popup"):
        st.write("This is a basic popup!")
        st.write("You can add any Streamlit elements here.")
```

### Popup with Different Sizes

```python
import streamlit as st

size = st.radio("Select popup size:", ["small", "medium", "large"])

if st.button("Open Popup"):
    with st.popup("Popup Demo", size=size):
        st.write(f"This is a {size}-sized popup.")
        st.image("https://via.placeholder.com/600x400", 
                 caption="Image in popup",
                 use_column_width=True)
```

### Conditional Popup

```python
import streamlit as st

# Initialize state
if "show_popup" not in st.session_state:
    st.session_state.show_popup = False

# Button to toggle popup visibility
if st.button("Toggle Popup"):
    st.session_state.show_popup = not st.session_state.show_popup

# Display popup based on state
with st.popup("Conditional Popup", triggered=st.session_state.show_popup):
    st.write("This popup is controlled by a state variable.")
    
    # Button to close the popup
    if st.button("Close"):
        st.session_state.show_popup = False
        st.rerun()
```

### Form in Popup

```python
import streamlit as st

# Initialize session state for form data and popup control
if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "email": "", "message": ""}
if "show_form_popup" not in st.session_state:
    st.session_state.show_form_popup = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Show current data
st.write("Current Data:")
st.json(st.session_state.form_data)

# Button to open the form popup
if st.button("Edit Information"):
    st.session_state.show_form_popup = True
    st.session_state.submitted = False

# Display popup with form
with st.popup("Edit Information", triggered=st.session_state.show_form_popup):
    with st.form("info_form"):
        name = st.text_input("Name", value=st.session_state.form_data["name"])
        email = st.text_input("Email", value=st.session_state.form_data["email"])
        message = st.text_area("Message", value=st.session_state.form_data["message"])
        submitted = st.form_submit_button("Save")
    
    if submitted:
        st.session_state.form_data = {
            "name": name,
            "email": email,
            "message": message
        }
        st.session_state.submitted = True
        st.session_state.show_form_popup = False
        st.rerun()
    
    # Add a cancel button outside the form
    if st.button("Cancel"):
        st.session_state.show_form_popup = False
        st.rerun()
```

### Popup with Rich Content

```python
import streamlit as st
import pandas as pd
import numpy as np

# Create some sample data
data = pd.DataFrame({
    'A': np.random.randn(10),
    'B': np.random.randn(10),
    'C': np.random.randn(10)
})

# Main interface
st.title("Popup with Rich Content Demo")
st.dataframe(data)

# Button to show details in a popup
if st.button("Show Details"):
    with st.popup("Detailed Analysis", size="large"):
        # Two-column layout inside the popup
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Summary Statistics")
            st.write(data.describe())
            
            st.subheader("Correlation Matrix")
            st.write(data.corr())
        
        with col2:
            st.subheader("Data Visualization")
            
            tab1, tab2 = st.tabs(["Line Chart", "Bar Chart"])
            with tab1:
                st.line_chart(data)
            with tab2:
                st.bar_chart(data)
        
        # Full-width section
        st.subheader("Individual Points Analysis")
        
        # Slider to select a data point
        point_index = st.slider("Select Point", 0, len(data)-1)
        
        # Show selected point details
        st.write(f"Selected Point (Index {point_index}):")
        st.json(data.iloc[point_index].to_dict())
        
        # Close button
        if st.button("Close Dialog"):
            st.rerun()
```

### Multi-Step Form in Popup

```python
import streamlit as st

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1
if "show_wizard" not in st.session_state:
    st.session_state.show_wizard = False
if "wizard_data" not in st.session_state:
    st.session_state.wizard_data = {
        "name": "",
        "email": "",
        "age": 18,
        "interests": [],
        "subscribe": False
    }

# Function to update session state
def update_data(key, value):
    st.session_state.wizard_data[key] = value

# Function to handle next step
def next_step():
    st.session_state.step += 1

# Function to handle previous step
def prev_step():
    st.session_state.step -= 1

# Function to complete the wizard
def complete_wizard():
    st.session_state.show_wizard = False
    st.session_state.step = 1

# Button to open the wizard
if st.button("Start Wizard"):
    st.session_state.show_wizard = True
    st.session_state.step = 1

# Display current data
st.write("Current Data:")
st.json(st.session_state.wizard_data)

# Display the multi-step wizard in a popup
with st.popup("Registration Wizard", triggered=st.session_state.show_wizard, size="large"):
    # Progress bar to show current step
    st.progress((st.session_state.step - 1) / 3)
    
    # Step 1: Basic Information
    if st.session_state.step == 1:
        st.header("Step 1: Basic Information")
        
        name = st.text_input("Name", value=st.session_state.wizard_data["name"])
        update_data("name", name)
        
        email = st.text_input("Email", value=st.session_state.wizard_data["email"])
        update_data("email", email)
        
        age = st.slider("Age", 18, 100, value=st.session_state.wizard_data["age"])
        update_data("age", age)
        
        # Navigation buttons
        col1, col2 = st.columns([1, 4])
        with col2:
            if st.button("Next", use_container_width=True):
                next_step()
                st.rerun()
    
    # Step 2: Preferences
    elif st.session_state.step == 2:
        st.header("Step 2: Preferences")
        
        interests = st.multiselect(
            "Select your interests",
            ["Technology", "Science", "Arts", "Sports", "Music", "Travel", "Food", "Other"],
            default=st.session_state.wizard_data["interests"]
        )
        update_data("interests", interests)
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous", use_container_width=True):
                prev_step()
                st.rerun()
        with col2:
            if st.button("Next", use_container_width=True):
                next_step()
                st.rerun()
    
    # Step 3: Confirmation
    elif st.session_state.step == 3:
        st.header("Step 3: Confirmation")
        
        st.write("Please review your information:")
        st.write(f"Name: {st.session_state.wizard_data['name']}")
        st.write(f"Email: {st.session_state.wizard_data['email']}")
        st.write(f"Age: {st.session_state.wizard_data['age']}")
        st.write(f"Interests: {', '.join(st.session_state.wizard_data['interests'])}")
        
        subscribe = st.checkbox("Subscribe to newsletter", value=st.session_state.wizard_data["subscribe"])
        update_data("subscribe", subscribe)
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous", use_container_width=True):
                prev_step()
                st.rerun()
        with col2:
            if st.button("Submit", type="primary", use_container_width=True):
                st.success("Registration completed successfully!")
                # In a real app, you would save the data here
                complete_wizard()
                st.rerun()
```

### Popup for Confirmation

```python
import streamlit as st

# Initialize session state
if "show_confirm_popup" not in st.session_state:
    st.session_state.show_confirm_popup = False
if "action_confirmed" not in st.session_state:
    st.session_state.action_confirmed = False
if "action_type" not in st.session_state:
    st.session_state.action_type = ""

# Function to prompt for confirmation
def confirm_action(action_type):
    st.session_state.show_confirm_popup = True
    st.session_state.action_type = action_type
    st.rerun()

# Main interface
st.title("Confirmation Popup Demo")

# Display action buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Delete Item"):
        confirm_action("delete")
with col2:
    if st.button("Send Message"):
        confirm_action("send")
with col3:
    if st.button("Publish Content"):
        confirm_action("publish")

# Show confirmation status
if st.session_state.action_confirmed:
    st.success(f"Action '{st.session_state.action_type}' was confirmed!")
    # Reset after showing confirmation
    st.session_state.action_confirmed = False

# Display confirmation popup
with st.popup("Confirm Action", triggered=st.session_state.show_confirm_popup, size="small"):
    # Display action-specific message
    if st.session_state.action_type == "delete":
        st.warning("Are you sure you want to delete this item? This action cannot be undone.")
    elif st.session_state.action_type == "send":
        st.info("Are you sure you want to send this message to all users?")
    elif st.session_state.action_type == "publish":
        st.info("Are you sure you want to publish this content? It will be visible to all users.")
    
    # Add buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_confirm_popup = False
            st.rerun()
    with col2:
        if st.button("Confirm", type="primary", use_container_width=True):
            st.session_state.action_confirmed = True
            st.session_state.show_confirm_popup = False
            st.rerun()
```

### Image Gallery Popup

```python
import streamlit as st

# Sample image data
images = [
    {"url": "https://via.placeholder.com/800x600/FF5733/FFFFFF?text=Image+1", "title": "Image 1", "description": "Description for Image 1"},
    {"url": "https://via.placeholder.com/800x600/33FF57/000000?text=Image+2", "title": "Image 2", "description": "Description for Image 2"},
    {"url": "https://via.placeholder.com/800x600/3357FF/FFFFFF?text=Image+3", "title": "Image 3", "description": "Description for Image 3"},
    {"url": "https://via.placeholder.com/800x600/F3FF33/000000?text=Image+4", "title": "Image 4", "description": "Description for Image 4"},
]

# Initialize session state
if "selected_image" not in st.session_state:
    st.session_state.selected_image = None

# Function to open image popup
def open_image(index):
    st.session_state.selected_image = index
    st.rerun()

# Main interface - image gallery
st.title("Image Gallery")

# Display thumbnails in a grid
cols = st.columns(2)
for i, image in enumerate(images):
    with cols[i % 2]:
        st.image(image["url"], caption=image["title"], width=300)
        if st.button(f"View Details", key=f"btn_{i}"):
            open_image(i)

# Image popup
if st.session_state.selected_image is not None:
    image = images[st.session_state.selected_image]
    
    with st.popup(image["title"], size="large"):
        # Display the image
        st.image(image["url"], use_column_width=True)
        
        # Image details
        st.subheader("Details")
        st.write(image["description"])
        
        # Extra details that would clutter the main gallery
        st.write("Additional details about this image would go here...")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # Previous button
        with col1:
            if st.session_state.selected_image > 0:
                if st.button("← Previous"):
                    st.session_state.selected_image -= 1
                    st.rerun()
        
        # Close button
        with col2:
            if st.button("Close", use_container_width=True):
                st.session_state.selected_image = None
                st.rerun()
        
        # Next button
        with col3:
            if st.session_state.selected_image < len(images) - 1:
                if st.button("Next →"):
                    st.session_state.selected_image += 1
                    st.rerun()
```

## Integration with Other Components

### Popup with Tabs

```python
import streamlit as st
import pandas as pd
import numpy as np

# Create sample data
data = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])

# Main app
st.title("Popup with Tabs Demo")

if st.button("Open Details Popup"):
    with st.popup("Data Analysis", size="large"):
        # Create tabs within the popup
        tab1, tab2, tab3 = st.tabs(["Data", "Charts", "Statistics"])
        
        # Tab 1: Data
        with tab1:
            st.write("### Raw Data")
            st.dataframe(data)
            
            if st.checkbox("Show data types"):
                st.write(data.dtypes)
        
        # Tab 2: Charts
        with tab2:
            st.write("### Data Visualization")
            
            chart_type = st.radio("Select chart type:", ["Line", "Bar", "Area"], horizontal=True)
            
            if chart_type == "Line":
                st.line_chart(data)
            elif chart_type == "Bar":
                st.bar_chart(data)
            else:
                st.area_chart(data)
        
        # Tab 3: Statistics
        with tab3:
            st.write("### Statistical Analysis")
            st.write("Summary Statistics:")
            st.write(data.describe())
            
            st.write("Correlation Matrix:")
            st.write(data.corr())
```

### Popup with Forms and Session State

```python
import streamlit as st

# Initialize session state for user data
if "users" not in st.session_state:
    st.session_state.users = [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "role": "Admin"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "role": "User"},
        {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "role": "Editor"}
    ]

if "edit_user" not in st.session_state:
    st.session_state.edit_user = None

if "show_edit_popup" not in st.session_state:
    st.session_state.show_edit_popup = False

if "show_add_popup" not in st.session_state:
    st.session_state.show_add_popup = False

# Functions for user management
def edit_user(user_id):
    for user in st.session_state.users:
        if user["id"] == user_id:
            st.session_state.edit_user = user.copy()
            break
    st.session_state.show_edit_popup = True
    st.rerun()

def add_user():
    st.session_state.edit_user = {"id": len(st.session_state.users) + 1, "name": "", "email": "", "role": "User"}
    st.session_state.show_add_popup = True
    st.rerun()

def save_edited_user(user_data):
    # Find and update the existing user
    for i, user in enumerate(st.session_state.users):
        if user["id"] == user_data["id"]:
            st.session_state.users[i] = user_data
            break
    st.session_state.show_edit_popup = False
    st.session_state.edit_user = None
    st.rerun()

def save_new_user(user_data):
    st.session_state.users.append(user_data)
    st.session_state.show_add_popup = False
    st.session_state.edit_user = None
    st.rerun()

def delete_user(user_id):
    st.session_state.users = [user for user in st.session_state.users if user["id"] != user_id]
    st.rerun()

# Main app
st.title("User Management System")

# Add user button
st.button("Add New User", on_click=add_user)

# Display users in a table
st.write("### Users")
for user in st.session_state.users:
    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
    col1.write(user["name"])
    col2.write(user["email"])
    col3.write(user["role"])
    with col4:
        st.button("Edit", key=f"edit_{user['id']}", on_click=edit_user, args=(user["id"],))
        st.button("Delete", key=f"delete_{user['id']}", on_click=delete_user, args=(user["id"],))
    st.divider()

# Edit user popup
with st.popup("Edit User", triggered=st.session_state.show_edit_popup):
    if st.session_state.edit_user:
        with st.form("edit_user_form"):
            user_id = st.session_state.edit_user["id"]
            st.write(f"Editing User #{user_id}")
            
            name = st.text_input("Name", value=st.session_state.edit_user["name"])
            email = st.text_input("Email", value=st.session_state.edit_user["email"])
            role = st.selectbox("Role", ["Admin", "Editor", "User"], 
                             index=["Admin", "Editor", "User"].index(st.session_state.edit_user["role"]))
            
            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancel")
            with col2:
                save = st.form_submit_button("Save Changes")
            
            if save:
                updated_user = {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "role": role
                }
                save_edited_user(updated_user)
            
            if cancel:
                st.session_state.show_edit_popup = False
                st.session_state.edit_user = None
                st.rerun()

# Add user popup
with st.popup("Add New User", triggered=st.session_state.show_add_popup):
    if st.session_state.edit_user:
        with st.form("add_user_form"):
            user_id = st.session_state.edit_user["id"]
            
            name = st.text_input("Name", value="")
            email = st.text_input("Email", value="")
            role = st.selectbox("Role", ["Admin", "Editor", "User"], index=2)
            
            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancel")
            with col2:
                save = st.form_submit_button("Add User")
            
            if save:
                new_user = {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "role": role
                }
                save_new_user(new_user)
            
            if cancel:
                st.session_state.show_add_popup = False
                st.session_state.edit_user = None
                st.rerun()
```

## Best Practices

1. **Use Meaningful Titles**: Choose clear, descriptive titles for your popups to help users understand their purpose.

2. **Select Appropriate Size**: Choose the appropriate size for your popup based on the content:
   - "small" for simple messages or confirmations
   - "medium" for forms or moderate content
   - "large" for complex visualizations or large forms

3. **Maintain Context**: Popups should be contextual to the action that triggered them.

4. **Provide Close Options**: Always include a way to close the popup (button, cancel option, etc.).

5. **Use Session State**: Manage popup visibility with session state for better control over when popups appear.

6. **Optimize for Readability**: Keep content within popups clear and concise. Don't overcrowd the popup.

7. **Use Proper Layout**: Organize popup content using columns, tabs, and other layout elements as needed.

8. **Avoid Excessive Nesting**: Don't nest popups within popups, as this can create a confusing user experience.

9. **Provide Visual Feedback**: For forms in popups, provide clear success/error messages before closing.

10. **Consider Mobile Users**: Test how your popups appear on mobile devices, and ensure they're usable on smaller screens.

## Common Issues and Solutions

1. **Popup Not Showing**: Ensure that the `triggered` parameter is set to `True`.

2. **Popup Reappears After Actions**: Make sure to update the state variable controlling the popup visibility after actions.

3. **Form Submission Issues**: Use `st.rerun()` after form submission to ensure the popup closes properly.

4. **Layout Problems**: If content overflows, try using a larger popup size or reorganizing the content with layout elements.

5. **Session State Persistence**: Remember that session state is preserved across app reruns, so you may need to reset certain state variables.

6. **Multiple Popups Conflict**: Be careful when managing multiple popups with session state to avoid unexpected behavior.

7. **Popup Content Executes Even When Hidden**: Code inside a popup block still runs even if the popup isn't displayed. Use conditional logic if certain operations should only happen when the popup is visible.

8. **Scrolling Inside Popups**: For large content, be aware that popups have their own scrolling behavior.