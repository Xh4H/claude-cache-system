#!/bin/bash
# Load secure credentials into environment variables for Claude Code

SECURE_SCRIPT="$HOME/.claude/scripts/secure-credentials.sh"

# Function to load a credential
load_credential() {
    local key=$1
    local env_var=$2
    local value=$($SECURE_SCRIPT get "$key" 2>/dev/null)
    if [ -n "$value" ]; then
        export "$env_var"="$value"
        echo "✅ Loaded $key into $env_var"
    else
        echo "❌ Failed to load $key"
    fi
}

# Load all credentials
echo "Loading secure credentials..."
load_credential "github_token" "GITHUB_PERSONAL_ACCESS_TOKEN"
load_credential "neo4j_password" "NEO4J_PASSWORD"
load_credential "postgres_password" "POSTGRES_PASSWORD"

# Also set for MCP servers that might need them
export NEO4J_URI="bolt://[::1]:7687"
export NEO4J_USER="neo4j"

echo "✅ Credentials loaded into environment"