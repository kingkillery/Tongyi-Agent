# Tongyi Agent

An agentic research assistant powered by Tongyi DeepResearch with sandbox execution, scholar integration, and data cleaning workhorse capabilities.

## Features

- **Tongyi DeepResearch Core**: Advanced reasoning via Alibaba's Tongyi DeepResearch model
- **Local-First Approach**: Searches project files first, external sources only when needed
- **Tool-Based Architecture**: Structured function calling for reliable, predictable behavior
- **Sandbox Execution**: Isolated Python code execution with resource caps and read-only project mounts
- **Scholar Integration**: Retrieve literature from Semantic Scholar, Crossref, arXiv, and OpenAlex with fallbacks
- **Data Cleaning Workhorse**: Clean CSV and markdown files safely in the sandbox
- **Verification Gate**: Ensure claims are backed by citations before inclusion

## Installation

### Prerequisites

1. Get an OpenRouter API key from https://openrouter.ai/keys
2. Create a `.env` file in the project root:
   ```
   OPENROUTER_API_KEY=your-api-key-here
   ```

### From source

```bash
git clone https://github.com/your-org/tongyi-agent.git
cd tongyi-agent
pip install -e .
```

### Using pip

```bash
pip install tongyi-agent
# Then create .env file with OPENROUTER_API_KEY
```

## Quick Start

### Command line

```bash
# Ask a question about the current directory
tongyi-agent "How does the sandbox enforce isolation?"

# Analyze a specific project folder
tongyi-agent "Summarize the delegation policy" --root /path/to/project

# Clean a CSV file
tongyi-agent "Please clean data.csv"

# Clean a markdown dump
tongyi-agent "Please clean daily_notes.md"

# Show available tools
tongyi-agent --tools
```

### Python API

```python
from src.tongyi_orchestrator import TongyiOrchestrator

orch = TongyiOrchestrator(root=".")
answer = orch.run("What does the verifier gate do?")
print(answer)
```

## Architecture

- **Tongyi DeepResearch**: Core reasoning engine that decides which tools to use
- **Tool Registry**: Structured tools with clear schemas:
  - `search_code`: Find code patterns in the project
  - `read_file`: Examine specific files
  - `run_sandbox`: Execute Python code safely
  - `search_papers`: Retrieve academic literature
  - `clean_csv`: Process and clean CSV files
  - `clean_markdown`: Structure and clean markdown files
- **Local-First Behavior**: System prompt instructs Tongyi to use local tools before external sources

## Configuration

Required environment variable:
```bash
OPENROUTER_API_KEY=your-openrouter-api-key
```

Optional:
```bash
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Lint and format:

```bash
ruff check src/
black src/
```

## Model Configuration

- **Model**: alibaba/tongyi-deepresearch-30b-a3b
- **Temperature**: 0.85 (balanced creativity)
- **Top P**: 0.95
- **Max Tokens**: 8192 (4K per tool call)
- **Context Length**: 131K

## License

MIT
