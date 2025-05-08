# Marimo Basics

Marimo is a reactive notebook for Python that combines the best aspects of notebooks, scripts, and applications. This document covers the fundamental concepts and usage patterns of Marimo.

## Installation

Marimo can be installed using pip or conda:

```bash
# Using pip
pip install marimo

# For recommended extras (SQL, AI, plotting)
pip install marimo[recommended]

# Using conda
conda install -c conda-forge marimo
```

## Getting Started

### Running the Tutorial

The quickest way to get started with Marimo is to run the built-in tutorial:

```bash
marimo tutorial intro
```

### Creating and Editing Notebooks

To create a new Marimo notebook or edit an existing one:

```bash
# Start with a blank notebook
marimo edit

# Edit a specific notebook
marimo edit your_notebook.py
```

### Running Notebooks as Applications

You can run a Marimo notebook as a web application, hiding the code and showing only outputs:

```bash
marimo run your_notebook.py
```

## Basic Structure

### Importing Marimo

Start by importing the marimo library, typically aliased as `mo`:

```python
import marimo as mo
```

### Initializing the Application

For a standalone Python file, initialize the Marimo application:

```python
import marimo

app = marimo.App(app_title="My Application")
```

### Defining Cells

In a Marimo Python file, cells are defined using the `@app.cell` decorator:

```python
@app.cell
def _():
    print("Hello, World!")
    return
```

The function name (typically `_`) is just a placeholder. If you need to define dependencies explicitly, you can include them as parameters:

```python
@app.cell
def _(x):
    y = x * 2
    return (y,)
```

### Returning Values

To make variables available to other cells, you need to return them explicitly:

```python
@app.cell
def _():
    x = 10
    y = 20
    return (x, y)  # Make both variables available to other cells
```

### Running the Application

If you're creating a standalone Python file, include this code at the end to run the application:

```python
if __name__ == "__main__":
    app.run()
```

## Markdown and Rich Output

### Rendering Markdown

Use `mo.md` to render markdown content:

```python
mo.md("# Header\n\nThis is **bold** and _italic_ text")
```

You can also include variables using f-strings:

```python
name = "World"
mo.md(f"# Hello, {name}!")
```

### Rendering LaTeX

Use `mo.latex` to render mathematical equations:

```python
mo.latex(r"\int_{a}^{b} f(x) \, dx = F(b) - F(a)")
```

### Rendering HTML

Use `mo.Html` to render raw HTML content:

```python
mo.Html("<div style='color: blue; background-color: #eee; padding: 10px;'>Custom HTML content</div>")
```

### Embedding UI Elements in Markdown

You can embed UI elements directly into markdown content:

```python
slider = mo.ui.slider(1, 10)
mo.md(f"""
# Interactive Demonstration

Select a value: {slider}

The selected value is: **{slider.value}**
""")
```

## Basic UI Components

### Sliders

Create a numeric slider:

```python
slider = mo.ui.slider(start=1, stop=10, value=5, label="Value")
```

### Buttons

Create a simple button:

```python
button = mo.ui.button(label="Click me")
```

Create a run button that triggers cell execution:

```python
run_button = mo.ui.run_button()
```

### Text Input

Create a text input field:

```python
text = mo.ui.text(placeholder="Enter text here", label="Input")
```

### Dropdowns

Create a dropdown with options:

```python
dropdown = mo.ui.dropdown(
    options=["Option 1", "Option 2", "Option 3"],
    value="Option 1",
    label="Select an option"
)
```

## Layouts

### Horizontal Layout

Arrange elements horizontally:

```python
mo.hstack([
    mo.md("Left content"),
    mo.md("Right content")
])
```

### Vertical Layout

Arrange elements vertically:

```python
mo.vstack([
    mo.md("Top content"),
    mo.md("Bottom content")
])
```

### Tabs

Create a tabbed interface:

```python
mo.tabs({
    "Tab 1": mo.md("Content for tab 1"),
    "Tab 2": mo.md("Content for tab 2")
})
```

### Accordion

Create an accordion interface:

```python
mo.accordion({
    "Section 1": mo.md("Content for section 1"),
    "Section 2": mo.md("Content for section 2")
})
```

## Data Handling

### Working with Pandas DataFrames

```python
import pandas as pd

# Create a DataFrame
df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35]
})

# Display the DataFrame (automatic table rendering)
df
```

### Working with Matplotlib

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 4))
plt.plot(x, y)
plt.title("Sine Wave")

# Return the current axes to display the plot
plt.gca()
```

### Working with Altair

```python
import altair as alt
import pandas as pd

data = pd.DataFrame({
    "x": range(10),
    "y": [i**2 for i in range(10)]
})

chart = alt.Chart(data).mark_line().encode(
    x="x",
    y="y"
)

# Make the chart interactive
mo.ui.altair_chart(chart)
```

## Reactive Programming Model

Marimo's reactive programming model automatically updates dependent cells when their dependencies change.

### Basic Reactivity

```python
# Cell 1
x = 10

# Cell 2 - Automatically updates when x changes
y = x * 2
mo.md(f"x = {x}, y = {y}")
```

### Reactive UI Elements

```python
# Cell 1
slider = mo.ui.slider(1, 10, value=5)
slider

# Cell 2 - Automatically updates when slider.value changes
mo.md(f"You selected: {slider.value}")
```

### Object Mutations

Marimo tracks dependencies at the variable level, not the object attribute level. For best results:

1. Perform all related mutations in a single cell
2. Or create new objects instead of modifying existing ones

```python
# GOOD: All modifications in a single cell
df = pd.DataFrame({"A": [1, 2]})
df["B"] = [3, 4]

# GOOD: Create a new object
df2 = df.copy()
df2["C"] = [5, 6]

# BAD: Modify object across cells (not recommended)
# Cell 1: df = pd.DataFrame({"A": [1, 2]})
# Cell 2: df["B"] = [3, 4]  # This won't trigger reactivity properly
```

## Running Code Conditionally

### Using mo.stop

You can conditionally stop cell execution using `mo.stop`:

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

## Controlling Execution Flow

### Interactive Controls

You can use interactive UI elements to control how and when code executes:

```python
# Create a counter button
button = mo.ui.button(value=0, on_click=lambda count: count + 1)
button

# Display different content based on click count
if button.value == 0:
    mo.md("Click the button to start")
elif button.value < 3:
    mo.md(f"You clicked the button {button.value} times. Keep going!")
else:
    mo.md("You've unlocked the content!")
    mo.ui.slider(1, 10)
```

## Best Practices

1. **Return Values**: Always return variables that other cells will use
2. **Object Mutations**: Avoid modifying objects across multiple cells
3. **Code Organization**: Group related functionality into the same cell
4. **UI Naming**: Give UI elements meaningful variable names for reactivity
5. **Documentation**: Use markdown cells to explain your notebook's purpose and usage