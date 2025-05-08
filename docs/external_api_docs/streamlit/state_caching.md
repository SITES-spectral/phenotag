# Streamlit Caching

This document provides comprehensive documentation on Streamlit's caching mechanisms to help improve your application's performance.

## Table of Contents
- [Caching Overview](#caching-overview)
- [st.cache_data](#stcache_data)
- [st.cache_resource](#stcache_resource)
- [Legacy Caching](#legacy-caching)
- [Caching Configuration](#caching-configuration)
- [Advanced Caching Patterns](#advanced-caching-patterns)
- [Best Practices](#best-practices)

## Caching Overview

Streamlit reruns your entire script from top to bottom when users interact with widgets. Caching helps improve performance by storing expensive computations and reusing them when needed, rather than recomputing them.

### Types of Caching

Streamlit provides two main caching decorators:

1. **`st.cache_data`**: For caching data objects like DataFrames, lists, or dictionaries
2. **`st.cache_resource`**: For caching resources like database connections, ML models, or API clients

### When to Use Each Cache Type

- **Use `st.cache_data` for**:
  - Loading or generating data
  - Processing or transforming data
  - Calculations that return data objects
  - Functions that should run again after a time interval

- **Use `st.cache_resource` for**:
  - Database connections
  - ML model initialization
  - API clients or sessions
  - Any resource that should persist throughout the app's lifetime

### Cache Mechanics

For both cache types:
1. Function inputs are hashed to create a unique key
2. If the inputs haven't changed, the cached result is returned
3. If inputs have changed, the function executes and its result is cached

## st.cache_data

`st.cache_data` is designed for caching data objects like DataFrames, arrays, or processed results.

### Basic Usage

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

@st.cache_data
def load_data():
    # Simulate an expensive operation
    time.sleep(2)
    return pd.DataFrame({
        'A': np.random.randn(100),
        'B': np.random.randn(100)
    })

# This runs only once, subsequent calls use the cached result
data = load_data()
st.dataframe(data)
```

### Cache Parameters

`st.cache_data` accepts several parameters to customize caching behavior:

```python
@st.cache_data(
    ttl=60 * 5,            # Time-to-live: 5 minutes
    max_entries=100,       # Maximum cache entries
    show_spinner=True,     # Show a spinner when executing
    persist="disk",        # Persist to disk
)
def fetch_data(query, page):
    # Expensive data operation
    # ...
    return result
```

#### TTL (Time-to-Live)

The `ttl` parameter specifies how long cached values remain valid:

```python
# Cache results for 1 hour
@st.cache_data(ttl=3600)
def fetch_hourly_data():
    # Expensive data operation
    return result

# Alternative format: string duration
@st.cache_data(ttl="1h")
def fetch_hourly_data():
    # Expensive data operation
    return result
```

Supported string formats for `ttl`:
- `"5s"`: 5 seconds
- `"2m"`: 2 minutes
- `"3h"`: 3 hours
- `"4d"`: 4 days
- `"5w"`: 5 weeks

#### Max Entries

The `max_entries` parameter limits the number of cached entries:

```python
# Only keep the most recent 10 results
@st.cache_data(max_entries=10)
def fetch_data(query):
    # Expensive data operation
    return result
```

This uses a Least Recently Used (LRU) eviction policy, removing the oldest accessed entries when the limit is reached.

### Clearing Cache

You can manually clear the cache:

```python
import streamlit as st
import pandas as pd
import time

@st.cache_data
def fetch_data():
    time.sleep(2)  # Simulate an expensive operation
    return pd.DataFrame({'data': [1, 2, 3]})

if st.button("Clear Cache"):
    # Clear the cache for this function
    fetch_data.clear()
    st.success("Cache cleared!")

# Clear all cached functions
if st.button("Clear All Caches"):
    st.cache_data.clear()
    st.success("All caches cleared!")

data = fetch_data()
st.dataframe(data)
```

### Mutability Warnings

`st.cache_data` assumes the cached objects are not modified after they're returned:

```python
import streamlit as st
import pandas as pd

@st.cache_data
def get_data():
    return pd.DataFrame({"A": [1, 2, 3]})

# WRONG: Modifying the cached DataFrame
data = get_data()
data["B"] = [4, 5, 6]  # This will trigger a warning
st.dataframe(data)

# RIGHT: Create a copy before modifying
data = get_data().copy()
data["B"] = [4, 5, 6]  # No warning
st.dataframe(data)

# ALTERNATIVE: Perform the modification inside the cached function
@st.cache_data
def get_data_with_b():
    df = pd.DataFrame({"A": [1, 2, 3]})
    df["B"] = [4, 5, 6]
    return df
```

### Using with Widgets

Streamlit 1.23.0+ added support for using widgets inside cached functions:

```python
import streamlit as st
import pandas as pd

@st.cache_data(experimental_allow_widgets=True)
def filter_data(df):
    # Widget inside a cached function
    column = st.selectbox("Select column", df.columns)
    min_value = st.slider("Minimum value", float(df[column].min()), float(df[column].max()))
    
    # Filter based on widget values
    filtered_df = df[df[column] >= min_value]
    return filtered_df

# Load data
data = pd.DataFrame({
    "A": [1, 2, 3, 4, 5],
    "B": [10, 20, 30, 40, 50],
    "C": [100, 200, 300, 400, 500]
})

# This function will cache its result per unique combination of widget values
filtered_data = filter_data(data)
st.dataframe(filtered_data)
```

## st.cache_resource

`st.cache_resource` is designed for caching resource objects like database connections, ML models, or API clients that should persist throughout the app's lifetime.

### Basic Usage

```python
import streamlit as st
import pandas as pd
import sqlite3
import time

@st.cache_resource
def init_database():
    # Simulate creating a database
    time.sleep(2)
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create a table
    cursor.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER, value TEXT)")
    
    # Insert some data
    for i in range(5):
        cursor.execute("INSERT INTO data VALUES (?, ?)", (i, f"Value {i}"))
    
    conn.commit()
    return conn

# This runs only once, subsequent calls use the cached connection
conn = init_database()

# Use the connection
query = st.text_input("Enter SQL query", "SELECT * FROM data")
try:
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)
except Exception as e:
    st.error(f"Error executing query: {e}")
```

### Caching Machine Learning Models

One common use case for `st.cache_resource` is caching ML models:

```python
import streamlit as st
import numpy as np
import time
from sklearn.ensemble import RandomForestRegressor

@st.cache_resource
def load_model():
    # Simulate loading a model
    time.sleep(3)
    model = RandomForestRegressor(n_estimators=100)
    # Train the model on some data
    X = np.random.rand(100, 4)
    y = np.random.rand(100)
    model.fit(X, y)
    return model

# Load the model (only once)
model = load_model()

# Create input features for prediction
st.subheader("Make predictions")
col1, col2, col3, col4 = st.columns(4)
with col1:
    feature1 = st.slider("Feature 1", 0.0, 1.0, 0.5)
with col2:
    feature2 = st.slider("Feature 2", 0.0, 1.0, 0.5)
with col3:
    feature3 = st.slider("Feature 3", 0.0, 1.0, 0.5)
with col4:
    feature4 = st.slider("Feature 4", 0.0, 1.0, 0.5)

# Make a prediction
features = np.array([[feature1, feature2, feature3, feature4]])
prediction = model.predict(features)[0]
st.metric("Prediction", f"{prediction:.4f}")
```

### Using with Widgets

Similar to `st.cache_data`, you can use widgets inside functions decorated with `st.cache_resource`:

```python
import streamlit as st
import pandas as pd
import sqlite3

@st.cache_resource(experimental_allow_widgets=True)
def get_database_connection():
    # Widget inside a cached function
    use_in_memory = st.checkbox("Use in-memory database", True)
    
    if use_in_memory:
        conn = sqlite3.connect(":memory:")
    else:
        conn = sqlite3.connect("app.db")
    
    # Initialize database
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER, value TEXT)")
    conn.commit()
    
    return conn

# Get connection based on checkbox value
conn = get_database_connection()

# Use the connection
if st.button("Add random data"):
    import random
    cursor = conn.cursor()
    random_id = random.randint(1, 1000)
    random_value = f"Value {random_id}"
    cursor.execute("INSERT INTO data VALUES (?, ?)", (random_id, random_value))
    conn.commit()
    st.success(f"Added: {random_id}, {random_value}")

# Display data
df = pd.read_sql_query("SELECT * FROM data", conn)
st.dataframe(df)
```

### Cache Parameters

`st.cache_resource` accepts fewer parameters than `st.cache_data`:

```python
@st.cache_resource(
    show_spinner=True,      # Show a spinner when executing
    experimental_allow_widgets=False  # Allow widgets in the function
)
def init_resource():
    # Initialize resource
    return resource
```

Unlike `st.cache_data`, `st.cache_resource` does not support `ttl` or `max_entries` parameters because resources are meant to persist throughout the app's lifetime.

### Clearing Cache

Clearing the resource cache works the same way as with `st.cache_data`:

```python
import streamlit as st
import time

@st.cache_resource
def init_resource():
    time.sleep(2)  # Simulate initialization
    return {"initialized_at": time.time()}

if st.button("Clear Resource Cache"):
    # Clear cache for this function
    init_resource.clear()
    st.success("Resource cache cleared!")

if st.button("Clear All Resource Caches"):
    # Clear all resource caches
    st.cache_resource.clear()
    st.success("All resource caches cleared!")

resource = init_resource()
st.write(f"Resource initialized at: {resource['initialized_at']}")
```

## Legacy Caching

Before Streamlit 1.10.0, the primary caching mechanism was `st.cache`. This has been deprecated in favor of `st.cache_data` and `st.cache_resource`.

### Migrating from st.cache

If you're using the legacy `st.cache` decorator, you should migrate to the new caching system:

```python
# Old way (deprecated)
@st.cache
def fetch_data():
    # ...
    return data

# New way (use cache_data for data objects)
@st.cache_data
def fetch_data():
    # ...
    return data

# New way (use cache_resource for resources)
@st.cache_resource
def init_model():
    # ...
    return model
```

### Keeping Legacy Code Working

If you can't update your code immediately, you can suppress warnings:

```python
# Suppress deprecation warning
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Use legacy caching
@st.cache
def legacy_function():
    # ...
    return result
```

## Caching Configuration

### Hashing Behavior

By default, Streamlit hashes the inputs to your function to determine if the cached value should be used. You can customize this behavior:

```python
import streamlit as st
import pandas as pd
from datetime import datetime

class CustomObject:
    def __init__(self, value):
        self.value = value
        self.created_at = datetime.now()

# Specify which attributes to hash
@st.cache_data(hash_funcs={CustomObject: lambda obj: obj.value})
def process_object(obj):
    return f"Processed value: {obj.value}, created at {obj.created_at}"

obj = CustomObject(st.slider("Select a value", 1, 10))
result = process_object(obj)
st.write(result)
```

### Handling Unhashable Objects

Sometimes your function arguments might include unhashable objects. You can define custom hashing functions:

```python
import streamlit as st
import numpy as np
import pandas as pd

# Custom hash function for DataFrames
@st.cache_data(hash_funcs={pd.DataFrame: lambda df: hash(df.to_string())})
def process_dataframe(df):
    return df.describe()

# Create a dataframe
data = pd.DataFrame(np.random.randn(100, 3), columns=["A", "B", "C"])

# Process the dataframe (cached based on content)
stats = process_dataframe(data)
st.dataframe(stats)
```

### Persistent Cache

You can persist cache to disk to maintain it between app restarts:

```python
import streamlit as st
import pandas as pd
import time

@st.cache_data(persist="disk")
def load_large_dataset():
    # Simulate loading a large dataset
    time.sleep(3)
    return pd.DataFrame({"data": range(10000)})

data = load_large_dataset()
st.success("Dataset loaded!")
st.dataframe(data.head())
```

### Multi-Process Caching

When running Streamlit in multi-process mode, caching behavior works across processes:

```python
# Set in .streamlit/config.toml
[server]
processesPerApp = 2
```

```python
import streamlit as st
import time

@st.cache_data
def expensive_computation(n):
    time.sleep(2)
    return n * 2

# This cache is shared across processes
result = expensive_computation(st.slider("Value", 1, 10))
st.write(f"Result: {result}")
```

## Advanced Caching Patterns

### Function Composition

Combine multiple cached functions for complex operations:

```python
import streamlit as st
import pandas as pd
import time

@st.cache_data
def fetch_raw_data():
    # Simulate API call
    time.sleep(2)
    return pd.DataFrame({
        "id": range(1000),
        "value": range(1000)
    })

@st.cache_data
def process_data(data, filter_value):
    # Filter and process data
    return data[data["value"] > filter_value]

# Composition of cached functions
raw_data = fetch_raw_data()
filter_value = st.slider("Minimum value", 0, 1000, 500)
filtered_data = process_data(raw_data, filter_value)
st.dataframe(filtered_data)
```

### Dynamic TTL

Implement dynamic TTL based on input parameters:

```python
import streamlit as st
import pandas as pd
import time
from datetime import datetime

def get_data_with_dynamic_ttl(freshness):
    # Convert freshness to appropriate TTL
    if freshness == "High (1 minute)":
        ttl = 60
    elif freshness == "Medium (1 hour)":
        ttl = 3600
    else:  # "Low (1 day)"
        ttl = 86400
    
    # Define a new cached function with the specified TTL
    @st.cache_data(ttl=ttl)
    def fetch_data(_freshness):
        # The _freshness parameter ensures different cache entries per freshness
        current_time = datetime.now().strftime("%H:%M:%S")
        time.sleep(1)  # Simulate data fetch
        return pd.DataFrame({
            "timestamp": [current_time],
            "value": [time.time()],
            "ttl": [ttl]
        })
    
    return fetch_data(freshness)

# Let user select data freshness
freshness = st.radio(
    "Select data freshness",
    ["High (1 minute)", "Medium (1 hour)", "Low (1 day)"]
)

# Fetch data with appropriate TTL
data = get_data_with_dynamic_ttl(freshness)
st.dataframe(data)
```

### Cached Property Pattern

Implement a property-like pattern using caching:

```python
import streamlit as st
import pandas as pd
import numpy as np

class DataAnalyzer:
    def __init__(self, data):
        self.data = data
    
    @property
    def summary(self):
        # Use a cached function to compute the summary
        return self._get_summary(self.data)
    
    @staticmethod
    @st.cache_data
    def _get_summary(data):
        return {
            "mean": data.mean().to_dict(),
            "median": data.median().to_dict(),
            "std": data.std().to_dict(),
            "count": len(data)
        }
    
    @property
    def correlation_matrix(self):
        return self._get_correlation(self.data)
    
    @staticmethod
    @st.cache_data
    def _get_correlation(data):
        return data.corr()

# Create some data
data = pd.DataFrame(np.random.randn(1000, 4), columns=["A", "B", "C", "D"])

# Create analyzer and access cached properties
analyzer = DataAnalyzer(data)
st.subheader("Data Summary")
st.json(analyzer.summary)

st.subheader("Correlation Matrix")
st.dataframe(analyzer.correlation_matrix)
```

### Parameterized Caching

Create factories for parametrized cached functions:

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

def create_cached_loader(dataset_name):
    """Factory function that creates a cached data loader for a specific dataset."""
    
    @st.cache_data
    def load_dataset():
        # Simulate loading data
        time.sleep(2)
        
        if dataset_name == "sales":
            return pd.DataFrame(np.random.randn(100, 3), columns=["Revenue", "Costs", "Profit"])
        elif dataset_name == "users":
            return pd.DataFrame({
                "User ID": range(1, 101),
                "Name": [f"User {i}" for i in range(1, 101)],
                "Active": np.random.choice([True, False], 100)
            })
        else:
            return pd.DataFrame({"Error": ["Unknown dataset"]})
    
    return load_dataset

# Let user select a dataset
dataset = st.selectbox("Select a dataset", ["sales", "users"])

# Create a loader for the selected dataset
loader = create_cached_loader(dataset)

# Load the dataset
data = loader()
st.dataframe(data)
```

## Best Practices

### 1. Choose the Right Cache Type

Choose the appropriate cache type for your use case:

```python
import streamlit as st
import pandas as pd
import requests
import sqlite3

# Use cache_data for data objects
@st.cache_data
def fetch_data(url):
    response = requests.get(url)
    return pd.DataFrame(response.json())

# Use cache_resource for resources
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("app.db")
    # Set up the database
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER, value TEXT)")
    conn.commit()
    return conn
```

### 2. Include All Dependencies

Ensure all dependencies are passed as function arguments:

```python
import streamlit as st
import pandas as pd
import numpy as np

# BAD: Using global variables or imports inside the function
global_var = 42

@st.cache_data
def bad_function():
    import some_module  # BAD: Import inside function
    return some_module.process(global_var)  # BAD: Using global variable

# GOOD: Pass all dependencies as arguments
@st.cache_data
def good_function(value):
    return pd.DataFrame({"value": [value] * 10})

# Usage
result = good_function(st.slider("Value", 1, 100))
st.dataframe(result)
```

### 3. Handle Side Effects

Be careful with functions that have side effects:

```python
import streamlit as st
import pandas as pd
import os

# BAD: Function with side effects
@st.cache_data
def bad_save_data(data, filename):
    # Side effect: writes to disk
    data.to_csv(filename)
    return "Data saved"

# GOOD: Separate side effects from cached functions
@st.cache_data
def process_data(data):
    # Pure function, no side effects
    return data.describe()

def save_data(data, filename):
    # Function with side effect, not cached
    data.to_csv(filename)
    return "Data saved"

# Usage
data = pd.DataFrame({"A": range(10)})
stats = process_data(data)
st.dataframe(stats)

if st.button("Save Data"):
    result = save_data(data, "data.csv")
    st.success(result)
```

### 4. Cache Invalidation Strategies

Implement cache invalidation when needed:

```python
import streamlit as st
import pandas as pd
import time
from datetime import datetime

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_data():
    time.sleep(2)  # Simulate data fetch
    return pd.DataFrame({
        "timestamp": [datetime.now().strftime("%H:%M:%S")],
        "value": [time.time()]
    })

# Display cached data
data = fetch_data()
st.dataframe(data)

# Add manual refresh option
if st.button("Refresh Data"):
    # Clear this function's cache
    fetch_data.clear()
    st.rerun()

# Display cache age
cache_time = datetime.strptime(data["timestamp"][0], "%H:%M:%S").time()
current_time = datetime.now().time()
st.write(f"Data timestamp: {cache_time}")
st.write(f"Current time: {current_time}")
```

### 5. Monitor Cache Size

Keep an eye on memory usage, especially for large datasets:

```python
import streamlit as st
import pandas as pd
import numpy as np
import sys
import gc

# Function to estimate object size
def get_size(obj):
    return sys.getsizeof(obj)

# Cache large dataset with size monitoring
@st.cache_data
def generate_large_dataset(rows, cols):
    st.write(f"Generating dataset of size {rows}x{cols}...")
    data = pd.DataFrame(np.random.randn(rows, cols))
    size_mb = get_size(data) / (1024 * 1024)
    st.write(f"Dataset size: {size_mb:.2f} MB")
    return data

# UI controls
rows = st.slider("Number of rows", 1000, 100000, 10000, step=1000)
cols = st.slider("Number of columns", 1, 100, 10)

# Generate and display data
data = generate_large_dataset(rows, cols)
st.dataframe(data.head())

# Add a button to clear cache and free memory
if st.button("Clear Cache"):
    generate_large_dataset.clear()
    gc.collect()  # Force garbage collection
    st.success("Cache cleared and memory freed")
```

### 6. Function Granularity

Use appropriately sized functions for caching:

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

# BAD: Monolithic function that does too much
@st.cache_data
def bad_process_everything(data, filter_col, filter_value, group_by):
    # Everything in one function
    filtered_data = data[data[filter_col] > filter_value]
    result = filtered_data.groupby(group_by).agg(["mean", "sum"])
    # ...more processing
    return result

# GOOD: Separate functions with appropriate granularity
@st.cache_data
def load_data():
    time.sleep(2)  # Simulate loading
    return pd.DataFrame({
        "A": np.random.randn(1000),
        "B": np.random.randn(1000),
        "C": np.random.choice(["X", "Y", "Z"], 1000)
    })

@st.cache_data
def filter_data(data, column, value):
    return data[data[column] > value]

@st.cache_data
def aggregate_data(data, group_by):
    return data.groupby(group_by).agg(["mean", "sum"])

# Usage
data = load_data()
column = st.selectbox("Filter column", ["A", "B"])
value = st.slider("Minimum value", -3.0, 3.0, 0.0, 0.1)
filtered = filter_data(data, column, value)
st.write(f"Filtered data shape: {filtered.shape}")

group = st.selectbox("Group by", ["C"])
if group:
    aggregated = aggregate_data(filtered, group)
    st.dataframe(aggregated)
```

### 7. Use Cache for Expensive Operations

Focus on caching expensive operations:

```python
import streamlit as st
import pandas as pd
import numpy as np
import time

# Cache expensive operations
@st.cache_data
def load_large_dataset():
    time.sleep(2)  # Simulate expensive loading
    return pd.DataFrame(np.random.randn(10000, 10))

# Don't cache inexpensive operations
def simple_calculation(a, b):
    return a + b

# Load data once
data = load_large_dataset()

# UI controls
a = st.slider("a", 1, 10)
b = st.slider("b", 1, 10)

# Non-cached simple operation
result = simple_calculation(a, b)
st.write(f"a + b = {result}")

# Show a sample of the cached data
st.dataframe(data.sample(10))
```

### 8. Implement Versioning

Add versioning to cached functions to handle code changes:

```python
import streamlit as st
import pandas as pd
import time

# Version your cached functions
@st.cache_data(show_spinner=False)
def process_data_v1(data):
    time.sleep(1)
    return data.describe()

# New version with additional functionality
@st.cache_data(show_spinner=False)
def process_data_v2(data):
    time.sleep(1)
    result = data.describe()
    result.loc["range"] = result.loc["max"] - result.loc["min"]
    return result

# Create sample data
data = pd.DataFrame({
    "A": range(100),
    "B": range(0, 200, 2)
})

# Let user choose the version
version = st.radio("Select version", ["v1", "v2"])

# Use the appropriate function based on version
if version == "v1":
    stats = process_data_v1(data)
else:
    stats = process_data_v2(data)

st.dataframe(stats)
```

## Related Components

- **[Session State](state_management.md)**: State management in Streamlit
- **[Execution Flow](execution_flow.md)**: How Streamlit scripts execute
- **[Connections](connections_config.md)**: Connecting to external data sources