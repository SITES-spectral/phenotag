# Streamlit Input Widgets

This document provides comprehensive documentation on Streamlit's input widgets that enable interactive user interfaces in your applications.

## Table of Contents
- [Buttons](#buttons)
- [Text Input](#text-input)
- [Number Input](#number-input)
- [Text Area](#text-area)
- [Date and Time Inputs](#date-and-time-inputs)
- [Selection Widgets](#selection-widgets)
- [File Uploads](#file-uploads)
- [Media Input](#media-input)
- [Color Picker](#color-picker)
- [Forms](#forms)
- [Managing Widget State](#managing-widget-state)
- [Best Practices](#best-practices)

## Buttons

### st.button

Creates a simple button that returns `True` when clicked, and `False` otherwise.

```python
clicked = st.button("Click me")
```

**Parameters:**
- `label`: Text to display on the button
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the button
- `on_click`: Callback function to run when button is clicked
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `type`: Button type ("primary" or "secondary")
- `disabled`: If True, button is disabled
- `use_container_width`: If True, button fills container width

**Examples:**

```python
import streamlit as st

# Basic button
if st.button("Click me"):
    st.write("Button was clicked!")

# Button with callback
def button_clicked():
    st.session_state.clicked = True

st.button("Click me", on_click=button_clicked)
if "clicked" in st.session_state and st.session_state.clicked:
    st.write("Button was clicked!")

# Primary button (highlighted)
st.button("Primary Button", type="primary")

# Full-width button
st.button("Full Width", use_container_width=True)
```

### st.download_button

Creates a button that triggers a file download when clicked.

```python
st.download_button(
    label="Download CSV",
    data=csv_data,
    file_name="data.csv",
    mime="text/csv"
)
```

**Parameters:**
- `label`: Text to display on the button
- `data`: Data to be downloaded
- `file_name`: Name of the file to be downloaded
- `mime`: MIME type of the file
- Other parameters similar to `st.button`

**Examples:**

```python
import streamlit as st
import pandas as pd

# Create sample data
df = pd.DataFrame({
    'Name': ['John', 'Emily', 'Sarah', 'Mike'],
    'Age': [28, 35, 42, 24]
})

# Convert DataFrame to CSV
csv = df.to_csv(index=False)

# Download button for CSV
st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name="data.csv",
    mime="text/csv"
)

# Download button for text file
text_contents = "This is some text content for a file."
st.download_button(
    label="Download text file",
    data=text_contents,
    file_name="text_file.txt"
)

# Download button for binary file (e.g., image)
with open("image.jpg", "rb") as file:
    image_bytes = file.read()
    
st.download_button(
    label="Download Image",
    data=image_bytes,
    file_name="image.jpg",
    mime="image/jpeg"
)
```

## Text Input

### st.text_input

Creates a single-line text input widget.

```python
name = st.text_input("Your name", "John Doe")
```

**Parameters:**
- `label`: Label displayed above the input
- `value`: Default value (default: "")
- `max_chars`: Maximum number of characters allowed
- `key`: Unique key for the widget
- `type`: Input type ("default" or "password")
- `help`: Tooltip shown when hovering over the input
- `autocomplete`: Enable/disable browser autocomplete
- `on_change`: Callback function executed when the input value changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `placeholder`: Placeholder text shown when the input is empty
- `disabled`: If True, input is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic text input
name = st.text_input("Your name")
if name:
    st.write(f"Hello, {name}!")

# Text input with default value
email = st.text_input("Email address", "user@example.com")

# Password input
password = st.text_input("Password", type="password")

# Input with character limit
username = st.text_input("Username", max_chars=15)

# Input with placeholder
search = st.text_input("Search", placeholder="Type to search...")

# Input with callback
def on_value_change():
    st.session_state.name_changed = True

name = st.text_input("Name", on_change=on_value_change, key="name_input")
if "name_changed" in st.session_state and st.session_state.name_changed:
    st.write("Name was changed!")
```

## Number Input

### st.number_input

Creates a numeric input widget.

```python
age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
```

**Parameters:**
- `label`: Label displayed above the input
- `min_value`: Minimum allowed value
- `max_value`: Maximum allowed value
- `value`: Default value
- `step`: Step size
- `format`: Format string for the displayed number
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the input
- `on_change`: Callback function executed when the input value changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, input is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Integer input
age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
st.write(f"You are {age} years old")

# Float input
weight = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=70.0, step=0.1, format="%.1f")
st.write(f"You weigh {weight} kg")

# Input with custom format
price = st.number_input("Price", min_value=0.0, value=9.99, step=0.01, format="$%.2f")

# Input without min/max limits
any_number = st.number_input("Enter any number", value=0.0)
```

## Text Area

### st.text_area

Creates a multi-line text input widget.

```python
text = st.text_area("Description", "Enter details here...")
```

**Parameters:**
- `label`: Label displayed above the text area
- `value`: Default value
- `height`: Height of the text area in pixels
- `max_chars`: Maximum number of characters allowed
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the text area
- `on_change`: Callback function executed when the text area value changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `placeholder`: Placeholder text shown when the text area is empty
- `disabled`: If True, text area is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic text area
description = st.text_area("Description")
if description:
    st.write(f"You wrote: {description}")

# Text area with default value
notes = st.text_area("Notes", "Enter your notes here...")

# Text area with custom height
message = st.text_area("Message", height=200)

# Text area with character limit
feedback = st.text_area("Feedback", max_chars=500)

# Text area with placeholder
comments = st.text_area("Comments", placeholder="Add comments here...")
```

## Date and Time Inputs

### st.date_input

Creates a date input widget.

```python
date = st.date_input("Select a date")
```

**Parameters:**
- `label`: Label displayed above the input
- `value`: Default date value(s)
- `min_value`: Minimum selectable date
- `max_value`: Maximum selectable date
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the input
- `on_change`: Callback function executed when the date changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `format`: Format string for the date
- `disabled`: If True, input is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st
from datetime import date, timedelta

# Basic date input
selected_date = st.date_input("Select a date")
st.write(f"Selected date: {selected_date}")

# Date input with default value
today = date.today()
d = st.date_input("Date", today)

# Date input with min/max range
start_date = st.date_input(
    "Start date",
    date.today(),
    min_value=date.today() - timedelta(days=30),
    max_value=date.today() + timedelta(days=30)
)

# Date range selection
date_range = st.date_input(
    "Select a date range",
    [date.today(), date.today() + timedelta(days=7)]
)
if len(date_range) == 2:
    st.write(f"Start date: {date_range[0]}")
    st.write(f"End date: {date_range[1]}")
```

### st.time_input

Creates a time input widget.

```python
time = st.time_input("Meeting time")
```

**Parameters:**
- `label`: Label displayed above the input
- `value`: Default time value
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the input
- `on_change`: Callback function executed when the time changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `step`: Step size in minutes
- `disabled`: If True, input is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st
from datetime import time

# Basic time input
meeting_time = st.time_input("Meeting time")
st.write(f"Meeting scheduled at: {meeting_time}")

# Time input with default value
appointment = st.time_input("Appointment", time(9, 30))

# Time input with step
alarm = st.time_input("Alarm", time(7, 0), step=300)  # 5-minute intervals
```

## Selection Widgets

### st.selectbox

Creates a dropdown select widget.

```python
option = st.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
```

**Parameters:**
- `label`: Label displayed above the selectbox
- `options`: List of options to display
- `index`: Index of the default selected option (default: 0)
- `format_func`: Function to format the display of options
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the selectbox
- `on_change`: Callback function executed when selection changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `placeholder`: Placeholder text shown when no option is selected
- `disabled`: If True, selectbox is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic selectbox
option = st.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
st.write(f"You selected: {option}")

# Selectbox with specific default selection
day = st.selectbox("Day of the week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=4)

# Selectbox with formatting function
def format_name(name):
    return f"User: {name}"

names = ["John", "Emily", "Sarah", "Mike"]
selected_name = st.selectbox("Select a user", names, format_func=format_name)

# Selectbox with more complex objects
class Item:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    
    def __str__(self):
        return self.name

items = [Item(1, "Item 1"), Item(2, "Item 2"), Item(3, "Item 3")]
selected_item = st.selectbox("Select an item", items)
st.write(f"You selected: {selected_item} with ID: {selected_item.id}")
```

### st.multiselect

Creates a multi-select widget.

```python
options = st.multiselect("Select multiple options", ["Option 1", "Option 2", "Option 3", "Option 4"])
```

**Parameters:**
- `label`: Label displayed above the multiselect
- `options`: List of options to display
- `default`: List of default selected options
- `format_func`: Function to format the display of options
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the multiselect
- `on_change`: Callback function executed when selection changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `placeholder`: Placeholder text shown when no option is selected
- `disabled`: If True, multiselect is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")
- `max_selections`: Maximum number of selections allowed

**Examples:**

```python
import streamlit as st

# Basic multiselect
options = st.multiselect("Select multiple options", ["Option 1", "Option 2", "Option 3", "Option 4"])
st.write(f"You selected: {', '.join(options)}")

# Multiselect with default selections
selected_fruits = st.multiselect(
    "Select fruits",
    ["Apple", "Banana", "Orange", "Mango", "Grapes"],
    ["Apple", "Orange"]
)

# Multiselect with formatting function
def format_language(lang):
    return f"{lang} Programming Language"

languages = ["Python", "JavaScript", "Java", "C++", "Ruby"]
selected_languages = st.multiselect("Select languages", languages, format_func=format_language)

# Multiselect with complex objects
class Country:
    def __init__(self, code, name):
        self.code = code
        self.name = name
    
    def __str__(self):
        return self.name

countries = [Country("US", "United States"), Country("CA", "Canada"), Country("UK", "United Kingdom")]
selected_countries = st.multiselect("Select countries", countries)
selected_codes = [country.code for country in selected_countries]
st.write(f"Selected country codes: {', '.join(selected_codes)}")
```

### st.radio

Creates a radio button group.

```python
option = st.radio("Select one option", ["Option 1", "Option 2", "Option 3"])
```

**Parameters:**
- `label`: Label displayed above the radio buttons
- `options`: List of options to display
- `index`: Index of the default selected option (default: 0)
- `format_func`: Function to format the display of options
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the radio buttons
- `on_change`: Callback function executed when selection changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, radio buttons are disabled
- `horizontal`: If True, radio buttons are displayed horizontally
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic radio button group
option = st.radio("Select one option", ["Option 1", "Option 2", "Option 3"])
st.write(f"You selected: {option}")

# Radio with specific default selection
day = st.radio(
    "Day of the week",
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    index=0
)

# Horizontal radio buttons
size = st.radio("Size", ["Small", "Medium", "Large"], horizontal=True)

# Radio with formatting function
def format_option(option):
    return f"Choice: {option}"

selected = st.radio("Make a selection", ["A", "B", "C"], format_func=format_option)
```

### st.checkbox

Creates a checkbox widget.

```python
agree = st.checkbox("I agree to the terms and conditions")
```

**Parameters:**
- `label`: Label displayed next to the checkbox
- `value`: Default value (True or False)
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the checkbox
- `on_change`: Callback function executed when checkbox value changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, checkbox is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic checkbox
agree = st.checkbox("I agree to the terms and conditions")
if agree:
    st.write("Thank you for agreeing!")

# Checkbox with default value
show_details = st.checkbox("Show details", value=True)
if show_details:
    st.write("Here are the details...")

# Checkbox with callback
def on_change():
    st.session_state.checked = not st.session_state.checked

if "checked" not in st.session_state:
    st.session_state.checked = False
    
st.checkbox("Toggle me", value=st.session_state.checked, on_change=on_change)
st.write(f"Checkbox state: {st.session_state.checked}")

# Multiple checkboxes
options = ["Email notifications", "SMS notifications", "Push notifications"]
selected_options = []

for option in options:
    if st.checkbox(option):
        selected_options.append(option)

st.write(f"Selected options: {', '.join(selected_options)}")
```

### st.slider

Creates a slider widget.

```python
age = st.slider("Age", 0, 100, 25)
```

**Parameters:**
- `label`: Label displayed above the slider
- `min_value`: Minimum allowed value
- `max_value`: Maximum allowed value
- `value`: Default value or tuple of values for a range slider
- `step`: Step size
- `format`: Format string for the displayed values
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the slider
- `on_change`: Callback function executed when slider value changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, slider is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic slider
age = st.slider("Age", 0, 100, 25)
st.write(f"Age: {age}")

# Float slider
height = st.slider("Height (m)", 0.0, 2.5, 1.7, step=0.01)
st.write(f"Height: {height} m")

# Range slider
price_range = st.slider("Price range", 0, 1000, (200, 800), step=50)
st.write(f"Selected range: ${price_range[0]} to ${price_range[1]}")

# Slider with formatting
temperature = st.slider("Temperature", -50.0, 50.0, 0.0, format="%.1f °C")

# Time slider
from datetime import time
appointment = st.slider(
    "Schedule your appointment",
    min_value=time(8, 0),
    max_value=time(18, 0),
    value=time(9, 0),
    step=timedelta(minutes=30),
    format="HH:mm"
)
st.write(f"Appointment time: {appointment}")

# Date slider
from datetime import date
start_date = st.slider(
    "Select a start date",
    min_value=date(2023, 1, 1),
    max_value=date(2023, 12, 31),
    value=date(2023, 7, 1),
    format="MM/DD/YYYY"
)
```

### st.select_slider

Creates a slider with discrete values.

```python
size = st.select_slider("Select size", options=["XS", "S", "M", "L", "XL"])
```

**Parameters:**
- `label`: Label displayed above the slider
- `options`: List of options to display
- `value`: Default value or tuple of values for a range slider
- `format_func`: Function to format the display of options
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the slider
- `on_change`: Callback function executed when slider value changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, slider is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic select slider
size = st.select_slider("Select size", options=["XS", "S", "M", "L", "XL"])
st.write(f"Selected size: {size}")

# Select slider with default value
color = st.select_slider(
    "Select color",
    options=["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet"],
    value="Green"
)

# Range select slider
price_range = st.select_slider(
    "Select price range",
    options=["$0-$100", "$100-$500", "$500-$1000", "$1000-$5000", "$5000+"],
    value=("$100-$500", "$1000-$5000")
)
st.write(f"Selected range: {price_range[0]} to {price_range[1]}")

# Select slider with formatting function
def format_number(num):
    return f"Level {num}"

level = st.select_slider("Select level", options=range(1, 11), format_func=format_number)
```

## File Uploads

### st.file_uploader

Creates a file upload widget.

```python
uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt"])
```

**Parameters:**
- `label`: Label displayed above the uploader
- `type`: List of allowed file types
- `accept_multiple_files`: If True, allows uploading multiple files
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the uploader
- `on_change`: Callback function executed when uploaded files change
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, uploader is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st
import pandas as pd
import io

# Basic file uploader
uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt"])
if uploaded_file is not None:
    # Read file as bytes
    bytes_data = uploaded_file.getvalue()
    st.write(f"Filename: {uploaded_file.name}")
    st.write(f"File size: {len(bytes_data)} bytes")
    
    # Read file as string
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    string_data = stringio.read()
    st.write(f"First 100 characters: {string_data[:100]}")
    
    # For CSV files
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)

# Multiple file upload
uploaded_files = st.file_uploader("Upload multiple files", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        st.write(f"Filename: {file.name}")
        
        # For images
        if file.name.endswith(('.jpg', '.jpeg', '.png')):
            st.image(file, caption=file.name)

# File upload with custom handling
uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_csv is not None:
    df = pd.read_csv(uploaded_csv)
    st.write("CSV Preview:")
    st.dataframe(df.head())
    
    # Allow user to select columns
    selected_column = st.selectbox("Select a column to analyze", df.columns)
    st.write(f"Summary statistics for {selected_column}:")
    st.write(df[selected_column].describe())
```

## Media Input

### st.camera_input

Creates a camera input widget.

```python
image = st.camera_input("Take a picture")
```

**Parameters:**
- `label`: Label displayed above the camera input
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the camera input
- `on_change`: Callback function executed when the image changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, camera input is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st
import cv2
import numpy as np
from PIL import Image

# Basic camera input
img_file_buffer = st.camera_input("Take a picture")

if img_file_buffer is not None:
    # Convert to OpenCV image
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # Convert from BGR to RGB
    cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    
    # Display image details
    st.write(f"Image shape: {cv2_img.shape}")
    
    # Basic image processing
    gray_img = cv2.cvtColor(cv2_img, cv2.COLOR_RGB2GRAY)
    st.image(gray_img, caption="Grayscale Image")
    
    # Using PIL
    pil_img = Image.open(img_file_buffer)
    st.write(f"Image size: {pil_img.size}")
    
    # Image filters with PIL
    from PIL import ImageFilter
    blurred_img = pil_img.filter(ImageFilter.BLUR)
    st.image(blurred_img, caption="Blurred Image")
```

### st.audio_input

Creates an audio input widget.

```python
audio = st.audio_input("Record audio")
```

**Parameters:**
- `label`: Label displayed above the audio input
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the audio input
- `on_change`: Callback function executed when the audio changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, audio input is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic audio input
audio_file = st.audio_input("Record a voice message")

if audio_file is not None:
    # Get the audio bytes
    audio_bytes = audio_file.getvalue()
    st.write(f"Audio file size: {len(audio_bytes)} bytes")
    
    # Play the recorded audio
    st.audio(audio_bytes, format="audio/wav")
    
    # Save the audio to a file
    with open("recorded_audio.wav", "wb") as f:
        f.write(audio_bytes)
    st.success("Audio saved to file: recorded_audio.wav")
```

## Color Picker

### st.color_picker

Creates a color picker widget.

```python
color = st.color_picker("Choose a color", "#00f900")
```

**Parameters:**
- `label`: Label displayed above the color picker
- `value`: Default color value in hex format
- `key`: Unique key for the widget
- `help`: Tooltip shown when hovering over the color picker
- `on_change`: Callback function executed when the color changes
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `disabled`: If True, color picker is disabled
- `label_visibility`: Visibility of the label ("visible", "hidden", or "collapsed")

**Examples:**

```python
import streamlit as st

# Basic color picker
color = st.color_picker("Choose a color", "#00f900")
st.write(f"Selected color: {color}")

# Use selected color in a UI element
st.markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px;'>This div has the selected color as background</div>", unsafe_allow_html=True)

# Multiple color pickers for a color palette
st.write("Create a color palette")
primary = st.color_picker("Primary color", "#1E88E5")
secondary = st.color_picker("Secondary color", "#FFC107")
accent = st.color_picker("Accent color", "#D81B60")

# Display the color palette
st.write("Your color palette:")
col1, col2, col3 = st.columns(3)
col1.markdown(f"<div style='background-color:{primary};height:50px;border-radius:5px;'></div>", unsafe_allow_html=True)
col2.markdown(f"<div style='background-color:{secondary};height:50px;border-radius:5px;'></div>", unsafe_allow_html=True)
col3.markdown(f"<div style='background-color:{accent};height:50px;border-radius:5px;'></div>", unsafe_allow_html=True)
```

## Forms

Forms allow bundling multiple widgets together and submitting them as a single unit.

```python
with st.form("my_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Submit")
```

**Form Parameters:**
- `key`: Unique key for the form
- `clear_on_submit`: If True, form inputs are cleared on submission

**Form Submit Button Parameters:**
- `label`: Text to display on the button
- `help`: Tooltip shown when hovering over the button
- `on_click`: Callback function executed when button is clicked
- `args`: Arguments to pass to the callback
- `kwargs`: Keyword arguments to pass to the callback
- `type`: Button type ("primary" or "secondary")
- `disabled`: If True, button is disabled
- `use_container_width`: If True, button fills container width

**Examples:**

```python
import streamlit as st

# Basic form
with st.form("my_form"):
    st.write("Contact Information")
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Submit")

if submitted:
    st.write(f"Form submitted with: Name={name}, Email={email}")
    st.write(f"Message: {message}")

# Form with multiple widgets and validation
with st.form("registration_form"):
    st.write("Registration Form")
    
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    age = st.number_input("Age", min_value=0, max_value=120)
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    gender = st.radio("Gender", ["Male", "Female", "Other"])
    
    interests = st.multiselect(
        "Interests",
        ["Technology", "Art", "Sports", "Music", "Books", "Travel"]
    )
    
    agreement = st.checkbox("I agree to the terms and conditions")
    
    submitted = st.form_submit_button("Register")

if submitted:
    # Validate inputs
    if not name or not email or not password:
        st.error("Please fill all required fields")
    elif password != confirm_password:
        st.error("Passwords do not match")
    elif not agreement:
        st.error("You must agree to the terms and conditions")
    else:
        st.success(f"Registration successful! Welcome, {name}!")
        st.json({
            "name": name,
            "email": email,
            "age": age,
            "gender": gender,
            "interests": interests
        })
```

## Managing Widget State

Widgets retain their state across app reruns using Streamlit's Session State.

```python
if "counter" not in st.session_state:
    st.session_state.counter = 0

def increment():
    st.session_state.counter += 1

st.button("Increment", on_click=increment)
st.write(f"Counter value: {st.session_state.counter}")
```

### Widget Keys and Session State

Every widget with a key automatically stores its value in Session State.

```python
st.text_input("Name", key="name")
st.number_input("Age", key="age")

# Access values from Session State
st.write(f"Name: {st.session_state.name}")
st.write(f"Age: {st.session_state.age}")
```

### Callback Functions

Widgets can trigger callbacks when their values change.

```python
def update_greeting():
    st.session_state.greeting = f"Hello, {st.session_state.name}!"

st.text_input("Enter your name", key="name", on_change=update_greeting)

if "greeting" in st.session_state:
    st.write(st.session_state.greeting)
```

## Best Practices

1. **Use Consistent Keys**: Give each widget a unique key to ensure reliable state management.
   
2. **Organize Related Widgets**: Use columns, containers, or expanders to group related widgets.

3. **Validate User Input**: Always validate user input before processing it.

4. **Provide Default Values**: Set sensible default values for a better user experience.

5. **Use Help Text**: Include help text to explain how to use complex widgets.

6. **Consider Mobile Users**: Test your app on mobile devices and adjust widget sizes accordingly.

7. **Avoid Too Many Widgets**: Don't overcrowd your app with too many widgets on one page.

8. **Use Callbacks Effectively**: Use callbacks to respond to user interactions without requiring button clicks.

9. **Widget Placement**: Place widgets in a logical order that follows a natural workflow.

10. **Form vs. Individual Widgets**: Use forms when you need to collect multiple related inputs at once.

## Related Components

- **[Session State](session_state.md)**: For managing widget state between app reruns
- **[Layouts](layout.md)**: For organizing widgets in the app
- **[Caching](state_caching.md)**: For improving app performance