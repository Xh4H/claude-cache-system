#!/bin/bash
# Load environment variables for Claude Code
if [ -f ~/.claude/.env ]; then
    set -a
    source ~/.claude/.env
    set +a
fi