# GitHub Actions Integration Example

This example demonstrates how to use Tongyi Agent in a GitHub Actions workflow for automated code analysis and documentation generation.

## Example: GitHub Actions Workflow

```yaml
# .github/workflows/tongyi-analysis.yml
name: Tongyi Code Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 00:00 UTC
    - cron: '0 0 * * *'

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install tongyi-cli-interactive

      - name: Set up API key
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" >> $GITHUB_ENV

      - name: Analyze code with Tongyi
        run: |
          # Get PR diff for targeted analysis
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin ${{ github.base_ref }}
            DIFF_FILES=$(git diff --name-only origin/${{ github.base_ref }} HEAD | grep '\.py$')
          else
            DIFF_FILES=$(git diff --name-only HEAD~1 HEAD | grep '\.py$')
          fi

          if [ -z "$DIFF_FILES" ]; then
            echo "No Python files changed"
          else
            echo "Analyzing changed files:"
            echo "$DIFF_FILES"

            # Run Tongyi analysis
            tongyi "Review these changed files for potential issues:
            $DIFF_FILES
            Focus on: security, performance, and best practices." \
              --root . \
              --model anthropic/claude-3.5-haiku

            # Output results to file for summary
            tongyi "Generate a summary of code quality issues in:
            $DIFF_FILES
            Format as: Issue - Severity - File:Line - Suggestion" \
              --root . > analysis_report.txt
          fi

      - name: Upload analysis report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: tongyi-analysis-report
          path: analysis_report.txt

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('analysis_report.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🤖 Tongyi Code Analysis\n\n${report}`
            });
```

## Example: Documentation Generation Workflow

```yaml
# .github/workflows/generate-docs.yml
name: Generate Documentation

on:
  workflow_dispatch:
  push:
    branches: [ main ]
    paths:
      - 'src/**/*.py'

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Tongyi CLI
        run: |
          pip install tongyi-cli-interactive

      - name: Set up API key
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" >> $GITHUB_ENV

      - name: Generate API documentation
        run: |
          # Generate overview
          tongyi "Generate API documentation overview for this project.
          Include: architecture, main modules, and usage examples." \
            --root . > docs/API_OVERVIEW.md

          # Document each module
          for module in src/tongyi_agent/*.py; do
            basename=$(basename "$module" .py)
            tongyi "Generate detailed documentation for $module:
            - Purpose and functionality
            - Key functions and classes
            - Parameters and return values
            - Usage examples" \
              --root . > "docs/modules/$basename.md"
          done

      - name: Commit documentation
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add docs/
          git diff --quiet && git diff --staged --quiet || git commit -m "docs: auto-generate API documentation [skip ci]"
          git push

      - name: Create PR for review
        if: github.ref != 'refs/heads/main'
        uses: peter-evans/create-pull-request@v5
        with:
          title: "docs: auto-generated API documentation"
          body: "This PR contains automatically generated documentation."
          branch: docs/auto-generated
```

## Example: Automated Testing with Tongyi

```yaml
# .github/workflows/tongyi-tests.yml
name: Tongyi Intelligent Tests

on:
  push:
    branches: [ main, develop ]

jobs:
  intelligent-testing:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install tongyi-cli-interactive

      - name: Set up API key
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" >> $GITHUB_ENV

      - name: Generate test cases
        run: |
          # Ask Tongyi to generate test cases
          tongyi "Generate comprehensive test cases for src/sandbox_exec.py.
          Include: unit tests, edge cases, and security tests.
          Output as pytest-compatible code." \
            --root . > test_sandbox_autogenerated.py

      - name: Run tests
        run: |
          pytest test_sandbox_autogenerated.py -v

      - name: Check for edge cases
        run: |
          # Use Tongyi to identify potential edge cases
          tongyi "Analyze src/*.py and list:
          1. Unhandled exception scenarios
          2. Missing input validation
          3. Potential security vulnerabilities
          4. Performance bottlenecks" \
            --root . > edge_case_report.txt

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: tongyi-test-reports
          path: |
            edge_case_report.txt
            test_sandbox_autogenerated.py
```

## Setup Instructions

1. **Add OpenRouter API Key to GitHub Secrets:**
   - Go to your repository: Settings → Secrets and variables → Actions
   - Add a new secret named `OPENROUTER_API_KEY`
   - Paste your API key from https://openrouter.ai/keys

2. **Copy workflow files:**
   ```bash
   mkdir -p .github/workflows
   cp examples/github_actions_ci.yml .github/workflows/
   ```

3. **Enable workflows:**
   - Push to your repository
   - Go to Actions tab in GitHub
   - Enable the workflows

## Tips for CI/CD Usage

- **Use faster models**: In CI, use `claude-3.5-haiku` or similar for speed
- **Cache dependencies**: Cache Python packages for faster builds
- **Rate limiting**: Be mindful of API rate limits in frequent runs
- **Artifact storage**: Store reports as artifacts for review
- **Conditional execution**: Only run Tongyi on specific file changes

## Example: Local Testing Before CI

```bash
# Test workflow locally with act (install act first)
act -j code-review --secret OPENROUTER_API_KEY=your-key

# Or test the Tongyi command locally
export OPENROUTER_API_KEY=your-key
tongyi "Review src/cli.py for issues" --root .
```
