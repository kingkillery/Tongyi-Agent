---
name: Configuration/Setup Issue
about: Report problems with installation, setup, or configuration
title: '[CONFIG] '
labels: 'configuration'
assignees: ''
---

## Issue Type

- [ ] Installation problem
- [ ] Configuration problem
- [ ] API key issue
- [ ] Model access issue
- [ ] Environment setup issue
- [ ] Other: ___________

## Description

Describe the configuration or setup issue you're experiencing.

## Steps Taken

What have you tried so far?

1. 
2. 
3. 

## Environment

- **Tongyi CLI Version**: Run `tongyi --version` or check installed version
- **Python Version**: Run `python --version`
- **Operating System**: e.g., Windows 10, macOS 13, Ubuntu 22.04
- **Installation Method**: PyPI (`pip install`) or source (`pip install -e .`)
- **Virtual Environment**: e.g., venv, conda, none

## Configuration Files

### `.env` file
**Note**: Redact your API key! Only show the format, not the actual key.

```bash
# Show your .env file (with API key redacted)
OPENROUTER_API_KEY=sk-or-v1-XXXXXX
# Other environment variables
```

### `models.ini` file
```ini
# Show your models.ini configuration
[model]
default_model = ...

[caching]
enabled = ...

# etc.
```

### Other configuration
```bash
# Any other relevant configuration
```

## Commands Tried

```bash
# Show the commands you've tried and their output
pip install tongyi-cli-interactive
# Output: ...

tongyi --help
# Output: ...

python -m config_validator --check-all
# Output: ...
```

## Error Messages

**Full error message**:
```
# Paste the full error message here
```

**Validation output** (if you ran config_validator):
```
# Paste the validation output here
```

## Troubleshooting Steps Already Attempted

- [ ] Checked that Python version is 3.11+
- [ ] Checked that package is installed: `pip list | grep tongyi`
- [ ] Verified API key is set: `echo $OPENROUTER_API_KEY` (Linux/Mac) or `echo %OPENROUTER_API_KEY%` (Windows)
- [ ] Reinstalled the package
- [ ] Updated to latest version
- [ ] Tried in a fresh virtual environment
- [ ] Checked firewall/network settings
- [ ] Other: ___________

## Additional Information

- **OpenRouter Account**: Can you access OpenRouter API directly? (e.g., via curl or Postman)
- **Network**: Are you behind a corporate firewall or proxy?
- **Other details**: Any other relevant information about your setup or environment

## Screenshots (Optional)

If applicable, add screenshots showing the issue or error.

## Checklist

- [ ] I have included my Python version and operating system
- [ ] I have included my CLI version
- [ ] I have included my configuration files (with sensitive data redacted)
- [ ] I have included the commands I tried and their output
- [ ] I have included full error messages
- [ ] I have tried the troubleshooting steps
- [ ] I have checked the INSTALLATION_GUIDE.md and SETUP_TROUBLESHOOTING.md
