# Streamlit Widgets

## Input Widgets

### Buttons

```python
if st.button("Click me"):
    st.write("Button clicked!")
```

### Checkboxes

```python
if st.checkbox("Show data"):
    st.dataframe(data)
```

### Selectors

```python
option = st.selectbox("Pick an option", ["Option 1", "Option 2", "Option 3"])
options = st.multiselect("Select multiple", ["Option 1", "Option 2", "Option 3"])
```

### Sliders

```python
number = st.slider("Select a number", 0, 100, 50)
size = st.select_slider("Pick a size", ["S", "M", "L"])
```

### Text Inputs

```python
text = st.text_input("Enter some text")
area = st.text_area("Enter multiple lines")
```

### File Uploads

```python
uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    # Process the file
```

### Date and Time

```python
date = st.date_input("Select a date")
time = st.time_input("Select a time")
```

### Color Picker

```python
color = st.color_picker("Pick a color")
```

## Advanced Widgets

### Data Editor

```python
edited = st.data_editor(df, num_rows="dynamic")
```

### Chat Input

```python
prompt = st.chat_input("Say something")
if prompt:
    st.write(f"The user has sent: {prompt}")
```

### Camera Input

```python
image = st.camera_input("Take a picture")
```

### Download Button

```python
st.download_button("Download file", data, file_name="file.csv")
```

## Chat Interface

```python
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    response = f"Echo: {prompt}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
```