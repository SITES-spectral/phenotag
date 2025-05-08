# Streamlit Version Compatibility

This document details the compatibility of various Streamlit features across different versions. Use this as a reference when developing the PhenoTag application to ensure compatibility.

## Current Version

The current version of Streamlit used in this project is **1.45.0**.

## Feature Compatibility

### Status Elements

| Feature | Introduced | Notes |
|---------|------------|-------|
| `st.status` | 1.32.0 | Status container for long-running processes. May have issues in 1.45.0. |
| `st.spinner` | Early version | Safe to use in all versions. |
| `st.progress` | Early version | Safe to use in all versions. |
| `st.success` | Early version | Safe to use in all versions. |
| `st.info` | Early version | Safe to use in all versions. |
| `st.warning` | Early version | Safe to use in all versions. |
| `st.error` | Early version | Safe to use in all versions. |

### Layout Components

| Feature | Introduced | Notes |
|---------|------------|-------|
| `st.columns` | Early version | Safe to use in all versions. |
| `st.expander` | Early version | Safe to use in all versions. |
| `st.tabs` | 1.12.0 | Safe to use in version 1.45.0. |
| `st.container` | Early version | Safe to use in all versions. |

### Data Display

| Feature | Introduced | Notes |
|---------|------------|-------|
| `st.dataframe` | Early version | Safe to use in all versions. |
| `st.data_editor` | 1.20.0 | Available but `on_selection_change` callback not supported in version 1.45.0. |
| `st.json` | Early version | Safe to use in all versions. |
| `st.metric` | 1.0.0 | Safe to use in version 1.45.0. |

### Interactive Widgets

| Feature | Introduced | Notes |
|---------|------------|-------|
| `st.button` | Early version | Safe to use in all versions. |
| `st.checkbox` | Early version | Safe to use in all versions. |
| `st.selectbox` | Early version | Safe to use in all versions. |
| `st.multiselect` | Early version | Safe to use in all versions. |
| `st.slider` | Early version | Safe to use in all versions. |
| `st.text_input` | Early version | Safe to use in all versions. |
| `st.file_uploader` | Early version | Safe to use in all versions. |

### Media Elements

| Feature | Introduced | Notes |
|---------|------------|-------|
| `st.image` | Early version | Safe to use in all versions. |
| `st.video` | Early version | Safe to use in all versions. |
| `st.audio` | Early version | Safe to use in all versions. |

### State Management

| Feature | Introduced | Notes |
|---------|------------|-------|
| `st.session_state` | 0.84.0 | Safe to use in version 1.45.0. |
| `st.cache_data` | 1.18.0 | Safe to use in version 1.45.0. |
| `st.cache_resource` | 1.18.0 | Safe to use in version 1.45.0. |

## Workarounds for Version Limitations

### Status Container Alternative

If `st.status` is causing issues, use a combination of these alternatives:

1. Use `st.spinner()` for indicating ongoing operations
2. Use `st.progress()` for operations with measurable progress
3. Use `st.success()`, `st.error()`, etc. for completion states

Example:
```python
# Instead of:
with st.status("Processing...") as status:
    # Do work
    status.update(label="Complete!", state="complete")

# Use:
with st.spinner("Processing..."):
    # Do work
    # (optional progress bar if applicable)
    progress_bar = st.progress(0)
    for i in range(100):
        # Do incremental work
        progress_bar.progress(i + 1)
    st.success("Complete!")
```

## Updating Streamlit

To update Streamlit to a specific version (if needed):

```bash
pip install streamlit==X.Y.Z
```

Where X.Y.Z is the desired version number. However, check for compatibility with other dependencies before updating.