# DuckDB Data Types

DuckDB supports a rich set of data types for various use cases. This document provides an overview of the available data types and how to use them effectively.

## Primitive Types

### Numeric Types

#### Integer Types

```sql
-- Integer types with different sizes
TINYINT    -- 1-byte signed integer (-128 to 127)
SMALLINT   -- 2-byte signed integer (-32,768 to 32,767)
INTEGER    -- 4-byte signed integer (-2,147,483,648 to 2,147,483,647)
BIGINT     -- 8-byte signed integer (-9,223,372,036,854,775,808 to 9,223,372,036,854,775,807)
HUGEINT    -- 16-byte signed integer (−170,141,183,460,469,231,731,687,303,715,884,105,728 to 170,141,183,460,469,231,731,687,303,715,884,105,727)
UTINYINT   -- 1-byte unsigned integer (0 to 255)
USMALLINT  -- 2-byte unsigned integer (0 to 65,535)
UINTEGER   -- 4-byte unsigned integer (0 to 4,294,967,295)
UBIGINT    -- 8-byte unsigned integer (0 to 18,446,744,073,709,551,615)
```

#### Floating-Point Types

```sql
-- Floating-point types
REAL       -- 4-byte floating-point number
FLOAT      -- 8-byte floating-point number (alias for DOUBLE)
DOUBLE     -- 8-byte floating-point number
```

#### Fixed-Point Types

```sql
-- Fixed-point types
DECIMAL(precision, scale)  -- Fixed-point decimal number
NUMERIC(precision, scale)  -- Alias for DECIMAL
```

### String Types

```sql
-- String types
VARCHAR    -- Variable-length character string (can specify max length)
CHAR(n)    -- Fixed-length character string
TEXT       -- Alias for VARCHAR
```

### Boolean Type

```sql
-- Boolean type
BOOLEAN    -- True or false values
```

### Temporal Types

```sql
-- Date and time types
DATE              -- Calendar date (year, month, day)
TIME              -- Time of day (hour, minute, second, microsecond)
TIMESTAMP         -- Date and time with microsecond precision
TIMESTAMP_S       -- Date and time with second precision
TIMESTAMP_MS      -- Date and time with millisecond precision
TIMESTAMP_NS      -- Date and time with nanosecond precision
TIMESTAMP WITH TIME ZONE -- Timestamp with timezone information
INTERVAL          -- Time interval
```

## Complex Types

### Array Type

Arrays store a sequence of values of the same type.

```sql
-- Array type declaration
CREATE TABLE items (
    id INTEGER,
    prices FLOAT[]  -- Array of FLOAT values
);

-- Array creation and insertion
INSERT INTO items VALUES (1, [10.5, 20.0, 15.75]);

-- Array access
SELECT id, prices[1] AS first_price FROM items;  -- Arrays are 1-indexed
```

#### Array Functions

```sql
-- Array functions
SELECT array_length([1, 2, 3]);                -- Returns 3
SELECT array_append([1, 2, 3], 4);             -- Returns [1, 2, 3, 4]
SELECT array_prepend(0, [1, 2, 3]);            -- Returns [0, 1, 2, 3]
SELECT array_concat([1, 2], [3, 4]);           -- Returns [1, 2, 3, 4]
SELECT array_contains([1, 2, 3], 2);           -- Returns true
SELECT array_position([1, 2, 3], 2);           -- Returns 2 (1-indexed)
SELECT array_slice([1, 2, 3, 4], 2, 3);        -- Returns [2, 3]
SELECT array_distance([1.0, 2.0], [2.0, 2.0]); -- Returns Euclidean distance
```

### Struct Type

Structs store multiple named fields that can have different types.

```sql
-- Struct type declaration
CREATE TABLE employees (
    id INTEGER,
    address STRUCT(street VARCHAR, city VARCHAR, zip VARCHAR)
);

-- Struct creation and insertion
INSERT INTO employees VALUES (
    1, 
    {'street': '123 Main St', 'city': 'Duckburg', 'zip': '12345'}
);

-- Struct field access
SELECT id, address.city FROM employees;
```

#### Struct Creation

```sql
-- Creating structs
SELECT {'name': 'DuckDB', 'type': 'database'} AS product;

-- Named struct construction
SELECT struct_pack(name := 'DuckDB', type := 'database') AS product;
```

### Map Type

Maps store key-value pairs.

```sql
-- Map type declaration
CREATE TABLE users (
    id INTEGER,
    properties MAP(VARCHAR, VARCHAR)
);

-- Map creation and insertion
INSERT INTO users VALUES (
    1, 
    map(['name', 'email'], ['John Doe', 'john@example.com'])
);

-- Map access
SELECT id, properties['name'] FROM users;
```

### Union Type

Unions can store values of different types in a single column.

```sql
-- Creating a union with a SQL query
SELECT union_value(num := 42)::UNION(num INTEGER, str VARCHAR) AS u
UNION ALL
SELECT union_value(str := 'hello')::UNION(num INTEGER, str VARCHAR) AS u;

-- Using unions in a table
CREATE TABLE mixed_data (
    id INTEGER,
    value UNION(int_val INTEGER, float_val FLOAT, text_val VARCHAR)
);

-- Inserting union values
INSERT INTO mixed_data VALUES 
    (1, union_value(int_val := 42)),
    (2, union_value(float_val := 3.14)),
    (3, union_value(text_val := 'hello'));

-- Querying union values
SELECT 
    id, 
    value.int_val, 
    value.float_val, 
    value.text_val 
FROM mixed_data;
```

### Enums

Enums represent a static set of string values.

```sql
-- Creating an enum type
CREATE TYPE mood AS ENUM ('sad', 'ok', 'happy');

-- Using enum in a table
CREATE TABLE person (
    name VARCHAR,
    current_mood mood
);

-- Inserting enum values
INSERT INTO person VALUES ('Pedro', 'happy');

-- Invalid enum value would cause an error
-- INSERT INTO person VALUES ('Mark', 'hungry');
```

## Nested Data Types

DuckDB excels at handling deeply nested data structures.

```sql
-- Nested struct with lists
SELECT {
    'birds': ['duck', 'goose', 'heron'], 
    'aliens': NULL, 
    'amphibians': ['frog', 'toad']
};

-- Struct with list of maps
SELECT {
    'test': [
        map([1, 5], [42.1, 45]), 
        map([1, 5], [42.1, 45])
    ]
};

-- A list of unions
SELECT [
    union_value(num := 2), 
    union_value(str := 'ABC')::UNION(str VARCHAR, num INTEGER)
];
```

## Type Conversion

### Explicit Casting

```sql
-- Explicit type casting
SELECT CAST(42 AS VARCHAR);            -- Converts integer to string
SELECT 42::VARCHAR;                     -- Alternative syntax

SELECT CAST('42' AS INTEGER);           -- Converts string to integer
SELECT '42'::INTEGER;                   -- Alternative syntax

SELECT CAST('2023-01-01' AS DATE);      -- Converts string to date
SELECT '2023-01-01'::DATE;              -- Alternative syntax
```

### Implicit Casting

Some conversions happen automatically:

```sql
-- Implicit conversions
SELECT 42 + 3.14;                       -- INTEGER + FLOAT -> FLOAT
SELECT TIMESTAMP '2023-01-01 12:00:00' + INTERVAL '1 day';  -- Adds 1 day to timestamp
```

## Using Data Types in Python

### Creating Tables with Various Types in Python

```python
import duckdb

con = duckdb.connect()

# Create a table with various data types
con.execute("""
CREATE TABLE sample_data (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    age SMALLINT,
    height FLOAT,
    is_active BOOLEAN,
    registration_date DATE,
    last_login TIMESTAMP,
    scores INTEGER[],
    metadata STRUCT(created_at TIMESTAMP, source VARCHAR)
)
""")

# Insert data
con.execute("""
INSERT INTO sample_data VALUES
(1, 'Alice', 28, 5.6, true, '2023-01-15', '2023-05-20 14:30:00', 
 [85, 92, 78], {'created_at': TIMESTAMP '2023-01-15 09:00:00', 'source': 'web'}),
(2, 'Bob', 34, 6.1, false, '2022-11-10', '2023-05-19 10:15:00', 
 [76, 88, 90], {'created_at': TIMESTAMP '2022-11-10 11:30:00', 'source': 'mobile'})
""")

# Query the data
result = con.execute("""
SELECT 
    id, 
    name, 
    scores[1] AS first_score, 
    metadata.source 
FROM sample_data
""").fetchall()

print(result)
```

### Handling Complex Types in Python

```python
import duckdb
import pandas as pd
import numpy as np

# Creating arrays and structs from Python data
con = duckdb.connect()

# Register Python lists and dictionaries
names = ['Alice', 'Bob', 'Charlie']
ages = [28, 34, 42]
attributes = [
    {'height': 5.6, 'weight': 135},
    {'height': 6.1, 'weight': 180},
    {'height': 5.9, 'weight': 170}
]

# Create a table using Python data
query = """
CREATE TABLE people AS
SELECT 
    unnest(?) AS name,
    unnest(?) AS age,
    unnest(?) AS attributes
"""
con.execute(query, [names, ages, attributes])

# Query with struct access
result = con.execute("""
SELECT 
    name, 
    age, 
    attributes.height,
    attributes.weight
FROM people
WHERE attributes.height > 5.8
""").fetchdf()

print(result)
```

## Working with JSON as Structs

DuckDB can automatically convert between JSON and structs.

```sql
-- Convert JSON to struct
SELECT json_extract('{"name":"DuckDB","features":["fast","columnar"]}', '$');

-- Access struct fields from parsed JSON
SELECT 
    json_extract('{"name":"DuckDB","features":["fast","columnar"]}', '$').name,
    json_extract('{"name":"DuckDB","features":["fast","columnar"]}', '$').features[1];

-- Convert struct to JSON
SELECT json_serialize({'name': 'DuckDB', 'features': ['fast', 'columnar']});
```

## Type Information Functions

```sql
-- Get the type of a value
SELECT typeof(42);                      -- Returns 'INTEGER'
SELECT typeof(42.0);                    -- Returns 'DOUBLE'
SELECT typeof('hello');                 -- Returns 'VARCHAR'

-- Check if two values have the same type
SELECT typeof(42) = typeof(43);         -- Returns true
```

## NULL Handling

NULL represents a missing or unknown value and works with all data types.

```sql
-- NULL with different types
SELECT NULL::INTEGER;                   -- NULL value of INTEGER type
SELECT NULL::VARCHAR;                   -- NULL value of VARCHAR type

-- NULL in operations
SELECT 42 + NULL;                       -- Result is NULL
SELECT 'hello' || NULL;                 -- Result is NULL

-- IS NULL check
SELECT column_name IS NULL FROM table_name;

-- IS NOT NULL check
SELECT column_name IS NOT NULL FROM table_name;

-- COALESCE - returns first non-NULL value
SELECT COALESCE(NULL, 'default_value'); -- Returns 'default_value'
```