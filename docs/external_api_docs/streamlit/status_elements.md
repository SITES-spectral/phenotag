# Streamlit Status Elements

This document provides comprehensive documentation on Streamlit's status elements, which help provide visual feedback about the state of your application.

## Table of Contents
- [Status Container](#status-container)
- [Progress Bar](#progress-bar)
- [Spinner](#spinner)
- [Success/Info/Warning/Error Messages](#successinfowarningerror-messages)
- [Exception Handling](#exception-handling)
- [Best Practices](#best-practices)

## Status Container

The `st.status` function creates a status container that can display an ongoing operation's status with expandable details.

### Basic Usage

```python
import streamlit as st
import time

with st.status("Processing data..."):
    # Simulate a long-running process
    time.sleep(2)
    st.write("Step 1: Data loading completed")
    time.sleep(1)
    st.write("Step 2: Data processing completed")
    time.sleep(1)
    st.write("Step 3: Analysis completed")
```

### Status States

The status container has three states: "running", "complete", and "error". You can update the state during execution:

```python
import streamlit as st
import time
import random

# Create a status container
with st.status("Running a complex workflow...") as status:
    # Stage 1
    st.write("Stage 1: Data acquisition")
    time.sleep(2)
    
    # Stage 2
    st.write("Stage 2: Data processing")
    time.sleep(2)
    
    # Simulate a possible error
    if random.random() < 0.3:  # 30% chance of error
        status.update(label="Error in workflow!", state="error")
        st.error("An error occurred during processing")
    else:
        # Successful completion
        status.update(label="Workflow complete!", state="complete")
        st.success("All stages completed successfully")
```

### Parameters

- `label`: The status message to display
- `expanded`: Whether to show the details by default (default is True)
- `state`: The initial state ("running", "complete", or "error") - defaults to "running"

```python
import streamlit as st
import time

# Create a status with initially hidden details
with st.status("Processing...", expanded=False) as status:
    # Some long process
    time.sleep(2)
    st.write("Details only shown when expanded")
    time.sleep(1)
    status.update(label="Done!", state="complete")
```

### Conditional Status Updates

You can conditionally update the status based on the execution result:

```python
import streamlit as st
import time
import numpy as np

# Create a function with potential for errors
def run_simulation(iterations):
    results = []
    with st.status("Running simulation...") as status:
        try:
            for i in range(iterations):
                # Simulate calculations that might fail
                if np.random.random() < 0.2 and i > 0:  # 20% chance of error after first iteration
                    raise ValueError(f"Simulation failed at iteration {i}")
                
                # Successful iteration
                value = np.random.normal(0, 1)
                results.append(value)
                st.write(f"Iteration {i+1}/{iterations}: {value:.4f}")
                time.sleep(0.5)
                
            # All iterations completed successfully
            status.update(label=f"Simulation completed with {iterations} iterations!", state="complete")
            return results
            
        except Exception as e:
            status.update(label=f"Simulation failed!", state="error")
            st.error(str(e))
            return results

# User input for number of iterations
iterations = st.slider("Number of iterations", 1, 20, 10)

if st.button("Run Simulation"):
    results = run_simulation(iterations)
    
    # Display results if available
    if results:
        st.subheader(f"Completed {len(results)} iterations")
        st.line_chart(results)
```

### Nested Status Containers

You can nest status containers to track sub-tasks:

```python
import streamlit as st
import time

# Main workflow
with st.status("Main workflow") as main_status:
    st.write("Starting main workflow...")
    time.sleep(1)
    
    # Subtask 1
    with st.status("Sub-task 1: Data processing") as sub1:
        st.write("Processing data...")
        time.sleep(2)
        sub1.update(label="Sub-task 1 complete", state="complete")
    
    # Subtask 2
    with st.status("Sub-task 2: Model training") as sub2:
        st.write("Training model...")
        time.sleep(3)
        sub2.update(label="Sub-task 2 complete", state="complete")
    
    # Complete main workflow
    main_status.update(label="Main workflow complete!", state="complete")
```

## Progress Bar

The `st.progress` function displays a progress bar that can be updated to show completion percentage.

### Basic Usage

```python
import streamlit as st
import time

progress_bar = st.progress(0)

for i in range(100):
    # Update progress bar
    progress_bar.progress(i + 1)
    time.sleep(0.05)

st.success('Done!')
```

### Simulating Long Operations

```python
import streamlit as st
import time
import numpy as np

# Function to simulate a long-running process
def process_data(num_steps):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(num_steps):
        # Simulate processing step
        time.sleep(0.1)
        current_progress = (i + 1) / num_steps
        
        # Update progress bar and status text
        progress_bar.progress(current_progress)
        status_text.text(f"Processing step {i+1}/{num_steps} ({current_progress*100:.1f}%)")
        
    # Clear the status text and show completion
    status_text.empty()
    return np.random.randn(num_steps)

# UI controls
num_steps = st.slider("Number of processing steps", 10, 100, 20)

if st.button("Start Processing"):
    result = process_data(num_steps)
    st.success("Processing complete!")
    st.line_chart(result)
```

### Dynamic Progress Updates

```python
import streamlit as st
import time
import numpy as np
import pandas as pd

# Function to simulate loading data with progress bar
def load_data_with_progress(rows, columns):
    data = pd.DataFrame()
    progress_bar = st.progress(0)
    
    # Create columns one by one with progress updates
    for i in range(columns):
        time.sleep(0.2)  # Simulate loading time
        data[f'Column {i+1}'] = np.random.randn(rows)
        
        # Update progress
        progress = (i + 1) / columns
        progress_bar.progress(progress)
        
    return data

# UI Controls
rows = st.number_input("Number of rows", 10, 1000, 100)
columns = st.number_input("Number of columns", 1, 20, 5)

if st.button("Generate Data"):
    data = load_data_with_progress(rows, columns)
    st.success(f"Generated DataFrame with {rows} rows and {columns} columns")
    st.dataframe(data.head())
```

## Spinner

The `st.spinner` function shows a temporary spinner while executing a block of code.

### Basic Usage

```python
import streamlit as st
import time

with st.spinner('Loading...'):
    time.sleep(3)
st.success('Done!')
```

### Spinner vs Progress Bar

Use a spinner when you can't measure the exact progress:

```python
import streamlit as st
import time
import requests

def fetch_data_from_api(url):
    with st.spinner(f"Fetching data from {url}..."):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return None

# URL input
url = st.text_input("API URL", "https://jsonplaceholder.typicode.com/todos/1")

if st.button("Fetch Data"):
    data = fetch_data_from_api(url)
    if data:
        st.success("Data fetched successfully!")
        st.json(data)
```

### Combining Spinner and Progress Bar

For a more detailed UX, combine spinner (for overall operation) with progress bar (for measurable sub-steps):

```python
import streamlit as st
import time
import numpy as np

def run_simulation():
    # Outer spinner for the overall process
    with st.spinner("Running simulation..."):
        # Initialize the data
        data = []
        
        # Progress bar for the individual steps
        progress_bar = st.progress(0)
        
        # Simulate 100 steps
        steps = 100
        for i in range(steps):
            # Simulate computation
            new_value = np.sin(i/5) + np.random.randn() * 0.1
            data.append(new_value)
            
            # Update progress
            progress_bar.progress((i + 1) / steps)
            time.sleep(0.05)
        
        return data

if st.button("Run Simulation"):
    data = run_simulation()
    st.success("Simulation complete!")
    st.line_chart(data)
```

## Success/Info/Warning/Error Messages

Streamlit provides several functions to display contextual messages:

- `st.success`: Display a success message
- `st.info`: Display an informational message
- `st.warning`: Display a warning message
- `st.error`: Display an error message

### Basic Usage

```python
import streamlit as st

st.success("Data processed successfully!")
st.info("This is a purely informational message")
st.warning("This action might cause issues")
st.error("An error has occurred!")
```

### Conditional Message Types

```python
import streamlit as st
import random

def simulate_operation():
    # Simulate an operation with different outcomes
    result = random.random()
    
    if result < 0.25:
        st.error("Operation failed: Critical error")
        return False
    elif result < 0.5:
        st.warning("Operation completed with warnings")
        return True
    elif result < 0.75:
        st.info("Operation completed successfully with notes")
        return True
    else:
        st.success("Operation completed successfully")
        return True

if st.button("Run Operation"):
    success = simulate_operation()
    st.write(f"Operation {'succeeded' if success else 'failed'}")
```

### Combining Messages with Other Elements

```python
import streamlit as st
import numpy as np
import pandas as pd

# Create a form for data input
with st.form("data_entry"):
    name = st.text_input("Name")
    age = st.number_input("Age", 0, 120, 30)
    email = st.text_input("Email")
    submitted = st.form_submit_button("Submit")

if submitted:
    # Validate inputs
    errors = []
    
    if not name:
        errors.append("Name is required")
    
    if not email:
        errors.append("Email is required")
    elif "@" not in email:
        errors.append("Email format is invalid")
    
    # Display errors if any
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Success case
        st.success("Form submitted successfully!")
        
        # Display submitted data
        st.info("Submitted Data")
        df = pd.DataFrame({
            "Field": ["Name", "Age", "Email"],
            "Value": [name, age, email]
        })
        st.table(df)
```

## Exception Handling

Streamlit allows you to handle exceptions gracefully with appropriate status elements.

### Basic Exception Handling

```python
import streamlit as st
import numpy as np
import pandas as pd

def process_file(file):
    try:
        # Attempt to read the file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            raise ValueError(f"Unsupported file format: {file.name}")
        
        # Return the processed data
        st.success(f"Successfully processed {file.name}")
        return df
    
    except pd.errors.EmptyDataError:
        st.error("The file is empty. Please upload a file with data.")
        return None
    
    except pd.errors.ParserError:
        st.error("Unable to parse the file. Please check the file format.")
        return None
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# File uploader
uploaded_file = st.file_uploader("Upload a data file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    data = process_file(uploaded_file)
    
    if data is not None:
        st.write("Data Preview:")
        st.dataframe(data.head())
        
        st.info(f"File Statistics: {len(data)} rows, {len(data.columns)} columns")
```

### Detailed Error Reporting

For debugging and more detailed error reporting:

```python
import streamlit as st
import traceback
import pandas as pd
import numpy as np

def run_analysis(data, analysis_type):
    try:
        if analysis_type == "Summary Statistics":
            result = data.describe()
            st.success("Summary statistics calculated successfully!")
            return result
        
        elif analysis_type == "Correlation Matrix":
            result = data.corr()
            st.success("Correlation matrix calculated successfully!")
            return result
        
        elif analysis_type == "Missing Values":
            result = pd.DataFrame({
                'Column': data.columns,
                'Missing Values': data.isnull().sum().values,
                'Percentage': 100 * data.isnull().sum().values / len(data)
            })
            st.success("Missing value analysis completed!")
            return result
        
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
            
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        
        # Display detailed error for debugging
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        
        return None

# Sample data
def generate_data():
    try:
        rows = st.slider("Number of rows", 10, 1000, 100)
        cols = st.slider("Number of columns", 2, 10, 5)
        
        # Generate data with some missing values
        data = pd.DataFrame(np.random.randn(rows, cols), 
                           columns=[f"Feature_{i+1}" for i in range(cols)])
        
        # Introduce some missing values
        for col in data.columns:
            mask = np.random.random(len(data)) < 0.1  # 10% missing values
            data.loc[mask, col] = np.nan
            
        return data
    
    except Exception as e:
        st.error(f"Error generating data: {str(e)}")
        
        # Display detailed error for debugging
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        
        return None

# Main app
st.title("Data Analysis with Error Handling")

# Generate data
data = generate_data()

if data is not None:
    st.write("Data Preview:")
    st.dataframe(data.head())
    
    # Analysis options
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Summary Statistics", "Correlation Matrix", "Missing Values", "Unknown Analysis"]
    )
    
    if st.button("Run Analysis"):
        with st.spinner(f"Running {analysis_type}..."):
            result = run_analysis(data, analysis_type)
            
            if result is not None:
                st.subheader("Analysis Result")
                st.dataframe(result)
```

## Best Practices

### 1. Choose the Right Status Element

Select the appropriate status element based on the type of operation:

```python
import streamlit as st
import time
import numpy as np

def demonstrate_status_elements():
    st.subheader("When to use different status elements")
    
    # 1. For operations with measurable progress
    st.write("1. Progress Bar: For operations with measurable progress")
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.01)
    
    # 2. For indeterminate operations
    st.write("2. Spinner: For operations where progress can't be measured")
    with st.spinner("Processing..."):
        time.sleep(2)
    
    # 3. For operations with detailed steps
    st.write("3. Status: For multi-step operations with detailed progress")
    with st.status("Running workflow...") as status:
        st.write("Step 1: Initialization")
        time.sleep(1)
        st.write("Step 2: Processing")
        time.sleep(1)
        status.update(label="Workflow complete!", state="complete")
    
    # 4. For quick feedback
    st.write("4. Success/Error messages: For quick feedback")
    st.success("Operation successful!")
    
demonstrate_status_elements()
```

### 2. Provide Appropriate Feedback

Give users the right amount of information:

```python
import streamlit as st
import time
import numpy as np

def analyze_data(dataset_size, analysis_type):
    with st.status(f"Analyzing {dataset_size} data points...") as status:
        # Simulate data loading
        st.write("Loading data...")
        progress = st.progress(0)
        for i in range(20):
            progress.progress((i + 1) / 20)
            time.sleep(0.1)
        
        # Simulate analysis
        st.write(f"Running {analysis_type} analysis...")
        progress = st.progress(0)
        for i in range(50):
            progress.progress((i + 1) / 50)
            time.sleep(0.05)
        
        # Simulate results processing
        st.write("Processing results...")
        progress = st.progress(0)
        for i in range(30):
            progress.progress((i + 1) / 30)
            time.sleep(0.05)
        
        # Complete the analysis
        status.update(label="Analysis complete!", state="complete")
        
        # Return fake results
        return {
            "mean": np.random.randn(),
            "std_dev": np.random.random() * 5,
            "min": np.random.randn() - 5,
            "max": np.random.randn() + 5,
        }

# UI
st.title("Data Analysis with Feedback")
dataset_size = st.slider("Dataset Size", 1000, 1000000, 10000)
analysis_type = st.selectbox("Analysis Type", ["Basic", "Advanced", "Comprehensive"])

if st.button("Run Analysis"):
    # Run the analysis
    results = analyze_data(dataset_size, analysis_type)
    
    # Display the results
    st.subheader("Analysis Results")
    st.metric("Mean", f"{results['mean']:.4f}")
    st.metric("Standard Deviation", f"{results['std_dev']:.4f}")
    st.metric("Minimum", f"{results['min']:.4f}")
    st.metric("Maximum", f"{results['max']:.4f}")
```

### 3. Estimate Realistic Timeframes

If possible, provide realistic timeframes for operations:

```python
import streamlit as st
import time
import numpy as np

def data_processing_with_timeframe(data_size):
    # Estimate processing time (simulate: 0.001s per data point)
    estimated_time = data_size * 0.001
    
    st.info(f"Estimated processing time: {estimated_time:.1f} seconds")
    
    with st.status(f"Processing {data_size} data points...") as status:
        start_time = time.time()
        
        # Simulate processing with progress updates
        progress = st.progress(0)
        processed = 0
        
        batch_size = max(1, data_size // 100)  # Process in batches
        
        while processed < data_size:
            # Process a batch
            time.sleep(batch_size * 0.001)  # Simulate work
            processed += batch_size
            
            # Update progress
            progress_pct = min(1.0, processed / data_size)
            progress.progress(progress_pct)
            
            # Update status periodically
            if processed % (data_size // 10) == 0 or processed == data_size:
                elapsed = time.time() - start_time
                remaining = (elapsed / progress_pct) - elapsed if progress_pct > 0 else 0
                status.update(label=f"Processing: {processed}/{data_size} ({progress_pct*100:.1f}%) - ETA: {remaining:.1f}s")
        
        # Complete
        elapsed = time.time() - start_time
        status.update(label=f"Processed {data_size} data points in {elapsed:.2f} seconds", state="complete")
        
        return np.random.randn(min(10, data_size))  # Return some sample data

# UI
st.title("Data Processing with Time Estimates")

data_size = st.slider("Data Size", 1000, 50000, 5000)

if st.button("Process Data"):
    result = data_processing_with_timeframe(data_size)
    
    st.success("Processing complete!")
    st.line_chart(result)
```

### 4. Handle Errors Gracefully

Provide helpful error messages and recovery options:

```python
import streamlit as st
import numpy as np
import pandas as pd
import time

def load_data(file_path):
    try:
        # Simulate file loading
        with st.status(f"Loading file: {file_path}") as status:
            # Check file extension
            if not (file_path.endswith('.csv') or file_path.endswith('.xlsx')):
                status.update(label=f"Invalid file format: {file_path}", state="error")
                return None
            
            # Simulate loading time
            time.sleep(2)
            st.write("Reading file...")
            
            # Simulate successful load
            status.update(label=f"File loaded successfully: {file_path}", state="complete")
            
            # Return dummy data
            return pd.DataFrame(np.random.randn(100, 5), columns=list('ABCDE'))
    
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def process_data(data):
    if data is None:
        st.error("No data to process. Please load a valid file first.")
        return None
    
    try:
        with st.status("Processing data...") as status:
            # Simulate processing steps
            st.write("Step 1: Cleaning data...")
            time.sleep(1)
            
            st.write("Step 2: Transforming data...")
            time.sleep(1)
            
            # Simulate a potential error
            operation = st.radio("Select operation", ["Safe Operation", "Risky Operation"])
            
            if operation == "Risky Operation" and np.random.random() < 0.7:  # 70% chance of error
                status.update(label="Error in data processing!", state="error")
                st.error("The risky operation failed! Try the safe operation instead.")
                return None
            
            st.write("Step 3: Finalizing...")
            time.sleep(1)
            
            # Complete successfully
            status.update(label="Data processed successfully!", state="complete")
            return data.describe()
    
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return None

# UI
st.title("Data Processing with Error Handling")

# File path input
file_path = st.text_input("File Path", "example.csv")

# Load data button
if st.button("Load Data"):
    data = load_data(file_path)
    
    if data is not None:
        st.session_state.data = data
        st.success("Data loaded successfully!")
        st.dataframe(data.head())
    else:
        st.warning("Please provide a valid file path (.csv or .xlsx)")

# Process data button (only if data is loaded)
if 'data' in st.session_state and st.button("Process Data"):
    result = process_data(st.session_state.data)
    
    if result is not None:
        st.subheader("Processing Results")
        st.dataframe(result)
```

### 5. Combine Status Elements for Complex Workflows

For complex workflows, combine different status elements:

```python
import streamlit as st
import time
import numpy as np
import pandas as pd

def complex_workflow():
    st.title("Complex Workflow Example")
    
    # Main status container for overall workflow
    with st.status("Running workflow...") as main_status:
        # Step 1: Data Generation
        st.write("Step 1: Generating data")
        
        with st.spinner("Generating random data..."):
            # Create progress bar for sub-task
            progress = st.progress(0)
            
            # Generate data in chunks
            chunks = 10
            data = []
            
            for i in range(chunks):
                # Simulate work
                time.sleep(0.2)
                
                # Add chunk of data
                chunk = np.random.randn(1000, 3)
                data.append(pd.DataFrame(chunk, columns=['A', 'B', 'C']))
                
                # Update progress
                progress.progress((i + 1) / chunks)
            
            # Combine chunks
            df = pd.concat(data, ignore_index=True)
            st.success(f"Generated dataset with {len(df)} rows")
        
        # Step 2: Data Processing
        st.write("Step 2: Processing data")
        
        # Create a new status for this step
        with st.status("Processing data...") as process_status:
            # Simulate multiple processing steps
            stages = ["Cleaning", "Normalizing", "Transforming", "Analyzing"]
            
            for i, stage in enumerate(stages):
                # Simulate processing
                st.write(f"Processing stage: {stage}")
                time.sleep(1)
                
                # Simulate possible error in the Normalizing stage
                if stage == "Normalizing" and np.random.random() < 0.3:  # 30% chance of error
                    process_status.update(label=f"Error in {stage} stage!", state="error")
                    main_status.update(label="Workflow failed at processing stage!", state="error")
                    st.error(f"An error occurred during the {stage} stage")
                    return None
            
            # Complete processing
            process_status.update(label="Data processing complete!", state="complete")
            
            # Show sample of processed data
            st.write("Processed data sample:")
            st.dataframe(df.head())
        
        # Step 3: Visualization
        st.write("Step 3: Creating visualizations")
        
        with st.spinner("Generating charts..."):
            # Create charts
            st.subheader("Data Visualization")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Chart 1: Line Chart")
                chart_data = df.iloc[:100, :].cumsum()
                st.line_chart(chart_data)
            
            with col2:
                st.write("Chart 2: Histogram")
                hist_data = pd.DataFrame({
                    'A': df['A'].sample(1000),
                    'B': df['B'].sample(1000),
                })
                st.bar_chart(hist_data)
            
            time.sleep(1)
        
        # Complete the workflow
        main_status.update(label="Workflow completed successfully!", state="complete")
        return df

# Run the workflow
if st.button("Start Workflow"):
    result = complex_workflow()
    
    if result is not None:
        st.balloons()
```

## Related Components

- **[Session State](session_state.md)**: State management across reruns
- **[Execution Flow](execution_flow.md)**: How Streamlit scripts execute
- **[Layout and Containers](layout_containers.md)**: Layout components for organizing UI elements