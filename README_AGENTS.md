# Using Documentation and Claude Agents in PhenoTag

This project uses the documentation and Claude agents from the `apps/jobelab/agents` directory. These agents provide integration with MCP context7 for documentation retrieval and Anthropic's Claude API for AI assistance.

## Quick Start

1. Make sure you have the required dependencies:
```bash
pip install anthropic requests
```

2. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

3. Run the example:
```bash
python -m ui.examples.using_agents
```

## Available Agents

The following agents are available for use in this project:

1. Documentation Agents:
   - DuckDB
   - Streamlit
   - Marimo
   - Polars
   - OpenCV

2. Claude Integration:
   - Ask questions with documentation context
   - Get code completion with documentation
   - Get code review with documentation

## Usage Examples

### Basic Usage

```python
from apps.jobelab.agents.cursor_claude_agent import CursorClaudeAgent

# Initialize the agent
agent = CursorClaudeAgent()

# Ask a question with documentation
response = agent.ask_with_docs(
    question="How do I create a sidebar in Streamlit?",
    library="streamlit",
    doc_query="How to create a sidebar?"
)
```

### Code Completion

```python
completion = agent.code_completion(
    code_context="import streamlit as st\n\nst.sidebar.",
    library="streamlit",
    doc_query="sidebar widgets"
)
```

### Code Review

```python
review = agent.code_review(
    code='''
import streamlit as st

def main():
    st.title("My App")
    st.sidebar.selectbox("Choose an option", ["A", "B", "C"])
    ''',
    library="streamlit",
    doc_query="best practices for sidebar"
)
```

## Configuration

The agents can be configured through environment variables:

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `MCP_CONTEXT7_URL`: URL of the MCP context7 server (default: http://localhost:8000)

Or through constructor parameters:

```python
agent = CursorClaudeAgent(
    api_key="your-api-key",  # Optional
    model="claude-3-sonnet-20240229",  # Optional
    context7_url="http://localhost:8000"  # Optional
)
```

## More Information

For more detailed information about the agents, including:
- Full API documentation
- Advanced usage examples
- Adding new libraries
- Contributing guidelines

Please see the main documentation in `apps/jobelab/agents/README.md`. 