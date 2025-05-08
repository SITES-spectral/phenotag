# Polars Expressions

## Basic Expressions

```python
import polars as pl

# Simple column selection
pl.col("column_name")

# Arithmetic operations
pl.col("weight") / (pl.col("height") ** 2)

# Literal values
pl.lit("fruits").alias("literal_string_fruits")
```

## Expression Expansion

```python
# Convert USD to EUR for all 'price' columns
df.with_columns(
    pl.col("^price_.*$").multiply(0.93).name.suffix("_eur")
)
```

## Conditional Operations

### When-Then-Otherwise

```python
# Collatz conjecture example
def collatz(n):
    return pl.when(n % 2 == 0).then(n / 2).otherwise(3 * n + 1)

# Apply the function 
df.with_column(
    pl.col("n").apply(lambda x: collatz(x)).alias("collatz_n")
)
```

## Aggregation

```python
# Basic aggregations
df.group_by("first_name").agg(
    pl.count(),
    pl.col("gender"),
    pl.col("last_name").first(),
).sort("count", descending=True).limit(5)
```

## Window Functions

```python
# Rank within groups
df_ranked = pokemon.select(
    pl.col("*"),
    pl.col("Speed").rank().over("Type 1").alias("Speed rank in type")
)

# Multiple window operations
pokemon.select(
    pl.all(),
    pl.col("Name").sort_by("Type 1").over("Type 1").head(3).alias("Type 1"),
    pl.col("Name").sort_by("Speed").over("Type 1").head(3).alias("fastest/group"),
    pl.col("Name").sort_by("Attack").over("Type 1").head(3).alias("strongest/group"),
    pl.col("Name").sort().over("Type 1").head(3).alias("sorted_by_alphabet")
)
```

## Missing Data Operations

### Identifying Missing Values

```python
# Create boolean mask of positions containing nulls
df.select(pl.col("a").is_null())

# Count nulls in all columns
df.null_count()

# Count nulls in one column
df["a"].null_count()
```

### Filling Missing Values

```python
# Use values from same column to fill nulls
df2.with_columns(
    forwards=pl.col("b").fill_null(strategy="forward"),
    backwards=pl.col("b").fill_null(strategy="backward"),
)
```

## Counting

```python
# Exact count of unique values
df.select(pl.col("a").n_unique())

# Approximate count (faster)
df.select(pl.col("a").approx_n_unique())
```

## Lists and Arrays

```python
# Explode lists into separate rows
df.select(
    pl.col("station"),
    pl.col("readings").explode()
)
```