# Tongyi Agent - First 5 Minutes

Get started with Tongyi Agent in under 5 minutes. This guide will take you from installation to your first AI-powered interaction.

---

## Minute 1: Installation

### Step 1: Get Your API Key

1. Visit https://openrouter.ai/keys
2. Sign up or log in
3. Generate a new API key
4. Copy your key (you'll need it in a moment)

### Step 2: Install Tongyi Agent

```bash
# Install from PyPI (easiest)
pip install tongyi-cli-interactive

# Or clone from source
git clone https://github.com/your-org/tongyi-agent.git
cd tongyi-agent
pip install -e .
```

### Step 3: Configure Your API Key

```bash
# Create .env file in your project directory
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

**✅ You're done with installation!**

---

## Minute 2: Verify Setup

### Step 1: Validate Your Configuration

```bash
# Run the configuration validator
python -m config_validator --check-all
```

You should see:
```
✓ models.ini found
✓ OPENROUTER_API_KEY set
✓ OpenRouter connection successful
✓ All checks passed!
```

**⚠️  If you see errors:** Check [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md)

### Step 2: Check Installation

```bash
# Verify Tongyi is installed
tongyi --help

# You should see help output with all available commands
```

**✅ Your installation is working!**

---

## Minute 3: Your First Question

### Step 1: Ask a Simple Question

```bash
# Ask a question about your current directory
tongyi "What files are in this directory?"
```

You'll see output like:
```
I'll examine the current directory structure for you...

Found: 12 files and 5 directories
- src/ (source code)
- tests/ (test files)
- docs/ (documentation)
...
```

### Step 2: Ask About Your Code

```bash
# Analyze a specific file
tongyi "Explain what src/cli.py does"
```

You'll get a detailed explanation of the CLI module.

**✅ You've successfully asked your first question!**

---

## Minute 4: Interactive Mode

### Step 1: Launch Interactive Mode

```bash
# Start the interactive CLI
tongyi
```

You'll see:
```
╔═══════════════════════════════════════╗
║         Tongyi Agent                  ║
║      Interactive Research Assistant  ║
╚═══════════════════════════════════════╝

Type 'help' for commands • Ctrl+C to exit

[Tongyi]>
```

### Step 2: Try Interactive Commands

Once in interactive mode, try these commands:

```bash
[Tongyi]> help              # Show available commands
[Tongyi]> tools             # List all available tools
[Tongyi]> status            # Show session statistics
```

### Step 3: Ask Questions Interactively

```bash
[Tongyi]> How does the sandbox work?
[Tongyi]> Find all Python files with errors
[Tongyi]> Explain the verifier gate
```

**✅ You're now in interactive mode!**

---

## Minute 5: Productive Use

### Step 1: Clean Data Files

```bash
# Clean a CSV file
tongyi "Please clean data.csv"

# Clean markdown
tongyi "Please clean notes.md"
```

### Step 2: Generate Code

```bash
# Generate test cases
tongyi "Generate pytest tests for src/cli.py"

# Write documentation
tongyi "Generate API docs for the orchestrator"
```

### Step 3: Search and Analyze

```bash
# Search for patterns
tongyi "Find where verification happens"

# Get code reviews
tongyi "Review src/sandbox_exec.py for security issues"
```

### Step 4: Use Different Models

```bash
# Use a faster model
tongyi "List all Python files" --model anthropic/claude-3.5-haiku

# Use a more capable model
tongyi "Explain this complex architecture" --model anthropic/claude-3.5-sonnet
```

**✅ You're productive in under 5 minutes!**

---

## Quick Reference

### Common Commands

| Command | Description |
|---------|-------------|
| `tongyi` | Start interactive mode |
| `tongyi "question"` | Ask a question (one-liner) |
| `tongyi --tools` | Show available tools |
| `tongyi --help` | Show help |
| `tongyi --models-info` | List available models |

### Interactive Mode Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `tools` | List all tools |
| `models` | Model management |
| `history` | Show conversation history |
| `status` | Show session stats |
| `clear` | Clear history |
| `exit` | Exit CLI |

### Available Tools

- `search_code` - Search code patterns
- `read_file` - Read and analyze files
- `run_sandbox` - Execute Python code safely
- `search_papers` - Search academic papers
- `clean_csv` - Clean CSV files
- `clean_markdown` - Clean markdown files

---

## Next Steps

### Learn More

- **[README.md](README.md)** - Full documentation with 10+ examples
- **[CLI_GUIDE.md](CLI_GUIDE.md)** - Complete CLI reference
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Detailed setup guide
- **[SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md)** - Troubleshooting help

### Try Advanced Features

```bash
# Use Python API
python examples/python_api_examples.py

# Use shell automation
bash examples/shell_automation.sh review src/cli.py

# VS Code integration
# See examples/vscode_integration.md
```

---

## Common Questions

### How do I switch models?

```bash
# In interactive mode
tongyi
> models set anthropic/claude-3.5-sonnet

# Or use flag
tongyi "Your question" --model anthropic/claude-3.5-haiku
```

### How do I clear conversation history?

```bash
# In interactive mode
tongyi
> clear

# Or delete history file
rm ~/.tongyi_agent_history.json
```

### How do I use this offline?

```bash
# Tongyi requires internet for API calls
# But it searches local files first (local-first approach)
tongyi "Analyze src/"  # Works on local files only
```

### How do I get more help?

```bash
# Configuration help
python -m config_validator --help

# CLI help
tongyi --help

# Interactive mode help
tongyi
> help
```

---

## Troubleshooting

### "OPENROUTER_API_KEY not set"

```bash
# Add to .env file
echo "OPENROUTER_API_KEY=your-key" > .env

# Or export environment variable
export OPENROUTER_API_KEY=your-key
```

### "Command not found: tongyi"

```bash
# Try with python module
python -m tongyi_agent.cli

# Or reinstall
pip install -e .
```

### Slow responses

```bash
# Use faster model
tongyi "Your question" --model anthropic/claude-3.5-haiku
```

---

## Tips for Success

1. **Start simple**: Ask basic questions first
2. **Use fast models**: Haiku for quick tasks, Sonnet/Opus for complex analysis
3. **Be specific**: More detailed questions get better answers
4. **Use tools**: Ask Tongyi to use specific tools (search_code, read_file, etc.)
5. **Iterate**: Follow up on answers with more questions
6. **Save results**: Pipe output to files for documentation

---

## Example Workflows

### Code Review Workflow

```bash
# 1. Analyze a file
tongyi "Review src/cli.py for issues"

# 2. Get suggestions
tongyi "Suggest improvements for src/cli.py"

# 3. Generate tests
tongyi "Generate tests for src/cli.py"

# 4. Get documentation
tongyi "Generate docs for src/cli.py"
```

### Research Workflow

```bash
# 1. Search code
tongyi "Find where verification happens"

# 2. Read files
tongyi "Read the verifier gate implementation"

# 3. Understand architecture
tongyi "Explain the overall architecture"

# 4. Generate documentation
tongyi "Create architecture diagram description"
```

### Data Cleaning Workflow

```bash
# 1. Clean CSV
tongyi "Please clean data.csv"

# 2. Analyze results
tongyi "Analyze the cleaned data.csv"

# 3. Generate insights
tongyi "What insights can we get from data.csv?"
```

---

## You're All Set! 🎉

You've completed the 5-minute quick start. You're now ready to:

- ✅ Ask questions about your codebase
- ✅ Analyze code for issues
- ✅ Generate documentation and tests
- ✅ Clean data files
- ✅ Search and understand code

**Explore further:**
- [README.md](README.md) for more examples
- [CLI_GUIDE.md](CLI_GUIDE.md) for advanced features
- [CONTRIBUTING.md](CONTRIBUTING.md) for contributing

Happy coding with Tongyi Agent! 🚀
