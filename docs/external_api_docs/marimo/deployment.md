# Marimo Deployment

Marimo notebooks can be run as interactive applications and deployed in various ways. This document covers different deployment options and best practices.

## Running as an Application

### Command Line

The simplest way to run a Marimo notebook as an application is with the `marimo run` command:

```bash
marimo run your_notebook.py
```

This runs the notebook as a web application, hiding the code cells and showing only outputs. Users can interact with UI elements but can't see or modify the code.

### Command Line Options

```bash
# Run with a specific port
marimo run your_notebook.py --port 8080

# Run with a custom title
marimo run your_notebook.py --title "My Application"

# Run in development mode (auto-reload on file changes)
marimo run your_notebook.py --watch
```

## Exporting Notebooks

### Export to HTML with WebAssembly

You can export a notebook as a standalone HTML file with WebAssembly, which can run entirely in the browser:

```bash
marimo export html-wasm your_notebook.py -o output_dir
```

Options:

```bash
# Export in edit mode (allows modifying code)
marimo export html-wasm your_notebook.py -o output_dir --mode edit

# Export in read mode (shows code but doesn't allow editing)
marimo export html-wasm your_notebook.py -o output_dir --mode read

# Export in app mode (hides code)
marimo export html-wasm your_notebook.py -o output_dir --mode app
```

### Export to Static HTML

Export a notebook to a static HTML file (for documentation or sharing):

```bash
marimo export html your_notebook.py -o output.html
```

This creates a non-interactive HTML snapshot of the notebook.

## Multi-Page Applications

Marimo supports multi-page applications through the `mo.routes` API.

### Creating Routes

```python
import marimo as mo

# Create routes
mo.routes.create("/", title="Home")
mo.routes.create("/about", title="About")
mo.routes.create("/dashboard", title="Dashboard")

# Get the current route
current_route = mo.routes.current()
```

### Route-Specific Content

Display different content based on the current route:

```python
# Display content based on current route
if current_route.path == "/":
    mo.md("# Home Page\nWelcome to my application!")
elif current_route.path == "/about":
    mo.md("# About\nThis application was built with Marimo.")
elif current_route.path == "/dashboard":
    mo.md("# Dashboard")
    mo.ui.slider(1, 10, label="Control")
```

### Navigation UI

Create navigation links between routes:

```python
# Create a navigation bar
mo.hstack([
    mo.routes.link("/", "Home"),
    mo.routes.link("/about", "About"),
    mo.routes.link("/dashboard", "Dashboard")
], gap=2)
```

## Embedding in Websites

### iframe Embedding

You can embed Marimo apps in other websites using iframes:

```html
<iframe 
  src="https://yourserver.com/marimo-app" 
  width="100%" 
  height="600px" 
  frameborder="0">
</iframe>
```

### Height Auto-Adjustment

Marimo apps can automatically adjust their height when embedded in iframes:

```python
# In your marimo app
mo.ui.iframe_resize()
```

## Integration with External Services

### Google Cloud Storage

```python
from google.cloud import storage

# Connect to GCS
client = storage.Client()
buckets = client.list_buckets()

# Create a bucket selector UI
selected_bucket = mo.ui.dropdown(
    label="Select bucket", 
    options=[b.name for b in buckets]
)

# Display bucket contents
if selected_bucket.value:
    bucket = client.bucket(selected_bucket.value)
    files = list(bucket.list_blobs())
    items = [
        {
            "Name": f.name,
            "Updated": f.updated.strftime("%h %d, %Y"),
            "Size": f.size,
        }
        for f in files
    ]
    mo.ui.table(items, selection="single")
```

### Database Connections

```python
import sqlite3
import pandas as pd

# Connect to a database
conn = sqlite3.connect("database.db")

# Create a query input
query = mo.ui.text_area(
    placeholder="SELECT * FROM table",
    label="SQL Query"
)

# Execute query button
run_button = mo.ui.button(label="Run Query")

# Display query results
if run_button.value > 0 and query.value:
    try:
        df = pd.read_sql_query(query.value, conn)
        mo.ui.table(df)
    except Exception as e:
        mo.md(f"**Error**: {str(e)}")
```

## Authentication and Security

### Basic Authentication

For basic deployment scenarios, you can use a reverse proxy like Nginx to add authentication:

```nginx
location /marimo-app/ {
    auth_basic "Restricted Content";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8080/;
}
```

### Environment Variables

Use environment variables for sensitive configuration:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access environment variables
api_key = os.environ.get("API_KEY")
```

## Deployment Options

### Docker

You can package Marimo applications in Docker containers for easy deployment:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY your_notebook.py .

EXPOSE 8080

CMD ["marimo", "run", "your_notebook.py", "--port", "8080", "--host", "0.0.0.0"]
```

### Cloud Platforms

Marimo apps can be deployed to various cloud platforms:

#### Heroku

```
# Procfile
web: marimo run your_notebook.py --port $PORT --host 0.0.0.0
```

#### Google Cloud Run

```bash
gcloud run deploy marimo-app \
  --source . \
  --platform managed \
  --allow-unauthenticated
```

## Performance Optimization

### Lazy Loading

Use `mo.lazy` to defer loading expensive components until they're visible:

```python
# Defer expensive computation
expensive_tab = mo.lazy(lambda: compute_expensive_data())

# Use in tabs
mo.tabs({
    "Main": mo.md("Main content"),
    "Expensive": expensive_tab
})
```

### Caching

Cache expensive computations:

```python
import functools

@functools.lru_cache(maxsize=32)
def expensive_computation(param):
    # ... expensive work ...
    return result
```

### Memory Usage

For large datasets, consider pagination or streaming:

```python
# Paginated table
page = mo.ui.number(1, 100, value=1, label="Page")
page_size = mo.ui.dropdown([10, 25, 50, 100], value=25, label="Page Size")

# Get paginated data
start = (page.value - 1) * page_size.value
end = start + page_size.value
paginated_data = all_data[start:end]

# Display paginated data
mo.ui.table(paginated_data)
```

## Best Practices

### Application Structure

1. **Organize Logically**: Group related cells together
2. **Separate Logic and UI**: Keep computation and display code separate
3. **Use Functions**: Encapsulate reusable logic in functions
4. **Add Documentation**: Include markdown cells explaining app usage

### Error Handling

Add robust error handling to improve user experience:

```python
try:
    # Potentially risky operation
    result = perform_operation(input_data)
    mo.md(f"Success! Result: {result}")
except Exception as e:
    mo.md(f"""
    ## Error
    
    An error occurred: **{str(e)}**
    
    Please try again with different inputs.
    """)
```

### Input Validation

Validate user inputs to prevent errors:

```python
# Input validation
number_input = mo.ui.text(label="Enter a number")

try:
    value = float(number_input.value)
    if value < 0:
        mo.md("⚠️ Please enter a positive number")
    else:
        mo.md(f"The square root is {value ** 0.5}")
except ValueError:
    mo.md("⚠️ Please enter a valid number")
```

### Loading States

Indicate when operations are in progress:

```python
# Create a run button
run_button = mo.ui.button(label="Run Analysis")

# Show loading state
if run_button.value > 0:
    # Display loading message
    mo.md("⏳ Running analysis, please wait...")
    
    # Perform actual computation
    result = run_long_analysis()
    
    # Show results
    mo.md(f"✅ Analysis complete! Result: {result}")
```

### Security Considerations

1. **Input Sanitization**: Sanitize user inputs, especially for database queries
2. **Credential Management**: Never hardcode credentials in your notebook
3. **Access Control**: Limit app functionality based on user roles
4. **Data Privacy**: Be careful with sensitive data displayed in UI elements