# Marimo Reactivity

Marimo's reactive programming model is one of its most powerful and distinctive features. This document explains how reactivity works in Marimo and how to use it effectively.

## Understanding Reactivity

Unlike traditional notebooks where cells must be manually executed in sequence, Marimo automatically tracks dependencies between cells and re-executes cells when their dependencies change. This creates a reactive execution flow that ensures outputs are always consistent with inputs.

### Key Concepts

1. **Dependency Tracking**: Marimo automatically detects when one cell references a variable defined in another cell
2. **Automatic Re-execution**: When a cell's dependencies change, Marimo automatically re-executes the cell
3. **Reactive Outputs**: UI components automatically update when their inputs change
4. **Cell Functions**: Each Marimo cell is actually a Python function that takes its dependencies as arguments

## Cell Dependencies

### Implicit Dependencies

When one cell uses a variable defined in another cell, an implicit dependency is created:

```python
# Cell 1
x = 10
```

```python
# Cell 2 - Depends on Cell 1
y = x + 5
```

If you change the value of `x` in Cell 1, Cell 2 will automatically re-execute with the new value.

### Explicit Dependencies

In Marimo, each cell is actually a function that takes its dependencies as arguments:

```python
@app.cell
def _(x):
    y = x + 5
    return (y,)
```

This makes dependencies explicit and enables Marimo to track them.

### Return Values

To make variables available to other cells, you need to return them:

```python
@app.cell
def _():
    x = 10
    return (x,)
```

If a variable isn't returned, it won't be available to other cells.

## Reactive UI

Marimo's UI components are reactive by design. When a UI component's value changes due to user interaction, any cell that depends on that value automatically re-executes.

### Basic Example

```python
# Cell 1
slider = mo.ui.slider(1, 10, value=5)
slider
```

```python
# Cell 2 - Automatically updates when slider changes
result = slider.value * 2
mo.md(f"The result is {result}")
```

### Chaining UI Components

UI components can depend on each other:

```python
# Cell 1
x = mo.ui.slider(1, 10, value=5, label="x")
x
```

```python
# Cell 2 - Depends on Cell 1
y = mo.ui.slider(1, x.value, value=2, label="y cannot exceed x")
y
```

```python
# Cell 3 - Depends on Cell 1 and Cell 2
mo.md(f"x = {x.value}, y = {y.value}, product = {x.value * y.value}")
```

## Creating Reactive Plots

Marimo makes it easy to create reactive visualizations that update in response to user input:

```python
# Cell 1
import matplotlib.pyplot as plt
import numpy as np

# Create a slider and display it
n_points = mo.ui.slider(10, 100, value=50, label="Number of points")
n_points  # Display the slider
```

```python
# Cell 2
# This cell automatically re-executes when n_points.value changes
x = np.random.rand(n_points.value)
y = np.random.rand(n_points.value)

plt.figure(figsize=(8, 6))
plt.scatter(x, y, alpha=0.7)
plt.title(f"Scatter plot with {n_points.value} points")
plt.xlabel("X axis")
plt.ylabel("Y axis")
plt.gca()  # Return the current axes to display the plot
```

## State Management

For more complex state handling, Marimo provides a dedicated state management system.

### Creating State

```python
# Create a counter state with initial value 0
get_counter, set_counter = mo.state(0)
```

This returns:
- `get_counter`: A function that returns the current state value
- `set_counter`: A function that updates the state value

### Using State

```python
# Use the getter to access the current state
current_value = get_counter()

# Use the setter to update the state with a direct value
set_counter(1)

# Use the setter with a function to update based on current value
set_counter(lambda count: count + 1)
```

### State with UI Components

State is often used with UI components to manage their values:

```python
# Create state
get_counter, set_counter = mo.state(0)

# Create UI components that use and update state
increment = mo.ui.button(
    label="increment",
    on_change=lambda _: set_counter(lambda v: v + 1),
)

decrement = mo.ui.button(
    label="decrement",
    on_change=lambda _: set_counter(lambda v: v - 1),
)

# Display UI and current state
mo.hstack([increment, decrement])
mo.md(f"Current count: {get_counter()}")
```

### Linking UI Components with State

You can link state to UI components for bidirectional updates:

```python
# Create state
get_x, set_x = mo.state(5)

# Create slider tied to state
x = mo.ui.slider(
    0, 10, 
    value=get_x(),  # Initialize from state
    on_change=set_x,  # Update state when slider changes
    label="$x$:"
)

# Create another UI element tied to the same state
x_plus_one = mo.ui.number(
    0, 11,
    value=get_x() + 1,
    on_change=lambda v: set_x(v - 1),
    label="$x + 1$:"
)

# Display both UI elements
[x, x_plus_one]
```

## Using Local Variables

For variables that shouldn't be part of the dependency chain, you can use underscore-prefixed names:

```python
# This variable won't be tracked by reactivity
_temp = 42

# This loop variable won't be tracked either
for _i in range(10):
    print(_i)
```

## Task Management with State

You can build complex stateful applications using Marimo's state management:

```python
# Define a Task class
class Task:
    def __init__(self, name, done=False):
        self.name = name
        self.done = done

# Create state for tasks
get_tasks, set_tasks = mo.state([])

# Create UI components
task_entry_box = mo.ui.text(
    placeholder="Enter a task",
    label="New task",
)

add_task_button = mo.ui.button(
    label="Add Task",
    on_click=lambda _: (
        set_tasks(lambda tasks: tasks + [Task(task_entry_box.value)])
        if task_entry_box.value
        else None
    ),
)

clear_tasks_button = mo.ui.button(
    label="Clear Tasks",
    on_click=lambda _: set_tasks([]),
)

# Create task list display
task_list = mo.ui.array(
    [mo.ui.checkbox(value=task.done, label=task.name) for task in get_tasks()],
    label="tasks",
    on_change=lambda v: set_tasks(
        lambda tasks: [Task(task.name, done=v[i]) for i, task in enumerate(tasks)]
    ),
)

# Layout UI components
mo.vstack([
    mo.hstack([task_entry_box, add_task_button, clear_tasks_button], justify="start"),
    task_list,
])
```

## Conditional Execution

### Using mo.stop

You can conditionally stop cell execution with `mo.stop`:

```python
run_button = mo.ui.run_button()
run_button

# Stop execution if the button hasn't been clicked
mo.stop(not run_button.value, mo.md("Click 👆 to run this cell"))
mo.md("You clicked the button! 🎉")
```

The `mo.stop` function takes two arguments:
1. A condition: If `True`, execution stops
2. Optional display content: What to show when execution stops

### Reactive Patterns

You can create different UI flows based on interaction:

```python
# Create a button that counts clicks
button = mo.ui.button(value=0, on_click=lambda count: count + 1)
button

# Display different content based on button state
if button.value == 0:
    mo.md("Click the button to continue")
elif button.value < 3:
    mo.md(f"You've clicked {button.value} times. Keep going!")
else:
    mo.md("You've unlocked the secret content!")
    mo.ui.slider(1, 10, label="Secret slider")
```

## Best Practices

### Data Mutation

Marimo tracks dependencies at the variable level, not the object attribute level. When modifying objects, follow these practices:

#### Bad Pattern (Not Tracked)

```python
# Cell 1
df = pd.DataFrame({"my_column": [1, 2]})
```

```python
# Cell 2 - This modification won't trigger updates
df["another_column"] = [3, 4]
```

#### Good Pattern (All in One Cell)

```python
# Cell 1
df = pd.DataFrame({"my_column": [1, 2]})
df["another_column"] = [3, 4]
```

#### Good Pattern (Create New Object)

```python
# Cell 1
df = pd.DataFrame({"my_column": [1, 2]})
```

```python
# Cell 2 - Create a new object instead of modifying
df_extended = df.copy()
df_extended["another_column"] = [3, 4]
```

### List Mutation

Same principle applies to lists:

#### Bad Pattern (Not Tracked)

```python
# Cell 1
l = [1, 2, 3]
```

```python
# Cell 2 - This won't trigger updates in dependent cells
l.append(4)
```

#### Good Pattern (All in One Cell)

```python
# Cell 1
l = [1, 2, 3]
l.append(4)
```

#### Good Pattern (Create New List)

```python
# Cell 1
l = [1, 2, 3]
```

```python
# Cell 2
new_l = l + [4]
```

## Reactive Functions

You can create reactive functions that automatically update when their inputs change:

```python
def calculate_statistics(data):
    return {
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }

# UI component for data input
data_input = mo.ui.text(
    placeholder="Enter comma-separated numbers",
    value="1,2,3,4,5"
)

# Parse input and calculate statistics
try:
    data = [float(x.strip()) for x in data_input.value.split(",")]
    stats = calculate_statistics(data)
    mo.md(f"""
    ### Statistics
    - Mean: {stats['mean']}
    - Min: {stats['min']}
    - Max: {stats['max']}
    """)
except (ValueError, ZeroDivisionError):
    mo.md("Please enter valid comma-separated numbers")
```

## Debugging Reactivity

### Understanding Execution Order

Marimo executes cells in dependency order, not in the order they appear in the notebook. To understand the execution flow:

1. Use `print()` statements to track when cells execute
2. Look at the "Run" count in the cell header to see how many times a cell has executed
3. Use the "Cell Info" panel to see a cell's dependencies and dependents

### Common Reactivity Issues

1. **Missing Dependencies**: A cell doesn't update because it doesn't properly reference its dependencies
2. **Missing Returns**: Variables aren't available because they weren't returned from a cell
3. **Object Mutation**: Changes to object attributes aren't tracked
4. **Circular Dependencies**: Cells depend on each other in a circular way

### Solving Reactivity Issues

1. **Missing Dependencies**: Ensure you're directly referencing the variables you depend on
2. **Missing Returns**: Return all variables that other cells need with `return (var1, var2, ...)`
3. **Object Mutation**: Perform all related mutations in a single cell, or create new objects
4. **Circular Dependencies**: Restructure your code to break the circular dependency

## Advanced Reactivity

### Lazy Evaluation

For performance reasons, you may want to defer expensive computations:

```python
import time

def expensive_computation():
    time.sleep(2)  # Simulate expensive work
    return "Expensive result"

# Use mo.lazy to defer rendering until needed
accordion = mo.accordion({
    "Expensive Section": mo.lazy(expensive_computation)
})
```

### Periodic Refreshing

For data that needs periodic updates:

```python
# Create a refresh control
refresh = mo.ui.refresh(
    label="Refresh",
    options=["1s", "5s", "10s", "30s"]
)

# This cell re-runs based on the refresh setting
refresh

# Get current timestamp
import datetime
datetime.datetime.now()
```

### Form Submission

For batched updates rather than reactive updates:

```python
# Create a form with a text area
form = mo.ui.text_area(placeholder="Enter text...").form()

# This only updates when the form is submitted, not on every keystroke
mo.md(f"You entered: {form.value}")
```