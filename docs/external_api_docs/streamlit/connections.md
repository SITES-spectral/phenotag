# Streamlit Connections

## Database Connections

### SQL Connection

```python
# Initialize connection
conn = st.connection("postgresql", type="sql")

# Perform query with caching
df = conn.query('SELECT * FROM mytable;', ttl="10m")

# Display results
for row in df.itertuples():
    st.write(f"{row.name} has a :{row.pet}:")
```

### Accessing Secrets

```python
# Access secrets from secrets.toml
key = st.secrets["OpenAI_key"]
```

### PostgreSQL Example

```python
# Initialize connection.
conn = st.connection("postgresql", type="sql")

# Perform query.
df = conn.query('SELECT * FROM mytable;', ttl="10m")

# Print results.
for row in df.itertuples():
    st.write(f"{row.name} has a :{row.pet}:")
```

## Authentication

```python
import streamlit as st

if not st.user.is_logged_in:
    st.button("Log in with Google", on_click=st.login, args=["google"])
    st.button("Log in with Microsoft", on_click=st.login, args=["microsoft"])
    st.stop()

st.button("Log out", on_click=st.logout)
st.markdown(f"Welcome! {st.user.name}")
```

### Microsoft Entra Authentication

```python
import streamlit as st

def login_screen():
    st.header("This app is private.")
    st.subheader("Please log in.")
    st.button("Log in with Microsoft", on_click=st.login)

if not st.user.is_logged_in:
    login_screen()
else:
    st.header(f"Welcome, {st.user.name}!")
    st.button("Log out", on_click=st.logout)
```

## Secrets Management

### secrets.toml

```toml
# .streamlit/secrets.toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "xxx"
client_id = "xxx"
client_secret = "xxx"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### Accessing Secrets

```python
st.secrets["OpenAI_key"] == "your OpenAI key"
"sally" in st.secrets.whitelist
st.secrets["database"]["user"] == "your username"
st.secrets.database.password == "your password"
```