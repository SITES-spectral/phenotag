# DuckDB Basics

## Creating Connections

### Python

```python
import duckdb

# In-memory connection (default)
con = duckdb.connect()

# Persistent connection
con = duckdb.connect('mydatabase.db')
```

### Node.js

```javascript
const con = db.connect();

con.all('SELECT 42 AS fortytwo', function(err, res) {
  if (err) {
    console.warn(err);
    return;
  }
  console.log(res[0].fortytwo)
});
```

## Basic SQL Operations

### Basic SELECT

```sql
SELECT * FROM table_name;
```

### SELECT with Arithmetic

```sql
SELECT col1 + col2 AS res, sqrt(col1) AS root FROM table_name;
```

### Complete SELECT Syntax

```sql
SELECT ⟨select_list⟩
FROM ⟨tables⟩
    USING SAMPLE ⟨sample_expression⟩
WHERE ⟨condition⟩
GROUP BY ⟨groups⟩
HAVING ⟨group_filter⟩
    WINDOW ⟨window_expression⟩
    QUALIFY ⟨qualify_filter⟩
ORDER BY ⟨order_expression⟩
LIMIT ⟨n⟩;
```

### WHERE Clause with Operators

```sql
SELECT *
FROM table_name
WHERE id = 3 OR id = 7;
```

### ORDER BY and LIMIT

```sql
SELECT * FROM tbl ORDER BY i DESC LIMIT 3;
```

### JOIN Examples

```sql
-- Using LATERAL Join
SELECT *
FROM range(3) t(i), LATERAL (SELECT i + 1) t2(j);
```

## Creating Tables

### Basic Table Creation

```sql
CREATE TABLE t1 (id INTEGER PRIMARY KEY, j VARCHAR);
```

### Creating Tables from Existing Data

```sql
CREATE TABLE new_tbl AS
    SELECT * FROM read_parquet('input.parquet');
```

## Configuration

### Setting Memory Limit

```sql
SET memory_limit = '10GB';
```