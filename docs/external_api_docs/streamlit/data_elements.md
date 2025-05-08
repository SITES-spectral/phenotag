# Streamlit Data Elements

This document provides comprehensive documentation on Streamlit's data display components that allow you to effectively present data in your applications.

## Table of Contents
- [Dataframes](#dataframes)
- [Tables](#tables)
- [Metrics](#metrics)
- [JSON](#json)
- [Charts](#charts)
- [Column Configuration](#column-configuration)

## Dataframes

### st.dataframe

`st.dataframe` displays an interactive table that users can sort, filter, and resize.

```python
st.dataframe(my_data_frame, use_container_width=True)
```

**Parameters:**
- `data`: Data to be displayed (DataFrame, list, dict, numpy array)
- `width`: Width of the frame (int, None, or "medium")
- `height`: Height of the frame (int or None)
- `use_container_width`: If True, sets the dataframe width to the container width (default: False)
- `hide_index`: If True, hides the index column (default: False)
- `column_order`: List of column names in the order to be displayed
- `column_config`: Configuration for column formatting (see [Column Configuration](#column-configuration))

**Examples:**

```python
import pandas as pd
import numpy as np
import streamlit as st

# Create sample data
df = pd.DataFrame({
    'Name': ['John', 'Emily', 'Sarah', 'Mike'],
    'Age': [28, 35, 42, 24],
    'City': ['New York', 'Boston', 'Chicago', 'San Francisco'],
    'Rating': [4.5, 3.8, 4.2, 4.9]
})

# Basic dataframe display
st.dataframe(df)

# Styled dataframe with container width
st.dataframe(df, use_container_width=True)

# Dataframe with specific dimensions
st.dataframe(df, width=600, height=300)

# Hide index column
st.dataframe(df, hide_index=True)

# Column ordering
st.dataframe(df, column_order=['City', 'Name', 'Age', 'Rating'])
```

### st.data_editor

`st.data_editor` creates an interactive, editable dataframe.

```python
edited_df = st.data_editor(df, num_rows="dynamic")
```

**Parameters:**
- All parameters from `st.dataframe`
- `num_rows`: Either "fixed" (default) or "dynamic" (allows adding rows)
- `key`: Unique key to access edited data via session state
- `disabled`: If True, makes the editor read-only (default: False)
- `on_change`: Callback function that's called when the editor changes

**Examples:**

```python
import pandas as pd
import streamlit as st

# Create sample data
df = pd.DataFrame({
    'Name': ['John', 'Emily', 'Sarah'],
    'Department': ['Engineering', 'Marketing', 'Sales']
})

# Basic editable dataframe
edited_df = st.data_editor(df)

# Editable dataframe with ability to add rows
edited_df = st.data_editor(df, num_rows="dynamic")

# Accessing edited data through session state
edited_df = st.data_editor(df, key="employee_data")
st.write("Current data:", st.session_state.employee_data)

# Callback when data changes
def on_data_change():
    st.session_state.has_changed = True

edited_df = st.data_editor(df, on_change=on_data_change)
```

## Tables

### st.table

`st.table` displays a static table. Unlike dataframes, tables cannot be sorted or filtered by the user.

```python
st.table(my_data_frame)
```

**Parameters:**
- `data`: Data to be displayed (DataFrame, list, dict, numpy array)
- `width`: Width of the table (int, None, or "medium")
- `height`: Height of the table (int or None)
- `use_container_width`: If True, sets the table width to the container width

**Examples:**

```python
import pandas as pd
import streamlit as st

# Create sample data
df = pd.DataFrame({
    'Name': ['John', 'Emily', 'Sarah', 'Mike'],
    'Age': [28, 35, 42, 24]
})

# Basic table display
st.table(df)

# Table with container width
st.table(df, use_container_width=True)
```

## Metrics

### st.metric

`st.metric` displays a metric with an optional delta indicator.

```python
st.metric("Temperature", "70 °F", "1.2 °F")
```

**Parameters:**
- `label`: The metric label
- `value`: The metric value (int, float, or string)
- `delta`: The change in the metric (int, float, or string)
- `delta_color`: Color scheme for the delta ("normal", "inverse", or "off")
- `help`: Tooltip shown when hovering over the metric

**Examples:**

```python
import streamlit as st

# Basic metric
st.metric("Revenue", "$12,345", "$1,234")

# Metric with negative delta
st.metric("Users", "1,234", "-5%")

# Metric with delta color scheme
st.metric("Temperature", "28 °C", "-5 °C", delta_color="inverse")

# Metric with help tooltip
st.metric("Accuracy", "85%", "3%", help="Model prediction accuracy")

# Multiple metrics in columns
col1, col2, col3 = st.columns(3)
col1.metric("Temperature", "32 °C", "2 °C")
col2.metric("Humidity", "62%", "-8%")
col3.metric("Wind Speed", "9 km/h", "-2 km/h")
```

## JSON

### st.json

`st.json` displays formatted JSON data.

```python
st.json(my_dict)
```

**Parameters:**
- `data`: JSON data to be displayed (dict, list, str, int, float, bool, None)
- `expanded`: If True, expands all nodes in the JSON tree (default: True)

**Examples:**

```python
import streamlit as st

# Display a simple JSON object
data = {
    "name": "John",
    "age": 30,
    "city": "New York",
    "skills": ["Python", "JavaScript", "SQL"],
    "experience": {
        "company": "Tech Inc.",
        "years": 5
    }
}

st.json(data)

# Display JSON with collapsed nodes
st.json(data, expanded=False)
```

## Charts

Streamlit provides several built-in chart types:

### st.line_chart

```python
st.line_chart(data)
```

### st.area_chart

```python
st.area_chart(data)
```

### st.bar_chart

```python
st.bar_chart(data)
```

### st.scatter_chart

```python
st.scatter_chart(data)
```

### st.map

```python
st.map(data)
```

**Parameters:**
- `data`: Data to be displayed (DataFrame, Series, numpy array)
- `x, y`: Column names to use for the respective axes
- `color`: Column name to use for color
- `size`: Column name to use for point size (scatter chart only)
- `use_container_width`: If True, sets the chart width to the container width (default: True)

**Examples:**

```python
import pandas as pd
import numpy as np
import streamlit as st

# Create sample data
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)

# Line chart
st.line_chart(chart_data)

# Area chart
st.area_chart(chart_data)

# Bar chart
st.bar_chart(chart_data)

# Scatter chart
scatter_data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'size': np.random.rand(100) * 10,
    'category': np.random.choice(['A', 'B', 'C'], 100)
})
st.scatter_chart(
    scatter_data,
    x='x',
    y='y', 
    size='size',
    color='category'
)

# Map chart (requires lat/lon columns)
map_data = pd.DataFrame({
    'lat': [37.7749, 40.7128, 34.0522],
    'lon': [-122.4194, -74.0060, -118.2437],
    'name': ['San Francisco', 'New York', 'Los Angeles']
})
st.map(map_data)
```

## Column Configuration

Streamlit provides extensive options for customizing how columns are displayed in dataframes and data editors.

```python
st.dataframe(
    df,
    column_config={
        "Name": st.column_config.TextColumn("Full Name"),
        "Age": st.column_config.NumberColumn("Age (years)", format="%d"),
        "Rating": st.column_config.ProgressColumn("Rating", min_value=0, max_value=5),
        "Photo": st.column_config.ImageColumn("Profile Photo")
    }
)
```

### Available Column Types:

#### TextColumn
For text data with optional formatting.

```python
st.column_config.TextColumn(
    "Column Label",
    help="Tooltip displayed on hover",
    width="medium",
    required=True
)
```

#### NumberColumn
For numeric data with formatting options.

```python
st.column_config.NumberColumn(
    "Price",
    help="Item price in USD",
    min_value=0,
    max_value=1000,
    step=0.01,
    format="$%.2f"
)
```

#### CheckboxColumn
For boolean values.

```python
st.column_config.CheckboxColumn(
    "Available",
    help="Is item in stock"
)
```

#### SelectboxColumn
For selecting from predefined options.

```python
st.column_config.SelectboxColumn(
    "Status",
    help="Item status",
    options=["Active", "Inactive", "Pending"]
)
```

#### DateColumn and DatetimeColumn
For date and datetime values.

```python
st.column_config.DateColumn(
    "Start Date",
    help="When the item becomes available",
    min_value=date(2023, 1, 1),
    max_value=date(2023, 12, 31),
    format="DD/MM/YYYY"
)

st.column_config.DatetimeColumn(
    "Timestamp",
    help="Event timestamp",
    min_value=datetime(2023, 1, 1),
    max_value=datetime(2023, 12, 31),
    format="DD/MM/YYYY hh:mm:ss"
)
```

#### ImageColumn, LinkColumn, and LineChartColumn
For rich content within cells.

```python
st.column_config.ImageColumn(
    "Product Image",
    help="Product thumbnail"
)

st.column_config.LinkColumn(
    "Website",
    help="Product website"
)

st.column_config.LineChartColumn(
    "Trend",
    help="Sales trend over time",
    width="medium"
)
```

#### ListColumn
For displaying lists of values.

```python
st.column_config.ListColumn(
    "Tags",
    help="Product tags"
)
```

## Best Practices

1. **Container Width**: Use `use_container_width=True` for responsive layouts.
2. **Appropriate Component**: Choose `st.table` for static data and `st.dataframe` for interactive displays.
3. **Column Configuration**: Use column configuration to improve readability and provide context.
4. **Pagination**: For large datasets, consider implementing pagination or filtering.
5. **Performance**: For very large datasets, consider caching data with `st.cache_data`.
6. **Delta Indicators**: Use delta indicators in metrics to highlight changes.
7. **Consistency**: Maintain consistency in formatting across metrics and data displays.

## Related Components

- **[st.image](image.md)**: Display images
- **[st.session_state](session_state.md)**: State management for working with data
- **[Caching](state_caching.md)**: Cache data for performance
- **[Layouts](layout.md)**: Layout components for organizing data displays