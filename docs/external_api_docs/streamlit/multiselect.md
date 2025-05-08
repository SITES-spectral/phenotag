# st.multiselect

## Overview

`st.multiselect` displays a multi-select widget in a Streamlit app. It allows users to select multiple options from a list of options.

## Syntax

```python
st.multiselect(
    label,
    options,
    default=None,
    format_func=None,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    disabled=False,
    label_visibility="visible",
    max_selections=None
)
```

## Parameters

- **label** (str):
  - A short label explaining to the user what this select widget is for.

- **options** (list, tuple, numpy.ndarray, pandas.Series, or pandas.DataFrame):
  - List of options to select from.
  - If a pandas.DataFrame is provided, the first column is used.

- **default** (list, tuple, numpy.ndarray, or None):
  - List of default values.
  - Default: None (no options selected)

- **format_func** (callable):
  - Function to format the display of the options.
  - Default: str

- **key** (str or None):
  - An optional string to use as the unique key for the widget.
  - If this is omitted, a key will be generated for the widget based on its content.
  - Multiple widgets with the same key will share the same state.

- **help** (str or None):
  - An optional tooltip that gets displayed next to the multiselect.

- **on_change** (callable or None):
  - An optional callback invoked when this multiselect's value changes.

- **args** (tuple or None):
  - An optional tuple of args to pass to the callback.

- **kwargs** (dict or None):
  - An optional dict of kwargs to pass to the callback.

- **disabled** (bool):
  - An optional boolean, which disables the multiselect if set to True.
  - Default: False

- **label_visibility** (str):
  - The visibility of the label.
  - One of: "visible", "hidden", or "collapsed".
  - Default: "visible"

- **max_selections** (int or None):
  - The maximum number of selections that can be made.
  - Default: None (unlimited selections)

## Returns

- A list containing the selected options.

## Examples

### Basic Multiselect

```python
import streamlit as st

options = ['Apple', 'Banana', 'Orange', 'Mango', 'Grapes']
selected_fruits = st.multiselect('Select fruits:', options)

st.write('You selected:', selected_fruits)
```

### Multiselect with Default Values

```python
import streamlit as st

options = ['Apple', 'Banana', 'Orange', 'Mango', 'Grapes']
default = ['Apple', 'Orange']
selected_fruits = st.multiselect('Select fruits:', options, default=default)

st.write('You selected:', selected_fruits)
```

### Custom Option Formatting

```python
import streamlit as st

# Dictionary of options (value: label)
options_dict = {
    'NY': 'New York',
    'CA': 'California',
    'TX': 'Texas',
    'FL': 'Florida',
    'IL': 'Illinois'
}

# Function to format options
def format_state(state_code):
    return options_dict[state_code]

# Display multiselect with formatted options
selected_states = st.multiselect(
    'Select states:',
    options=list(options_dict.keys()),
    format_func=format_state
)

# Show the selected state codes
st.write('You selected:', selected_states)

# Show the full state names
selected_state_names = [options_dict[code] for code in selected_states]
st.write('Full state names:', selected_state_names)
```

### Multiselect with Callback

```python
import streamlit as st

# Initialize counter in session state if it doesn't exist
if 'selection_count' not in st.session_state:
    st.session_state.selection_count = 0

# Define callback function
def update_counter():
    st.session_state.selection_count += 1

# Options
options = ['Red', 'Green', 'Blue', 'Yellow', 'Purple', 'Orange']

# Multiselect with callback
selected_colors = st.multiselect(
    'Select colors:',
    options=options,
    on_change=update_counter
)

# Display selection and counter
st.write('You selected:', selected_colors)
st.write('Number of selections made:', st.session_state.selection_count)
```

### Multiselect with Maximum Selections

```python
import streamlit as st

options = ['Red', 'Green', 'Blue', 'Yellow', 'Purple', 'Orange']

# Allow a maximum of 3 selections
selected_colors = st.multiselect(
    'Select up to 3 colors:',
    options=options,
    max_selections=3
)

st.write('You selected:', selected_colors)
```

### Using pandas DataFrame as a Data Source

```python
import streamlit as st
import pandas as pd

# Create a sample DataFrame
df = pd.DataFrame({
    'country_code': ['US', 'CA', 'UK', 'AU', 'JP'],
    'country_name': ['United States', 'Canada', 'United Kingdom', 'Australia', 'Japan']
})

# Display the DataFrame
st.write("Available Countries:")
st.dataframe(df)

# Use the DataFrame as the source for multiselect
selected_countries = st.multiselect(
    'Select countries:',
    options=df['country_name'].tolist()
)

st.write('You selected:', selected_countries)
```

### Dynamic Options Based on Other Inputs

```python
import streamlit as st

# Categories and their options
categories = {
    'Fruits': ['Apple', 'Banana', 'Orange', 'Mango', 'Grapes'],
    'Vegetables': ['Carrot', 'Broccoli', 'Tomato', 'Potato', 'Spinach'],
    'Meats': ['Beef', 'Chicken', 'Pork', 'Lamb', 'Turkey']
}

# Select category
category = st.selectbox('Select a category:', list(categories.keys()))

# Multiselect options based on the selected category
selected_items = st.multiselect(
    f'Select {category}:',
    options=categories[category]
)

st.write('You selected:', selected_items)
```

### Handling Empty Selections

```python
import streamlit as st

options = ['Apple', 'Banana', 'Orange', 'Mango', 'Grapes']
selected_fruits = st.multiselect('Select fruits:', options)

if not selected_fruits:
    st.warning('Please select at least one fruit.')
else:
    st.success(f'You selected: {", ".join(selected_fruits)}')
```

### Multiselect for Filtering DataFrames

```python
import streamlit as st
import pandas as pd
import numpy as np

# Create a sample DataFrame
df = pd.DataFrame({
    'Category': np.random.choice(['A', 'B', 'C'], 20),
    'Value': np.random.randn(20),
    'Status': np.random.choice(['Active', 'Inactive', 'Pending'], 20)
})

# Display the original DataFrame
st.write("Original DataFrame:")
st.dataframe(df)

# Multiselect for categories
selected_categories = st.multiselect(
    'Filter by category:',
    options=df['Category'].unique().tolist(),
    default=df['Category'].unique().tolist()  # Initially select all
)

# Multiselect for status
selected_status = st.multiselect(
    'Filter by status:',
    options=df['Status'].unique().tolist(),
    default=df['Status'].unique().tolist()  # Initially select all
)

# Filter the DataFrame based on selections
filtered_df = df[
    df['Category'].isin(selected_categories) &
    df['Status'].isin(selected_status)
]

# Display the filtered DataFrame
st.write("Filtered DataFrame:")
st.dataframe(filtered_df)

# Show the count of rows after filtering
st.write(f"Showing {len(filtered_df)} of {len(df)} rows")
```

## Best Practices

1. **Meaningful Labels**: Use clear, concise labels that explain what the user should select.

2. **Reasonable Options Length**: Avoid overwhelming users with too many options. If you have a long list, consider categorizing or filtering options.

3. **Default Values**: Set sensible default values when applicable to help users understand the expected input.

4. **Use with Session State**: Combine multiselect with session state for more complex interactions:
   ```python
   if 'selected_options' not in st.session_state:
       st.session_state.selected_options = ['Default1', 'Default2']
   
   selected = st.multiselect(
       'Select options:',
       options=['Option1', 'Option2', 'Option3', 'Option4'],
       default=st.session_state.selected_options
   )
   
   # Update session state
   st.session_state.selected_options = selected
   ```

5. **Validation**: Add validation to ensure the user makes appropriate selections:
   ```python
   if len(selected) < min_required:
       st.error(f"Please select at least {min_required} options.")
   ```

6. **Feedback**: Provide immediate feedback based on the user's selections:
   ```python
   if selected:
       st.success(f"You selected {len(selected)} options: {', '.join(selected)}")
   else:
       st.info("No options selected.")
   ```

## Common Issues

1. **Default Value Not Found in Options**: If a default value is not in the list of options, it will be ignored. Make sure default values are valid options.

2. **Type Mismatch**: Ensure that the type of values in options and default lists match (e.g., strings vs. integers).

3. **Performance with Large Option Lists**: Multiselect widgets can become slow with very large option lists. Consider filtering or chunking large datasets.

4. **Order of Operations**: Streamlit executes code from top to bottom, so define any variables used in the multiselect before using the widget.

5. **Session State Updates**: Remember that using widgets with on_change callbacks will trigger a full rerun of the app. Plan your app flow accordingly.