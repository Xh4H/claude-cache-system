#!/usr/bin/env python3
"""
Search tool for indexed Claude sessions
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import json

# Configuration
DB_PATH = Path.home() / '.claude' / 'sessions.db'

def search_sessions(query, search_type='all', limit=20):
    """Search sessions based on various criteria"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    results = []
    
    if search_type == 'all' or search_type == 'content':
        # Search in summaries and messages
        cursor.execute('''
            SELECT DISTINCT s.*, 
                   GROUP_CONCAT(DISTINCT sf.file_path) as files,
                   GROUP_CONCAT(DISTINCT st.tool_name) as tools,
                   GROUP_CONCAT(DISTINCT sp.topic) as topics
            FROM sessions s
            LEFT JOIN session_files sf ON s.session_id = sf.session_id
            LEFT JOIN session_tools st ON s.session_id = st.session_id
            LEFT JOIN session_topics sp ON s.session_id = sp.session_id
            WHERE s.summary LIKE ? OR s.first_message LIKE ? OR s.last_message LIKE ?
            GROUP BY s.session_id
            ORDER BY s.modified_time DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        results.extend(cursor.fetchall())
    
    if search_type == 'all' or search_type == 'file':
        # Search by file path
        cursor.execute('''
            SELECT DISTINCT s.*, 
                   GROUP_CONCAT(DISTINCT sf.file_path) as files,
                   GROUP_CONCAT(DISTINCT st.tool_name) as tools,
                   GROUP_CONCAT(DISTINCT sp.topic) as topics
            FROM sessions s
            JOIN session_files sf ON s.session_id = sf.session_id
            LEFT JOIN session_tools st ON s.session_id = st.session_id
            LEFT JOIN session_topics sp ON s.session_id = sp.session_id
            WHERE sf.file_path LIKE ?
            GROUP BY s.session_id
            ORDER BY s.modified_time DESC
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        for row in cursor.fetchall():
            if row['session_id'] not in [r['session_id'] for r in results]:
                results.append(row)
    
    if search_type == 'all' or search_type == 'tool':
        # Search by tool name
        cursor.execute('''
            SELECT DISTINCT s.*, 
                   GROUP_CONCAT(DISTINCT sf.file_path) as files,
                   GROUP_CONCAT(DISTINCT st.tool_name) as tools,
                   GROUP_CONCAT(DISTINCT sp.topic) as topics
            FROM sessions s
            JOIN session_tools st ON s.session_id = st.session_id
            LEFT JOIN session_files sf ON s.session_id = sf.session_id
            LEFT JOIN session_topics sp ON s.session_id = sp.session_id
            WHERE st.tool_name LIKE ?
            GROUP BY s.session_id
            ORDER BY s.modified_time DESC
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        for row in cursor.fetchall():
            if row['session_id'] not in [r['session_id'] for r in results]:
                results.append(row)
    
    if search_type == 'all' or search_type == 'topic':
        # Search by topic
        cursor.execute('''
            SELECT DISTINCT s.*, 
                   GROUP_CONCAT(DISTINCT sf.file_path) as files,
                   GROUP_CONCAT(DISTINCT st.tool_name) as tools,
                   GROUP_CONCAT(DISTINCT sp.topic) as topics
            FROM sessions s
            JOIN session_topics sp ON s.session_id = sp.session_id
            LEFT JOIN session_files sf ON s.session_id = sf.session_id
            LEFT JOIN session_tools st ON s.session_id = st.session_id
            WHERE sp.topic LIKE ?
            GROUP BY s.session_id
            ORDER BY s.modified_time DESC
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        for row in cursor.fetchall():
            if row['session_id'] not in [r['session_id'] for r in results]:
                results.append(row)
    
    conn.close()
    return results

def list_recent_sessions(days=7, limit=20):
    """List recent sessions"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, 
               GROUP_CONCAT(DISTINCT sf.file_path) as files,
               GROUP_CONCAT(DISTINCT st.tool_name) as tools,
               GROUP_CONCAT(DISTINCT sp.topic) as topics
        FROM sessions s
        LEFT JOIN session_files sf ON s.session_id = sf.session_id
        LEFT JOIN session_tools st ON s.session_id = st.session_id
        LEFT JOIN session_topics sp ON s.session_id = sp.session_id
        WHERE datetime(s.modified_time) > datetime('now', '-' || ? || ' days')
        GROUP BY s.session_id
        ORDER BY s.modified_time DESC
        LIMIT ?
    ''', (days, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results

def show_stats():
    """Show database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM sessions')
    stats['total_sessions'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT file_path) FROM session_files')
    stats['unique_files'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT tool_name) FROM session_tools')
    stats['unique_tools'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT topic) FROM session_topics')
    stats['unique_topics'] = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT tool_name, COUNT(*) as count 
        FROM session_tools 
        GROUP BY tool_name 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    stats['top_tools'] = cursor.fetchall()
    
    cursor.execute('''
        SELECT topic, COUNT(*) as count 
        FROM session_topics 
        GROUP BY topic 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    stats['top_topics'] = cursor.fetchall()
    
    conn.close()
    return stats

def format_session(session):
    """Format a session for display"""
    modified = datetime.fromisoformat(session['modified_time']).strftime('%Y-%m-%d %H:%M')
    
    output = f"\n{'='*80}\n"
    output += f"Session: {session['session_id']}\n"
    output += f"Modified: {modified} | Messages: {session['message_count']} | Size: {session['file_size']:,} bytes\n"
    
    if session['summary']:
        output += f"\nSummary: {session['summary'][:200]}{'...' if len(session['summary']) > 200 else ''}\n"
    
    if session['files']:
        files = session['files'].split(',')[:5]
        output += f"\nKey files: {', '.join(files)}\n"
    
    if session['tools']:
        tools = session['tools'].split(',')[:5]
        output += f"Tools used: {', '.join(tools)}\n"
    
    if session['topics']:
        topics = session['topics'].split(',')
        output += f"Topics: {', '.join(topics)}\n"
    
    output += f"\nFile: {session['file_path']}\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(description='Search Claude sessions')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('-t', '--type', choices=['all', 'content', 'file', 'tool', 'topic'], 
                       default='all', help='Search type')
    parser.add_argument('-r', '--recent', type=int, metavar='DAYS',
                       help='Show sessions from last N days')
    parser.add_argument('-l', '--limit', type=int, default=20,
                       help='Maximum results (default: 20)')
    parser.add_argument('-s', '--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    
    args = parser.parse_args()
    
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run 'index-sessions.py' first to create the index")
        return
    
    if args.stats:
        stats = show_stats()
        print(f"\nSession Database Statistics")
        print(f"{'='*40}")
        print(f"Total sessions: {stats['total_sessions']}")
        print(f"Unique files: {stats['unique_files']}")
        print(f"Unique tools: {stats['unique_tools']}")
        print(f"Unique topics: {stats['unique_topics']}")
        
        print(f"\nTop Tools:")
        for tool, count in stats['top_tools']:
            print(f"  {tool}: {count}")
        
        print(f"\nTop Topics:")
        for topic, count in stats['top_topics']:
            print(f"  {topic}: {count}")
        
        return
    
    if args.recent:
        results = list_recent_sessions(args.recent, args.limit)
        if args.json:
            print(json.dumps([dict(r) for r in results], indent=2))
        else:
            print(f"\nRecent sessions (last {args.recent} days):")
            for session in results:
                print(format_session(session))
    
    elif args.query:
        results = search_sessions(args.query, args.type, args.limit)
        if args.json:
            print(json.dumps([dict(r) for r in results], indent=2))
        else:
            print(f"\nSearch results for '{args.query}' (type: {args.type}):")
            for session in results:
                print(format_session(session))
            
            if not results:
                print("No results found.")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()