# Setup & Troubleshooting Guide

This guide helps you set up Tongyi Agent and resolve common configuration issues.

## Quick Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   - Get an OpenRouter API key from https://openrouter.ai/keys
   - Add to your `.env` file:
     ```
     OPENROUTER_API_KEY=sk-or-v1-your-key-here
     ```

3. **Validate Configuration**
   ```bash
   python -m config_validator --check-all
   ```

4. **Start the Agent**
   ```bash
   python -m src.tongyi_agent.cli
   ```

---

## Configuration Validation Tool

The `config_validator` tool helps diagnose setup issues. Run it before using the agent.

### Usage

```bash
# Basic validation (no network calls)
python -m config_validator

# Validate models.ini only
python -m config_validator --check-models

# Test OpenRouter connection and API key
python -m config_validator --check-openrouter

# Run all validations (including OpenRouter connectivity)
python -m config_validator --check-all

# Show detailed output
python -m config_validator --verbose

# Output JSON for automation
python -m config_validator --json
```

### Validation Checks

| Check | Description |
|-------|-------------|
| models.ini | Validates configuration file exists and has required sections |
| OPENROUTER_API_KEY | Checks if environment variable is set |
| OpenRouter connectivity | Tests connection to OpenRouter API |
| Model availability | Verifies configured models are available on OpenRouter |
| training_config.ini | Validates optional training configuration |

---

## Common Issues

### Issue: "OPENROUTER_API_KEY not set"

**Symptom:** Validation fails with API key error.

**Solution:**
```bash
# Create .env file in project root
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env

# Or export environment variable
export OPENROUTER_API_KEY=sk-or-v1-your-key-here  # Linux/macOS
set OPENROUTER_API_KEY=sk-or-v1-your-key-here     # Windows (cmd)
```

**Verification:**
```bash
python -m config_validator --check-openrouter
```

---

### Issue: "Missing models.ini"

**Symptom:** Validation reports missing models.ini file.

**Solution:**
```bash
# Check if models.ini exists in project root
ls models.ini

# If missing, copy from the repository
cp models.ini.example models.ini

# Or create manually:
cat > models.ini << EOF
[models]
primary = "alibaba/tongyi-deepresearch-30b-a3b"
fallback = "openai/gpt-3.5-turbo"
fallback_interval = 3

[openrouter]
base_url = "https://openrouter.ai/api/v1"
EOF
```

---

### Issue: "OpenRouter connectivity failed (401)"

**Symptom:** Authentication error when connecting to OpenRouter.

**Solution:**
1. Verify your API key is correct:
   ```bash
   # Check .env file
   cat .env | grep OPENROUTER_API_KEY
   ```

2. Ensure your key has the required permissions:
   - Visit https://openrouter.ai/keys
   - Check that your key is active and has access to models

3. Test the key directly:
   ```bash
   curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        https://openrouter.ai/api/v1/models
   ```

---

### Issue: "Model not available"

**Symptom:** Validation warns that a configured model is not found on OpenRouter.

**Solution:**
```bash
# List available models on OpenRouter
python -m src.tongyi_agent.cli --models-info

# Update models.ini with an available model
python -m config_validator --check-all  # Shows available models
```

**Common model names:**
- Primary: `alibaba/tongyi-deepresearch-30b-a3b`
- Fallback: `openai/gpt-3.5-turbo`, `anthropic/claude-3-haiku`

---

### Issue: Network/Connection Timeout

**Symptom:** Validation times out connecting to OpenRouter.

**Solution:**
1. Check internet connection:
   ```bash
   ping openrouter.ai
   ```

2. Verify firewall/proxy settings:
   - Ensure HTTPS traffic to `openrouter.ai` is allowed
   - Configure proxy if needed:
     ```bash
     export HTTP_PROXY=http://proxy.example.com:8080
     export HTTPS_PROXY=http://proxy.example.com:8080
     ```

3. Test connectivity:
   ```bash
   curl https://openrouter.ai/api/v1/models
   ```

---

### Issue: "Invalid base URL"

**Symptom:** Validation reports invalid OpenRouter base URL.

**Solution:**
```bash
# Verify models.ini [openrouter].base_url is correct
# Should be: https://openrouter.ai/api/v1

# Edit models.ini:
[openrouter]
base_url = "https://openrouter.ai/api/v1"
```

---

## Advanced Configuration

### Multiple API Keys

If you have multiple API keys for different environments:

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-primary-key
OPENROUTER_API_KEY_BACKUP=sk-or-v1-backup-key
```

### Custom OpenRouter Endpoint

If using a custom endpoint or proxy:

```ini
# models.ini
[openrouter]
base_url = "https://your-custom-endpoint.com/api/v1"
```

### Training Configuration (Optional)

For Agent Lightning features, configure `training_config.ini`:

```ini
[training]
mode = "prompt"  # Options: prompt, rl, sft
training_data_path = ".tongyi_training"
auto_save_interval = 10
```

---

## CLI Validation Integration

You can also validate configuration from the main CLI:

```bash
# Validate before starting
python -m src.tongyi_agent.cli --validate-config

# This runs full validation and exits
```

---

## Getting Help

If you're still having trouble:

1. Run validation with verbose output:
   ```bash
   python -m config_validator --check-all --verbose
   ```

2. Check the logs:
   ```bash
   # Check error log
   cat error_log.md

   # Check git status for uncommitted changes
   git status
   ```

3. Visit documentation:
   - [README.md](README.md) - Main project documentation
   - [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Detailed installation steps
   - [CLI_GUIDE.md](CLI_GUIDE.md) - CLI usage reference

4. Create an issue with:
   - Output of `python -m config_validator --check-all --verbose`
   - Your `models.ini` (redact API keys)
   - Your Python version: `python --version`
   - Your OS version

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python -m config_validator --check-all` | Full configuration check |
| `python -m config_validator --check-openrouter` | Test API key and connectivity |
| `python -m config_validator --check-models` | Validate models.ini |
| `python -m config_validator --verbose` | Show detailed output |
| `python -m src.tongyi_agent.cli --validate-config` | Validate from main CLI |
| `python -m src.tongyi_agent.cli --models-info` | List available models |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Yes |
| `MODEL_OVERRIDE` | Override model setting | Optional |
| `HTTP_PROXY` | Proxy for HTTP requests | Optional |
| `HTTPS_PROXY` | Proxy for HTTPS requests | Optional |

---

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| `models.ini` | Project root | Model configuration |
| `training_config.ini` | Project root | Training settings |
| `.env` | Project root | Environment variables |
| `.tongyi_training/` | Project root | Training data (if enabled) |
| `~/.tongyi_agent_history.json` | Home directory | Conversation history |

---

## Validation Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | All checks passed |
| 1 | Some checks failed (non-critical warnings) |
| 2 | Critical errors (missing files, invalid config) |
| 3 | Network/connection error |

Use in scripts:
```bash
python -m config_validator --check-all
if [ $? -eq 0 ]; then
    echo "Configuration valid, starting agent..."
    python -m src.tongyi_agent.cli
else
    echo "Configuration invalid, fix errors above."
fi
```

---

## Next Steps

Once validation passes:

1. Start the CLI: `python -m src.tongyi_agent.cli`
2. Type `help` to see available commands
3. Type `models` to manage model selection
4. Ask a question to start using the agent

For more information, see:
- [CLI_GUIDE.md](CLI_GUIDE.md) - Complete CLI reference
- [README.md](README.md) - Project overview
- [AGENTS.md](AGENTS.md) - Agent architecture
