# Polars I/O and Integration

## File I/O

### CSV

```python
# Reading CSV
df = pl.read_csv("path/to/file.csv")

# Writing CSV
df.write_csv("path/to/output.csv")
```

### Parquet

```python
# Reading Parquet
df = pl.read_parquet("path/to/file.parquet")

# Writing Parquet
df.write_parquet("path/to/file.parquet")
```

### JSON

```python
# Reading JSON
df = pl.read_json("path/to/file.json")
```

### Database

```python
# Reading from a database
df = pl.read_database_uri("postgresql://username:password@host:port/database", 
                          "SELECT * FROM foo")

# Writing to a database
df.write_database("records", connection="sqlite:///some.db", engine="adbc")
```

### Cloud Storage

```python
# Write to S3
df.write_parquet("s3://bucket/file.parquet", storage_options=storage_options)
```

## Integration with Other Libraries

### Pandas

```python
# Convert Polars DataFrame to Pandas
pandas_df = df.to_pandas()

# Convert Pandas DataFrame to Polars
polars_df = pl.from_pandas(pandas_df)
```

### NumPy

```python
# Convert to NumPy
numpy_arr = df.to_numpy()

# Import from NumPy
import numpy as np
my_arr = np.array([(1, 9.0), (2, 8.0), (3, 7.0)])
duckdb.sql("SELECT * FROM my_arr")
```

### Arrow

```python
# Convert to Arrow Table
arrow_table = df.to_arrow()

# Import from Arrow
import pyarrow as pa
table = pa.Table.from_pydict({"a": [1, 2, 3]})
df = pl.from_arrow(table)
```

## SQL Integration

### Executing SQL

```python
import polars as pl
import pandas as pd

polars_df = pl.DataFrame({"a": [1, 2, 3, 4], "b": [4, 5, 6, 7]})
pandas_df = pd.DataFrame({"a": [3, 4, 5, 6], "b": [6, 7, 8, 9]})
polars_series = (polars_df["a"] * 2).rename("c")
pyarrow_table = polars_df.to_arrow()

result = pl.sql(
    """
    SELECT a, b, SUM(c) AS c_total FROM (
      SELECT * FROM polars_df                  -- polars frame
        UNION ALL SELECT * FROM pandas_df      -- pandas frame
        UNION ALL SELECT * FROM pyarrow_table  -- pyarrow table
    ) all_data
    INNER JOIN polars_series
      ON polars_series.c = all_data.b          -- polars series
    GROUP BY "a", "b"
    ORDER BY "a", "b"
    """
).collect()
```

### Using SQLContext

```python
import polars as pl

df1 = pl.DataFrame({"id": [1, 2, 3], "value": [0.1, 0.2, 0.3]})
df2 = pl.DataFrame({"id": [3, 2, 1], "value": [25.6, 53.4, 12.7]})

with pl.SQLContext(df_a=df1, df_b=df2, eager=True) as ctx:
    df = ctx.execute("""
      SELECT
        a.id,
        a.value AS value_a,
        b.value AS value_b
      FROM df_a AS a INNER JOIN df_b AS b USING (id)
      ORDER BY id
    """)
```

## Exporting Series

```python
# Available methods for Series
s.__array__()                 # Python objects
s.__arrow_c_stream__()        # Arrow C stream
s.to_arrow()                  # Arrow Table
s.to_frame()                  # Polars DataFrame
s.to_init_repr()              # Initialization representation
s.to_jax()                    # JAX array
s.to_list()                   # Python list
s.to_numpy()                  # NumPy array
s.to_pandas()                 # Pandas Series
s.to_torch()                  # PyTorch tensor
```