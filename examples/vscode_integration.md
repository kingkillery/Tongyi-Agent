# VS Code Integration for Tongyi CLI

This guide shows how to integrate Tongyi Agent into your VS Code workflow for enhanced development productivity.

## Option 1: Using Tasks in VS Code

Create `.vscode/tasks.json` in your project:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Tongyi: Analyze Current File",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Analyze ${file} for potential issues, improvements, and best practices"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Tongyi: Explain Selection",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Explain this code: ${selectedText}"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Tongyi: Generate Tests",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Generate comprehensive test cases for ${file} using pytest"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Tongyi: Review Code",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Review the entire codebase for security, performance, and best practice issues"
      ],
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Tongyi: Generate Documentation",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Generate API documentation for ${file} with examples"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

### Usage

- Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
- Type "Tasks: Run Task"
- Select a Tongyi task from the list

## Option 2: Using VS Code Extensions

### Recommended Extensions

1. **Code Runner** - Run Tongyi commands directly from editor
2. **Shellcheck** - For shell script integration
3. **REST Client** - For testing API endpoints
4. **GitLens** - Enhanced Git integration

### Shell Script Integration

Create `tongyi_helper.sh`:

```bash
#!/bin/bash

# Tongyi helper script for VS Code integration

case "$1" in
  "analyze")
    tongyi "Analyze $(code -r) for issues"
    ;;
  "explain")
    tongyi "Explain $(code -r) in detail"
    ;;
  "test")
    tongyi "Generate tests for $(code -r)"
    ;;
  "doc")
    tongyi "Generate documentation for $(code -r)"
    ;;
  *)
    echo "Usage: $0 {analyze|explain|test|doc}"
    exit 1
    ;;
esac
```

Then create VS Code keybindings in `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+t a",
    "command": "workbench.action.terminal.sendSequence",
    "args": {
      "text": "bash tongyi_helper.sh analyze\n"
    }
  },
  {
    "key": "ctrl+shift+t e",
    "command": "workbench.action.terminal.sendSequence",
    "args": {
      "text": "bash tongyi_helper.sh explain\n"
    }
  },
  {
    "key": "ctrl+shift+t t",
    "command": "workbench.action.terminal.sendSequence",
    "args": {
      "text": "bash tongyi_helper.sh test\n"
    }
  },
  {
    "key": "ctrl+shift+t d",
    "command": "workbench.action.terminal.sendSequence",
    "args": {
      "text": "bash tongyi_helper.sh doc\n"
    }
  }
]
```

## Option 3: Using VS Code Terminal

### Quick Terminal Commands

Add these aliases to your shell (`.bashrc`, `.zshrc`):

```bash
# Tongyi aliases for VS Code
alias ta='tongyi "Analyze this file:"'
alias te='tongyi "Explain this code:"'
alias tt='tongyi "Generate tests for:"'
alias td='tongyi "Generate documentation for:"'
alias tr='tongyi "Review this code for issues:"'
alias tf='tongyi "Find the function:"'
alias tc='tongyi "Clean this file:"'

# Analyze current file in VS Code
function tongyi_analyze_current() {
    local file=$(code -r 2>/dev/null || echo "")
    [ -n "$file" ] && tongyi "Analyze $file for issues" || echo "No file open"
}
```

### Usage in VS Code Terminal

```bash
# Analyze current file
ta $(code -r)

# Explain current selection
te "$(cat)"

# Generate tests for current file
tt $(code -r)

# Clean a CSV file
tc data.csv
```

## Option 4: Python API Integration

Create a VS Code helper script `tongyi_vscode.py`:

```python
#!/usr/bin/env python3
"""
VS Code integration helper for Tongyi Agent
"""

import sys
import os
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from tongyi_orchestrator import TongyiOrchestrator
except ImportError:
    print("Tongyi Agent not installed")
    sys.exit(1)


def analyze_current_file():
    """Analyze the currently open VS Code file"""
    try:
        # Get current file from VS Code
        result = subprocess.run(
            ['code', '-r'],
            capture_output=True,
            text=True,
            timeout=5
        )
        file_path = result.stdout.strip()

        if not file_path or not os.path.exists(file_path):
            print("No file open or file not found")
            return

        # Analyze with Tongyi
        orch = TongyiOrchestrator(root=os.path.dirname(file_path))
        answer = orch.run(f"Analyze {os.path.basename(file_path)} for potential issues")

        print(f"\n📄 Analysis of {file_path}")
        print("=" * 60)
        print(answer)

    except Exception as e:
        print(f"Error: {e}")


def explain_selection():
    """Explain selected code"""
    selection = sys.stdin.read()

    if not selection.strip():
        print("No selection to explain")
        return

    orch = TongyiOrchestrator(root=".")
    answer = orch.run(f"Explain this code:\n\n{selection}")

    print("\n💡 Explanation:")
    print("=" * 60)
    print(answer)


def generate_tests_for_file(file_path: str):
    """Generate test cases for a file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    orch = TongyiOrchestrator(root=os.path.dirname(file_path))
    answer = orch.run(f"Generate pytest test cases for {os.path.basename(file_path)}")

    print(f"\n🧪 Tests for {file_path}")
    print("=" * 60)
    print(answer)

    # Save to test file
    test_file = f"test_{os.path.basename(file_path)}"
    with open(test_file, 'w') as f:
        f.write(answer)
    print(f"\n✅ Saved to {test_file}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python tongyi_vscode.py <command> [args]")
        print("Commands:")
        print("  analyze        Analyze current file")
        print("  explain        Explain selection from stdin")
        print("  test <file>    Generate tests for file")
        print("  doc <file>     Generate documentation for file")
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze":
        analyze_current_file()
    elif command == "explain":
        explain_selection()
    elif command == "test" and len(sys.argv) > 2:
        generate_tests_for_file(sys.argv[2])
    elif command == "doc" and len(sys.argv) > 2:
        generate_docs_for_file(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Usage in VS Code Tasks

```json
{
  "label": "Tongyi: Python API Analyze",
  "type": "shell",
  "command": "python",
  "args": [
    "${workspaceFolder}/examples/tongyi_vscode.py",
    "analyze"
  ],
  "problemMatcher": [],
  "presentation": {
    "reveal": "always"
  }
}
```

## Option 5: Debug Integration

Use Tongyi to help debug issues:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Tongyi: Debug Current Error",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Help debug this error: ${file}:${lineNumber}\n${selectedText}"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    },
    {
      "label": "Tongyi: Suggest Fix",
      "type": "shell",
      "command": "tongyi",
      "args": [
        "Suggest a fix for the code at ${file}:${lineNumber}:\n${selectedText}"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    }
  ]
}
```

## Tips for Effective Integration

1. **Use keyboard shortcuts**: Map common tasks to shortcuts for quick access
2. **Terminal management**: Use dedicated terminal for Tongyi output
3. **Context-aware commands**: Use `${file}`, `${lineNumber}` for targeted analysis
4. **Model selection**: Use faster models (Haiku) for quick feedback, Sonnet/Opus for deep analysis
5. **Save results**: Pipe output to files for documentation

## Example: Complete Setup Workflow

1. Create `.vscode/tasks.json` with Tongyi tasks
2. Create `.vscode/keybindings.json` with keyboard shortcuts
3. Add shell aliases to your `.bashrc` or `.zshrc`
4. Install helper scripts in `examples/` directory
5. Test with: `Ctrl+Shift+P` → "Tasks: Run Task" → "Tongyi: Analyze Current File"

## Troubleshooting

### "Command not found" errors
- Ensure Tongyi is installed globally: `pip install -e .`
- Verify PATH includes the installation location

### VS Code doesn't recognize files
- Use absolute paths in tasks
- Check workspace folder settings

### Slow responses
- Use faster models for quick tasks
- Cache results when possible
- Reduce scope of analysis
