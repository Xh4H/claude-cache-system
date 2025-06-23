#\!/usr/bin/env python3
import json
import sys
import os

# Load the config
with open('/home/mik/.claude.json', 'r') as f:
    config = json.load(f)

# Extract the main mcpServers (should be only one at top level)
main_mcp_servers = None
if 'mcpServers' in config and config['mcpServers']:
    main_mcp_servers = config['mcpServers']

# Clean up credentials in MCP servers
if main_mcp_servers:
    # Update memento to use env vars
    if 'memento' in main_mcp_servers:
        main_mcp_servers['memento']['env'] = {
            "NEO4J_URI": "${NEO4J_URI}",
            "NEO4J_USER": "${NEO4J_USER}",
            "NEO4J_PASSWORD": "${NEO4J_PASSWORD}"
        }
    
    # Update postgres to use env var
    if 'postgres' in main_mcp_servers:
        main_mcp_servers['postgres']['env'] = {
            "CONNECTION_STRING": "${POSTGRES_CONNECTION_STRING}"
        }
    
    # Update github to use env var
    if 'github' in main_mcp_servers:
        main_mcp_servers['github']['env'] = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
        }

# Remove empty project configurations
if 'projects' in config:
    cleaned_projects = {}
    for path, project_config in config['projects'].items():
        # Keep project if it has non-empty mcpServers or other meaningful config
        has_content = False
        
        # Check for meaningful content
        if 'mcpServers' in project_config and project_config['mcpServers']:
            has_content = True
        elif 'allowedTools' in project_config and project_config['allowedTools']:
            has_content = True
        elif 'history' in project_config and project_config['history']:
            has_content = True
        
        if has_content:
            # Remove nested empty mcpServers
            if 'mcpServers' in project_config and not project_config['mcpServers']:
                del project_config['mcpServers']
            cleaned_projects[path] = project_config
    
    config['projects'] = cleaned_projects

# Ensure only one top-level mcpServers
config['mcpServers'] = main_mcp_servers if main_mcp_servers else {}

# Remove duplicate mcpServers keys (keep only the populated one)
keys_to_check = list(config.keys())
mcp_count = 0
for key in keys_to_check:
    if key == 'mcpServers':
        mcp_count += 1
        if mcp_count > 1 or not config[key]:
            del config[key]

print(json.dumps(config, indent=2))
