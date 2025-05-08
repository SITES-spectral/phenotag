# Polars Basics

## Installation

```bash
pip install polars
```

## Importing

```python
import polars as pl
```

## Creating DataFrames

### From Dictionary

```python
df = pl.DataFrame(
    {
        "a": [1, 2, 3, 4, 5],
        "b": [6, 7, 8, 9, 10],
        "c": ["a", "b", "c", "d", "e"],
    }
)
print(df)
```

### Creating a Series

```python
# Simple series
s = pl.Series(name="a", values=[1, 2, 3, 4, 5])
print(s)

# With explicit data type
s = pl.Series(name="a", values=[1, 2, 3, 4, 5], dtype=pl.Float32)
print(s)
```

## Basic Operations

### Viewing Data

```python
# Print the first n rows
print(df.head(3))
```

### Arithmetic Operations

```python
# Basic operations between series and literals
s1 + s2
s1 * 5
```

### Expressions

```python
# Create an expression
expr = pl.col("weight") / (pl.col("height") ** 2)
```

## Context Operations

### Select

```python
# Select specific columns
df.select(["a", "b"])

# Select with expressions
df.select([
    pl.col("name"),
    (pl.col("weight") / (pl.col("height") ** 2)).alias("bmi"),
    pl.lit(1).alias("constant")
])
```

### Filter

```python
# Filter rows where column "a" > 2
df.filter(pl.col("a") > 2)

# Multiple filter conditions
df.filter(
    (pl.col("a") > 2) &
    (pl.col("b") < 10)
)
```

### With Columns

```python
# Add a new calculated column
df.with_columns([
    (pl.col("weight") / (pl.col("height") ** 2)).alias("bmi")
])

# Add multiple columns
df.with_columns(
    tenXValue=pl.col("value") * 10,
    hundredXValue=pl.col("value") * 100,
)
```

### Group By

```python
# Group by and aggregate
df.group_by("category").agg(
    pl.col("value").mean().alias("avg_value"),
    pl.col("value").count().alias("count")
)

# Group by multiple columns with custom aggregations
df.group_by(
    [
        (pl.col("birth") // 10 * 10).alias("decade"),
        (pl.col("height") < 1.7).alias("is_short")
    ]
).agg([
    pl.col("weight", "height").mean().name.prefix("avg_"),
    pl.col("name").len().alias("group_size")
])
```

### Sort

```python
# Sort by one column
df.sort("column_name")

# Sort by multiple columns in different directions
df.sort(["column1", "column2"], descending=[True, False])
```

### Join

```python
# Left join
left_df.join(right_df, on="key_column", how="left")

# Inner join
df1.join(df2, on="property", how="inner")
```