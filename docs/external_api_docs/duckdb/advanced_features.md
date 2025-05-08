# DuckDB Advanced Features

This document covers advanced DuckDB features that can help you build more powerful data processing applications.

## Window Functions

Window functions perform calculations across a set of rows that are related to the current row.

### Basic Window Functions

```sql
-- ROW_NUMBER: Assign a unique number to each row
SELECT 
    product_name,
    category,
    price,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS price_rank
FROM products;

-- RANK: Similar to ROW_NUMBER but with gaps for ties
SELECT 
    student_name,
    score,
    RANK() OVER (ORDER BY score DESC) AS score_rank
FROM exam_results;

-- DENSE_RANK: Like RANK but without gaps
SELECT 
    student_name,
    score,
    DENSE_RANK() OVER (ORDER BY score DESC) AS score_rank
FROM exam_results;
```

### Aggregate Window Functions

```sql
-- Running sum
SELECT 
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;

-- Moving average
SELECT 
    order_date,
    amount,
    AVG(amount) OVER (
        ORDER BY order_date 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3_days
FROM orders;

-- Percentage of total
SELECT 
    category,
    amount,
    amount / SUM(amount) OVER () * 100 AS percentage_of_total
FROM sales;
```

### Advanced Window Frame Specifications

```sql
-- Specifying window frames
SELECT 
    date,
    value,
    AVG(value) OVER (
        ORDER BY date 
        ROWS BETWEEN 3 PRECEDING AND 1 FOLLOWING
    ) AS centered_avg
FROM time_series;

-- Using RANGE instead of ROWS
SELECT 
    date,
    value,
    SUM(value) OVER (
        ORDER BY date 
        RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW
    ) AS sum_last_day
FROM time_series;
```

## User-Defined Functions (UDFs)

### Python UDFs

```python
import duckdb
from duckdb.typing import *

# Simple UDF
def add_one(x):
    if x is None:
        return None
    return x + 1

# Register the UDF
duckdb.create_function("add_one", add_one, [INTEGER], INTEGER)

# Use the UDF
result = duckdb.sql("SELECT add_one(42)").fetchall()
print(result)  # [(43,)]

# UDF with custom NULL handling
def process_text(text):
    if text is None or text == '':
        return 'N/A'
    return text.upper()

# Register with special NULL handling
duckdb.create_function("process_text", process_text, [VARCHAR], VARCHAR, null_handling='special')

# Use the UDF
result = duckdb.sql("SELECT process_text(NULL), process_text(''), process_text('hello')").fetchall()
print(result)  # [('N/A', 'N/A', 'HELLO')]
```

### Vectorized UDFs

```python
import duckdb
from duckdb.typing import *
import numpy as np

# Define a vectorized UDF
def add_arrays(a, b):
    if a is None or b is None:
        return None
    return np.add(a, b).tolist()

# Register the function as "native" type for vectorized execution
duckdb.create_function("add_arrays", add_arrays, [FLOAT_ARRAY, FLOAT_ARRAY], FLOAT_ARRAY, type="native")

# Use the UDF
result = duckdb.sql("""
    SELECT add_arrays([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
""").fetchall()
print(result)  # [([5.0, 7.0, 9.0],)]
```

### UDFs with Side Effects

```python
import duckdb
from duckdb.typing import *
import random

# UDF with side effects (e.g., random number generation)
def random_int(min_val, max_val):
    return random.randint(min_val, max_val)

# Register with side_effects=True to prevent optimization removing it
duckdb.create_function("random_int", random_int, [INTEGER, INTEGER], INTEGER, side_effects=True)

# Each call will generate a different random number
result = duckdb.sql("""
    SELECT random_int(1, 100) FROM range(5)
""").fetchall()
print(result)
```

## Lambda Functions

Lambda functions allow you to create inline, anonymous functions within SQL queries.

### Basic Lambda Usage

```sql
-- Using lambda with list_transform
SELECT list_transform([1, 2, 3, 4], x -> x * x) AS squared_values;
-- Returns: [1, 4, 9, 16]

-- Filtering with list_filter
SELECT list_filter([1, 2, 3, 4, 5], x -> x % 2 = 0) AS even_numbers;
-- Returns: [2, 4]

-- Aggregation with list_reduce
SELECT list_reduce([1, 2, 3, 4], 0, (acc, x) -> acc + x) AS sum;
-- Returns: 10
```

### Multi-Parameter Lambdas

```sql
-- Lambda with two parameters
SELECT list_zip([1, 2, 3], [4, 5, 6], (x, y) -> x + y) AS element_sums;
-- Returns: [5, 7, 9]

-- Lambda with three parameters
SELECT list_zip([1, 2, 3], [4, 5, 6], [7, 8, 9], 
                (x, y, z) -> x + y + z) AS triplet_sums;
-- Returns: [12, 15, 18]
```

### Lambda with Struct Transformation

```sql
-- Transform array of structs
SELECT list_transform(
    [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}],
    p -> {'name': p.name, 'birth_year': 2023 - p.age}
) AS birth_years;
```

## Recursive Common Table Expressions (CTEs)

Recursive queries can be used to work with hierarchical or graph-structured data.

### Tree Traversal

```sql
-- Sample data representing a category hierarchy
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    parent_id INTEGER
);

INSERT INTO categories VALUES
(1, 'Electronics', NULL),
(2, 'Computers', 1),
(3, 'Laptops', 2),
(4, 'Desktops', 2),
(5, 'Smartphones', 1),
(6, 'Accessories', 5);

-- Recursive query to get the full path for each category
WITH RECURSIVE category_paths(id, name, path) AS (
    -- Base case: root categories (no parent)
    SELECT id, name, [name] AS path
    FROM categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- Recursive case: add child categories
    SELECT c.id, c.name, list_prepend(c.name, cp.path)
    FROM categories c
    JOIN category_paths cp ON c.parent_id = cp.id
)
SELECT id, name, path FROM category_paths;
```

### Graph Traversal

```sql
-- Sample data representing a network
CREATE TABLE connections (
    from_node INTEGER,
    to_node INTEGER,
    weight INTEGER
);

INSERT INTO connections VALUES
(1, 2, 5),
(1, 3, 10),
(2, 4, 7),
(3, 4, 2),
(4, 5, 3),
(3, 5, 15);

-- Find all paths from node 1 to node 5 with max 3 hops
WITH RECURSIVE paths(from_node, to_node, path, total_weight, hops) AS (
    -- Base case: direct connections from node 1
    SELECT 
        from_node, 
        to_node, 
        [from_node, to_node] AS path, 
        weight AS total_weight,
        1 AS hops
    FROM connections
    WHERE from_node = 1
    
    UNION ALL
    
    -- Recursive case: Add one more hop
    SELECT 
        p.from_node, 
        c.to_node, 
        array_append(p.path, c.to_node) AS path, 
        p.total_weight + c.weight AS total_weight,
        p.hops + 1 AS hops
    FROM paths p
    JOIN connections c ON p.to_node = c.from_node
    WHERE p.hops < 3 AND NOT array_contains(p.path, c.to_node)
)
SELECT * FROM paths
WHERE to_node = 5
ORDER BY total_weight;
```

## JSON Processing

DuckDB offers powerful JSON processing capabilities.

### JSON Extraction and Querying

```sql
-- Extract specific fields from JSON
SELECT 
    json_extract('{"name":"DuckDB","stats":{"users":1000,"queries":5000}}', '$.name') AS name,
    json_extract('{"name":"DuckDB","stats":{"users":1000,"queries":5000}}', '$.stats.users') AS users;

-- Extract array elements
SELECT json_extract('{"values":[10,20,30]}', '$.values[1]');  -- Returns 20 (0-indexed)

-- Check if a JSON key exists
SELECT json_contains('{"a":1,"b":2}', '$.c');  -- Returns false
```

### JSON Creation and Modification

```sql
-- Create JSON from values
SELECT json_object('name', 'DuckDB', 'version', '0.9.0') AS json_data;

-- Combine multiple JSON objects
SELECT json_merge_patch(
    '{"name":"DuckDB","stats":{"users":1000}}',
    '{"stats":{"queries":5000},"open_source":true}'
) AS merged;
```

### JSON Arrays

```sql
-- Create a JSON array
SELECT json_array(1, 'abc', 3.14, NULL) AS json_arr;

-- Transform SQL results to JSON array
SELECT json_array_elements('[1,2,3]');

-- Aggregate rows into a JSON array
SELECT json_group_array(name) FROM users;
```

### Converting JSON to Tables (JSON Normalization)

```sql
-- Flatten nested JSON to a table
SELECT * FROM json_read_table('
[
  {"id": 1, "name": "Alice", "skills": ["SQL", "Python"]},
  {"id": 2, "name": "Bob", "skills": ["Java", "C++"]}
]');
```

## Spatial Functions

When using the spatial extension, DuckDB supports geospatial operations.

### Getting Started with Spatial Data

```sql
-- Install and load the spatial extension
INSTALL spatial;
LOAD spatial;

-- Create a point geometry
SELECT ST_Point(1.0, 2.0) AS point;

-- Create a linestring
SELECT ST_LineString(ARRAY[ST_Point(1, 2), ST_Point(3, 4), ST_Point(5, 6)]) AS line;

-- Create a polygon
SELECT ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))') AS polygon;
```

### Spatial Analysis

```sql
-- Calculate distance between points
SELECT ST_Distance(ST_Point(1, 2), ST_Point(3, 4)) AS distance;

-- Check if geometries intersect
SELECT ST_Intersects(
    ST_GeomFromText('LINESTRING(0 0, 2 2)'),
    ST_GeomFromText('LINESTRING(0 2, 2 0)')
) AS intersects;

-- Calculate area of a polygon
SELECT ST_Area(ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))')) AS area;
```

### Spatial Joins

```sql
-- Spatial join example
SELECT cities.name, states.name AS state
FROM cities JOIN states
ON ST_Within(cities.geom, states.geom);
```

## Time Series Analysis

DuckDB has several features that make time series analysis efficient.

### Time Manipulation

```sql
-- Extract parts from timestamps
SELECT 
    ts,
    EXTRACT(YEAR FROM ts) AS year,
    EXTRACT(MONTH FROM ts) AS month,
    EXTRACT(DAY FROM ts) AS day,
    EXTRACT(HOUR FROM ts) AS hour
FROM timestamps;

-- Date/time arithmetic
SELECT 
    DATE '2023-01-01' + INTERVAL '1 month' AS next_month,
    TIMESTAMP '2023-01-01 12:00:00' - INTERVAL '2 hours' AS two_hours_earlier;
    
-- Date/time functions
SELECT 
    current_timestamp() AS now,
    date_trunc('hour', current_timestamp()) AS truncated_hour,
    date_part('dow', DATE '2023-01-01') AS day_of_week;
```

### Time Series Aggregation

```sql
-- Aggregate by time periods
SELECT 
    date_trunc('month', order_date) AS month,
    SUM(amount) AS monthly_total
FROM orders
GROUP BY date_trunc('month', order_date)
ORDER BY month;

-- Rolling window calculations
SELECT 
    order_date,
    amount,
    AVG(amount) OVER (
        ORDER BY order_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_day_avg
FROM orders;

-- Cumulative sums by time period
SELECT 
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;
```

## Advanced Optimization Techniques

### Query Profiling

```sql
-- Get a breakdown of query execution time
EXPLAIN ANALYZE SELECT * FROM large_table WHERE id > 1000;

-- Set profiling output mode
PRAGMA explain_output = 'optimized_only';
EXPLAIN SELECT * FROM table1 JOIN table2 ON table1.id = table2.id;
```

### Memory Management

```sql
-- Set memory limit
SET memory_limit = '8GB';

-- Set maximum memory per query
SET max_memory = '4GB';
```

### Parallel Processing

```sql
-- Control the number of threads DuckDB uses
SET threads = 8;

-- Check current parallelism settings
SELECT current_setting('threads');
```

### Persistence and Checkpointing

```sql
-- Force checkpointing to disk
CHECKPOINT;

-- Pragmas for WAL management
PRAGMA wal_autocheckpoint = 16384;  -- Checkpoint every 16384 pages (64MB by default)
```

### Custom Schema and Table Options

```sql
-- Table options for compression
CREATE TABLE compressed_data (
    id INTEGER,
    payload VARCHAR
) WITH (compression = 'snappy');
```

## Integration with Machine Learning

### Feature Preparation

```sql
-- One-hot encoding with SQL
SELECT 
    id,
    CASE WHEN color = 'red' THEN 1 ELSE 0 END AS is_red,
    CASE WHEN color = 'blue' THEN 1 ELSE 0 END AS is_blue,
    CASE WHEN color = 'green' THEN 1 ELSE 0 END AS is_green
FROM items;

-- Scaling features to 0-1 range
SELECT 
    id,
    (price - MIN(price) OVER ()) / (MAX(price) OVER () - MIN(price) OVER ()) AS price_scaled
FROM products;

-- Feature arrays for ML
SELECT 
    id,
    [age, height, weight]::FLOAT[] AS features
FROM people;
```

### Python ML Integration

```python
import duckdb
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Connect to DuckDB
con = duckdb.connect()

# Create and populate a table
con.execute("""
CREATE TABLE iris AS
SELECT * FROM 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv'
""")

# Prepare data for machine learning
df = con.execute("""
SELECT 
    sepal_length, sepal_width, petal_length, petal_width,
    species
FROM iris
""").df()

# Prepare features and target
X = df.iloc[:, 0:4].values
y = df['species'].values

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train a model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Create a UDF to make predictions
def predict_species(sl, sw, pl, pw):
    features = np.array([[sl, sw, pl, pw]])
    pred = model.predict(features)[0]
    return pred

# Register the UDF
con.create_function("predict_species", predict_species, ['FLOAT', 'FLOAT', 'FLOAT', 'FLOAT'], 'VARCHAR')

# Use the model in SQL
result = con.execute("""
SELECT 
    sepal_length, sepal_width, petal_length, petal_width,
    species AS actual_species,
    predict_species(sepal_length, sepal_width, petal_length, petal_width) AS predicted_species
FROM iris
LIMIT 10
""").df()

print(result)
```

## Extensions System

DuckDB's capabilities can be extended through various extensions.

### Managing Extensions

```sql
-- List available extensions
SELECT * FROM duckdb_extensions();

-- Install an extension
INSTALL httpfs;

-- Load an extension
LOAD httpfs;

-- Update installed extensions
UPDATE EXTENSIONS (httpfs, spatial);

-- Uninstall an extension
UNINSTALL httpfs;
```

### Using Cloud Storage Extensions

```sql
-- Read data from S3 (with httpfs extension)
LOAD httpfs;
SELECT * FROM 's3://bucket-name/path/to/file.parquet';

-- Set S3 credentials
SET s3_region='us-east-1';
SET s3_access_key_id='your-access-key';
SET s3_secret_access_key='your-secret-key';
```

### Using the SQLite Extension

```sql
-- Load SQLite extension
INSTALL sqlite;
LOAD sqlite;

-- Query an SQLite database
SELECT * FROM sqlite_scan('path/to/sqlite.db', 'table_name');

-- Attach an SQLite database
ATTACH 'path/to/sqlite.db' AS sqlite_db;
SELECT * FROM sqlite_db.table_name;
```

## External Functions

External functions allow you to call functionality from other systems within DuckDB.

### HTTP Requests

```sql
-- Load httpfs extension for HTTP support
INSTALL httpfs;
LOAD httpfs;

-- Perform HTTP GET request
SELECT http_get('https://api.example.com/data', NULL);

-- POST request with JSON body
SELECT http_post(
    'https://api.example.com/submit',
    '{"key": "value"}',
    '{"Content-Type": "application/json"}'
);
```

### Python UDFs with External Libraries

```python
import duckdb
import requests
from duckdb.typing import VARCHAR

# UDF that makes an HTTP request
def fetch_data(url):
    try:
        response = requests.get(url)
        return response.text if response.status_code == 200 else None
    except:
        return None

# Register the UDF
duckdb.create_function("http_fetch", fetch_data, [VARCHAR], VARCHAR)

# Use the UDF in a query
result = duckdb.sql("""
    SELECT http_fetch('https://example.com/api/data')
""").fetchall()

print(result)
```