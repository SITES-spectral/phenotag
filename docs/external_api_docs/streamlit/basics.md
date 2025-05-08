# Streamlit Basics

## Importing Streamlit

```python
import streamlit as st
```

## Page Configuration

```python
st.set_page_config(
    page_title="My App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

## Basic Elements

### Display Text

```python
st.title("Title")
st.header("Header")
st.subheader("Subheader")
st.write("Text or variable")
st.markdown("**Markdown** content")
```

### Display Data

```python
st.dataframe(my_dataframe)
st.table(data.iloc[0:10])
st.json({"foo":"bar","fu":"ba"})
st.metric("My metric", 42, 2)
```

### Display Media

```python
st.image("image.jpg")
st.audio("audio.wav")
st.video("video.mp4")
```

## Layout

### Sidebar

```python
with st.sidebar:
    st.[element_name]
```

### Columns

```python
col1, col2 = st.columns(2)
with col1:
    st.write("This is column 1")
with col2:
    st.write("This is column 2")
```