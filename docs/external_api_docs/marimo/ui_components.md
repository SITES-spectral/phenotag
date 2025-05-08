# Marimo UI Components

Marimo provides a rich set of UI components that allow you to create interactive interfaces directly within your notebooks. This document covers the various UI components available in Marimo and how to use them effectively.

## Basic Usage

All UI components are available through the `marimo.ui` namespace after importing the library:

```python
import marimo as mo

# Create a UI component
slider = mo.ui.slider(1, 10, value=5, label="Value")

# Display the component
slider

# Access the component's value
slider.value
```

## Input Components

### Slider

Create numeric sliders for selecting values within a range:

```python
# Basic slider
slider = mo.ui.slider(start=1, stop=10, label="Simple Slider")

# Slider with custom step size and initial value
slider = mo.ui.slider(
    start=0, 
    stop=100, 
    step=5, 
    value=50, 
    label="Increment by 5"
)

# Accessing the value
mo.md(f"The selected value is {slider.value}")
```

### Range Slider

Select a range of values:

```python
range_slider = mo.ui.range_slider(
    start=1, 
    stop=10, 
    step=2, 
    value=[2, 6], 
    full_width=True
)
```

### Text Input

Create text input fields:

```python
# Basic text input
text = mo.ui.text(placeholder="Search...", label="Filter")

# Email input
email = mo.ui.text(placeholder="Email", kind="email")

# Password input
password = mo.ui.text(placeholder="Password", kind="password")

# Multiline text area
text_area = mo.ui.text_area(placeholder="Enter notes here...")
```

### Number Input

Create numeric input fields:

```python
number = mo.ui.number(
    start=1, 
    stop=20, 
    label="Number",
    step=0.5
)
```

### Button

Create interactive buttons:

```python
# Simple button
button = mo.ui.button(label="Click me")

# Button with value and on_click handler
counter = mo.ui.button(
    value=0, 
    label="Count",
    on_click=lambda count: count + 1
)

# Toggle button
toggle = mo.ui.button(
    value=False, 
    on_click=lambda value: not value
)
```

### Checkbox

Create checkboxes for boolean selections:

```python
checkbox = mo.ui.checkbox(label="Agree to terms", value=False)
```

### Switch

Create toggle switches:

```python
switch = mo.ui.switch(label="Dark mode")
```

### Radio

Create radio button groups:

```python
radio = mo.ui.radio(
    options=["Apples", "Oranges", "Pears"],
    label="Choose one"
)
```

### Dropdown

Create dropdown menus:

```python
# Dropdown with string options
dropdown = mo.ui.dropdown(
    options=["Apples", "Oranges", "Pears"], 
    label="Choose fruit"
)

# Dropdown with key-value pairs
dropdown_dict = mo.ui.dropdown(
    options={"Apples": 1, "Oranges": 2, "Pears": 3},
    value="Apples",  # initial value
    label="Choose fruit with dict options"
)

# Access values
dropdown.value  # Returns the selected value
dropdown_dict.selected_key  # Returns the key of the selected option
```

### Date and Time

Create date and time pickers:

```python
# Date picker
date = mo.ui.date(label="Start Date")

# Date range picker
date_range = mo.ui.date_range(label="Date Range")

# Date and time picker
datetime = mo.ui.datetime(label="Start Time")
```

### File Input

Create file upload components:

```python
# Button-style file input
file_button = mo.ui.file(kind="button")

# Drag-and-drop area
file_area = mo.ui.file(kind="area")

# Display both styles
mo.vstack([file_button, file_area])
```

### Microphone

Record audio from the user's microphone:

```python
microphone = mo.ui.microphone(label="Record Audio")

# Display microphone and recorded audio
mo.hstack([microphone, mo.audio(microphone.value)])
```

### Refresh

Create refresh controls for periodic updates:

```python
refresh = mo.ui.refresh(
    label="Refresh",
    options=["1s", "5s", "10s", "30s"]
)
```

## Container Components

### Array

Group multiple instances of the same UI element:

```python
# Create a template element
wish = mo.ui.text(placeholder="Wish")

# Create an array of three text inputs
wishes = mo.ui.array([wish] * 3, label="Three wishes")

# Access values as an array
wishes.value
```

### Dictionary

Group different UI elements with named keys:

```python
# Create individual elements
first_name = mo.ui.text(placeholder="First name")
last_name = mo.ui.text(placeholder="Last name")
email = mo.ui.text(placeholder="Email", kind="email")

# Group them in a dictionary
dictionary = mo.ui.dictionary({
    "First name": first_name,
    "Last name": last_name,
    "Email": email,
})

# Access values as a dictionary
dictionary.value
```

### Batch

Embed UI elements within a markdown template:

```python
batch = mo.md("{start} → {end}").batch(
    start=mo.ui.date(label="Start Date"),
    end=mo.ui.date(label="End Date")
)

# Access values as a dictionary
batch.value
```

### Form

Wrap UI elements in a form that requires explicit submission:

```python
form = mo.ui.text_area().form()

# Or with custom submit button
form = mo.ui.text_area().form(submit_button_label="Submit")
```

## Data Components

### Table

Create interactive tables with selection capabilities:

```python
# Create a table from a list of dictionaries
table = mo.ui.table(
    data=[
        {"first_name": "Michael", "last_name": "Scott"},
        {"first_name": "Jim", "last_name": "Halpert"},
        {"first_name": "Pam", "last_name": "Beesly"}
    ],
    pagination=True,
    selection="single"  # or "multi" or "cell" or None
)

# Access selected rows
table.value
```

### Data Explorer

Create an interactive data exploration interface for DataFrames:

```python
import pandas as pd

# Create or load a DataFrame
df = pd.read_csv("data.csv")

# Create a data explorer
mo.ui.data_explorer(df)
```

### Altair Chart

Create interactive Altair visualizations:

```python
import altair as alt
import vega_datasets

# Load data
cars = vega_datasets.data.cars()

# Create an Altair chart
chart = alt.Chart(cars).mark_point().encode(
    x='Horsepower',
    y='Miles_per_Gallon',
    color='Origin',
)

# Make it reactive
mo.ui.altair_chart(chart)
```

## Layout Components

### Horizontal and Vertical Stacks

Arrange UI elements horizontally or vertically:

```python
# Horizontal arrangement
mo.hstack([
    mo.ui.text(label="Name"),
    mo.ui.button(label="Submit")
], justify="start", align="center", gap=0.5)

# Vertical arrangement
mo.vstack([
    mo.md("# Form"),
    mo.ui.text(label="Name"),
    mo.ui.text(label="Email")
], align="stretch", gap=1)
```

Alignment and justification options:
- `justify`: "start", "center", "end", "space-between", "space-around"
- `align`: "start", "center", "end", "stretch"
- `gap`: spacing between elements (in rem)
- `wrap`: boolean to enable wrapping (for hstack)

### Accordion

Create collapsible sections:

```python
mo.accordion({
    "Section 1": mo.md("Content for section 1"),
    "Section 2": mo.ui.text(label="Input in section 2"),
    "Section 3": mo.ui.slider(1, 10)
})
```

### Tabs

Create tabbed interfaces:

```python
mo.tabs({
    "Tab 1": mo.md("Content for tab 1"),
    "Tab 2": mo.ui.text(label="Input in tab 2"),
    "Tab 3": mo.ui.slider(1, 10)
})
```

### Grid

Arrange elements in a grid layout:

```python
mo.grid([
    [mo.md("Top left"), mo.md("Top right")],
    [mo.md("Bottom left"), mo.md("Bottom right")]
])
```

### Tree

Create hierarchical structures:

```python
mo.tree(
    ["entry", "another entry", {"key": [0, mo.ui.slider(1, 10, value=5), 2]}],
    label="A tree of elements."
)
```

## Other Components

### Markdown

Render markdown content:

```python
mo.md("# Heading\nThis is **bold** and this is *italic*.")

# With inline UI elements
slider = mo.ui.slider(1, 10)
mo.md(f"Choose a value: {slider}")
```

### HTML

Render raw HTML content:

```python
mo.Html("<div style='color: red'>Custom HTML</div>")
```

### LaTeX

Render LaTeX equations:

```python
mo.latex(r"\int_0^1 x^2 dx = \frac{1}{3}")
```

### Audio

Play audio content:

```python
mo.audio("path/to/audio.mp3")

# Or from microphone input
mo.audio(microphone.value)
```

### Image

Display images:

```python
mo.image("path/to/image.png")
```

### Plot

Render matplotlib plots:

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 4))
plt.plot(x, y)
plt.title("Sine Wave")
plt.gca()  # Return the current axes to display
```

## Performance Optimization

### Lazy Loading

Defer rendering of expensive UI components:

```python
# Lazy load a UI component
mo.lazy(mo.ui.table(large_dataframe))

# Lazy load with a function
def expensive_component():
    # Expensive computation
    return mo.ui.table(compute_large_data())

mo.lazy(expensive_component)
```

## Custom Components

### Creating Custom Components with anywidget

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

# Wrap the custom widget for use in marimo
widget = mo.ui.anywidget(CounterWidget())
```

## Best Practices

1. **Component Naming**: Give UI components meaningful variable names to enable reactive updates
2. **Stateless Design**: Prefer stateless components where possible to leverage Marimo's reactivity
3. **Composition**: Compose small UI components into larger interfaces using layout components
4. **Event Handlers**: Use `on_change` and `on_click` handlers for responsive interfaces
5. **State Management**: For complex state, use `mo.state()` to create getters and setters
6. **Performance**: Use `mo.lazy()` for expensive components that aren't immediately visible