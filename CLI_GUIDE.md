# Tongyi Agent Interactive CLI Guide

## Overview

Tongyi Agent now features a modern interactive CLI similar to Gemini CLI, Codex, or Claude Code. The enhanced interface provides:

- **Rich UI** with colored output and tables (when Rich library is available)
- **Session Management** with conversation history persistence
- **Interactive Commands** for help, tools, history, and status
- **Backward Compatibility** with existing non-interactive mode
- **Markdown Rendering** for formatted responses

## Installation

```bash
# Install dependencies (includes Rich for enhanced UI)
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Usage

### Interactive Mode (Default)

Simply run the CLI to start the interactive session:

```bash
python src/tongyi_agent/cli.py
# or if installed:
tongyi-agent
```

This will display a welcome banner and enter interactive mode where you can:
- Ask questions naturally
- Use special commands (see below)
- View conversation history
- Get real-time responses with formatted output

### Non-Interactive Mode

For scripting or one-off queries:

```bash
# Direct question
python src/tongyi_agent/cli.py "Your question here"

# Or use the flag
python src/tongyi_agent/cli.py --no-interactive "Your question here"
```

## Interactive Commands

While in interactive mode, you can use these special commands:

| Command | Description |
|---------|-------------|
| `help` or `?` | Show available commands and help |
| `tools` | List all available tools and their status |
| `history` | Show recent conversation history |
| `clear` | Clear conversation history |
| `context` | Show recent conversation context |
| `status` | Display session status and statistics |
| `exit`, `quit`, `q` | Exit the interactive agent |

### Command Line Options

| Option | Description |
|--------|-------------|
| `--root PATH` | Specify root directory to analyze (default: current directory) |
| `--tools` | Show available tools and exit |
| `--no-interactive` | Disable interactive mode |
| `--help` | Show help message |

## Features

### Rich UI (When Available)

When the Rich library is installed, the CLI provides:
- Colored text and syntax highlighting
- Tables for tool lists and status information
- Panels and borders for better visual organization
- Markdown rendering for formatted responses
- Progress indicators during processing

### Session Management

- **History Persistence**: Conversations are automatically saved to `~/.tongyi_agent_history.json`
- **Context Awareness**: Recent conversations are available as context for follow-up questions
- **Session Statistics**: Track session duration, number of exchanges, and more

### Fallback Mode

If Rich is not available, the CLI automatically falls back to a basic text interface while maintaining all functionality.

## Examples

### Starting Interactive Mode

```bash
$ python src/tongyi_agent/cli.py

╔═══════════════════════════════════════╗
║         Tongyi Agent                  ║
║      Interactive Research Assistant  ║
╚═══════════════════════════════════════╝

Type 'help' for commands • Ctrl+C to exit

[Tongyi]> help
```

### Using Commands

```bash
[Tongyi]> tools
┏━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name         ┃
┡━━━━━━━━━━━━━━━━━━━┩
│ search_code       │
│ read_file         │
│ run_sandbox       │
│ search_papers     │
│ clean_csv         │
│ clean_markdown    │
│ summarize_results │
└───────────────────┘

[Tongyi]> status
Session Status:
  Duration: 0:05:23
  Exchanges: 7
  History File: C:\Users\user\.tongyi_agent_history.json
  Rich UI: Enabled
```

### Natural Conversation

```bash
[Tongyi]> What files are in the src directory?
[Response]:
I'll search the src directory for you...
[Tool results displayed]

[Tongyi]> Can you read the main orchestrator file?
[Response]:
Reading the main orchestrator file...
[File contents displayed with syntax highlighting]
```

## Configuration

The CLI reads configuration from:
- Environment variables (for API keys, etc.)
- Project configuration files
- Command line arguments

### Environment Variables

```bash
export OPENROUTER_API_KEY="your-api-key"
export TONGYI_MODEL="alibaba/tongyi-deepresearch-30b-a3b"
```

## Troubleshooting

### Unicode Issues on Windows

If you encounter encoding issues, ensure your console supports UTF-8 or the CLI will automatically fall back to basic text mode.

### Missing Dependencies

```bash
# Install Rich for enhanced UI
pip install rich>=13.0

# Or install all dependencies
pip install -r requirements.txt
```

### History File Issues

The conversation history is stored in `~/.tongyi_agent_history.json`. If you experience issues:
- Delete the file to reset history
- Check file permissions
- Ensure sufficient disk space

## Development

To extend the CLI:

1. **Add new commands**: Modify `process_command()` in `cli.py`
2. **Enhance UI**: Add Rich components for better visualization
3. **Session features**: Extend the `Session` class for new persistence options
4. **Tool integration**: Register new tools in the orchestrator

## Comparison with Other CLIs

| Feature | Tongyi Agent | Gemini CLI | Claude Code |
|---------|--------------|------------|-------------|
| Interactive Mode | ✅ | ✅ | ✅ |
| Session History | ✅ | ✅ | ✅ |
| Rich UI | ✅ | ✅ | ✅ |
| Tool Integration | ✅ | Limited | ✅ |
| Local-First | ✅ | ❌ | ❌ |
| Open Source | ✅ | ❌ | ❌ |

Tongyi Agent provides a unique combination of local-first operation, extensive tool integration, and open-source flexibility.
