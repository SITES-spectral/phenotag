# DuckDB Python Integration

## Basic Usage

```python
import duckdb

# Execute a query
duckdb.sql("SELECT 42 AS fortytwo")

# Create a connection
con = duckdb.connect()

# Create a table and insert data
con.execute("CREATE TABLE items(item VARCHAR, value DECIMAL(10,2), count INTEGER)")
con.execute("INSERT INTO items VALUES ('jeans', 20.0, 1), ('hammer', 42.2, 2)")

# Query the data
con.execute("SELECT * FROM items")
print(con.fetchall())
# Output: [('jeans', 20.0, 1), ('hammer', 42.2, 2)]
```

## Working with DataFrames

### Querying Pandas DataFrames

```python
import duckdb
import pandas as pd

# Create a Pandas dataframe
pandas_df = pd.DataFrame({"a": [1, 2, 3, 4], "b": ["one", "two", "three", "four"]})

# Query the Pandas DataFrame
duckdb.sql("SELECT * FROM pandas_df")
```

### Creating Tables from DataFrames

```python
# Create a table from a DataFrame
con.execute("CREATE TABLE test_df_table AS SELECT * FROM test_df")

# Insert into an existing table from a DataFrame
con.execute("INSERT INTO test_df_table SELECT * FROM test_df")
```

### Inserting Data by Column Name

```python
duckdb.sql("INSERT INTO my_table BY NAME SELECT * FROM my_df")
```

### Converting Results to DataFrames

```python
import duckdb

# Python objects
result = duckdb.sql("SELECT 42").fetchall()   

# Pandas DataFrame
df = duckdb.sql("SELECT 42").df()         

# Polars DataFrame
pl_df = duckdb.sql("SELECT 42").pl()         

# Arrow Table
arrow_table = duckdb.sql("SELECT 42").arrow()      

# NumPy Arrays
numpy_array = duckdb.sql("SELECT 42").fetchnumpy() 
```

## Working with Other Array Types

### NumPy

```python
import duckdb
import numpy as np

my_arr = np.array([(1, 9.0), (2, 8.0), (3, 7.0)])

duckdb.sql("SELECT * FROM my_arr")
```

### PyArrow

```python
import duckdb
import pyarrow as pa

arrow_table = pa.Table.from_pydict({"a": [42]})
duckdb.sql("SELECT * FROM arrow_table")
```

## Context Manager for Connections

```python
import duckdb

with duckdb.connect("file.db") as con:
    con.sql("CREATE TABLE test (i INTEGER)")
    con.sql("INSERT INTO test VALUES (42)")
    con.table("test").show()
    # the context manager closes the connection automatically
```

## Writing Results to Disk

```python
import duckdb

duckdb.sql("SELECT 42").write_parquet("out.parquet") # Write to a Parquet file
duckdb.sql("SELECT 42").write_csv("out.csv")         # Write to a CSV file
duckdb.sql("COPY (SELECT 42) TO 'out.parquet'")      # Copy to a Parquet file
```

## Using Prepared Statements

```python
# Insert with parameter
con.execute("INSERT INTO items VALUES (?, ?, ?)", ["laptop", 2000, 1])

# Insert multiple rows
con.executemany("INSERT INTO items VALUES (?, ?, ?)", [["chainsaw", 500, 10], ["iphone", 300, 2]])

# Query with parameter
con.execute("SELECT item FROM items WHERE value > ?", [400])
print(con.fetchall())
# Output: [('laptop',), ('chainsaw',)]

# Using dollar sign parameters
con.execute("SELECT $1, $1, $2", ["duck", "goose"])
print(con.fetchall())
# Output: [('duck', 'duck', 'goose')]
```