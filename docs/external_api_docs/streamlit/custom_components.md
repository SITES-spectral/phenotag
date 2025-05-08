# Streamlit Custom Components

Custom components in Streamlit allow developers to extend the platform with reusable UI elements, interactive widgets, and integrations with other libraries. This document provides a comprehensive guide to working with custom components in Streamlit.

## Table of Contents

- [Introduction to Custom Components](#introduction-to-custom-components)
- [Using Built-in Component Tools](#using-built-in-component-tools)
  - [HTML Components](#html-components)
  - [IFrame Components](#iframe-components)
- [Creating Bi-directional Components](#creating-bi-directional-components)
  - [Component Architecture](#component-architecture)
  - [Declaring Components](#declaring-components)
  - [Component Communication](#component-communication)
  - [Theming Support](#theming-support)
- [Working with Component Templates](#working-with-component-templates)
  - [React Template](#react-template)
  - [TypeScript-only Template](#typescript-only-template)
- [Publishing Components](#publishing-components)
- [Using Third-Party Components](#using-third-party-components)
  - [Popular Components](#popular-components)
  - [Installation and Usage](#installation-and-usage)
- [Best Practices](#best-practices)

## Introduction to Custom Components

Streamlit custom components enable you to:
- Create reusable UI elements not available in core Streamlit
- Build bi-directional interfaces between Python and JavaScript
- Integrate third-party JavaScript libraries
- Extend Streamlit with domain-specific visualizations

## Using Built-in Component Tools

### HTML Components

The `html` function allows embedding raw HTML directly in your Streamlit app:

```python
import streamlit as st
import streamlit.components.v1 as components

# Simple HTML content
components.html("<p>Hello, world!</p>", height=100)

# More complex HTML with external resources
components.html(
    """
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js"></script>
    <div id="accordion">
      <div class="card">
        <div class="card-header" id="headingOne">
          <h5 class="mb-0">
            <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne">
            Collapsible Group Item #1
            </button>
          </h5>
        </div>
        <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
          <div class="card-body">
            Content for section #1
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header" id="headingTwo">
          <h5 class="mb-0">
            <button class="btn btn-link collapsed" data-toggle="collapse" data-target="#collapseTwo">
            Collapsible Group Item #2
            </button>
          </h5>
        </div>
        <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordion">
          <div class="card-body">
            Content for section #2
          </div>
        </div>
      </div>
    </div>
    """,
    height=600,
)
```

### IFrame Components

The `iframe` function allows embedding external web content in your Streamlit app:

```python
import streamlit as st
import streamlit.components.v1 as components

# Embed an external webpage
components.iframe("https://example.com", height=500)

# Embed a local HTML file
components.iframe("./local_page.html", height=500, scrolling=True)
```

## Creating Bi-directional Components

### Component Architecture

A bi-directional component consists of:
1. **Frontend**: JavaScript/TypeScript code that renders the UI
2. **Backend**: Python code that interacts with the component

### Declaring Components

Use `declare_component` to register your component with Streamlit:

```python
import streamlit.components.v1 as components

# Development mode (loads from a local dev server)
my_component = components.declare_component(
    "my_component",
    url="http://localhost:3001"  # URL where component is served
)

# Production mode (loads from a bundled directory)
# parent_dir = os.path.dirname(os.path.abspath(__file__))
# build_dir = os.path.join(parent_dir, "frontend/build")
# my_component = components.declare_component("my_component", path=build_dir)
```

### Component Communication

**Python to JavaScript:**

```python
# Send arguments from Python to the component
result = my_component(greeting="Hello", name="Streamlit")
```

**JavaScript to Python:**

```javascript
// In your React component
import { Streamlit } from "streamlit-component-lib"

// Send data back to Python
Streamlit.setComponentValue(3.14)
```

**Accessing arguments in JavaScript:**

```javascript
// Access arguments sent from Python
let greeting = this.props.args["greeting"]  // "Hello"
let name = this.props.args["name"]  // "Streamlit"
```

**Accessing component value in Python:**

```python
# Get the value returned from the component
result = my_component(greeting="Hello", name="Streamlit")
st.write("Value returned from component:", result)  # result = 3.14
```

### Theming Support

Components can access the current Streamlit theme through the `theme` object:

```javascript
// Theme object structure
{
  "base": "lightORdark",
  "primaryColor": "someColor1",
  "backgroundColor": "someColor2",
  "secondaryBackgroundColor": "someColor3",
  "textColor": "someColor4",
  "font": "someFont"
}
```

Using theme colors in CSS:

```css
.mySelector {
  color: var(--text-color);
}
```

## Working with Component Templates

### React Template

Starting with the React template:

```bash
# Initialize and install dependencies
cd template/my_component/frontend
npm install
npm run start  # Start the Webpack dev server
```

Run the example app:

```bash
cd template
. venv/bin/activate  # Activate your Python environment
pip install -e .  # Install the template as an editable package
streamlit run my_component/example.py  # Run the example
```

### TypeScript-only Template

For a lighter template without React:

```bash
# Initialize and install dependencies
cd template-reactless/my_component/frontend
npm install
npm run start  # Start the Webpack dev server
```

Run the example app:

```bash
cd template-reactless
. venv/bin/activate
pip install -e .
streamlit run my_component/example.py
```

## Publishing Components

1. Build the frontend:

```bash
cd frontend
npm run build
```

2. Update the component declaration to use the build path:

```python
import os
import streamlit.components.v1 as components

# Change from development mode to production mode
parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "frontend/build")
component = components.declare_component("new_component_name", path=build_dir)
```

3. Create a Python wheel:

```bash
# From your component's top-level directory
python setup.py sdist bdist_wheel
```

4. Publish to PyPI:

```bash
pip install twine
twine upload dist/*
```

## Using Third-Party Components

### Popular Components

1. **AgGrid** - Interactive data tables:

```bash
pip install streamlit-aggrid
```

```python
from st_aggrid import AgGrid
import pandas as pd

df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
AgGrid(df)
```

2. **Ace Editor** - Code editor:

```bash
pip install streamlit-ace
```

```python
from streamlit_ace import st_ace

content = st_ace()
st.write("Editor content:", content)
```

3. **Folium** - Interactive maps:

```bash
pip install streamlit-folium
```

```python
import folium
from streamlit_folium import st_folium

m = folium.Map(location=[39.949610, -75.150282], zoom_start=16)
folium.Marker([39.949610, -75.150282], popup="Liberty Bell").add_to(m)
st_data = st_folium(m, width=725)
```

4. **Custom Notification Box** - Enhanced notifications:

```bash
pip install streamlit-custom-notification-box
```

```python
from streamlit_custom_notification_box import custom_notification_box

styles = {
    'material-icons': {'color': 'red'}, 
    'text-icon-link-close-container': {'box-shadow': '#3896de 0px 4px'}, 
    'notification-text': {''}, 
    'close-button': {''}, 
    'link': {''}
}

custom_notification_box(
    icon='info', 
    textDisplay='We are almost done with your registration...', 
    externalLink='more info', 
    url='#', 
    styles=styles, 
    key="notification1"
)
```

5. **Authentication Components**:

```bash
pip install streamlit-authenticator
```

```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    config['credentials'], 
    config['cookie']['name'],
    config['cookie']['key'], 
    config['cookie']['expiry_days'], 
    config['preauthorized']
)

# Login users
name, authentication_status, username = authenticator.login('Login', 'main')
```

```bash
pip install streamlit-auth0-component
```

```python
from auth0_component import login_button

client_id = "your-client-id"
domain = "your-domain.auth0.com"
user_info = login_button(client_id, domain=domain)
st.write(user_info)
```

### Installation and Usage

Most third-party components follow a similar pattern:

1. Install via pip:
```bash
pip install streamlit-component-name
```

2. Import and use in your Streamlit app:
```python
from streamlit_component_name import component_function

result = component_function(arg1, arg2)
```

## Best Practices

1. **Performance**: Keep JavaScript dependencies lightweight to ensure fast loading times
2. **Reactivity**: Follow Streamlit's reactivity model by triggering reruns appropriately
3. **Error Handling**: Implement proper error handling in both Python and JavaScript
4. **Accessibility**: Ensure components are accessible to all users
5. **Documentation**: Provide clear documentation for your component's API and usage
6. **Theming**: Support Streamlit's theming system for consistent UI
7. **Session State**: Use Streamlit's session state appropriately with components
8. **Version Compatibility**: Test components with different Streamlit versions