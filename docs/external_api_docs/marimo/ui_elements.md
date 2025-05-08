# Marimo UI Elements

Marimo provides a rich set of UI elements that allow you to create interactive interfaces directly within your Python notebooks. This document covers the various UI elements available in Marimo and how to use them effectively.

## Basic Input Elements

### Sliders

```python
# Basic numeric slider
slider = mo.ui.slider(1, 10, value=5, label="Value")

# Slider with step size
slider_step = mo.ui.slider(0, 1, step=0.01, value=0.5, label="Probability")

# Range slider (select a range of values)
range_slider = mo.ui.range_slider(0, 100, value=[25, 75], label="Range")

# Access slider values
mo.md(f"Selected value: {slider.value}")
mo.md(f"Selected range: {range_slider.value}")
```

### Buttons

```python
# Simple button
button = mo.ui.button(label="Click me")

# Button with value and on_click handler
counter = mo.ui.button(
    value=0, 
    label="Count",
    on_click=lambda count: count + 1
)

# Run button (for triggering cell execution)
run_button = mo.ui.run_button()

# Access button values
mo.md(f"Button was clicked: {button.value}")
mo.md(f"Counter value: {counter.value}")
```

### Text Inputs

```python
# Single-line text input
text = mo.ui.text(
    placeholder="Enter text here",
    label="Input"
)

# Multi-line text area
text_area = mo.ui.text_area(
    placeholder="Enter longer text here...",
    label="Comments"
)

# Password input
password = mo.ui.text(
    placeholder="Password",
    kind="password",
    label="Password"
)

# Form-wrapped text input (only updates on submit)
form = mo.ui.text(placeholder="Search...").form(
    submit_button_label="Search"
)

# Access text values
mo.md(f"Text input: {text.value}")
```

### Numeric Inputs

```python
# Number input with constraints
number = mo.ui.number(
    start=0,
    stop=100,
    step=5,
    value=50,
    label="Quantity"
)

# Access number values
mo.md(f"Selected number: {number.value}")
```

### Checkboxes and Switches

```python
# Checkbox
checkbox = mo.ui.checkbox(
    label="I agree to terms",
    value=False
)

# Switch (toggle)
switch = mo.ui.switch(
    label="Dark mode"
)

# Access boolean values
mo.md(f"Checkbox status: {checkbox.value}")
mo.md(f"Switch status: {switch.value}")
```

### Radio Buttons

```python
# Radio button group
radio = mo.ui.radio(
    options=["Option 1", "Option 2", "Option 3"],
    value="Option 1", 
    label="Select one option"
)

# With dictionary options
radio_dict = mo.ui.radio(
    options={"Option A": 1, "Option B": 2, "Option C": 3},
    value="Option A",
    label="Select one option"
)

# Access radio values
mo.md(f"Selected option: {radio.value}")
mo.md(f"Selected value: {radio_dict.selected_key}")
```

### Dropdowns

```python
# Simple dropdown
dropdown = mo.ui.dropdown(
    options=["Option 1", "Option 2", "Option 3"],
    value="Option 1", 
    label="Select from dropdown"
)

# With dictionary options
dropdown_dict = mo.ui.dropdown(
    options={"Red": "#ff0000", "Green": "#00ff00", "Blue": "#0000ff"},
    value="Red",
    label="Select color"
)

# Access dropdown values
mo.md(f"Selected option: {dropdown.value}")
mo.md(f"Selected color: {dropdown_dict.selected_key} - {dropdown_dict.value}")
```

### Date and Time Pickers

```python
# Date picker
date = mo.ui.date(label="Select date")

# Date range picker
date_range = mo.ui.date_range(label="Select date range")

# Datetime picker
datetime = mo.ui.datetime(label="Select date and time")

# Access date values
mo.md(f"Selected date: {date.value}")
mo.md(f"Selected date range: {date_range.value}")
```

### File Inputs

```python
# Button-style file input
file_button = mo.ui.file(kind="button")

# Drag-and-drop area
file_area = mo.ui.file(kind="area")

# Multiple file selection
file_multi = mo.ui.file(kind="area", multiple=True)

# Access file data
if file_button.value:
    mo.md(f"Filename: {file_button.value.name}")
    mo.md(f"Size: {len(file_button.value.contents)} bytes")
    # For text files
    mo.md(f"Content preview: {file_button.value.contents[:100].decode('utf-8')}")
```

### Microphone Input

```python
# Microphone recording
microphone = mo.ui.microphone(label="Record audio")

# Display recorded audio
mo.audio(microphone.value)
```

### Refresh Control

```python
# Refresh control
refresh = mo.ui.refresh(
    label="Refresh",
    options=["1s", "5s", "10s", "30s"]
)

# This cell re-runs based on the refresh setting
refresh
import datetime
mo.md(f"Last refreshed: {datetime.datetime.now()}")
```

## Container Components

### Arrays

Group multiple instances of the same UI element:

```python
# Create a template element
wish = mo.ui.text(placeholder="Wish")

# Create an array of three text inputs
wishes = mo.ui.array([wish] * 3, label="Three wishes")

# Access array values
mo.md(f"Your wishes: {wishes.value}")
```

### Dictionaries

Group different UI elements with named keys:

```python
# Create individual elements
first_name = mo.ui.text(placeholder="First name")
last_name = mo.ui.text(placeholder="Last name")
email = mo.ui.text(placeholder="Email", kind="email")

# Group them in a dictionary
person = mo.ui.dictionary({
    "First name": first_name,
    "Last name": last_name,
    "Email": email,
})

# Access dictionary values
mo.md(f"Person data: {person.value}")
```

### Batch

Embed UI elements within a markdown template:

```python
# Create a batch of UI elements within markdown
form = mo.md("""
# User Information

### Personal Details
**Name**: {name}
**Age**: {age}

### Contact
**Email**: {email}
**Phone**: {phone}
""").batch(
    name=mo.ui.text(placeholder="Your name"),
    age=mo.ui.number(18, 120),
    email=mo.ui.text(placeholder="Email", kind="email"),
    phone=mo.ui.text(placeholder="Phone number")
)

# Access batch values
mo.md(f"Form data: {form.value}")
```

### Forms

Wrap UI elements in a form that requires explicit submission:

```python
# Simple form
form = mo.ui.text_area(placeholder="Enter text...").form(
    submit_button_label="Submit"
)

# Multiple elements in a form
form_complex = mo.vstack([
    mo.ui.text(label="Username"),
    mo.ui.text(label="Password", kind="password")
]).form(submit_button_label="Login")

# Access form values
mo.md(f"Submitted text: {form.value}")
```

## Data Components

### Tables

Create interactive tables with selection capabilities:

```python
# Create table from list of dictionaries
table = mo.ui.table(
    data=[
        {"name": "Alice", "age": 25},
        {"name": "Bob", "age": 30},
        {"name": "Charlie", "age": 35}
    ],
    pagination=True,
    selection="single"  # "multi", "cell", or None
)

# Table with DataFrame
import pandas as pd
df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35]
})
df_table = mo.ui.table(df, selection="multi")

# Access selected rows
mo.md(f"Selected row: {table.value}")
mo.md(f"Selected rows: {df_table.value}")
```

### Data Explorer

Create an interactive data exploration interface:

```python
# Create a data explorer for a DataFrame
import pandas as pd
df = pd.read_csv("data.csv")
mo.ui.data_explorer(df)
```

### Altair Charts

Create interactive Altair visualizations:

```python
import altair as alt
import pandas as pd

# Create a DataFrame
data = pd.DataFrame({
    "x": range(10),
    "y": [i**2 for i in range(10)],
    "category": ["A"] * 5 + ["B"] * 5
})

# Create an Altair chart
chart = alt.Chart(data).mark_circle().encode(
    x='x',
    y='y',
    color='category'
)

# Make it interactive
interactive_chart = mo.ui.altair_chart(chart)

# Access selections from the chart
mo.md(f"Selected points: {interactive_chart.value}")
```

## Layout Components

### Horizontal Stack

Arrange elements horizontally:

```python
# Basic horizontal layout
mo.hstack([
    mo.md("Left content"),
    mo.md("Right content")
])

# With alignment and spacing
mo.hstack(
    [mo.md("Left"), mo.md("Center"), mo.md("Right")],
    justify="space-between",  # Options: "start", "end", "center", "space-between", "space-around"
    align="center",  # Options: "start", "end", "center", "stretch"
    gap=2,  # Gap between elements in rem
    wrap=True  # Allow wrapping to multiple lines
)
```

### Vertical Stack

Arrange elements vertically:

```python
# Basic vertical layout
mo.vstack([
    mo.md("Top content"),
    mo.md("Bottom content")
])

# With alignment
mo.vstack(
    [mo.md("Top"), mo.md("Middle"), mo.md("Bottom")],
    align="stretch",  # Options: "start", "end", "center", "stretch"
    gap=1  # Gap between elements in rem
)
```

### Tabs

Create a tabbed interface:

```python
# Simple tabs
mo.tabs({
    "Tab 1": mo.md("Content for tab 1"),
    "Tab 2": mo.md("Content for tab 2"),
    "Tab 3": mo.ui.slider(1, 10)
})
```

### Accordion

Create an accordion interface:

```python
# Simple accordion
mo.accordion({
    "Section 1": mo.md("Content for section 1"),
    "Section 2": mo.md("Content for section 2"),
    "Controls": mo.ui.slider(1, 10)
})
```

### Grid

Create a grid layout:

```python
# 2x2 grid
mo.grid([
    [mo.md("Top left"), mo.md("Top right")],
    [mo.md("Bottom left"), mo.md("Bottom right")]
])
```

### Tree

Create a hierarchical display:

```python
# Tree of elements
mo.tree(
    [
        "Root item",
        {"Nested group": [
            "Nested item 1",
            "Nested item 2",
            mo.ui.slider(1, 10)
        ]},
        "Another root item"
    ],
    label="Navigation"
)
```

## Display Components

### Markdown

Render markdown content:

```python
# Basic markdown
mo.md("# Heading\nThis is **bold** and this is *italic*.")

# With variables
name = "World"
mo.md(f"# Hello, {name}!\nWelcome to my **Marimo** notebook.")

# Multiline formatting
mo.md(f"""
# Project Dashboard

## Statistics
- Total items: **{total_items}**
- Completed: **{completed_items}**
- Progress: **{completed_items / total_items * 100:.1f}%**
""")
```

### LaTeX

Render mathematical equations:

```python
# Inline LaTeX
mo.md("The formula is $E = mc^2$")

# Block LaTeX
mo.latex(r"\int_{a}^{b} f(x) \, dx = F(b) - F(a)")
```

### HTML

Render raw HTML content:

```python
# Raw HTML
mo.Html("<div style='color: blue; background-color: #eee; padding: 10px;'>Custom HTML content</div>")

# HTML with variables
color = "red"
mo.Html(f"<div style='color: {color}; font-weight: bold;'>Dynamic color</div>")
```

### Audio

Play audio content:

```python
# From file path
mo.audio("path/to/audio.mp3")

# From binary data
mo.audio(audio_data)

# From microphone input
mo.audio(microphone.value)
```

### Image

Display images:

```python
# From file path
mo.image("path/to/image.png")

# From binary data
mo.image(image_data)

# With width and height
mo.image("path/to/image.png", width=400, height=300)
```

## Interactive Patterns

### Conditional Display

Show different content based on user input:

```python
# Create a toggle
show_details = mo.ui.checkbox(label="Show details", value=False)

# Conditional display
if show_details.value:
    mo.md("""
    ## Detailed Information
    
    This section contains additional information that is only shown
    when the checkbox is checked.
    """)
else:
    mo.md("Check the box to see detailed information.")
```

### Delayed Execution

Control when code executes:

```python
# Create a run button
button = mo.ui.run_button()
button

# Stop execution if button hasn't been clicked
mo.stop(not button.value, mo.md("Click the button above to continue"))

# This code only executes when the button is clicked
import random
random.randint(1, 100)
```

### Interactive Filtering

Filter data based on user input:

```python
# Create filter controls
min_value = mo.ui.slider(0, 100, value=20, label="Minimum Value")
category = mo.ui.dropdown(
    options=["All", "A", "B", "C"],
    value="All",
    label="Category"
)

# Filter DataFrame based on controls
filtered_df = df[df["value"] >= min_value.value]
if category.value != "All":
    filtered_df = filtered_df[filtered_df["category"] == category.value]

# Display filtered data
mo.ui.table(filtered_df)
```

### Lazy Loading

Defer expensive calculations until needed:

```python
def expensive_function():
    # ...expensive computation...
    return result

# Lazy loading in tabs
mo.tabs({
    "Main": mo.md("Main content is immediate"),
    "Expensive": mo.lazy(expensive_function)
})
```

## Custom Components

### Custom UI with anywidget

Create custom interactive widgets:

```python
import anywidget
import traitlets
import marimo as mo

class CounterWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = """
        function render({ model, el }) {
            let getCount = () => model.get("count");
            let button = document.createElement("button");
            button.innerHTML = `count is ${getCount()}`;
            button.addEventListener("click", () => {
                model.set("count", getCount() + 1);
                model.save_changes();
            });
            model.on("change:count", () => {
                button.innerHTML = `count is ${getCount()}`;
            });
            el.appendChild(button);
        }
        export default { render };
    """
    _css = """
        button {
            padding: 5px !important;
            border-radius: 5px !important;
            background-color: #f0f0f0 !important;

            &:hover {
                background-color: lightblue !important;
                color: white !important;
            }
        }
    """

    # Stateful property that can be accessed by JavaScript & Python
    count = traitlets.Int(0).tag(sync=True)

# Use the custom widget in Marimo
widget = mo.ui.anywidget(CounterWidget())
mo.md(f"Counter value: {widget.count}")
```

## Best Practices

1. **Descriptive Labels**: Always include clear labels for UI elements
2. **Meaningful Defaults**: Set sensible default values for inputs
3. **Input Validation**: Validate user inputs to prevent errors
4. **Responsive Layouts**: Use `mo.hstack` and `mo.vstack` with appropriate alignment
5. **Error Handling**: Handle potential errors when processing user inputs
6. **Visual Hierarchy**: Use tabs and accordions to organize complex interfaces
7. **Performance**: Use lazy loading for expensive components
8. **Accessibility**: Provide alternative text and descriptive labels
9. **Feedback**: Provide clear feedback for user actions