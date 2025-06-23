#!/bin/bash
# Load credentials from secure storage for MCP servers

# Get credentials from secure storage
export GITHUB_PERSONAL_ACCESS_TOKEN=$(/home/mik/.claude/scripts/secure-credentials.sh get github_token 2>/dev/null)
export NEO4J_PASSWORD=$(/home/mik/.claude/scripts/secure-credentials.sh get neo4j_password 2>/dev/null)
export POSTGRES_PASSWORD=$(/home/mik/.claude/scripts/secure-credentials.sh get postgres_password 2>/dev/null)

# Verify credentials loaded
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "⚠️  GitHub token not found in secure storage"
    echo "   Run: claude-secure set github_token 'your-token'"
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "⚠️  Neo4j password not found in secure storage"
    echo "   Run: claude-secure set neo4j_password 'your-password'"
fi

echo "✅ Credentials loaded into environment"