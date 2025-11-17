# Tongyi CLI Interactive

A modern interactive CLI for Tongyi Agent with rich terminal interface, session management, and tool integration.

## Features

- **🤖 Interactive CLI**: Modern terminal interface with rich UI, session management, and command system
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
pip install tongyi-cli-interactive
# Then create .env file with OPENROUTER_API_KEY
```

## Quick Start

### Interactive CLI (Recommended)

Start the interactive terminal session:

```bash
# Launch interactive mode
tongyi-cli

# Or run from source
python src/tongyi_agent/cli.py
```

Once in interactive mode, you can:
- Ask questions naturally
- Use commands like `help`, `tools`, `history`, `status`
- View conversation history and context
- Get rich, formatted responses

### Command line

```bash
# Ask a question about the current directory
tongyi-cli "How does the sandbox enforce isolation?"

# Analyze a specific project folder
tongyi-cli "Summarize the delegation policy" --root /path/to/project

# Clean a CSV file
tongyi-cli "Please clean data.csv"

# Clean a markdown dump
tongyi-cli "Please clean daily_notes.md"

# Show available tools
tongyi-cli --tools
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

## CLI Guide

For detailed information about the interactive CLI features, commands, and configuration, see [CLI_GUIDE.md](CLI_GUIDE.md).

---

## 📋 Project Status & Tracking

### ✅ Completed Features

#### Core Functionality
- **Tongyi Orchestrator**: Complete integration with OpenRouter API
- **Interactive CLI**: Rich terminal interface with session management
- **Tool-Based Architecture**: 7+ integrated tools (Read, Write, Bash, Grep, WebFetch, etc.)
- **Sandbox Execution**: Isolated Python code execution with resource limits
- **Scholar Integration**: Literature search across Semantic Scholar, arXiv, OpenAlex
- **Configuration Management**: Comprehensive INI-based configuration system
- **Session Management**: Conversation history and persistence

#### Advanced Features
- **Agent Lightning Integration**: Complete wrapper system with training capabilities
- **Claude Agent SDK Integration**: Async support with full tool integration
- **Security Features**: Path traversal protection, data sanitization, input validation
- **Performance Monitoring**: Training statistics and performance metrics
- **Export/Import**: Training data export with security controls
- **Multi-Model Support**: OpenRouter integration with model switching

#### Testing & Quality
- **Comprehensive Test Suite**: 117+ test cases across all modules
- **Security Tests**: Full path traversal and data sanitization testing
- **Integration Tests**: End-to-end workflow validation
- **Code Quality**: Proper error handling and logging

### 🚧 In Progress

#### Current Focus Areas
1. **Fixing Incomplete Implementations**: Core modules with `pass` statements
2. **Enhanced Error Handling**: User-friendly error messages and graceful fallbacks
3. **Configuration Validation**: Tool to validate setup and API connections
4. **Performance Optimizations**: Caching and async processing improvements

### 📅 Next Steps (Priority Order)

#### Phase 1: Critical Completion (1-2 weeks)
- [ ] **Complete Core Implementations**
  - [ ] Fix `pass` statements in `claude_agent_orchestrator.py` (lines 46, 57, 70)
  - [ ] Fix `pass` statement in `optimized_claude_agent.py` (line 380)
  - [ ] Fix `pass` statement in `optimized_tongyi_agent.py` (line 346)
  - [ ] Fix `pass` statement in `md_utils.py` (line 48)
  - [ ] Fix `pass` statement in `react_parser.py` (line 157)

- [ ] **Enhanced Error Handling**
  - [ ] Add user-friendly error messages for common failure scenarios
  - [ ] Implement graceful fallbacks for API unavailability
  - [ ] Add retry mechanisms for network failures
  - [ ] Improve input validation and error reporting

#### Phase 2: User Experience (2-3 weeks)
- [ ] **Configuration Validation Tool**
  - [ ] Build CLI tool to validate configuration files
  - [ ] Add API key validation and connection testing
  - [ ] Add model availability checking
  - [ ] Create setup troubleshooting guide

- [ ] **Documentation & Examples**
  - [ ] Create API documentation for developers
  - [ ] Add simple usage examples for beginners
  - [ ] Create integration examples with other tools
  - [ ] Write development setup guide for contributors

#### Phase 3: Performance & Features (3-4 weeks)
- [ ] **Performance Optimizations**
  - [ ] Implement caching mechanisms for repeated API calls
  - [ ] Add async processing for better concurrency
  - [ ] Optimize memory usage for large file processing
  - [ ] Improve response times through smarter tool selection

- [ ] **Testing Enhancements**
  - [ ] Add comprehensive integration tests
  - [ ] Implement performance and load testing
  - [ ] Add better mock tests for external dependencies
  - [ ] Create security tests for sandbox escapes

#### Phase 4: Advanced Features (Future)
- [ ] **Plugin System**: Framework for custom tool development
- [ ] **Web Interface**: Browser-based alternative to CLI
- [ ] **Analytics Dashboard**: Tool usage and performance monitoring
- [ ] **Advanced Security**: Enhanced sandbox protections

### 📊 Current Metrics

#### Code Quality
- **Test Coverage**: 117 test cases passing
- **Security Tests**: 8/8 security tests passing
- **Core Modules**: 15+ modules with proper error handling
- **Documentation**: 5 comprehensive guides

#### Known Issues
- **Incomplete Implementations**: 5 `pass` statements requiring completion
- **Unicode Handling**: Some Windows compatibility issues (partially fixed)
- **Error Messages**: Could be more user-friendly in some scenarios
- **Performance**: No caching mechanism currently implemented

### 🎯 Success Criteria

#### Short-term (1 month)
- [ ] All `pass` statements completed
- [ ] User-friendly error handling implemented
- [ ] Configuration validation tool available
- [ ] Basic performance optimizations in place

#### Medium-term (3 months)
- [ ] Plugin system foundation
- [ ] Comprehensive API documentation
- [ ] Performance monitoring dashboard
- [ ] Web interface prototype

#### Long-term (6 months)
- [ ] Full plugin ecosystem
- [ ] Advanced analytics and reporting
- [ ] Multi-user support
- [ ] Enterprise features

### 🔗 Related Documents

- [Agent Lightning Integration Summary](OPENROUTER_INTEGRATION_SUMMARY.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Model Management Guide](MODEL_MANAGEMENT_GUIDE.md)
- [Security Fixes Summary](SUBTLE_BUG_FIXES_SUMMARY.md)

---

*Last Updated: 2025-01-16*
