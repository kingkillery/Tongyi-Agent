# Release Notes v0.1.0

## 🎉 First Release: tongyi-cli-interactive v0.1.0

### Overview
Tongyi CLI Interactive is a modern terminal interface for Tongyi Agent research assistant, featuring rich UI, session management, and comprehensive tool integration.

### ✨ Key Features

#### 🎨 Modern Interactive Interface
- **Rich Terminal UI**: Beautiful colored output, tables, and panels using Rich library
- **Markdown Rendering**: Automatic formatting for structured responses
- **Professional Design**: Clean, intuitive interface similar to modern CLI tools
- **Cross-Platform**: Works on Windows, macOS, and Linux with proper Unicode handling

#### 💾 Session Management
- **Persistent History**: Conversations automatically saved to `~/.tongyi_agent_history.json`
- **Context Awareness**: Recent conversations available for follow-up questions
- **Session Statistics**: Track duration, exchanges, and usage metrics
- **Graceful Cleanup**: Automatic history management and cleanup

#### ⚡ Interactive Commands
- `help` - Show available commands and usage
- `tools` - Display available tools with rich table formatting
- `history` - View recent conversation history
- `clear` - Clear conversation history
- `context` - Show recent conversation context
- `status` - Display session statistics and information
- `exit/quit/q` - Graceful exit

#### 🛠 Tool Integration
- **search_code**: Find code patterns in projects
- **read_file**: Examine specific files with context
- **run_sandbox**: Execute Python code safely
- **search_papers**: Retrieve academic literature
- **clean_csv**: Process and clean CSV files
- **clean_markdown**: Structure and clean markdown files
- **summarize_results**: Generate comprehensive summaries

#### 🔄 Backward Compatibility
- All existing CLI arguments preserved
- Non-interactive mode still supported
- Existing API and configuration unchanged

### 📦 Installation

#### From PyPI (Recommended)
```bash
pip install tongyi-cli-interactive
```

#### From Source
```bash
git clone https://github.com/your-org/tongyi-cli-interactive.git
cd tongyi-cli-interactive
pip install -e .
```

### 🚀 Quick Start

#### Interactive Mode
```bash
tongyi-cli
```

#### Command Line Usage
```bash
# Ask questions
tongyi-cli "What files are in this project?"

# Show tools
tongyi-cli --tools

# Non-interactive mode
tongyi-cli --no-interactive "Your question here"
```

### 🔧 Configuration

Required environment variable:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

### 🏗 Architecture

- **Core**: Tongyi DeepResearch model for advanced reasoning
- **CLI Layer**: Rich terminal interface with session management
- **Tool Registry**: Structured function calling system
- **Verification**: Source citation and claim validation
- **Local-First**: Prioritizes project files over external sources

### 📋 Requirements

- Python 3.11+
- OpenRouter API key
- Rich library (automatically installed)

### 🔒 Security & Privacy

- ✅ No private information in package
- ✅ API keys only from environment variables
- ✅ Local-first operation
- ✅ Sandboxed code execution
- ✅ No telemetry or data collection

### 🐛 Known Issues

- Windows console may need UTF-8 support for optimal emoji rendering
- Some dependency conflicts in complex environments (normal)

### 🗺 Roadmap

#### v0.2.0 (Planned)
- Configuration file support
- Plugin system for custom tools
- Enhanced error handling
- Performance optimizations

#### v0.3.0 (Planned)
- Multi-language support
- Theme customization
- Advanced search filters
- Integration with more data sources

### 🤝 Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

### 📄 License

MIT License - see LICENSE file for details.

### 🙏 Acknowledgments

- Tongyi DeepResearch team for the core model
- Rich library developers for beautiful terminal UI
- OpenRouter for API access
- All contributors and testers

---

## 📦 Package Contents

- `tongyi_agent/cli.py` - Main CLI interface
- `src/` - Core implementation files
- `schemas/` - JSON schemas for validation
- `README.md` - Main documentation
- `CLI_GUIDE.md` - Detailed CLI usage guide
- `LICENSE` - MIT license

## 🔗 Links

- **Homepage**: https://github.com/your-org/tongyi-cli-interactive
- **Documentation**: https://github.com/your-org/tongyi-cli-interactive/blob/main/CLI_GUIDE.md
- **Issues**: https://github.com/your-org/tongyi-cli-interactive/issues
- **PyPI**: https://pypi.org/project/tongyi-cli-interactive/
