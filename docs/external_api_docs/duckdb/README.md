# DuckDB Documentation

This directory contains comprehensive documentation for DuckDB, an in-process analytical database designed to be fast, efficient, and easy to use.

## Overview

DuckDB is an embeddable SQL OLAP database management system designed for analytical queries on local datasets. It provides a simple, feature-rich, and efficient SQL interface for data analysis.

Key features:
- In-process database (like SQLite) but optimized for analytical queries
- Column-oriented storage
- Vectorized execution engine
- Transactional support (ACID properties)
- Support for complex nested data types
- Zero external dependencies
- Multi-platform support (Linux, macOS, Windows)
- Integration with Python, R, Java, and more

## Documentation Contents

This documentation is organized into the following sections:

1. **[Basics](basics.md)** - Fundamental concepts, connection setup, and basic SQL operations
   - Creating connections
   - Basic SQL operations
   - Table creation
   - Configuration options

2. **[File Operations](file_operations.md)** - Working with various file formats
   - Reading and writing CSV files
   - Reading and writing Parquet files
   - Reading and writing JSON files
   - Database import/export

3. **[Python Integration](python_integration.md)** - Using DuckDB with Python
   - Basic usage
   - DataFrame integration
   - Result conversion
   - Prepared statements
   - Context managers

4. **[Data Types](data_types.md)** - Comprehensive guide to DuckDB data types
   - Primitive types (numeric, string, temporal)
   - Complex types (array, struct, map, union)
   - Nested data types
   - Type conversion
   - NULL handling

5. **[Vector Similarity Search](vector_similarity.md)** - Working with vector embeddings
   - Using the VSS extension
   - Creating HNSW indexes
   - Similarity search queries
   - Cosine, Euclidean, and other distance metrics
   - Python integration for vector search

6. **[Advanced Features](advanced_features.md)** - Advanced functionality for complex use cases
   - Window functions
   - User-defined functions (UDFs)
   - Lambda functions
   - Recursive CTEs
   - JSON processing
   - Spatial functions
   - Time series analysis
   - Machine learning integration
   - Extensions system

## Getting Started

If you're new to DuckDB, we recommend starting with the [Basics](basics.md) documentation to understand fundamental concepts. For those working with Python, the [Python Integration](python_integration.md) page provides essential information on using DuckDB with Python.

## Additional Resources

For more information, visit the official DuckDB resources:

- [DuckDB Official Website](https://duckdb.org/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckDB GitHub Repository](https://github.com/duckdb/duckdb)
- [DuckDB Extension Repository](https://github.com/duckdb/duckdb-extension-catalog)

## Version Information

This documentation was updated for DuckDB version 1.1 (as of May 2024).