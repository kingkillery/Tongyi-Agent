# Release Notes v1.0.0-beta.1

**Release Date**: 2025-12-23
**Status**: Beta Release

---

## Overview

Tongyi CLI Interactive v1.0.0-beta.1 is a major beta release featuring a production-ready interactive CLI for deep research using Alibaba's Tongyi DeepResearch model via OpenRouter. This release delivers comprehensive functionality with 100% test pass rate (96/96 tests passing), enhanced error handling, performance optimizations, and complete documentation.

---

## What's New

### Major Features

#### 🎨 Modern Interactive CLI
- Rich terminal interface with colored output, tables, and panels using Rich library
- Markdown rendering for structured responses
- Professional design with clean, intuitive interface
- Cross-platform support (Windows, macOS, Linux) with proper Unicode handling

#### 💾 Session Management
- Persistent conversation history saved to `~/.tongyi_agent_history.json`
- Context awareness for follow-up questions
- Session statistics tracking (duration, exchanges, usage metrics)
- Graceful history management and cleanup

#### ⚡ Interactive Commands
- `help` - Show available commands and usage
- `tools` - Display available tools with rich table formatting
- `history` - View recent conversation history
- `clear` - Clear conversation history
- `context` - Show recent conversation context
- `status` - Display session statistics and performance metrics
- `exit/quit/q` - Graceful exit

#### 🛠 Tool Integration
- `search_code` - Find code patterns in projects
- `read_file` - Examine specific files with context
- `run_sandbox` - Execute Python code safely with resource caps
- `search_papers` - Retrieve academic literature from Semantic Scholar, Crossref, arXiv, OpenAlex
- `clean_csv` - Process and clean CSV files
- `clean_markdown` - Structure and clean markdown files
- `summarize_results` - Generate comprehensive summaries

#### 🏗 Model Management
- Model switching via CLI and interactive mode
- Model search and listing capabilities
- Configuration via `models.ini` file
- Support for all OpenRouter models

#### 🔧 Configuration Management
- INI-based configuration system (`models.ini`)
- API key validation and connection testing
- Environment variable support (`.env` file)
- Configuration validation CLI tool (`config_validator.py`)

#### 🔒 Security & Privacy
- Path traversal protection in file operations
- Data sanitization for exports
- Input validation with clear error messages
- Sandboxed code execution with resource limits
- No telemetry or data collection
- No private information in package

### Enhanced Error Handling (BETA-3)

#### Custom Exception Classes
- `TongyiAgentError` - Base exception for all Tongyi Agent errors
- `ConfigurationError` - Invalid or missing configuration
- `APIKeyError` - Invalid or missing API key
- `NetworkError` - Network operation failures
- `RateLimitError` - API rate limits exceeded
- `ModelNotFoundError` - Requested model not available
- `ValidationError` - User input validation failures
- `TimeoutError` - Operation timeouts

#### Retry Mechanisms
- Exponential backoff with random jitter
- Configurable retry count (default: 3 attempts)
- Maximum delay cap (default: 30 seconds)
- Selective retry for retryable error types
- Per-call override option

#### Graceful Fallbacks
- Automatic fallback on specified error types
- Callback notification when fallback is activated
- Detailed error reporting if both primary and fallback fail

#### User-Friendly Error Messages
- Clear, actionable error messages with troubleshooting steps
- Setup instructions for configuration issues
- Model availability suggestions
- Rate limit mitigation guidance

### Performance Optimizations (BETA-6)

#### Caching System
- In-memory caching with configurable TTL (10 min for API, 30 min for files)
- Optional file-based persistence
- Thread-safe operations using RLock
- Cache statistics tracking (hits, misses, hit rate, evictions)
- LRU-style eviction when cache reaches max size
- Cache directory: `~/.tongyi_cache`

#### Memory Optimizations
- File size checking for large files (>10MB warning)
- Streaming read option for line-by-line processing
- CSV chunked reading (10,000 rows per chunk)
- Efficient data type usage with pyarrow backend
- File snippet caching (<10KB)

#### Performance Metrics
- API call tracking (total, from cache)
- Response time measurements
- Tool usage statistics
- Memory warning counts
- Performance display in `status` command

### Agent Lightning Integration (Optional)
- Complete wrapper system for Agent Lightning
- Training capabilities with statistics tracking
- Graceful degradation when Agent Lightning not installed
- Security: path validation and data sanitization

### Claude Agent SDK Integration
- Async support with full tool integration
- Specific timeout handling for async operations
- Error handling for import/connection failures

---

## Bug Fixes

### BETA-1 Critical Fixes
- Fixed missing `STDIO_LIMIT` constant in sandbox_exec.py
- Implemented abstract `run()` method in ClaudeAgentOrchestrator
- Fixed API key validation test behavior
- Achieved 100% test pass rate (96/96 tests passing)

### Other Fixes
- Unicode handling issues on Windows CLI - replaced with ASCII equivalents
- Memory usage high for large files - added chunked processing
- Error messages not user-friendly - comprehensive error handling system

### Security Fixes
- Path traversal vulnerability in export - comprehensive validation added
- Data sanitization missing sensitive info - export now properly sanitizes data
- CLI emoji causing crashes on Windows - replaced with ASCII equivalents

---

## Installation

### Prerequisites

1. Get an OpenRouter API key from https://openrouter.ai/keys
2. Create a `.env` file in project root:
   ```
   OPENROUTER_API_KEY=your-api-key-here
   ```

### From PyPI (Recommended)

```bash
pip install tongyi-cli-interactive==1.0.0-beta.1
```

### From Source

```bash
git clone https://github.com/your-org/tongyi-agent.git
cd tongyi-agent
git checkout v1.0.0-beta.1
pip install -e .
```

### Validate Your Setup

After installation, verify your configuration:

```bash
# Run all validations including API connectivity
python -m config_validator --check-all

# For help with setup issues
# See SETUP_TROUBLESHOOTING.md
```

---

## Quick Start

### Interactive Mode (Recommended)

```bash
# Launch interactive mode
tongyi

# Or using full command name
tongyi-cli

# Once inside, you can ask questions:
> help                              # Show available commands
> What files are in src/?           # Ask about your codebase
> How does the sandbox work?        # Get explanations
> exit                              # Quit CLI
```

### Command Line Usage

```bash
# Ask a single question
tongyi "What does the orchestrator do?"

# Analyze a specific file
tongyi "Explain the verification gate in verifier_gate.py"

# Show available tools
tongyi --tools

# Use a specific model
tongyi "Explain this code" --model anthropic/claude-3.5-sonnet
```

### Python API Usage

```python
from tongyi_orchestrator import TongyiOrchestrator

orch = TongyiOrchestrator(root=".")

# Ask a question
answer = orch.run("What does the verifier gate do?")
print(answer)

# Use specific tools
answer = orch.run("Search for delegation policy")
print(answer)
```

---

## Configuration

### Required Environment Variables

```bash
OPENROUTER_API_KEY=your-openrouter-api-key
```

### Optional Configuration

```bash
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### models.ini Configuration

Create or edit `models.ini` in your project root:

```ini
[model]
default_model = anthropic/claude-3.5-haiku

[caching]
enabled = true
api_cache_ttl = 600
file_cache_ttl = 1800
max_cache_entries = 500
persistent_file_cache = true
cache_dir = ~/.tongyi_cache

[memory]
large_file_warning_threshold = 10485760
max_csv_sample_rows = 1000
```

---

## Known Issues

### Current Limitations
1. Windows console may need UTF-8 support for optimal emoji rendering
2. Tool calls are not cached (stateful operations)
3. Cache invalidation is time-based only (TTL)
4. No manual cache invalidation for specific entries

### Future Enhancements
1. Smart cache invalidation based on file changes
2. Metrics persistence between sessions
3. Adaptive TTL based on hit/miss patterns
4. Memory profiling to track actual memory usage
5. Cache compression for large cached values

---

## Breaking Changes

### From v0.1.0-alpha

1. **Package name changed**: Package name is now `tongyi-cli-interactive` (was `tongyi-agent`)
2. **Version format**: Following semantic versioning with beta releases
3. **Python version**: Minimum Python version increased to 3.11

### Migration Notes

If you were using v0.1.0-alpha:

```bash
# Uninstall old version
pip uninstall tongyi-agent

# Install new version
pip install tongyi-cli-interactive==1.0.0-beta.1

# Update your .env file (no changes needed)
# Update imports in your code:
# OLD: from tongyi_agent import TongyiOrchestrator
# NEW: from tongyi_orchestrator import TongyiOrchestrator
```

---

## Documentation

### Available Documentation

- [README.md](README.md) - Main documentation and features overview
- [CLI_GUIDE.md](CLI_GUIDE.md) - Complete CLI reference
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Installation and setup
- [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) - Troubleshooting guide
- [QUICKSTART.md](QUICKSTART.md) - 5-minute getting started guide
- [MODEL_MANAGEMENT_GUIDE.md](MODEL_MANAGEMENT_GUIDE.md) - Model configuration
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development and contribution guide

---

## Testing

### Test Coverage

- **Total Tests**: 96
- **Pass Rate**: 100% (96/96 passing)
- **Security Tests**: 8/8 passing
- **Integration Tests**: All passing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_file_read.py
```

---

## Requirements

### Python
- Python 3.11 or higher
- Python 3.12+ recommended

### Dependencies

Core dependencies:
- `pydantic>=2.0` - Data validation
- `requests>=2.28` - HTTP requests
- `pandas>=2.0` - Data processing
- `markdown>=3.5` - Markdown parsing
- `PyYAML>=6.0` - YAML config
- `rich>=13.0` - Terminal UI
- `python-dotenv>=1.0.0` - Environment variables
- `aiohttp>=3.8.0` - Async HTTP
- `click>=8.0.0` - CLI framework
- `tabulate>=0.9.0` - Table formatting
- `colorama>=0.4.0` - Colors

Optional dependencies:
- `claude-agent-sdk>=0.1.0` - Claude SDK integration
- `nest-asyncio>=1.5.0` - Async support

Development dependencies:
- `pytest>=8.0` - Testing
- `pytest-cov>=4.0` - Coverage
- `black>=23.0` - Formatting
- `ruff>=0.1` - Linting

---

## Model Configuration

### Recommended Models

| Model | Best For | Speed | Cost | Notes |
|-------|-----------|-------|------|-------|
| anthropic/claude-3.5-haiku | Quick tasks | Fast | Low | Default |
| anthropic/claude-3.5-sonnet | General use | Medium | Medium | Balanced |
| anthropic/claude-3-opus | Complex reasoning | Slow | High | Most capable |
| gpt-4o | General use | Medium | Medium | Good alternative |

### Default Model Settings

- **Model**: alibaba/tongyi-deepresearch-30b-a3b
- **Temperature**: 0.85 (balanced creativity)
- **Top P**: 0.95
- **Max Tokens**: 8192 (4K per tool call)
- **Context Length**: 131K

---

## Roadmap

### v1.1.0-beta (Planned: 2026-01-30)
- Plugin system foundation
- Web interface prototype
- Advanced caching features
- Comprehensive API documentation

### v2.0.0 (Planned: Future)
- Full plugin ecosystem
- Multi-user support
- Enterprise features
- Advanced analytics dashboard

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

```bash
# Clone repository
git clone https://github.com/your-org/tongyi-agent.git
cd tongyi-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Make changes and create pull request
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Tongyi DeepResearch Team** - Core model and research
- **OpenRouter** - API access and model hosting
- **Rich Library** - Beautiful terminal UI
- **Anthropic** - Claude SDK and models
- **All Contributors** - Bug reports, feature requests, and code contributions

---

## Support

### Getting Help

1. **Documentation**: Check available docs (see [Documentation](#documentation) section)
2. **FAQ**: See FAQ section in [README.md](README.md)
3. **Configuration Validation**: Run `python -m config_validator --check-all`
4. **Error Logs**: Check `error_log.md`
5. **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/tongyi-agent/issues)

### Reporting Issues

When reporting issues, please include:
- Your Python version: `python --version`
- Your OS version
- The command you ran
- Full error message or unexpected behavior
- Steps to reproduce the issue

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

*Last Updated: 2025-12-23*
