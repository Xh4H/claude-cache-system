#!/bin/bash
# Service wrapper for Claude components

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

case "$1" in
    credentials)
        shift
        "$CLAUDE_HOME/scripts/secure-credentials.sh" "$@"
        ;;
    health)
        "$CLAUDE_HOME/scripts/health-check.sh"
        ;;
    performance)
        "$CLAUDE_HOME/scripts/performance-monitor.sh" "${2:-report}"
        ;;
    session)
        shift
        "$CLAUDE_HOME/scripts/session-manager.sh" "$@"
        ;;
    knowledge)
        shift
        "$CLAUDE_HOME/scripts/knowledge-extractor.sh" "$@"
        ;;
    *)
        echo "Available services:"
        echo "  credentials - Secure credential management"
        echo "  health      - System health check"
        echo "  performance - Performance monitoring"
        echo "  session     - Session management"
        echo "  knowledge   - Knowledge extraction"
        ;;
esac
