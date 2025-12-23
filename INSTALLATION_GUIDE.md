# Installation Guide for Tongyi CLI

## 🎉 **Successfully Installed Globally!**

Your Tongyi CLI is now installed and available globally on your system. You can call it from anywhere using either:

```bash
tongyi          # Short command
tongyi-cli       # Full command
```

## 📋 **Available Commands**

### **Global Usage**
```bash
# Show help
tongyi --help

# Start interactive mode
tongyi

# Ask a question directly
tongyi "What is this project?"

# Use specific model
tongyi "Explain this code" --model anthropic/claude-3.5-haiku

# Show available models
tongyi --models-info

# Show tools
tongyi --tools

# Specify project root
tongyi --root /path/to/project
```

### **Interactive Mode Commands**
Once in interactive mode, you can use:
```bash
> help                    # Show help
> models                  # Show current model
> models list             # List all models
> models set <model>      # Switch model
> models search coding    # Search models
> tools                   # Show tools
> history                 # Show history
> exit                    # Exit
```

## 🔧 **Installation Details**

### **What Was Installed:**
- ✅ **Package**: `tongyi-cli-interactive` (version 0.1.0)
- ✅ **Entry Points**: `tongyi` and `tongyi-cli`
- ✅ **Mode**: Editable installation (changes reflect immediately)
- ✅ **Dependencies**: All required packages installed

### **Installation Method:**
```bash
pip install -e .
```

This installed in **editable mode**, meaning any changes to the source code will be immediately reflected in the global installation.

### **Package Location:**
- **Source**: `C:\Users\prest\Desktop\Desktop_Projects\May-Dec-2025\Tongyi-Agent`
- **Installation**: Global Python environment
- **Commands**: Available from any directory

## 🚀 **Testing Your Installation**

### **1. Verify Commands Work:**
```bash
tongyi --help
tongyi-cli --help
```

### **2. Test Model Management:**
```bash
tongyi --models-info
```

### **3. Test Interactive Mode:**
```bash
tongyi
# Then try:
> models current
> models recommended
> exit
```

### **4. Test Direct Queries:**
```bash
tongyi "What is 2+2?" --model anthropic/claude-3.5-haiku
```

## 📝 **Configuration**

### **Environment Variables (Required):**
```bash
# OpenRouter API Key (required for functionality)
OPENROUTER_API_KEY=your-api-key-here

# Optional model overrides
CLAUDE_MODEL_NAME=anthropic/claude-3.5-sonnet
```

### **Create .env file:**
```bash
# In your project directory or home directory
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

## 🎯 **Available Models**

### **Quick Model Switching:**
```bash
# Set model for session
tongyi --model anthropic/claude-3.5-sonnet

# Or in interactive mode
tongyi
> models set anthropic/claude-3.5-haiku
```

### **Popular Models:**
- `anthropic/claude-3.5-sonnet` - Best overall (default)
- `anthropic/claude-3.5-haiku` - Fast & affordable
- `anthropic/claude-3-opus` - Complex reasoning
- `mistralai/codestral` - Code generation
- `qwen/qwen-72b-chat` - Budget-friendly

## 🔄 **Development Mode**

Since you installed in editable mode, any changes to the source files are immediately available:

1. **Make changes** to files in the project directory
2. **Test immediately** with `tongyi` command
3. **No reinstallation needed**

## 📁 **Project Structure**

```
Tongyi-Agent/
├── src/
│   ├── tongyi_agent/
│   │   └── cli.py              # Main CLI entry point
│   ├── claude_agent_orchestrator.py
│   ├── model_manager.py
│   └── ...
├── config.py                    # Configuration
├── pyproject.toml              # Package configuration
├── setup.py                    # Setup script
└── .env                        # Environment variables
```

## 🐛 **Troubleshooting**

**Need more help?** See [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) for comprehensive troubleshooting guide.

### **Command Not Found:**
```bash
# Check if pip installed in current Python environment
pip list | grep tongyi

# Try with python -m
python -m tongyi_agent.cli --help

# Reinstall if needed
pip install -e .
```

### **Import Errors:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify package installation
python -c "from tongyi_agent.cli import main; print('OK')"
```

### **Model Management Issues:**
```bash
# Test model manager directly
python -c "
from src.model_manager import model_manager
print('Available models:', len(model_manager.list_available_models()))
print('Current model:', model_manager.get_current_model())
"
```

### **Configuration Issues:**
```bash
# Validate your configuration
python -m config_validator --check-all

# Test API key and connectivity
python -m config_validator --check-openrouter

# Validate models.ini
python -m config_validator --check-models
```

## 🎉 **Success!**

Your Tongyi CLI is now:
- ✅ **Globally available** from any directory
- ✅ **Fully functional** with model management
- ✅ **Ready for testing** with all features
- ✅ **In development mode** for easy updates

**Start using it now:**
```bash
tongyi "Hello, world! What can you do?"
```

## 📚 **Next Steps**

1. **Set up your API key** in `.env` file
2. **Try different models** with `--model` flag
3. **Explore interactive mode** with `tongyi`
4. **Check out the model management** features
5. **Test with your own projects** using `--root` flag

## 🔧 **Common Issues**

### **"Command not found: tongyi"**

**Problem:** The `tongyi` command is not recognized.

**Solutions:**
```bash
# Try using python module instead
python -m tongyi_agent.cli --help

# Reinstall the package
pip install -e .

# Check if package is installed
pip list | grep tongyi
```

**More details:** See [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) - "Command Not Found" section

---

### **"OPENROUTER_API_KEY not set"**

**Problem:** API key is not configured.

**Solutions:**
```bash
# Create .env file in project root
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env

# Or export as environment variable
export OPENROUTER_API_KEY=sk-or-v1-your-key-here  # Linux/macOS
set OPENROUTER_API_KEY=sk-or-v1-your-key-here       # Windows cmd
```

**More details:** See [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) - "API Key Issues" section

---

### **"Import errors" or "Module not found"**

**Problem:** Python can't find the required modules.

**Solutions:**
```bash
# Reinstall from project root
cd /path/to/tongyi-agent
pip install -e .

# Install all dependencies
pip install -r requirements.txt

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"
```

---

### **"Connection timeout" or "Network errors"**

**Problem:** Cannot connect to OpenRouter API.

**Solutions:**
```bash
# Check internet connection
ping openrouter.ai

# Test connectivity
curl https://openrouter.ai/api/v1/models

# Check firewall/proxy settings
# Ensure HTTPS traffic to openrouter.ai is allowed
```

**More details:** See [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) - "Network Issues" section

---

### **"Model not available" errors**

**Problem:** The specified model cannot be found.

**Solutions:**
```bash
# List available models
tongyi --models-info

# Use a common model
tongyi "Your question" --model anthropic/claude-3.5-haiku

# Validate model configuration
python -m config_validator --check-models
```

---

### **Validation fails with "401 Unauthorized"**

**Problem:** API key is invalid or expired.

**Solutions:**
```bash
# Verify API key is correct
cat .env | grep OPENROUTER_API_KEY

# Test API key directly
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Generate a new key at https://openrouter.ai/keys
```

**More details:** See [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) - "Authentication Issues" section

---

### **Other Issues**

For more comprehensive troubleshooting:

1. **Run full validation:**
   ```bash
   python -m config_validator --check-all --verbose
   ```

2. **Check error logs:**
   ```bash
   cat error_log.md
   ```

3. **Consult full troubleshooting guide:**
   - [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md) - Complete troubleshooting guide
   - [CLI_GUIDE.md](CLI_GUIDE.md) - CLI-specific issues
   - [FAQ in README.md](README.md#faq) - Common user questions

4. **Get help:**
   - Check [README.md](README.md) - Main documentation
   - [QUICKSTART.md](QUICKSTART.md) - Quick start guide
   - [GitHub Issues](https://github.com/your-org/tongyi-agent/issues) - Report bugs

Happy coding with Tongyi CLI! 🚀