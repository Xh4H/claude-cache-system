#!/bin/bash

# Load environment variables
source /home/mik/.memento-env

# Export all required environment variables
export NODE_ENV=production

# For Neo4j running on Windows, you need to:
# 1. Make sure Neo4j is configured to listen on all interfaces (0.0.0.0) not just localhost
# 2. Windows Firewall allows connections on port 7687
# 3. Use the Windows host machine's IP address

# Try to get Windows host IP - this is usually the default gateway in WSL2
WINDOWS_HOST=$(ip route | grep default | awk '{print $3}' | head -1)

# If that doesn't work, you may need to manually set this to your Windows machine's IP
# You can find it by running 'ipconfig' in Windows and looking for your main network adapter
# Uncomment and set the IP below if automatic detection doesn't work:
# WINDOWS_HOST="192.168.1.100"  # Replace with your actual Windows IP

echo "Attempting to connect to Neo4j at ${WINDOWS_HOST}:7687"

export NEO4J_URI="bolt://${WINDOWS_HOST}:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="alfredisgone"
export NEO4J_ENCRYPTED="false"
export ALLOW_FILE_TRACKING="true"
export ALLOW_WEB_TRACKING="true"
export ALLOW_BASH_TRACKING="true"
export NODE_OPTIONS="--no-experimental-fetch"

# Execute memento-mcp-server with all arguments
exec npx -y @gannonh/memento-mcp "$@"