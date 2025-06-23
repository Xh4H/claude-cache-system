#!/usr/bin/env python3
"""
Session Indexing System for Claude Sessions
Indexes all .jsonl files in ~/.claude/sessions/ for fast searching
"""

import json
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
import re
from collections import Counter

# Configuration
SESSIONS_DIR = Path.home() / '.claude' / 'sessions'
DB_PATH = Path.home() / '.claude' / 'sessions.db'

def extract_session_metadata(session_path):
    """Extract metadata from a session file"""
    metadata = {
        'session_id': session_path.stem,
        'file_path': str(session_path),
        'file_size': session_path.stat().st_size,
        'modified_time': datetime.fromtimestamp(session_path.stat().st_mtime).isoformat(),
        'message_count': 0,
        'first_message': None,
        'last_message': None,
        'summary': None,
        'key_files': [],
        'tools_used': [],
        'topics': []
    }
    
    messages = []
    file_mentions = []
    tool_calls = []
    
    try:
        with open(session_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                        
                        # Extract file mentions
                        if 'content' in msg:
                            content = str(msg.get('content', ''))
                            # Find file paths
                            file_paths = re.findall(r'[~/\w\-./]+\.[a-zA-Z0-9]+', content)
                            file_mentions.extend(file_paths)
                            
                            # Extract tool calls
                            if 'tool_calls' in content or 'function_calls' in content:
                                tools = re.findall(r'name="(\w+)"', content)
                                tool_calls.extend(tools)
                    except json.JSONDecodeError:
                        continue
        
        metadata['message_count'] = len(messages)
        
        if messages:
            # First and last messages
            first_msg = messages[0]
            last_msg = messages[-1]
            
            metadata['first_message'] = first_msg.get('content', '')[:200]
            metadata['last_message'] = last_msg.get('content', '')[:200]
            
            # Generate summary from first user message
            for msg in messages:
                if msg.get('role') == 'user':
                    summary = msg.get('content', '')[:300]
                    # Clean up the summary
                    summary = re.sub(r'<[^>]+>', '', summary)  # Remove XML tags
                    summary = summary.strip()
                    metadata['summary'] = summary
                    break
            
            # Key files (most mentioned)
            file_counter = Counter(file_mentions)
            metadata['key_files'] = [f[0] for f in file_counter.most_common(10)]
            
            # Tools used
            tool_counter = Counter(tool_calls)
            metadata['tools_used'] = [t[0] for t in tool_counter.most_common(10)]
            
            # Extract topics (simple keyword extraction)
            all_content = ' '.join([str(m.get('content', '')) for m in messages[:10]])
            # Common programming/tech keywords
            topic_patterns = [
                'python', 'javascript', 'docker', 'git', 'database', 'sql', 'api',
                'claude', 'mcp', 'searxng', 'neo4j', 'postgresql', 'sqlite',
                'configuration', 'setup', 'install', 'debug', 'error', 'fix',
                'script', 'function', 'class', 'module', 'package', 'test'
            ]
            topics = []
            for pattern in topic_patterns:
                if re.search(r'\b' + pattern + r'\b', all_content, re.IGNORECASE):
                    topics.append(pattern)
            metadata['topics'] = topics[:10]
            
    except Exception as e:
        print(f"Error processing {session_path}: {e}")
    
    return metadata

def create_database():
    """Create the SQLite database and tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            modified_time TEXT,
            message_count INTEGER,
            first_message TEXT,
            last_message TEXT,
            summary TEXT,
            indexed_time TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    # Create tools table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            tool_name TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    # Create topics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            topic TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_summary ON sessions(summary)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_modified ON sessions(modified_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files ON session_files(file_path)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools ON session_tools(tool_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topics ON session_topics(topic)')
    
    conn.commit()
    return conn

def index_session(conn, session_path):
    """Index a single session file"""
    cursor = conn.cursor()
    
    metadata = extract_session_metadata(session_path)
    
    # Insert or update session
    cursor.execute('''
        INSERT OR REPLACE INTO sessions 
        (session_id, file_path, file_size, modified_time, message_count, 
         first_message, last_message, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        metadata['session_id'],
        metadata['file_path'],
        metadata['file_size'],
        metadata['modified_time'],
        metadata['message_count'],
        metadata['first_message'],
        metadata['last_message'],
        metadata['summary']
    ))
    
    # Clear existing related data
    cursor.execute('DELETE FROM session_files WHERE session_id = ?', (metadata['session_id'],))
    cursor.execute('DELETE FROM session_tools WHERE session_id = ?', (metadata['session_id'],))
    cursor.execute('DELETE FROM session_topics WHERE session_id = ?', (metadata['session_id'],))
    
    # Insert files
    for file_path in metadata['key_files']:
        cursor.execute('INSERT INTO session_files (session_id, file_path) VALUES (?, ?)',
                      (metadata['session_id'], file_path))
    
    # Insert tools
    for tool in metadata['tools_used']:
        cursor.execute('INSERT INTO session_tools (session_id, tool_name) VALUES (?, ?)',
                      (metadata['session_id'], tool))
    
    # Insert topics
    for topic in metadata['topics']:
        cursor.execute('INSERT INTO session_topics (session_id, topic) VALUES (?, ?)',
                      (metadata['session_id'], topic))
    
    conn.commit()

def main():
    """Main indexing function"""
    print(f"Indexing sessions from: {SESSIONS_DIR}")
    print(f"Database path: {DB_PATH}")
    
    # Create database
    conn = create_database()
    
    # Get all session files
    session_files = list(SESSIONS_DIR.glob('*.jsonl'))
    print(f"Found {len(session_files)} session files")
    
    # Index each session
    for i, session_path in enumerate(session_files):
        print(f"Indexing {i+1}/{len(session_files)}: {session_path.name}", end='\r')
        index_session(conn, session_path)
    
    print("\nIndexing complete!")
    
    # Show statistics
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sessions')
    session_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT file_path) FROM session_files')
    file_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT tool_name) FROM session_tools')
    tool_count = cursor.fetchone()[0]
    
    print(f"\nStatistics:")
    print(f"  Sessions indexed: {session_count}")
    print(f"  Unique files referenced: {file_count}")
    print(f"  Unique tools used: {tool_count}")
    
    conn.close()

if __name__ == '__main__':
    main()