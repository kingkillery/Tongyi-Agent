#!/bin/bash

# Tongyi Agent Shell Automation Examples
# This script demonstrates how to integrate Tongyi CLI into shell scripts

set -e

# Configuration
TONGYI_CMD="tongyi"
MODEL="${MODEL:-anthropic/claude-3.5-haiku}"  # Default: Haiku for speed
ROOT="${ROOT:-.}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# ============================================
# Example 1: Code Review Automation
# ============================================
code_review() {
    local file="$1"

    if [ -z "$file" ]; then
        echo "Usage: $0 review <file>"
        exit 1
    fi

    if [ ! -f "$file" ]; then
        echo "Error: File not found: $file"
        exit 1
    fi

    log_info "Reviewing $file..."

    $TONGYI_CMD "Review $file for:
- Security issues
- Performance problems
- Code quality concerns
- Best practice violations" \
        --root "$ROOT" \
        --model "$MODEL"
}

# ============================================
# Example 2: Documentation Generator
# ============================================
generate_docs() {
    local file="$1"

    if [ -z "$file" ]; then
        echo "Usage: $0 docs <file>"
        exit 1
    fi

    log_info "Generating documentation for $file..."

    $TONGYI_CMD "Generate comprehensive documentation for $file:
- Purpose and functionality
- Functions and classes
- Parameters and return values
- Usage examples" \
        --root "$ROOT" \
        --model "$MODEL"
}

# ============================================
# Example 3: Test Case Generator
# ============================================
generate_tests() {
    local file="$1"

    if [ -z "$file" ]; then
        echo "Usage: $0 tests <file>"
        exit 1
    fi

    log_info "Generating tests for $file..."

    local output_file="test_$(basename "$file")"

    $TONGYI_CMD "Generate pytest test cases for $file:
- Unit tests
- Edge cases
- Error handling
- Integration scenarios" \
        --root "$ROOT" \
        --model "$MODEL" > "$output_file"

    log_success "Tests saved to $output_file"
}

# ============================================
# Example 4: Batch Code Analysis
# ============================================
batch_analyze() {
    local pattern="$1"

    if [ -z "$pattern" ]; then
        pattern="*.py"  # Default: all Python files
    fi

    log_info "Analyzing files matching: $pattern"

    for file in $pattern; do
        if [ -f "$file" ]; then
            log_info "Analyzing $file..."
            $TONGYI_CMD "Analyze $file for issues" \
                --root "$ROOT" \
                --model "$MODEL"
            echo ""
        fi
    done

    log_success "Batch analysis complete"
}

# ============================================
# Example 5: Code Cleanup
# ============================================
cleanup_code() {
    local file="$1"

    if [ -z "$file" ]; then
        echo "Usage: $0 cleanup <file>"
        exit 1
    fi

    log_info "Cleaning up $file..."

    $TONGYI_CMD "Clean up $file:
- Remove unused imports
- Fix formatting issues
- Add missing docstrings
- Improve variable naming" \
        --root "$ROOT" \
        --model "$MODEL"
}

# ============================================
# Example 6: Security Scan
# ============================================
security_scan() {
    local dir="$1"

    if [ -z "$dir" ]; then
        dir="$ROOT"
    fi

    log_info "Running security scan on $dir..."

    $TONGYI_CMD "Scan $dir for security issues:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Path traversal risks
- Insecure configurations" \
        --root "$dir" \
        --model "$MODEL"
}

# ============================================
# Example 7: Performance Analysis
# ============================================
performance_check() {
    local file="$1"

    if [ -z "$file" ]; then
        echo "Usage: $0 perf <file>"
        exit 1
    fi

    log_info "Checking performance of $file..."

    $TONGYI_CMD "Analyze $file for performance issues:
- Inefficient loops
- Memory leaks
- Unnecessary computations
- Database query optimization" \
        --root "$ROOT" \
        --model "$MODEL"
}

# ============================================
# Example 8: Git Hook Integration
# ============================================
pre_commit_review() {
    log_info "Running pre-commit review..."

    # Get changed files
    local changed_files=$(git diff --cached --name-only | grep '\.py$' || true)

    if [ -z "$changed_files" ]; then
        log_info "No Python files changed"
        return 0
    fi

    log_info "Reviewing $(echo "$changed_files" | wc -l) Python files..."

    for file in $changed_files; do
        if [ -f "$file" ]; then
            log_info "Checking $file..."

            # Quick review with fast model
            $TONGYI_CMD "Quick review of $file:
            - Obvious bugs
            - Syntax errors
            - Missing error handling" \
                --root "$ROOT" \
                --model anthropic/claude-3.5-haiku
        fi
    done

    log_success "Pre-commit review complete"
}

# ============================================
# Example 9: Daily Standup Helper
# ============================================
daily_summary() {
    local yesterday="yesterday"
    local today="today"

    if [ -n "$1" ]; then
        yesterday="$1"
    fi

    if [ -n "$2" ]; then
        today="$2"
    fi

    log_info "Generating daily summary..."

    $TONGYI_CMD "Generate a daily standup summary:
    - What I completed yesterday: ${yesterday}
    - What I'm working on today: ${today}
    - Format as: Completed, Working On, Blockers" \
        --root "$ROOT"
}

# ============================================
# Example 10: Migration Helper
# ============================================
migration_helper() {
    local old_code="$1"
    local new_pattern="$2"

    if [ -z "$old_code" ]; then
        echo "Usage: $0 migrate '<old code pattern>' '<new pattern>'"
        exit 1
    fi

    log_info "Generating migration guide..."

    $TONGYI_CMD "Help migrate from '${old_code}' to '${new_pattern}':
    - Search for all occurrences
    - Show how to replace each occurrence
    - Provide examples
    - List potential breaking changes" \
        --root "$ROOT"
}

# ============================================
# Example 11: CSV Cleaner Wrapper
# ============================================
clean_csv() {
    local file="$1"

    if [ -z "$file" ]; then
        echo "Usage: $0 clean-csv <file.csv>"
        exit 1
    fi

    log_info "Cleaning CSV file: $file"

    $TONGYI_CMD "Please clean $file" \
        --root "$ROOT"

    log_success "CSV cleaned"
}

# ============================================
# Example 12: Interactive Session with History
# ============================================
interactive_with_history() {
    log_info "Starting interactive session..."

    # Show recent history
    if [ -f ~/.tongyi_agent_history.json ]; then
        log_info "Recent history:"
        tail -5 ~/.tongyi_agent_history.json || true
    fi

    # Start interactive mode
    $TONGYI_CMD
}

# ============================================
# Example 13: Project Health Check
# ============================================
project_health() {
    log_info "Running project health check..."

    # Check for common issues
    local checks=(
        "Check for unused imports"
        "Check for TODO comments"
        "Check for long functions"
        "Check for duplicate code"
        "Check for missing error handling"
    )

    for check in "${checks[@]}"; do
        log_info "Running: $check"
        $TONGYI_CMD "$check" --root "$ROOT" --model "$MODEL"
        echo ""
    done

    log_success "Health check complete"
}

# ============================================
# Example 14: CI/CD Integration
# ============================================
ci_checks() {
    log_info "Running CI checks..."

    # Validate configuration
    if command -v python &> /dev/null; then
        python -m config_validator --check-all || true
    fi

    # Code review
    batch_analyze "*.py"

    log_success "CI checks complete"
}

# ============================================
# Main Menu
# ============================================
show_help() {
    cat << EOF
Tongyi Agent Shell Automation Examples

Usage: $0 <command> [args]

Commands:
  review <file>          Code review for a specific file
  docs <file>             Generate documentation
  tests <file>            Generate test cases
  batch [pattern]         Batch analyze files (default: *.py)
  cleanup <file>          Code cleanup
  security [dir]          Security scan
  perf <file>             Performance check
  pre-commit              Pre-commit hook review
  summary [y] [t]         Daily standup summary
  migrate <old> <new>     Migration helper
  clean-csv <file>        Clean CSV file
  interactive             Interactive session with history
  health                  Project health check
  ci                      Run CI checks
  help                    Show this help

Environment Variables:
  MODEL                   Model to use (default: claude-3.5-haiku)
  ROOT                    Root directory (default: .)

Examples:
  $0 review src/cli.py
  $0 docs src/orchestrator.py
  $0 tests src/sandbox_exec.py
  $0 batch "*.py"
  $0 security
  MODEL=anthropic/claude-3.5-sonnet $0 review src/cli.py

EOF
}

# ============================================
# Main
# ============================================
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    local command="$1"
    shift

    case "$command" in
        review)
            code_review "$@"
            ;;
        docs)
            generate_docs "$@"
            ;;
        tests)
            generate_tests "$@"
            ;;
        batch)
            batch_analyze "$@"
            ;;
        cleanup)
            cleanup_code "$@"
            ;;
        security)
            security_scan "$@"
            ;;
        perf)
            performance_check "$@"
            ;;
        pre-commit)
            pre_commit_review
            ;;
        summary)
            daily_summary "$@"
            ;;
        migrate)
            migration_helper "$@"
            ;;
        clean-csv)
            clean_csv "$@"
            ;;
        interactive)
            interactive_with_history
            ;;
        health)
            project_health
            ;;
        ci)
            ci_checks
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "Unknown command: $command"
            echo "Run '$0 help' for usage"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
