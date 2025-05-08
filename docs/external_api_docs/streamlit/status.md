# Streamlit Status Component

The `st.status` component displays a status container that shows the output of long-running processes or external API calls. It provides visual feedback to users while operations are in progress.

## Basic Usage

```python
import streamlit as st
import time

with st.status("Running a complex operation...") as status:
    # Perform some operations
    time.sleep(2)
    st.write("Operation in progress...")
    time.sleep(2)
    
    # Update the status when complete
    status.update(label="Operation complete!", state="complete")
```

## Parameters

The `st.status` function accepts the following parameters:

- **label** (str): The initial status message to display.
- **expanded** (bool, optional): Whether to expand the status container by default to show the details. Defaults to `True`.
- **state** (str, optional): The initial state of the container. Can be one of "running", "complete", or "error". Defaults to "running".

## Status States

The status container can be in one of three states:

1. **running**: Indicates that the operation is in progress.
2. **complete**: Indicates that the operation has successfully completed.
3. **error**: Indicates that the operation has failed.

You can update the state during execution using the `update` method:

```python
status.update(label="New message", state="complete")
```

## Update Method

The status container provides an `update` method that allows you to change its label and state during execution. This method accepts the following parameters:

- **label** (str, optional): The new status message to display.
- **state** (str, optional): The new state of the container. Can be one of "running", "complete", or "error".

## Compatibility Notes

The `st.status` component was introduced in Streamlit 1.22.0 and had a major update in Streamlit 1.26.0. It may have issues in some Streamlit versions.

If you encounter issues with `st.status`, you can use the following alternatives:

1. **For progress indicators**:
   ```python
   progress_bar = st.progress(0)
   for i in range(100):
       progress_bar.progress(i + 1)
       time.sleep(0.05)
   ```

2. **For status messages**:
   ```python
   status_container = st.empty()
   status_container.text("Operation in progress...")
   # Perform operations
   status_container.success("Operation complete!")
   ```

3. **For spinners**:
   ```python
   with st.spinner("Operation in progress..."):
       # Perform operations
       time.sleep(2)
   st.success("Operation complete!")
   ```

## Best Practices

1. **Be descriptive**: Provide clear, concise status messages that inform users about what's happening.
2. **Update appropriately**: Update the status when significant stages of the operation are completed.
3. **Show progress**: For operations with measurable progress, consider using a progress bar inside the status container.
4. **Handle errors gracefully**: If an error occurs, update the status state to "error" and provide helpful information about the error.
5. **Don't nest status containers**: Avoid nesting status containers within each other, as this can lead to UI issues.

## Example: Multi-step Process

```python
import streamlit as st
import time

with st.status("Running multi-step process...") as status:
    # Step 1
    st.write("Step 1: Initializing...")
    time.sleep(1)
    
    # Step 2
    st.write("Step 2: Processing data...")
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.02)
    
    # Step 3
    st.write("Step 3: Finalizing...")
    time.sleep(1)
    
    # Complete
    status.update(label="Process completed successfully!", state="complete")
```

## Example: Error Handling

```python
import streamlit as st
import time
import random

with st.status("Processing data...") as status:
    st.write("Fetching data...")
    time.sleep(1)
    
    # Simulate a random error
    if random.random() < 0.3:
        status.update(label="Error: Could not process data", state="error")
        st.error("An unexpected error occurred during processing.")
    else:
        st.write("Analyzing data...")
        time.sleep(1)
        status.update(label="Data processed successfully!", state="complete")
```