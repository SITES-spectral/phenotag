# Streamlit Connections and Configuration

This document provides comprehensive documentation on Streamlit's connections API and configuration options that allow you to easily connect to data sources and customize application behavior.

## Table of Contents
- [Connections API](#connections-api)
- [SQL Connections](#sql-connections)
- [Custom Connections](#custom-connections)
- [Configuration Options](#configuration-options)
- [Secrets Management](#secrets-management)
- [Best Practices](#best-practices)

## Connections API

Streamlit's Connections API provides a standardized way to connect to data sources with built-in caching, retries, and connection pooling.

### Basic Usage

The `st.connection` function creates and manages connections to external data sources:

```python
import streamlit as st

# Create a connection to a SQL database
conn = st.connection("my_database", type="sql")

# Query the database
df = conn.query("SELECT * FROM users LIMIT 10")
st.dataframe(df)
```

### Connection Types

Streamlit provides several built-in connection types:

- **SQL**: For connecting to SQL databases
- **Snowflake**: For connecting to Snowflake
- **Snowpark**: For using Snowpark with Snowflake

You can also create [custom connections](#custom-connections) for other data sources.

### Connection Configuration

Connections are typically configured through the `secrets.toml` file:

```toml
# .streamlit/secrets.toml

[connections.my_database]
type = "sql"
dialect = "mysql"
host = "localhost"
port = 3306
database = "mydatabase"
username = "user"
password = "password"
```

### Connection Caching

The Connections API includes built-in caching:

```python
# Query with caching (cached for 10 minutes)
df = conn.query("SELECT * FROM users", ttl="10m")

# Use different TTL formats
df = conn.query("SELECT * FROM users", ttl=600)  # 600 seconds
df = conn.query("SELECT * FROM users", ttl="1h")  # 1 hour
df = conn.query("SELECT * FROM users", ttl="1d")  # 1 day
```

## SQL Connections

### Connecting to SQL Databases

SQL connections can connect to various database types:

```python
import streamlit as st
import pandas as pd

# Create a SQL connection
conn = st.connection("my_db", type="sql")

# Query data
df = conn.query("SELECT * FROM users")
st.dataframe(df)

# Parameterized queries
user_id = st.number_input("User ID", min_value=1)
user = conn.query(
    "SELECT * FROM users WHERE id = :id",
    params={"id": user_id}
)
st.write(user)

# Query with computed DataFrame value
computed_values = pd.DataFrame({"value": [1, 2, 3]})
result = conn.query(
    "SELECT * FROM my_table WHERE value IN :values",
    params={"values": tuple(computed_values["value"])}
)
```

### SQL Connection Configuration

SQL connections support various dialects and configuration options:

```toml
# MySQL connection
[connections.mysql_db]
type = "sql"
dialect = "mysql"
host = "localhost"
port = 3306
database = "mydatabase"
username = "user"
password = "password"
query = { charset = "utf8mb4" }

# PostgreSQL connection
[connections.postgres_db]
type = "sql"
dialect = "postgresql"
host = "localhost"
port = 5432
database = "mydatabase"
username = "user"
password = "password"
connect_args = { sslmode = "require" }

# SQLite connection
[connections.sqlite_db]
type = "sql"
url = "sqlite:///path/to/database.db"

# Connection string format
[connections.db_from_url]
type = "sql"
url = "postgresql://user:password@localhost:5432/mydatabase"
```

### Advanced SQL Operations

Beyond basic queries, SQL connections support transactions and other operations:

```python
import streamlit as st

conn = st.connection("my_db", type="sql")

# Using a session for transactions
with conn.session as s:
    # Multiple statements in a transaction
    s.execute("INSERT INTO users (name) VALUES (:name)", params={"name": "Alice"})
    s.execute("UPDATE user_counts SET count = count + 1")
    s.commit()  # Explicitly commit the transaction

# Error handling
try:
    with conn.session as s:
        s.execute("INSERT INTO users (name) VALUES (:name)", params={"name": "Bob"})
        s.execute("INVALID SQL STATEMENT")  # This will fail
        s.commit()
except Exception as e:
    st.error(f"Transaction failed: {e}")
    # The transaction is automatically rolled back on exception
```

## Custom Connections

### Creating a Custom Connection

You can create custom connections by extending the `BaseConnection` class:

```python
import streamlit as st
from streamlit.connections import BaseConnection
import pandas as pd
import redis

class RedisConnection(BaseConnection[redis.Redis]):
    """Connection to a Redis database."""
    
    def _connect(self, **kwargs) -> redis.Redis:
        """Connect to Redis using connection parameters from secrets."""
        # Get connection parameters from secrets
        params = self._secrets.to_dict()
        
        # Override with any kwargs
        params.update(kwargs)
        
        # Connect to Redis
        return redis.Redis(**params)
    
    def get(self, key: str) -> str:
        """Get a value from Redis."""
        return self._instance.get(key)
    
    def set(self, key: str, value: str) -> bool:
        """Set a value in Redis."""
        return self._instance.set(key, value)
    
    def query(self, pattern: str) -> pd.DataFrame:
        """Query keys matching a pattern and return as a DataFrame."""
        keys = self._instance.keys(pattern)
        data = {}
        
        for key in keys:
            key_str = key.decode('utf-8')
            value = self._instance.get(key)
            data[key_str] = value.decode('utf-8') if value else None
        
        return pd.DataFrame(list(data.items()), columns=['key', 'value'])

# Use the custom connection
@st.cache_resource
def get_redis_connection():
    return RedisConnection("redis")

conn = get_redis_connection()

# Set a value
if st.button("Set Value"):
    conn.set("example_key", "example_value")
    st.success("Value set!")

# Get a value
if st.button("Get Value"):
    value = conn.get("example_key")
    st.write(f"Value: {value}")

# Query values
df = conn.query("example_*")
st.dataframe(df)
```

### Connection Secrets for Custom Connections

Configure custom connections in your `secrets.toml` file:

```toml
[connections.redis]
host = "localhost"
port = 6379
db = 0
password = "your_password"  # Optional
```

### Connection Cache and TTL

Implement caching in your custom connection:

```python
import streamlit as st
from streamlit.connections import BaseConnection
import pandas as pd
import requests
from datetime import timedelta

class APIConnection(BaseConnection[requests.Session]):
    """Connection to a REST API."""
    
    def _connect(self, **kwargs) -> requests.Session:
        """Create a session for API calls."""
        session = requests.Session()
        
        # Configure the session with auth if provided
        if "api_key" in self._secrets:
            session.headers.update({"Authorization": f"Bearer {self._secrets['api_key']}"})
        
        return session
    
    def get(self, endpoint: str, params: dict = None, ttl: str = None) -> dict:
        """Get data from the API with caching."""
        # Determine cache key based on endpoint and params
        @st.cache_data(ttl=ttl)
        def _get(url, params):
            response = self._instance.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        base_url = self._secrets.get("base_url", "")
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        return _get(url, params)
    
    def query(self, endpoint: str, params: dict = None, ttl: str = None) -> pd.DataFrame:
        """Query the API and return data as a DataFrame."""
        data = self.get(endpoint, params, ttl)
        
        # Handle different response formats
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and "results" in data:
            return pd.DataFrame(data["results"])
        elif isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame([data])

# Use the custom API connection
conn = st.connection("pokeapi", type=APIConnection)

# Query with caching
pokemon = st.text_input("Enter a Pokémon name", "pikachu")
if pokemon:
    try:
        data = conn.get(f"pokemon/{pokemon.lower()}", ttl="1h")
        st.write(f"Name: {data['name'].title()}")
        st.write(f"Height: {data['height']} dm")
        st.write(f"Weight: {data['weight']} hg")
        st.write("Abilities:")
        for ability in data['abilities']:
            st.write(f"- {ability['ability']['name'].replace('-', ' ').title()}")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
```

## Configuration Options

Streamlit offers numerous configuration options to customize the behavior and appearance of your application.

### Configuration Methods

There are three ways to configure Streamlit, in order of precedence:

1. **Command-line arguments**: Highest precedence
2. **Environment variables**: Medium precedence
3. **Configuration file**: Lowest precedence

### Command-Line Arguments

```bash
# Run with custom theme and server port
streamlit run app.py --theme.primaryColor="#f63366" --server.port=8080

# Run with custom page title and icon
streamlit run app.py --browser.serverAddress="localhost" --browser.serverPort=8501
```

### Environment Variables

```bash
# Set environment variables
export STREAMLIT_THEME_PRIMARY_COLOR="#f63366"
export STREAMLIT_SERVER_PORT=8080

# Run the app (will use the environment variables)
streamlit run app.py
```

### Configuration File

The most common way to configure Streamlit is through the `.streamlit/config.toml` file:

```toml
# .streamlit/config.toml

[theme]
primaryColor = "#f63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8080
headless = true
enableCORS = false

[browser]
serverAddress = "localhost"
serverPort = 8080
gatherUsageStats = false
```

### Viewing Current Configuration

To see all available configuration options and their current values:

```bash
streamlit config show
```

### Common Configuration Options

#### Theme Configuration

```toml
[theme]
# Primary accent color for interactive elements
primaryColor = "#f63366"

# Background color for the main content area
backgroundColor = "#FFFFFF"

# Background color for sidebar and most interactive widgets
secondaryBackgroundColor = "#F0F2F6"

# Color used for almost all text
textColor = "#262730"

# Font family for all text in the app, except code blocks
# Accepted values: "sans serif", "serif", "monospace"
font = "sans serif"
```

#### Server Configuration

```toml
[server]
# Port where the server will listen for client and browser connections
port = 8501

# Address where the server will listen for client and browser connections
address = "localhost"

# If true, will attempt to open the browser to the app
headless = false

# Max size, in megabytes, for files uploaded with the file_uploader
maxUploadSize = 200

# Enables support for Cross-Origin Resource Sharing (CORS)
enableCORS = true

# Enables support for websocket compression
enableWebsocketCompression = true
```

#### Browser Configuration

```toml
[browser]
# Internet address where users should point their browsers
serverAddress = "localhost"

# Port where users should point their browsers
serverPort = 8501

# Whether to send usage statistics to Streamlit
gatherUsageStats = true
```

#### Runner Configuration

```toml
[runner]
# Allows you to type command-line options directly in the app
magicEnabled = true

# Makes values returned by st.metrics always serializable
enforceSerializableSessionState = false
```

#### Logger Configuration

```toml
[logger]
# Level of logging: 'error', 'warning', 'info', or 'debug'
level = "info"

# String format for logging messages
messageFormat = "%(asctime)s %(levelname)s %(threadName)s %(message)s"
```

### Application-Level Configuration

Beyond the `.streamlit/config.toml` file, you can also configure certain aspects of your app from within your Python code using `st.set_page_config()`:

```python
import streamlit as st

# Must be the first Streamlit command used in your app
st.set_page_config(
    page_title="My Streamlit App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': "# My Cool App\nThis is my awesome Streamlit application!"
    }
)

st.title("My Streamlit Application")
```

## Secrets Management

Streamlit provides a way to securely manage sensitive information like API keys and database credentials.

### Local Secrets Management

For local development, create a `.streamlit/secrets.toml` file:

```toml
# .streamlit/secrets.toml

# Database credentials
[connections.mydatabase]
type = "sql"
dialect = "postgresql"
host = "localhost"
port = 5432
database = "mydatabase"
username = "username"
password = "password"

# API keys
api_key = "your-api-key-here"
another_api_key = "another-api-key"

# Nested secrets
[services]
[services.my_service]
api_key = "service-specific-key"
url = "https://api.example.com"
```

### Accessing Secrets

Access your secrets in your Streamlit app:

```python
import streamlit as st

# Access top-level secrets
api_key = st.secrets["api_key"]

# Access nested secrets
service_url = st.secrets["services"]["my_service"]["url"]

# Use secrets for connections (automatically used)
conn = st.connection("mydatabase", type="sql")
```

### Deploying with Secrets

When deploying to Streamlit Cloud or another hosting provider, set up secrets according to their documentation.

For Streamlit Cloud specifically:
1. Go to your app's page
2. Navigate to the "Settings" tab
3. Under "Secrets", add your secrets in TOML format
4. Save your changes

### Environment-Specific Connections

Create environment-specific connection configurations:

```toml
# .streamlit/secrets.toml

[connections.development]
type = "sql"
url = "sqlite:///dev.db"

[connections.production]
type = "sql"
url = "postgresql://user:pass@prod-server:5432/prod_db"
```

Then use environment variables to choose the right connection:

```python
import streamlit as st
import os

# Get the environment from an environment variable
env = os.environ.get("STREAMLIT_ENV", "development")

# Connect to the appropriate database
conn = st.connection(f"env:{env}", type="sql")
```

## Best Practices

### Connection Management

1. **Use Connection Pooling**: Avoid creating multiple connections to the same data source.

```python
# BAD: Creating a new connection for each query
def get_data():
    conn = st.connection("my_db", type="sql")
    return conn.query("SELECT * FROM data")

# GOOD: Reuse the same connection
conn = st.connection("my_db", type="sql")

def get_data():
    return conn.query("SELECT * FROM data")
```

2. **Parameterize Queries**: Always use parameterized queries to prevent SQL injection.

```python
# BAD: String interpolation (vulnerable to SQL injection)
user_id = st.text_input("User ID")
data = conn.query(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD: Parameterized query
user_id = st.text_input("User ID")
data = conn.query("SELECT * FROM users WHERE id = :id", params={"id": user_id})
```

3. **Handle Connection Errors**: Implement proper error handling for connection failures.

```python
import streamlit as st

try:
    conn = st.connection("my_db", type="sql")
    data = conn.query("SELECT * FROM users")
    st.dataframe(data)
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Please check your database configuration or try again later.")
```

### Security Practices

1. **Keep Secrets Secure**: Never hardcode credentials in your app.

```python
# BAD: Hardcoded credentials
conn = st.connection(
    "my_db",
    type="sql",
    url="mysql://username:password@localhost:3306/database"
)

# GOOD: Use secrets
conn = st.connection("my_db", type="sql")
```

2. **Minimal Permissions**: Use connection credentials with the minimal required permissions.

3. **Validate User Input**: Always validate and sanitize user input before using it in queries.

```python
import streamlit as st
import re

# Input validation
table_name = st.text_input("Table Name")
if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
    st.error("Invalid table name. Use only letters, numbers, and underscores.")
else:
    # Proceed with the query using the validated table name
    query = f"SELECT * FROM {table_name}"
    st.code(query)  # Show the query for transparency
    
    try:
        data = conn.query(query)
        st.dataframe(data)
    except Exception as e:
        st.error(f"Query error: {e}")
```

### Configuration Best Practices

1. **Use Configuration Files**: Store configuration in `.streamlit/config.toml` rather than hardcoding.

2. **Environment-Specific Configs**: Create different configurations for development and production.

```python
import streamlit as st
import os

# Check the environment
env = os.environ.get("STREAMLIT_ENV", "development")

# Display environment info
if env == "development":
    st.info("Running in development mode")
    # Show additional debug information
    if st.checkbox("Show configuration"):
        st.json(st.session_state.to_dict())
```

3. **Version Control**: Add `.streamlit/secrets.toml` to your `.gitignore` file to avoid committing secrets.

4. **Documentation**: Document your configuration options and provide examples.

```python
# Add a configuration section to your README.md
"""
## Configuration

This app can be configured using environment variables or a `.streamlit/config.toml` file.

### Required Configuration

- `STREAMLIT_SERVER_PORT`: The port to run the server on (default: 8501)
- `DATABASE_URL`: Connection string for the database

### Optional Configuration

- `DEBUG`: Enable debug mode (true/false)
- `THEME_COLOR`: Primary theme color (hex code)

Example `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#f63366"

[server]
port = 8080
```
"""
```

### Custom Connections

1. **Implement Timeouts**: Always include timeouts in your custom connections.

```python
class APIConnection(BaseConnection):
    def _connect(self, **kwargs):
        session = requests.Session()
        
        # Set default timeout
        timeout = kwargs.pop('timeout', 10)
        session.request = functools.partial(session.request, timeout=timeout)
        
        return session
```

2. **Implement Proper Error Handling**: Provide meaningful error messages.

```python
def query(self, endpoint, params=None):
    try:
        response = self._instance.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Failed to connect to {endpoint}. Check your network connection.")
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request to {endpoint} timed out. Try again later.")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP Error: {e}")
    except ValueError:
        raise ValueError(f"Invalid JSON response from {endpoint}")
```

3. **Implement Caching**: Use Streamlit's caching mechanisms.

```python
def get_data(self, query_params, ttl=None):
    # Create a cache key based on the query parameters
    cache_key = hash(frozenset(query_params.items()))
    
    # Check if result is in cache
    if cache_key in self._cache:
        cache_time, result = self._cache[cache_key]
        if ttl is None or (time.time() - cache_time) < ttl:
            return result
    
    # Fetch fresh data
    result = self._fetch_data(query_params)
    
    # Store in cache
    self._cache[cache_key] = (time.time(), result)
    
    return result
```

## Related Components

- **[Session State](session_state.md)**: State management in Streamlit
- **[Caching](state_caching.md)**: Caching in Streamlit
- **[Deployment](deployment.md)**: Deploying Streamlit applications