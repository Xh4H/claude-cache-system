#!/usr/bin/env python3
import json
import sys
import os

def validate_and_fix_claude_config(file_path):
    """Fix common issues in Claude configuration files"""
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return False
    
    issues_found = []
    
    # Check for MCP servers with long names
    if 'mcpServers' in data:
        for server_name in list(data['mcpServers'].keys()):
            if len(server_name) > 64:
                issues_found.append(f"MCP server name too long: {server_name} ({len(server_name)} chars)")
                # Truncate the name
                new_name = server_name[:60] + "..."
                data['mcpServers'][new_name] = data['mcpServers'].pop(server_name)
    
    # Clear conversation history to remove the API errors
    if 'conversations' in data:
        print(f"Found {len(data['conversations'])} conversations")
        # Keep conversations but clear problematic content
        for conv_id, conv in data['conversations'].items():
            if 'messages' in conv:
                # Clear messages that might contain problematic tool definitions
                conv['messages'] = []
                issues_found.append(f"Cleared messages from conversation {conv_id}")
    
    # Backup original file
    backup_path = file_path + '.backup.' + str(int(os.path.getmtime(file_path)))
    with open(backup_path, 'w') as f:
        with open(file_path, 'r') as orig:
            f.write(orig.read())
    print(f"Created backup: {backup_path}")
    
    # Write fixed configuration
    if issues_found:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nFixed {len(issues_found)} issues:")
        for issue in issues_found:
            print(f"  - {issue}")
        return True
    else:
        print("No issues found in configuration")
        return False

if __name__ == "__main__":
    claude_config = "/home/mik/.claude.json"
    
    if os.path.exists(claude_config):
        print(f"Checking Claude configuration: {claude_config}")
        validate_and_fix_claude_config(claude_config)
    else:
        print(f"Configuration file not found: {claude_config}")