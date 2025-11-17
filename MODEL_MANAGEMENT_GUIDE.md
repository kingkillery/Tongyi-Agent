# Model Management Guide for Tongyi Agent

## Overview

Tongyi Agent now includes a comprehensive model management system that allows you to easily switch between different OpenRouter models, save preferences, and find the best model for your specific use case.

## 🎯 **Key Features**

### **Easy Model Switching**
- Switch between models without editing configuration files
- Persistent preferences saved automatically
- Support for 8+ popular OpenRouter models

### **Rich Model Information**
- Detailed model specifications (context length, pricing, capabilities)
- Capability-based filtering (coding, reasoning, fast, etc.)
- Smart suggestions for different use cases

### **Command-Line Interface**
- Interactive model management commands
- Non-interactive mode with `--model` flag
- Rich UI with tables and formatting

## 📋 **Available Models**

### **Claude Models**
| Model | Display Name | Context | Price/Mtok | Best For |
|-------|--------------|---------|------------|----------|
| `anthropic/claude-3.5-sonnet` | Claude 3.5 Sonnet | 200K | $3.0 | Overall excellence |
| `anthropic/claude-3.5-haiku` | Claude 3.5 Haiku | 200K | $0.8 | Fast & affordable |
| `anthropic/claude-3-opus` | Claude 3 Opus | 200K | $15.0 | Complex reasoning |
| `anthropic/claude-3-sonnet` | Claude 3 Sonnet | 200K | $3.0 | Balanced tasks |
| `anthropic/claude-3-haiku` | Claude 3 Haiku | 200K | $0.25 | Simple tasks |

### **Open Source Models**
| Model | Display Name | Context | Price/Mtok | Best For |
|-------|--------------|---------|------------|----------|
| `mistralai/mistral-large` | Mistral Large | 32K | $2.0 | Multilingual tasks |
| `mistralai/codestral` | Mistral Codestral | 32K | $1.0 | Code generation |
| `qwen/qwen-72b-chat` | Qwen-72B Chat | 32K | $0.9 | Budget-friendly |

## 🚀 **Usage Examples**

### **Interactive Mode**

```bash
# Start the CLI
python -m tongyi_agent.cli

# Show current model
> models

# List all available models
> models list

# Switch to a different model
> models set anthropic/claude-3.5-haiku

# Get model information
> models info anthropic/claude-3.5-haiku

# Search models by capability
> models search coding

# Get models with specific capability
> models capability reasoning

# Get model suggestion for use case
> models suggest fast
```

### **Non-Interactive Mode**

```bash
# Use specific model for one query
python -m tongyi_agent.cli "Explain this code" --model anthropic/claude-3.5-sonnet

# Set model for the session
python -m tongyi_agent.cli --model anthropic/claude-3.5-haiku

# Show available models
python -m tongyi_agent.cli --models-info
```

## 📖 **Command Reference**

### **Model Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `models` | Show current model | `models` |
| `models list` | List all available models | `models list` |
| `models recommended` | Show recommended models | `models recommended` |
| `models set <model>` | Switch to a model | `models set anthropic/claude-3.5-haiku` |
| `models info <model>` | Get model details | `models info anthropic/claude-3.5-sonnet` |
| `models search <query>` | Search models | `models search coding` |
| `models capability <cap>` | Filter by capability | `models capability reasoning` |
| `models suggest <usecase>` | Get suggestion | `models suggest fast` |

### **Command Line Arguments**

| Argument | Description | Example |
|----------|-------------|---------|
| `--model <name>` | Use specific model | `--model anthropic/claude-3.5-sonnet` |
| `--models-info` | Show model information | `--models-info` |
| `--help` | Show all commands | `--help` |

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required for OpenRouter API access
OPENROUTER_API_KEY=your-api-key-here

# Optional model overrides
CLAUDE_MODEL_NAME=anthropic/claude-3.5-sonnet
```

### **Preference Storage**
Model preferences are automatically saved to:
- **Location**: `~/.tongyi_agent_models.json`
- **Content**: Current model, last changed location, usage stats
- **Format**: JSON for easy editing and backup

### **Configuration Files**

**config.py** additions:
```python
class ClaudeConfig(BaseModel):
    model_name: str = OpenRouterModels.CLAUDE_35_SONNET.name
    model_preferences_file: str = "~/.tongyi_agent_models.json"
    save_model_choices: bool = True
```

## 🎯 **Model Selection Guide**

### **By Use Case**

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| **General Purpose** | `anthropic/claude-3.5-sonnet` | Best balance of capability and cost |
| **Fast/Cheap** | `anthropic/claude-3.5-haiku` | Fast responses, low cost |
| **Complex Reasoning** | `anthropic/claude-3-opus` | Highest reasoning capability |
| **Code Generation** | `mistralai/codestral` | Specialized for coding tasks |
| **Budget-Conscious** | `anthropic/claude-3-haiku` | Lowest cost option |
| **Multilingual** | `mistralai/mistral-large` | Strong language support |

### **By Capability**

| Capability | Models |
|------------|--------|
| **tool-calling** | All Claude 3.5/3 models |
| **coding** | Claude 3.5/3, Codestral, Qwen |
| **reasoning** | Claude 3 Opus, Claude 3.5 Sonnet |
| **fast** | Claude 3.5/3 Haiku models |
| **long-context** | All Claude models (200K) |
| **multilingual** | Mistral Large, Qwen |

## 🔄 **Model Switching Workflow**

1. **Interactive Mode**:
   ```bash
   > models list
   > models set anthropic/claude-3.5-haiku
   > models current  # Verify change
   ```

2. **One-Time Selection**:
   ```bash
   python -m tongyi_agent.cli "Your query" --model anthropic/claude-3.5-haiku
   ```

3. **Session Default**:
   ```bash
   python -m tongyi_agent.cli --model anthropic/claude-3.5-haiku
   # All subsequent queries use this model
   ```

## 💾 **Import/Export Preferences**

### **Export Preferences**
```python
from model_manager import model_manager
model_manager.export_preferences('my_models.json')
```

### **Import Preferences**
```python
from model_manager import model_manager
model_manager.import_preferences('my_models.json')
```

## 🛠️ **Advanced Usage**

### **Programmatic Model Management**
```python
from model_manager import model_manager

# Get current model
current = model_manager.get_current_model()

# Switch model
model_manager.set_model('anthropic/claude-3.5-haiku')

# Get models with capability
coding_models = model_manager.get_models_by_capability('coding')

# Get model suggestion
suggestion = model_manager.get_model_suggestion('fast')
```

### **Custom Configuration**
```python
from model_manager import ModelManager

# Custom preferences file
manager = ModelManager('~/custom_models.json')

# Initialize with specific model
manager.set_model('anthropic/claude-3-opus')
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Model not found**: Use `models list` to see available models
2. **API key errors**: Check `OPENROUTER_API_KEY` environment variable
3. **Preferences not saving**: Check file permissions for `~/.tongyi_agent_models.json`

### **Debug Commands**
```bash
# Check model manager availability
python -c "from src.model_manager import model_manager; print(model_manager.get_usage_stats())"

# Validate model name
python -c "from src.model_manager import model_manager; print(model_manager.validate_model('anthropic/claude-3.5-sonnet'))"
```

## 📊 **Performance Comparison**

| Model | Speed | Quality | Cost/Mtok | Context |
|-------|-------|---------|-----------|---------|
| Claude 3.5 Sonnet | Fast | Excellent | $3.0 | 200K |
| Claude 3.5 Haiku | Very Fast | Very Good | $0.8 | 200K |
| Claude 3 Opus | Medium | Outstanding | $15.0 | 200K |
| Mistral Large | Fast | Good | $2.0 | 32K |
| Codestral | Fast | Good (Code) | $1.0 | 32K |
| Qwen-72B | Medium | Good | $0.9 | 32K |

## 🎉 **Summary**

The model management system provides:

- ✅ **Easy Switching**: Simple commands to change models
- ✅ **Persistent Preferences**: Choices saved automatically
- ✅ **Rich Information**: Detailed specs and capabilities
- ✅ **Smart Suggestions**: Context-aware recommendations
- ✅ **Flexible Usage**: Interactive and programmatic access
- ✅ **Cost Awareness**: Pricing information for budget decisions

You can now easily optimize your Tongyi Agent experience by selecting the perfect model for each task!