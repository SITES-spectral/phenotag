# DuckDB Vector Similarity Search

DuckDB provides powerful vector similarity search capabilities through its Vector Similarity Search (VSS) extension. This document covers how to use these features for efficient vector operations, which are essential for machine learning, embeddings, and nearest neighbor search operations.

## Installation and Setup

### Installing the VSS Extension

```sql
-- Install and load the VSS extension
INSTALL vss;
LOAD vss;
```

### Updating the VSS Extension

```sql
-- Update to the latest version
UPDATE EXTENSIONS (vss);
```

## Creating Vector Tables

### Basic Vector Table Creation

```sql
-- Create a table with a FLOAT vector column of dimension 3
CREATE TABLE my_vector_table (vec FLOAT[3]);

-- Insert sample vector data
INSERT INTO my_vector_table
    SELECT array_value(a, b, c)
    FROM range(1, 10) ra(a), range(1, 10) rb(b), range(1, 10) rc(c);
```

### Creating Tables with Embeddings

```sql
-- Create example tables with random embeddings
CREATE TABLE items AS
    SELECT
        i AS id,
        [random(), random(), random()]::FLOAT[3] AS embedding
    FROM generate_series(1, 10_000) r(i);

CREATE TABLE queries AS
    SELECT
        i AS id,
        [random(), random(), random()]::FLOAT[3] AS embedding 
    FROM generate_series(1, 10_000) r(i);
```

## Creating HNSW Indexes

The HNSW (Hierarchical Navigable Small World) index dramatically speeds up vector similarity searches.

### Basic HNSW Index

```sql
-- Create an HNSW index on the vector column
CREATE INDEX my_hnsw_index ON my_vector_table USING HNSW (vec);
```

### HNSW Index with Custom Distance Metric

```sql
-- Create an HNSW index using cosine similarity instead of Euclidean distance
CREATE INDEX my_hnsw_cosine_index
ON my_vector_table
USING HNSW (vec)
WITH (metric = 'cosine');
```

## Vector Similarity Search Queries

### Basic Vector Similarity Search

```sql
-- Find the closest vectors to [1, 2, 3]
SELECT *
FROM my_vector_table
ORDER BY array_distance(vec, [1, 2, 3]::FLOAT[3])
LIMIT 3;
```

### Using min_by for Quick Nearest Neighbor Search

```sql
-- Find the single nearest neighbor using min_by
SELECT min_by(my_vector_table, array_distance(vec, [1, 2, 3]::FLOAT[3]), 1) AS result
FROM my_vector_table;
```

### Finding Top-K Similar Vectors

```sql
-- Find the top-3 vectors closest to [2, 2, 2]
SELECT
    arg_min(vecs, array_distance(vec, [2, 2, 2]::FLOAT[3]), 3)
FROM
    vecs;
```

### Verifying HNSW Index Usage

```sql
-- Explain the query plan to verify HNSW index usage
EXPLAIN
SELECT *
FROM my_vector_table
ORDER BY array_distance(vec, [1, 2, 3]::FLOAT[3])
LIMIT 3;
```

## Vector Similarity Joins

### Using vss_join

```sql
-- Create sample tables for vector join
CREATE TABLE haystack (id int, vec FLOAT[3]);
CREATE TABLE needle (search_vec FLOAT[3]);

-- Insert sample data
INSERT INTO haystack
    SELECT row_number() OVER (), array_value(a, b, c)
    FROM range(1, 10) ra(a), range(1, 10) rb(b), range(1, 10) rc(c);

INSERT INTO needle
    VALUES ([5, 5, 5]), ([1, 1, 1]);

-- Perform vector similarity join - find 3 closest matches for each needle
SELECT *
FROM vss_join(needle, haystack, search_vec, vec, 3) res;
```

### Using LATERAL Join for Vector Search

```sql
-- Collect the 5 closest items to each query embedding
SELECT queries.id AS id, list(inner_id) AS matches 
    FROM queries, LATERAL (
        SELECT
            items.id AS inner_id,
            array_distance(queries.embedding, items.embedding) AS dist
        FROM items 
        ORDER BY dist 
        LIMIT 5
    )
GROUP BY queries.id;
```

### Using vss_match

```sql
-- Alternative syntax using vss_match
SELECT *
FROM needle, vss_match(haystack, search_vec, vec, 3) res;
```

## Distance Functions

### Euclidean Distance (Default)

```sql
-- Calculate Euclidean distance between two vectors
SELECT array_distance(
    array_value(1.0::FLOAT, 2.0::FLOAT, 3.0::FLOAT), 
    array_value(2.0::FLOAT, 3.0::FLOAT, 4.0::FLOAT)
);
```

### Cosine Similarity

```sql
-- Calculate cosine similarity between two vectors
SELECT array_cosine_similarity(
    array_value(1.0::FLOAT, 2.0::FLOAT, 3.0::FLOAT), 
    array_value(2.0::FLOAT, 3.0::FLOAT, 4.0::FLOAT)
);
```

### Cosine Distance

```sql
-- Calculate cosine distance between two vectors
SELECT array_cosine_distance(
    array_value(1.0::FLOAT, 2.0::FLOAT, 3.0::FLOAT), 
    array_value(2.0::FLOAT, 3.0::FLOAT, 4.0::FLOAT)
);
```

## Python Integration for Vector Search

### Basic Vector Search in Python

```python
import duckdb
import numpy as np

# Create connection and load VSS extension
con = duckdb.connect()
con.execute("INSTALL vss; LOAD vss;")

# Create a table with vector data
con.execute("""
CREATE TABLE vectors AS
SELECT 
    row_number() OVER () AS id,
    [a, b, c]::FLOAT[3] AS vec
FROM 
    range(1, 4) AS x(a), 
    range(1, 4) AS y(b), 
    range(1, 4) AS z(c)
""")

# Create HNSW index
con.execute("CREATE INDEX hnsw_idx ON vectors USING HNSW (vec)")

# Perform vector similarity search
result = con.execute("""
SELECT * 
FROM vectors 
ORDER BY array_distance(vec, [2, 2, 2]::FLOAT[3]) 
LIMIT 3
""").fetchall()

print(result)
```

### Working with Embeddings from Libraries

```python
import duckdb
import numpy as np
from sentence_transformers import SentenceTransformer

# Load a pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create some text embeddings
texts = [
    "This is a sample sentence",
    "Another example text",
    "DuckDB is great for vector search"
]
embeddings = model.encode(texts)

# Create a table with the embeddings
con = duckdb.connect()
con.execute("INSTALL vss; LOAD vss;")

# Register the numpy array
con.execute("""
CREATE TABLE text_embeddings AS
SELECT * FROM (
    SELECT 
        unnest([1, 2, 3]) AS id,
        unnest(?) AS text,
        unnest(?) AS embedding
)
""", [texts, embeddings.tolist()])

# Create HNSW index
con.execute("""
CREATE INDEX hnsw_text_idx ON text_embeddings 
USING HNSW (embedding)
WITH (metric = 'cosine')
""")

# Search for similar embeddings
query = "Find text about database systems"
query_embedding = model.encode([query])[0]

result = con.execute("""
SELECT id, text, array_cosine_similarity(embedding, ?) AS similarity
FROM text_embeddings
ORDER BY similarity DESC
LIMIT 1
""", [query_embedding.tolist()]).fetchall()

print(result)
```

## Advanced Vector Operations

### Combining Filtering with Vector Search

```sql
-- Find similar vectors but only for a specific subset
SELECT *
FROM my_vector_table
WHERE category = 'electronics'  -- Apply filtering condition
ORDER BY array_distance(vec, [1, 2, 3]::FLOAT[3])
LIMIT 3;
```

### Generating Vector Embeddings Inside DuckDB

Using Python UDFs to generate embeddings:

```python
import duckdb
from sentence_transformers import SentenceTransformer
import numpy as np

# Create a model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Register a UDF for generating embeddings
def get_embedding(text):
    if text is None or text == '':
        return None
    return model.encode(text).tolist()

con = duckdb.connect()
con.create_function("text_to_embedding", get_embedding, ['VARCHAR'], 'FLOAT[]')

# Use the UDF in queries
con.execute("""
CREATE TABLE documents AS
SELECT 
    row_number() OVER () as id,
    unnest(['DuckDB is fast', 'Vector search is powerful', 'SQL is versatile']) as text,
    text_to_embedding(unnest(['DuckDB is fast', 'Vector search is powerful', 'SQL is versatile'])) as embedding
""")

# Now you can use these embeddings for similarity search
result = con.execute("""
SELECT id, text, array_cosine_similarity(embedding, text_to_embedding('How fast is DuckDB?')) as similarity
FROM documents
ORDER BY similarity DESC
""").fetchall()

print(result)
```

## Performance Optimization Tips

1. **Always use HNSW indexes** for large vector collections
2. **Choose the right distance metric** for your use case:
   - Euclidean distance: Default, good for general purpose
   - Cosine similarity: Better for text embeddings
3. **Limit the number of results** to improve performance
4. **Use the right data type** - FLOAT for most embeddings
5. **Pre-filter** your data when possible before applying vector search
6. **Batch your vector operations** for better throughput
7. **Set appropriate memory limits** for large vector operations:
   ```sql
   SET memory_limit = '16GB';
   ```