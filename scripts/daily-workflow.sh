#!/bin/bash

# Claude Code Daily Workflow Script
# Add to your shell rc file: alias cw='~/.claude/scripts/daily-workflow.sh'

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Main workflow
case "${1:-help}" in
    morning|m)
        print_header "Morning Workflow"
        
        print_info "Checking git status across recent projects..."
        for dir in ~/projects/*/; do
            if [ -d "$dir/.git" ]; then
                echo -e "\n${BLUE}$(basename "$dir"):${NC}"
                git -C "$dir" status -s
            fi
        done
        
        print_info "Running Claude to check TODOs..."
        claude "What should I work on today based on my TODOs and recent commits?"
        ;;
        
    commit|c)
        print_header "Smart Commit"
        
        print_info "Running pre-commit checks..."
        claude "Check my changes for issues, then create a commit"
        ;;
        
    review|r)
        print_header "Code Review"
        
        print_info "Reviewing uncommitted changes..."
        claude "Review my uncommitted changes and suggest improvements"
        ;;
        
    standup|s)
        print_header "Daily Standup"
        
        print_info "Generating standup summary..."
        claude "Summarize my git commits from the last 24 hours across all projects"
        ;;
        
    learn|l)
        print_header "Learning Mode"
        
        if [ -n "$2" ]; then
            claude "Explain how $2 works in this codebase"
        else
            claude "What interesting patterns or techniques are used in this codebase?"
        fi
        ;;
        
    refactor|ref)
        print_header "Refactoring Assistant"
        
        if [ -n "$2" ]; then
            claude "Suggest refactoring improvements for $2"
        else
            claude "Find code that could benefit from refactoring"
        fi
        ;;
        
    test|t)
        print_header "Test Generation"
        
        if [ -n "$2" ]; then
            claude "Generate tests for $2"
        else
            claude "Generate tests for recent changes"
        fi
        ;;
        
    docs|d)
        print_header "Documentation"
        
        if [ -n "$2" ]; then
            claude "Generate documentation for $2"
        else
            claude "Update documentation for recent changes"
        fi
        ;;
        
    perf|p)
        print_header "Performance Analysis"
        
        claude "Analyze code for performance issues and suggest optimizations"
        ;;
        
    deps|dep)
        print_header "Dependency Check"
        
        claude "Check for outdated dependencies and security vulnerabilities"
        ;;
        
    todo|todos)
        print_header "TODO List"
        
        claude "Find all TODOs, FIXMEs, and HACKs in the codebase and prioritize them"
        ;;
        
    pr|pull)
        print_header "Pull Request"
        
        claude "Create a pull request with a summary of all changes"
        ;;
        
    help|h|--help|-h|*)
        print_header "Claude Workflow Commands"
        
        cat << EOF
Usage: cw [command] [args]

Commands:
  morning, m       - Morning routine: check git status and TODOs
  commit, c        - Smart commit with pre-checks
  review, r        - Review uncommitted changes
  standup, s       - Generate daily standup summary
  learn, l [file]  - Learn about codebase or specific file
  refactor, ref    - Get refactoring suggestions
  test, t [file]   - Generate tests
  docs, d [file]   - Generate documentation
  perf, p          - Performance analysis
  deps, dep        - Check dependencies
  todo, todos      - List and prioritize TODOs
  pr, pull         - Create pull request
  help, h          - Show this help

Examples:
  cw morning                    # Start your day
  cw commit                     # Smart commit
  cw learn src/auth.js         # Learn about auth.js
  cw test src/utils.ts         # Generate tests for utils
  
Tip: Add alias to ~/.bashrc or ~/.zshrc:
  alias cw='~/.claude/scripts/daily-workflow.sh'
EOF
        ;;
esac

print_success "Done!"