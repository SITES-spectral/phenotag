# DuckDB File Operations

## Reading Files

### Reading CSV

```sql
-- Direct query
SELECT * FROM read_csv_auto('input.csv');
```

```python
# Python
import duckdb
duckdb.read_csv("example.csv")                # read a CSV file into a Relation
duckdb.sql("SELECT * FROM 'example.csv'")     # directly query a CSV file
```

### Reading Parquet

```sql
-- Direct query
SELECT * FROM 'test.parquet';
```

```python
# Python
import duckdb
duckdb.read_parquet("example.parquet")        # read a Parquet file into a Relation
duckdb.sql("SELECT * FROM 'example.parquet'") # directly query a Parquet file
```

### Reading Multiple Parquet Files

```sql
-- read all files that match the glob pattern
SELECT * FROM 'test/*.parquet';

-- read 3 parquet files and treat them as a single table
SELECT * FROM read_parquet(['file1.parquet', 'file2.parquet', 'file3.parquet']);

-- Read all parquet files from 2 specific folders
SELECT * FROM read_parquet(['folder1/*.parquet','folder2/*.parquet']);

-- read all parquet files that match the glob pattern at any depth
SELECT * FROM read_parquet('dir/**/*.parquet');
```

### Reading JSON

```sql
SELECT * FROM read_json_auto('test.json');
```

```python
# Python
import duckdb
duckdb.read_json("example.json")              # read a JSON file into a Relation
duckdb.sql("SELECT * FROM 'example.json'")    # directly query a JSON file
```

## Writing Files

### Writing to CSV

```sql
COPY (SELECT * FROM range(3) tbl(n)) TO 'output.csv';
```

### Writing to Parquet

```sql
COPY (SELECT l_orderkey, l_partkey FROM lineitem) TO 'lineitem.parquet' (COMPRESSION zstd);
```

### Writing to JSON

```sql
COPY (SELECT * FROM range(3) tbl(n) ) TO 'output.json';
```

## Importing Data

### Importing CSV

```sql
-- Create a table from CSV 
CREATE TABLE new_tbl AS SELECT * FROM read_csv_auto('input.csv');

-- Load data into existing table
COPY weather FROM '/home/user/weather.csv';
```

### Importing Parquet

```sql
-- Create a table from a Parquet file
CREATE TABLE new_tbl AS SELECT * FROM read_parquet('input.parquet');

-- Load data into existing table
COPY tbl FROM 'test.parquet';
```

### Importing JSON

```sql
COPY tbl FROM 'input.json';
```

## Database Export/Import

```sql
-- Export entire database
EXPORT DATABASE 'target_directory';
```