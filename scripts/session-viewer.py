#!/usr/bin/env python3
"""
View and analyze individual Claude session files
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import re
import sys

def parse_session(session_path):
    """Parse and analyze a session file"""
    messages = []
    
    with open(session_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue
    
    return messages

def format_message(msg, index, show_full=False):
    """Format a single message for display"""
    role = msg.get('role', 'unknown')
    content = msg.get('content', '')
    
    # Extract timestamp if available
    timestamp = msg.get('timestamp', '')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # Clean content
    content = re.sub(r'<function_calls>.*?