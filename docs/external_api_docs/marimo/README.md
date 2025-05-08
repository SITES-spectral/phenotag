# Marimo Documentation

This directory contains comprehensive documentation for Marimo, a reactive notebook for Python that combines the benefits of notebooks, scripts, and apps into a single tool.

## Overview

Marimo is a next-generation Python notebook designed for reproducibility, interactivity, and deployment. Unlike traditional notebooks, Marimo:

- Is **reactive**: cells automatically update when their dependencies change
- Provides **rich UI components**: create interactive interfaces easily
- Supports **script execution**: run notebooks as Python scripts
- Allows **application deployment**: share notebooks as web apps
- Integrates with **version control**: marimo files are clean Python scripts

## Documentation Contents

This documentation is organized into the following sections:

1. **[Basics](basics.md)** - Core concepts and getting started
   - Installation and setup
   - Creating and running notebooks
   - Cell execution model
   - Reactive programming model

2. **[UI Components](ui_components.md)** - Interactive UI elements
   - Inputs (sliders, buttons, dropdowns, etc.)
   - Containers and layouts
   - Data visualization components
   - Forms and validation

3. **[Reactivity](reactivity.md)** - Understanding Marimo's reactive execution
   - Cell dependencies
   - State management
   - Reactive patterns
   - Debugging reactive issues

4. **[Deployment](deployment.md)** - Sharing and deploying Marimo notebooks
   - Running notebooks as applications
   - Deployment options
   - Configuration and customization
   - Security considerations

## Getting Started

### Installation

```bash
# Install marimo
pip install marimo

# Install with recommended extras (SQL, AI, plotting)
pip install marimo[recommended]

# Or with conda
conda install -c conda-forge marimo
```

### Creating Your First Notebook

```bash
# Start the interactive tutorial
marimo tutorial intro

# Or create a new notebook
marimo edit my_notebook.py
```

### Basic Usage

```python
import marimo as mo

# Create UI elements
slider = mo.ui.slider(1, 10, value=5, label="Value")

# Display UI elements
slider

# Access values reactively
mo.md(f"The selected value is: {slider.value}")

# Create layouts
mo.hstack([
    mo.ui.text(label="Name"),
    mo.ui.button(label="Submit")
])
```

## Key Features

- **Reactive Execution**: Cells automatically re-execute when their dependencies change
- **Rich UI Components**: Built-in interactive elements that integrate seamlessly with Python
- **Clean Python Files**: Marimo notebooks are regular Python files, making them version control friendly
- **Flexible Deployment**: Run as scripts, notebooks, or web applications
- **AI Integration**: Create notebooks from natural language prompts with AI assistance
- **SQL Support**: Built-in SQL cell support for database interaction

## Additional Resources

For more information, visit the official Marimo resources:

- [Marimo Official Website](https://marimo.io)
- [Marimo Documentation](https://docs.marimo.io)
- [Marimo GitHub Repository](https://github.com/marimo-team/marimo)
- [Marimo Community on Discord](https://discord.gg/JE7nhX6mD8)

## Version Information

This documentation was updated for Marimo version 0.5.9 (as of May 2024).