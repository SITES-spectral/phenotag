# Polars Lazy API

## Introduction to Lazy API

The Lazy API allows you to build complex query plans that are only executed when you call `collect()`. This enables more efficient query optimization.

## Eager vs. Lazy Approach

### Eager API

```python
# Each operation is executed immediately
df = pl.read_csv("data.csv")
df = df.filter(pl.col("sepal_length") > 5.0)
df = df.group_by("species").agg(pl.mean("sepal_width"))
```

### Lazy API

```python
# Define query plan but don't execute yet
lazy_df = pl.scan_csv("data.csv")
lazy_df = lazy_df.filter(pl.col("sepal_length") > 5.0)
lazy_df = lazy_df.group_by("species").agg(pl.mean("sepal_width"))

# Execute the query plan
result = lazy_df.collect()
```

## Scanning Data Sources

```python
# Scan CSV
lf = pl.scan_csv("data.csv")

# Scan Parquet
lf = pl.scan_parquet("data.parquet")

# Custom transformations
lf = pl.scan_csv("reddit.csv")
   .with_columns(pl.col("name").str.to_uppercase())
   .filter(pl.col("comment_karma") > 0)
```

## Building Incremental Queries

```python
import duckdb

r1 = duckdb.sql("SELECT 42 AS i")
duckdb.sql("SELECT i * 2 AS k FROM r1").show()
```

## Execution Modes

### Standard Execution

```python
result = lazy_df.collect()
```

### Streaming Execution

For processing larger-than-memory datasets:

```python
result = lazy_df.collect(engine="streaming")
```

## Sink Operations

```python
# Sink to Parquet files with partitioning
lf = scan_csv("my_dataset/*.csv").filter(pl.all().is_not_null())
lf.sink_parquet(
    pl.PartitionMaxSize(
        "my_table_{part}.parquet"
        max_size=512_000
    )
)
```

## Query Plan Visualization

```python
# Visualize the optimized query plan
q.show_graph(output_path="optimized_plan.svg")
```

## Recommended Pattern vs. Sequential Pattern

### Sequential Pipe Pattern (Not Recommended)

```python
def get_foo(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("col_a").some_computation().alias("foo"))

def get_bar(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("col_b").some_computation().alias("bar"))

def get_ham(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col("col_c").some_computation().alias("ham"))

# Sequential transformations (inefficient)
df = get_foo(df)
df = get_bar(df)
df = get_ham(df)
```

### Expression-Based Pattern (Recommended)

```python
def get_foo(input_column: str) -> pl.Expr:
    return pl.col(input_column).some_computation().alias("foo")

def get_bar(input_column: str) -> pl.Expr:
    return pl.col(input_column).some_computation().alias("bar")

def get_ham(input_column: str) -> pl.Expr:
    return pl.col(input_column).some_computation().alias("ham")

# This single context will run all 3 expressions in parallel
df.with_columns(
    get_ham("col_a"),
    get_bar("col_b"),
    get_foo("col_c"),
)
```