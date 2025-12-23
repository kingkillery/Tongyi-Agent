---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Command used**:
```bash
# Paste the exact command you ran
```

**Expected behavior**: A clear and concise description of what you expected to happen.

**Actual behavior**: What actually happened. Include error messages if any.

## Environment

- **Tongyi CLI Version**: Run `tongyi --version` or check installed version
- **Python Version**: Run `python --version`
- **Operating System**: e.g., Windows 10, macOS 13, Ubuntu 22.04
- **Installation Method**: PyPI (`pip install`) or source (`pip install -e .`)
- **OpenRouter Model**: Which model are you using? (e.g., claude-3.5-haiku, gpt-4o)

## Configuration

**`.env` file** (redact any sensitive data):
```bash
OPENROUTER_API_KEY=sk-or-v1-XXXXXX
# Any other configuration
```

**`models.ini`** (if applicable):
```ini
# Paste your models.ini configuration
```

## Error Logs

**Full error message or traceback**:
```
# Paste the full error message or traceback here
```

**Additional logs**:
```bash
# Run with verbose mode if available
tongyi --verbose "your command"

# Or check error_log.md
cat error_log.md
```

## Screenshots

If applicable, add screenshots to help explain your problem.

## Additional Context

Add any other context about the problem here:
- Does this happen consistently or intermittently?
- Have you recently updated the CLI or any dependencies?
- Does the issue persist after reinstalling?
- Are there any workarounds you've found?

## Checklist

- [ ] I have searched for existing issues that report the same problem
- [ ] I have provided a minimal, reproducible example
- [ ] I have included the full error message or traceback
- [ ] I have included my Python version and operating system
- [ ] I have included my CLI version
- [ ] I have redacted any sensitive information (API keys, passwords, etc.)
