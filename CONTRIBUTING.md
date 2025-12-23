# Contributing to Tongyi Agent

Thank you for your interest in contributing to Tongyi Agent! This guide will help you get started with development, testing, and submitting contributions.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style Guidelines](#code-style-guidelines)
- [Project Structure](#project-structure)
- [Common Development Tasks](#common-development-tasks)
- [Submitting Changes](#submitting-changes)
- [Pull Request Process](#pull-request-process)

---

## Getting Started

### Prerequisites

Before you start contributing, make sure you have:

- **Python 3.9+** installed
- **Git** installed and configured
- **OpenRouter API key** (for testing AI features)
- Basic knowledge of Python, CLI tools, and test frameworks

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork locally**:

   ```bash
   git clone https://github.com/your-username/tongyi-agent.git
   cd tongyi-agent
   ```

3. **Add upstream remote**:

   ```bash
   git remote add upstream https://github.com/original-owner/tongyi-agent.git
   ```

---

## Development Setup

### 1. Create a Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or install separately
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required for AI features
OPENROUTER_API_KEY=your-api-key-here

# Optional
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 4. Verify Installation

```bash
# Check that CLI works
tongyi --help

# Validate configuration
python -m config_validator --check-all

# Run tests
pytest
```

---

## Running Tests

### Test Suite Overview

The project uses `pytest` for testing. Test files are located in `tests/` directory.

### Run All Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=src --cov-report=html
```

### Run Specific Tests

```bash
# Run tests for a specific module
pytest tests/test_sandbox_exec.py

# Run tests matching a pattern
pytest -k "test_verification"

# Run a specific test
pytest tests/test_sandbox_exec.py::test_execute_basic
```

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test interaction between components
- **Security Tests**: Test for vulnerabilities and edge cases

### Adding New Tests

When adding new features, follow this pattern:

```python
# tests/test_new_feature.py
import pytest

def test_basic_functionality():
    """Test basic functionality of new feature"""
    # Arrange
    input_data = {...}

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result is not None
    assert result.status == "success"

def test_edge_case():
    """Test edge cases"""
    # Test boundary conditions
    with pytest.raises(ValueError):
        function_to_test(invalid_input)

def test_error_handling():
    """Test error handling"""
    # Test graceful failures
    result = function_to_test(problematic_input)
    assert result.error is not None
```

---

## Code Style Guidelines

### Python Code Style

We follow standard Python conventions:

- **PEP 8** for style guidelines
- **Type hints** for function signatures
- **Docstrings** for all public functions and classes

### Formatting

```bash
# Format code with black
black src/

# Check formatting
black --check src/

# Format specific file
black src/tongyi_agent/cli.py
```

### Linting

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Check specific file
ruff check src/tongyi_agent/cli.py
```

### Example of Proper Style

```python
from typing import Optional, Dict, List

class MyClass:
    """Summary of class purpose.

    Longer description of class behavior and usage.

    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2
    """

    def __init__(self, param1: str, param2: Optional[int] = None):
        """Initialize MyClass.

        Args:
            param1: Description of param1
            param2: Description of param2 (optional)

        Raises:
            ValueError: If param1 is empty
        """
        self.attribute1 = param1
        self.attribute2 = param2

        if not param1:
            raise ValueError("param1 cannot be empty")

    def method_name(self, input_data: Dict[str, str]) -> List[str]:
        """Process input data and return results.

        Args:
            input_data: Dictionary containing input parameters

        Returns:
            List of processed results

        Raises:
            KeyError: If required key is missing
        """
        if "key" not in input_data:
            raise KeyError("Required key 'key' not found")

        # Process data
        result = self._process_data(input_data["key"])
        return result

    def _process_data(self, data: str) -> List[str]:
        """Private method for processing data.

        Args:
            data: Raw data to process

        Returns:
            Processed data as list
        """
        return data.split()
```

### Documentation Guidelines

- **All public functions** must have docstrings
- **Docstrings should** explain: purpose, parameters, returns, raises
- **Use `>>>` examples** for complex functions
- **Keep docstrings concise but complete**

---

## Project Structure

```
tongyi-agent/
├── src/                      # Source code
│   ├── tongyi_agent/         # Main package
│   │   ├── cli.py           # CLI entry point
│   │   └── ...              # Other modules
│   ├── tongyi_orchestrator.py
│   ├── claude_agent_orchestrator.py
│   ├── model_manager.py
│   └── ...
├── tests/                   # Test files
│   ├── test_sandbox_exec.py
│   ├── test_*.py
│   └── ...
├── examples/                # Example code and integrations
│   ├── python_api_examples.py
│   ├── shell_automation.sh
│   └── ...
├── docs/                    # Documentation
├── schemas/                 # JSON schemas
├── .env.example             # Environment template
├── README.md                # Main documentation
├── CONTRIBUTING.md          # This file
├── INSTALLATION_GUIDE.md
├── CLI_GUIDE.md
└── ...
```

### Key Modules

- **`cli.py`**: Interactive CLI and command handling
- **`tongyi_orchestrator.py`**: Tongyi DeepResearch integration
- **`claude_agent_orchestrator.py`**: Claude SDK integration
- **`model_manager.py`**: Model selection and management
- **`sandbox_exec.py`**: Safe code execution
- **`code_search.py`**: Code search functionality
- **`verifier_gate.py`**: Verification and citation system

---

## Common Development Tasks

### Adding a New Tool

1. **Define the tool function** in appropriate module:

```python
from typing import Dict, Any

def my_new_tool(param1: str, param2: int = 0) -> Dict[str, Any]:
    """Description of tool purpose.

    Args:
        param1: Description
        param2: Description (default: 0)

    Returns:
        Dictionary with tool results

    Raises:
        ValueError: If parameters are invalid
    """
    # Implementation here
    return {"status": "success", "data": param1}
```

2. **Register the tool** in tool registry:

```python
# In orchestrator initialization
self.tool_registry.register("my_new_tool", my_new_tool)
```

3. **Add tests** for the new tool:

```python
# tests/test_my_new_tool.py
import pytest

def test_my_new_tool_basic():
    result = my_new_tool("test", 5)
    assert result["status"] == "success"
    assert "data" in result

def test_my_new_tool_edge_cases():
    with pytest.raises(ValueError):
        my_new_tool("")
```

4. **Update documentation** with usage examples

### Adding a New CLI Command

1. **Add command handler** in `cli.py`:

```python
def handle_my_command(args: list) -> bool:
    """Handle my new command.

    Args:
        args: Command arguments

    Returns:
        True if command was handled
    """
    if args and args[0] == "mycommand":
        # Handle command
        print("My command executed")
        return True
    return False
```

2. **Register command** in command processing:

```python
def process_command(command: str) -> bool:
    """Process user commands."""
    if handle_my_command(command.split()):
        return True
    # ... other command handlers
```

3. **Update help text** with command description

### Debugging Issues

1. **Enable debug logging**:

```bash
# Set log level
export TONGYI_LOG_LEVEL=DEBUG

# Run with verbose output
tongyi "Your question" --verbose
```

2. **Use Python debugger**:

```python
# In your code
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

3. **Check error logs**:

```bash
# View error log
cat error_log.md

# Check recent logs
tail -50 error_log.md
```

### Performance Profiling

```bash
# Profile a function
python -m cProfile -o profile.stats your_script.py

# Analyze profile
python -m pstats profile.stats

# Use snakeviz for visualization
pip install snakeviz
snakeviz profile.stats
```

---

## Submitting Changes

### Branch Naming Convention

Use clear branch names that describe the change:

- `feature/new-tool-name` - New feature
- `fix/issue-description` - Bug fix
- `docs/update-description` - Documentation update
- `refactor/component-name` - Code refactoring

### Commit Message Format

Follow conventional commit format:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(cli): add export command for session history

fix(sandbox): prevent infinite loop in execution

docs(readme): update installation instructions

test(verifier): add tests for citation validation
```

### Before Submitting

1. **Run all tests**:

```bash
pytest -v
```

2. **Check code formatting**:

```bash
black --check src/
ruff check src/
```

3. **Update documentation** if needed

4. **Ensure no merge conflicts**:

```bash
git fetch upstream
git rebase upstream/main
```

---

## Pull Request Process

### Creating a Pull Request

1. **Push your branch**:

```bash
git push origin feature/my-feature
```

2. **Create pull request** on GitHub:
   - Click "New Pull Request"
   - Select your branch
   - Provide clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages follow conventions
```

### Review Process

1. **Automated checks** (CI/CD) must pass
2. **Code review** by maintainers
3. **Address feedback** and make requested changes
4. **Approval** from maintainers
5. **Merge** into main branch

### After Merge

1. **Update your local repository**:

```bash
git fetch upstream
git checkout main
git pull upstream main
```

2. **Delete your feature branch** (optional):

```bash
git branch -d feature/my-feature
```

---

## Getting Help

### Resources

- **Documentation**: [README.md](README.md), [CLI_GUIDE.md](CLI_GUIDE.md), [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/tongyi-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/tongyi-agent/discussions)

### Asking Questions

When asking for help, include:

1. **Your environment**:
   - Python version: `python --version`
   - OS version
   - Installed packages: `pip list`

2. **What you tried**:
   - Commands you ran
   - Code you wrote

3. **What happened**:
   - Expected behavior
   - Actual behavior
   - Error messages

### Reporting Bugs

When reporting bugs:

1. **Search existing issues** first
2. **Create a minimal reproduction** case
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Full error traceback
   - Environment details

---

## Development Workflow Example

Here's a complete workflow for a typical contribution:

```bash
# 1. Start from main branch
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/add-new-tool

# 3. Make changes
# Edit files...
# Add tests...

# 4. Run tests
pytest -v

# 5. Check formatting
black src/
ruff check src/

# 6. Commit changes
git add .
git commit -m "feat(tools): add new tool for X"

# 7. Push to remote
git push origin feature/add-new-tool

# 8. Create PR on GitHub
# Wait for review...
# Address feedback...
# Merge!
```

---

## Code of Conduct

- Be respectful and constructive
- Welcome new contributors
- Focus on what is best for the community
- Show empathy towards other community members

---

Thank you for contributing to Tongyi Agent! 🚀
