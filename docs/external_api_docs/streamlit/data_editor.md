# st.data_editor

## Overview

`st.data_editor` displays a data editor widget in a Streamlit app, allowing viewers to edit, add, and/or delete rows and columns of a DataFrame or data collection.

## Syntax

```python
st.data_editor(
    data,
    width=None,
    height=None,
    use_container_width=False,
    hide_index=None,
    column_order=None,
    column_config=None,
    num_rows="fixed",
    disabled=False,
    key=None,
    on_change=None,
    args=None,
    kwargs=None
)
```

## Parameters

- **data** (pandas.DataFrame, pandas.Series, numpy.ndarray, list, dict, or None):
  - The data to edit.

- **width** (int or None):
  - The width of the data editor in pixels.
  - Default: None (auto)

- **height** (int or None):
  - The height of the data editor in pixels.
  - Default: None (auto)

- **use_container_width** (bool):
  - If True, sets the data editor width to the full width of the container.
  - Default: False

- **hide_index** (bool or None):
  - If True, hides the index column.
  - Default: None (show the index)

- **column_order** (list of str or None):
  - Specifies the order of columns.
  - Default: None (use the order from the data source)

- **column_config** (dict or None):
  - Controls how columns are displayed.
  - Default: None (use the default column display)

- **num_rows** (str or int):
  - Controls the number of rows in the data editor:
    - "fixed": Use the number of rows in the data
    - "dynamic": Allow adding or deleting rows
    - int: Fix the number of rows to a specific value
  - Default: "fixed"

- **disabled** (bool):
  - If True, makes the data editor read-only.
  - Default: False

- **key** (str or None):
  - An optional unique key that identifies this data editor.
  - Default: None

- **on_change** (callable or None):
  - Callback to run when the data editor value changes.
  - Default: None

- **args** (tuple or None):
  - Args to pass to the on_change callback.
  - Default: None

- **kwargs** (dict or None):
  - Kwargs to pass to the on_change callback.
  - Default: None

## Returns

- Data of the same type as the input data, containing the edited values.

## Examples

### Basic Data Editor

```python
import streamlit as st
import pandas as pd

# Create a simple DataFrame
data = pd.DataFrame({
    'Name': ['John', 'Mary', 'Bob'],
    'Age': [30, 25, 40],
    'City': ['New York', 'San Francisco', 'Los Angeles'],
})

# Display a data editor
edited_data = st.data_editor(data)

# Show the edited data
st.write("Edited data:", edited_data)
```

### Dynamic Row Editor

```python
import streamlit as st
import pandas as pd

# Create a DataFrame with some initial data
data = pd.DataFrame({
    'Name': ['John', 'Mary'],
    'Age': [30, 25],
    'City': ['New York', 'San Francisco'],
})

# Display a data editor with dynamic rows
edited_data = st.data_editor(data, num_rows="dynamic")

# Show the edited data
st.write("Edited data:", edited_data)
```

### Custom Column Configuration

```python
import streamlit as st
import pandas as pd

# Create a DataFrame
data = pd.DataFrame({
    'name': ['John', 'Mary', 'Bob'],
    'age': [30, 25, 40],
    'birthday': pd.to_datetime(['1992-01-15', '1997-05-20', '1982-10-10']),
    'salary': [5000, 6000, 7000],
})

# Define column configuration
column_config = {
    "name": st.column_config.TextColumn(
        "Full Name",
        help="The person's name",
        width="medium",
        required=True,
    ),
    "age": st.column_config.NumberColumn(
        "Age (years)",
        help="The person's age",
        min_value=0,
        max_value=120,
        step=1,
        format="%d years",
    ),
    "birthday": st.column_config.DateColumn(
        "Birthday",
        help="The person's birthday",
        min_value=pd.to_datetime("1900-01-01"),
        max_value=pd.to_datetime("2005-01-01"),
        format="YYYY-MM-DD",
    ),
    "salary": st.column_config.NumberColumn(
        "Salary (USD)",
        help="The person's salary in USD",
        min_value=0,
        format="$%d",
    ),
}

# Display a data editor with custom column configuration
edited_data = st.data_editor(
    data,
    column_config=column_config,
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True,
)
```

### Column Types

```python
import streamlit as st
import pandas as pd
import numpy as np

# Create a sample DataFrame with various data types
data = pd.DataFrame({
    'text': ['Sample text', 'Another text'],
    'number': [1234, 5678],
    'boolean': [True, False],
    'date': pd.to_datetime(['2023-01-15', '2023-05-20']),
    'time': pd.to_datetime(['2023-01-01 12:30:00', '2023-01-01 15:45:00']).time,
    'selectbox': ['Option 1', 'Option 2'],
})

# Configure columns
column_config = {
    "text": st.column_config.TextColumn("Text", width="medium"),
    "number": st.column_config.NumberColumn("Number", format="%d"),
    "boolean": st.column_config.CheckboxColumn("Boolean"),
    "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
    "time": st.column_config.TimeColumn("Time", format="hh:mm"),
    "selectbox": st.column_config.SelectboxColumn(
        "Dropdown",
        options=["Option 1", "Option 2", "Option 3"],
        width="medium",
    ),
}

# Display the data editor with configured columns
edited_data = st.data_editor(
    data,
    column_config=column_config,
    use_container_width=True,
)
```

### Custom Column Order

```python
import streamlit as st
import pandas as pd

# Create a DataFrame
data = pd.DataFrame({
    'name': ['John', 'Mary', 'Bob'],
    'age': [30, 25, 40],
    'city': ['New York', 'San Francisco', 'Los Angeles'],
})

# Display a data editor with custom column order
edited_data = st.data_editor(
    data,
    column_order=["age", "name", "city"],  # Specify the column order
    use_container_width=True,
)
```

### On Change Callback

```python
import streamlit as st
import pandas as pd

# Create a DataFrame
data = pd.DataFrame({
    'name': ['John', 'Mary', 'Bob'],
    'age': [30, 25, 40],
})

# Define a callback function
def on_data_change():
    st.session_state.data_changed = True
    st.session_state.change_count += 1

# Initialize session state variables if they don't exist
if 'data_changed' not in st.session_state:
    st.session_state.data_changed = False
if 'change_count' not in st.session_state:
    st.session_state.change_count = 0

# Display a data editor with a callback
edited_data = st.data_editor(
    data,
    key="data_editor",
    on_change=on_data_change,
    use_container_width=True,
)

# Display the state
st.write(f"Data changed: {st.session_state.data_changed}")
st.write(f"Number of changes: {st.session_state.change_count}")
```

## Advanced Features

### Column Config Options

Streamlit provides specialized column types that can be used in the `column_config` parameter:

1. **TextColumn**: For text data.
2. **NumberColumn**: For numeric data with formatting options.
3. **CheckboxColumn**: For boolean data.
4. **SelectboxColumn**: For dropdown selection.
5. **DateColumn**: For date values.
6. **TimeColumn**: For time values.
7. **DatetimeColumn**: For combined date and time values.
8. **ListColumn**: For list data.
9. **LinkColumn**: For URL links.
10. **ImageColumn**: For displaying images.
11. **LineChartColumn**: For embedding small charts in each cell.
12. **BarChartColumn**: For embedding bar charts in each cell.
13. **ProgressColumn**: For displaying progress bars.

Example with multiple column types:

```python
column_config = {
    "name": st.column_config.TextColumn("Name", width="medium"),
    "age": st.column_config.NumberColumn("Age", min_value=0, max_value=120),
    "city": st.column_config.SelectboxColumn(
        "City", 
        options=["New York", "San Francisco", "Los Angeles", "Chicago", "Other"]
    ),
    "employed": st.column_config.CheckboxColumn("Employed"),
    "rating": st.column_config.ProgressColumn(
        "Rating", 
        min_value=0, 
        max_value=5,
        format="%d ⭐"
    ),
    "website": st.column_config.LinkColumn("Website"),
}
```

## Common Issues

1. **Data Not Updating**:
   - Ensure you're capturing the return value of `st.data_editor` which contains the edited data.
   - Use `key` parameter to ensure consistent widget identity across reruns.

2. **Format Errors**:
   - Verify that the format strings match the data type of the column.
   - Check that min/max values are compatible with the data type.

3. **Performance Issues**:
   - Large DataFrames may cause performance issues in the browser.
   - Consider limiting the number of rows/columns or implementing pagination.

4. **Column Width Issues**:
   - Use the `width` parameter in column configuration to adjust column widths.
   - Set `use_container_width=True` to make the editor use the full container width.