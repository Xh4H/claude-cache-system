#!/usr/bin/env python3
"""
Claude Cache Security Enhanced v3.0
Optimized for large-scale security analysis with git integration
"""

import os
import json
import hashlib
import gzip
import time
import sqlite3
import logging
import glob
import psutil
import gc
import asyncio
import aiofiles
import aiosqlite
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Set, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager
from threading import Lock, Event
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import queue
import mimetypes
import mmap
from cachetools import LRUCache, TTLCache
from collections import defaultdict
import numpy as np
from enum import Enum
import git  # GitPython for git integration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileType(Enum):
    """File types for optimized handling"""
    SOURCE_CODE = "source"
    CONFIG = "config"
    BINARY = "binary"
    DOCUMENTATION = "docs"
    DATA = "data"
    SECURITY_SENSITIVE = "security"

@dataclass
class SecurityPattern:
    """Security pattern for vulnerability detection"""
    pattern: str
    severity: str
    description: str
    file_types: List[str]
    regex: Optional[re.Pattern] = None
    
    def __post_init__(self):
        if self.pattern and not self.regex:
            self.regex = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)

@dataclass
class GitChange:
    """Represents a git change for incremental updates"""
    file_path: str
    change_type: str  # added, modified, deleted
    old_sha: Optional[str]
    new_sha: Optional[str]
    diff_lines: List[Tuple[int, str]]  # line number, content

@dataclass
class CacheEntry:
    """Enhanced cache entry with security metadata"""
    path: str
    checksum: str
    size: int
    modified_time: float
    cached_time: float
    compressed: bool
    access_count: int
    last_accessed: float
    content_path: str
    file_type: FileType
    git_sha: Optional[str]
    security_score: float
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    partition_key: Optional[str] = None

@dataclass
class CachePartition:
    """Cache partition for better performance on large codebases"""
    partition_id: str
    path_prefix: str
    db_file: Path
    size_mb: float
    file_count: int
    last_updated: float

class SecurityAnalyzer:
    """Fast security pattern analyzer"""
    
    def __init__(self):
        self.patterns = self._load_security_patterns()
        self._compiled_patterns = {}
        self._init_patterns()
    
    def _load_security_patterns(self) -> List[SecurityPattern]:
        """Load security patterns for vulnerability detection"""
        patterns = [
            # Authentication & Secrets
            SecurityPattern(
                r'(?:password|passwd|pwd)\s*=\s*["\']([^"\']+)["\']',
                "HIGH", "Hardcoded password", [".py", ".js", ".java", ".cs", ".go"]
            ),
            SecurityPattern(
                r'(?:api[_-]?key|apikey)\s*=\s*["\']([^"\']+)["\']',
                "HIGH", "Hardcoded API key", [".py", ".js", ".java", ".cs", ".go", ".yml", ".yaml"]
            ),
            SecurityPattern(
                r'(?:secret|token)\s*=\s*["\']([^"\']+)["\']',
                "HIGH", "Hardcoded secret/token", [".py", ".js", ".java", ".cs", ".go"]
            ),
            
            # SQL Injection
            SecurityPattern(
                r'(?:execute|query)\s*\(\s*["\'].*?\%s.*?["\'].*?\%.*?\)',
                "HIGH", "Potential SQL injection", [".py", ".php", ".java"]
            ),
            SecurityPattern(
                r'(?:execute|query)\s*\(\s*f["\'].*?\{.*?\}.*?["\']',
                "HIGH", "SQL injection via f-string", [".py"]
            ),
            
            # Command Injection
            SecurityPattern(
                r'os\.system\s*\([^)]*\+[^)]*\)',
                "CRITICAL", "Command injection risk", [".py"]
            ),
            SecurityPattern(
                r'subprocess\.(?:call|run|Popen)\s*\([^,\)]*\+[^,\)]*',
                "HIGH", "Command injection via subprocess", [".py"]
            ),
            SecurityPattern(
                r'eval\s*\([^)]*(?:request|input|argv)',
                "CRITICAL", "Code injection via eval", [".py", ".js", ".php"]
            ),
            
            # Path Traversal
            SecurityPattern(
                r'(?:open|file)\s*\([^)]*\.\.[/\\]',
                "MEDIUM", "Path traversal vulnerability", [".py", ".js", ".java"]
            ),
            
            # Cryptography
            SecurityPattern(
                r'(?:MD5|SHA1)\s*\(',
                "MEDIUM", "Weak cryptographic hash", [".py", ".js", ".java", ".cs"]
            ),
            SecurityPattern(
                r'random\.random\s*\(\)',
                "LOW", "Insecure random for security", [".py"]
            ),
            
            # CORS/Security Headers
            SecurityPattern(
                r'Access-Control-Allow-Origin.*?\*',
                "MEDIUM", "Overly permissive CORS", [".py", ".js", ".java"]
            ),
            
            # Deserialization
            SecurityPattern(
                r'pickle\.loads?\s*\(',
                "HIGH", "Unsafe deserialization", [".py"]
            ),
            SecurityPattern(
                r'yaml\.load\s*\([^,)]*\)',
                "HIGH", "Unsafe YAML loading", [".py"]
            ),
        ]
        return patterns
    
    def _init_patterns(self):
        """Pre-compile regex patterns for performance"""
        for pattern in self.patterns:
            if pattern.regex:
                self._compiled_patterns[pattern.pattern] = pattern.regex
    
    def analyze_content(self, content: str, file_path: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Analyze content for security vulnerabilities"""
        vulnerabilities = []
        security_score = 100.0
        
        file_ext = Path(file_path).suffix.lower()
        
        for pattern in self.patterns:
            if file_ext not in pattern.file_types:
                continue
            
            if pattern.regex:
                matches = pattern.regex.findall(content)
                if matches:
                    vuln = {
                        "type": pattern.description,
                        "severity": pattern.severity,
                        "pattern": pattern.pattern[:50] + "...",
                        "matches": len(matches),
                        "file": file_path
                    }
                    vulnerabilities.append(vuln)
                    
                    # Adjust security score based on severity
                    if pattern.severity == "CRITICAL":
                        security_score -= 30
                    elif pattern.severity == "HIGH":
                        security_score -= 20
                    elif pattern.severity == "MEDIUM":
                        security_score -= 10
                    else:
                        security_score -= 5
        
        return max(0, security_score), vulnerabilities

class GitIntegration:
    """Git integration for incremental cache updates"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = None
        self._init_repo()
    
    def _init_repo(self):
        """Initialize git repository"""
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            logger.warning(f"Not a git repository: {self.repo_path}")
    
    def get_changed_files(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> List[GitChange]:
        """Get changed files between two git references"""
        if not self.repo:
            return []
        
        changes = []
        try:
            diff = self.repo.git.diff(base_ref, target_ref, name_status=True)
            for line in diff.split('\n'):
                if not line:
                    continue
                    
                parts = line.split('\t')
                if len(parts) >= 2:
                    change_type = parts[0]
                    file_path = parts[1]
                    
                    change = GitChange(
                        file_path=str(self.repo_path / file_path),
                        change_type=self._parse_change_type(change_type),
                        old_sha=None,
                        new_sha=None,
                        diff_lines=[]
                    )
                    changes.append(change)
        except Exception as e:
            logger.error(f"Error getting git changes: {e}")
        
        return changes
    
    def _parse_change_type(self, git_status: str) -> str:
        """Parse git status code to change type"""
        if git_status.startswith('A'):
            return 'added'
        elif git_status.startswith('M'):
            return 'modified'
        elif git_status.startswith('D'):
            return 'deleted'
        elif git_status.startswith('R'):
            return 'renamed'
        else:
            return 'unknown'
    
    def get_file_at_commit(self, file_path: str, commit_sha: str) -> Optional[str]:
        """Get file content at specific commit"""
        if not self.repo:
            return None
        
        try:
            relative_path = Path(file_path).relative_to(self.repo_path)
            return self.repo.git.show(f"{commit_sha}:{relative_path}")
        except Exception as e:
            logger.error(f"Error getting file at commit: {e}")
            return None

class ClaudeCacheSecurityEnhanced:
    """Enhanced cache system for security analysis of large codebases"""
    
    def __init__(self, cache_dir: str = None, allowed_dirs: List[str] = None):
        """Initialize enhanced cache system"""
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.claude/cache"))
        self.config_file = self.cache_dir / "config" / "security_cache.json"
        self.db_file = self.cache_dir / "files" / "security_index.db"
        
        # Security: Define allowed directories
        self.allowed_dirs = allowed_dirs or [
            os.path.expanduser("~"),
            "/tmp",
        ]
        
        # Thread safety
        self._db_lock = Lock()
        self._stats_lock = Lock()
        self._partition_lock = Lock()
        
        # Performance executors
        self._io_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="io")
        self._cpu_executor = ProcessPoolExecutor(max_workers=4)
        
        # Initialize components
        self.security_analyzer = SecurityAnalyzer()
        self.git_integration = None
        
        # Cache partitions for large codebases
        self.partitions: Dict[str, CachePartition] = {}
        self._init_partitions()
        
        # Multi-level caching
        self._memory_cache = LRUCache(maxsize=1000)  # Hot cache
        self._ttl_cache = TTLCache(maxsize=5000, ttl=3600)  # Warm cache
        
        # Connection pools
        self._db_pools: Dict[str, sqlite3.Connection] = {}
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize database
        self._init_database()
        
        # Statistics
        self.stats = defaultdict(int)
        
        # Background workers
        self._start_background_workers()
        
        logger.info(f"Security-enhanced cache initialized at {self.cache_dir}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load enhanced configuration"""
        default_config = {
            "cache_size_limit_gb": 10.0,
            "partition_size_mb": 500,
            "max_file_size_mb": 50,
            "compression_threshold_kb": 100,
            "security_analysis": True,
            "git_integration": True,
            "parallel_workers": 8,
            "memory_cache_size": 1000,
            "ttl_cache_size": 5000,
            "ttl_seconds": 3600,
            "incremental_update_interval": 300,
            "vulnerability_scan_interval": 3600,
            "allowed_extensions": [
                ".py", ".js", ".ts", ".java", ".cs", ".go", ".php", ".rb",
                ".c", ".cpp", ".h", ".hpp", ".rs", ".swift", ".kt",
                ".yml", ".yaml", ".json", ".xml", ".conf", ".ini",
                ".md", ".txt", ".sql", ".sh", ".bash", ".ps1"
            ],
            "security_patterns_file": "security_patterns.json",
            "partition_strategy": "prefix",  # prefix, hash, size
            "index_strategy": "btree",  # btree, hash, rtree
        }
        
        if self.config_file.exists():
            with open(self.config_file) as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_partitions(self):
        """Initialize cache partitions for better performance"""
        partition_dir = self.cache_dir / "partitions"
        partition_dir.mkdir(exist_ok=True)
        
        # Create partitions based on configuration
        partition_count = self.config.get("partition_count", 4)
        
        for i in range(partition_count):
            partition_id = f"partition_{i}"
            partition = CachePartition(
                partition_id=partition_id,
                path_prefix="",
                db_file=partition_dir / f"{partition_id}.db",
                size_mb=0,
                file_count=0,
                last_updated=time.time()
            )
            self.partitions[partition_id] = partition
    
    def _get_partition_for_path(self, file_path: str) -> str:
        """Determine which partition a file should go to"""
        # Simple hash-based partitioning
        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        partition_index = int(path_hash[:2], 16) % len(self.partitions)
        return f"partition_{partition_index}"
    
    def _init_database(self):
        """Initialize enhanced database schema"""
        # Main index database
        with self._get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_cache (
                    path TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    cached_time REAL NOT NULL,
                    compressed BOOLEAN NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL,
                    content_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    git_sha TEXT,
                    security_score REAL DEFAULT 100.0,
                    vulnerabilities TEXT,
                    metadata TEXT,
                    partition_key TEXT,
                    FOREIGN KEY (partition_key) REFERENCES partitions(partition_id)
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_path ON security_cache(path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_git_sha ON security_cache(git_sha)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_security_score ON security_cache(security_score)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_partition ON security_cache(partition_key)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON security_cache(file_type)')
            
            # Git tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS git_commits (
                    commit_sha TEXT PRIMARY KEY,
                    commit_time REAL NOT NULL,
                    files_changed INTEGER NOT NULL,
                    cached_time REAL NOT NULL
                )
            ''')
            
            # Vulnerability tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    vulnerability_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    line_number INTEGER,
                    detected_time REAL NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (file_path) REFERENCES security_cache(path)
                )
            ''')
            
            # Performance metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    timestamp REAL PRIMARY KEY,
                    cache_hits INTEGER,
                    cache_misses INTEGER,
                    avg_response_time_ms REAL,
                    memory_usage_mb REAL,
                    partition_balance TEXT
                )
            ''')
            
            conn.commit()
        
        # Initialize partition databases
        for partition in self.partitions.values():
            self._init_partition_db(partition)
    
    def _init_partition_db(self, partition: CachePartition):
        """Initialize partition-specific database"""
        with sqlite3.connect(str(partition.db_file)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS partition_cache (
                    path TEXT PRIMARY KEY,
                    content BLOB,
                    compressed BOOLEAN,
                    size INTEGER,
                    checksum TEXT,
                    FOREIGN KEY (path) REFERENCES security_cache(path)
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_path ON partition_cache(path)')
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self, partition_id: str = None) -> sqlite3.Connection:
        """Get database connection with pooling"""
        db_file = self.partitions[partition_id].db_file if partition_id else self.db_file
        
        with self._db_lock:
            if str(db_file) not in self._db_pools:
                conn = sqlite3.connect(str(db_file), check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                self._db_pools[str(db_file)] = conn
            
            yield self._db_pools[str(db_file)]
    
    def _start_background_workers(self):
        """Start background workers for async operations"""
        # Incremental update worker
        self._update_thread = Thread(target=self._incremental_update_worker, daemon=True)
        self._update_thread.start()
        
        # Vulnerability scan worker
        self._scan_thread = Thread(target=self._vulnerability_scan_worker, daemon=True)
        self._scan_thread.start()
        
        # Partition rebalance worker
        self._rebalance_thread = Thread(target=self._partition_rebalance_worker, daemon=True)
        self._rebalance_thread.start()
    
    def _incremental_update_worker(self):
        """Background worker for incremental git updates"""
        interval = self.config.get("incremental_update_interval", 300)
        
        while True:
            try:
                time.sleep(interval)
                if self.git_integration:
                    self.update_from_git()
            except Exception as e:
                logger.error(f"Incremental update error: {e}")
    
    def _vulnerability_scan_worker(self):
        """Background worker for periodic vulnerability scanning"""
        interval = self.config.get("vulnerability_scan_interval", 3600)
        
        while True:
            try:
                time.sleep(interval)
                self.scan_all_vulnerabilities()
            except Exception as e:
                logger.error(f"Vulnerability scan error: {e}")
    
    def _partition_rebalance_worker(self):
        """Background worker for partition rebalancing"""
        interval = 3600  # 1 hour
        
        while True:
            try:
                time.sleep(interval)
                self._rebalance_partitions()
            except Exception as e:
                logger.error(f"Partition rebalance error: {e}")
    
    def set_git_repo(self, repo_path: str):
        """Set git repository for incremental updates"""
        self.git_integration = GitIntegration(repo_path)
        logger.info(f"Git integration enabled for: {repo_path}")
    
    def cache_file_enhanced(self, file_path: str, force: bool = False) -> Optional[CacheEntry]:
        """Enhanced file caching with security analysis"""
        if not self._validate_path(file_path):
            return None
        
        try:
            path = Path(file_path).resolve()
            
            # Check if already cached and up-to-date
            if not force:
                cached_entry = self._get_cache_entry(str(path))
                if cached_entry and cached_entry.modified_time >= path.stat().st_mtime:
                    self._update_access_stats(str(path))
                    return cached_entry
            
            # Determine file type
            file_type = self._determine_file_type(path)
            
            # Read file content
            content = self._read_file_efficiently(path)
            if content is None:
                return None
            
            # Security analysis
            security_score = 100.0
            vulnerabilities = []
            
            if self.config.get("security_analysis", True) and file_type == FileType.SOURCE_CODE:
                security_score, vulnerabilities = self.security_analyzer.analyze_content(
                    content.decode('utf-8', errors='ignore'), 
                    str(path)
                )
            
            # Calculate checksum
            checksum = hashlib.sha256(content).hexdigest()
            
            # Determine partition
            partition_id = self._get_partition_for_path(str(path))
            
            # Compress if needed
            compressed = False
            if len(content) > self.config.get("compression_threshold_kb", 100) * 1024:
                content = gzip.compress(content, compresslevel=6)
                compressed = True
            
            # Get git SHA if available
            git_sha = None
            if self.git_integration:
                try:
                    git_sha = self.git_integration.repo.git.hash_object(str(path))
                except:
                    pass
            
            # Create cache entry
            entry = CacheEntry(
                path=str(path),
                checksum=checksum,
                size=path.stat().st_size,
                modified_time=path.stat().st_mtime,
                cached_time=time.time(),
                compressed=compressed,
                access_count=1,
                last_accessed=time.time(),
                content_path=f"{partition_id}/{checksum}",
                file_type=file_type,
                git_sha=git_sha,
                security_score=security_score,
                vulnerabilities=vulnerabilities,
                partition_key=partition_id,
                metadata={
                    "mime_type": mimetypes.guess_type(str(path))[0],
                    "encoding": "utf-8",
                    "lines": content.decode('utf-8', errors='ignore').count('\n') if not compressed else -1
                }
            )
            
            # Store in partition
            self._store_in_partition(entry, content, partition_id)
            
            # Update main index
            self._update_index(entry)
            
            # Update caches
            with self._db_lock:
                self._memory_cache[str(path)] = entry
                self._ttl_cache[str(path)] = entry
            
            # Store vulnerabilities
            if vulnerabilities:
                self._store_vulnerabilities(str(path), vulnerabilities)
            
            self.stats['cached_files'] += 1
            
            return entry
            
        except Exception as e:
            logger.error(f"Error caching file {file_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    def _determine_file_type(self, path: Path) -> FileType:
        """Determine file type for optimized handling"""
        ext = path.suffix.lower()
        
        source_extensions = {'.py', '.js', '.ts', '.java', '.cs', '.go', '.php', '.rb', '.c', '.cpp', '.rs'}
        config_extensions = {'.yml', '.yaml', '.json', '.xml', '.conf', '.ini', '.toml'}
        doc_extensions = {'.md', '.txt', '.rst', '.adoc'}
        
        if ext in source_extensions:
            return FileType.SOURCE_CODE
        elif ext in config_extensions:
            return FileType.CONFIG
        elif ext in doc_extensions:
            return FileType.DOCUMENTATION
        elif path.name in {'Dockerfile', 'Makefile', '.env', '.gitignore'}:
            return FileType.CONFIG
        else:
            return FileType.DATA
    
    def _read_file_efficiently(self, path: Path) -> Optional[bytes]:
        """Read file efficiently based on size"""
        try:
            file_size = path.stat().st_size
            max_size = self.config.get("max_file_size_mb", 50) * 1024 * 1024
            
            if file_size > max_size:
                logger.warning(f"File too large: {path} ({file_size} bytes)")
                return None
            
            # Use memory mapping for large files
            if file_size > 1024 * 1024:  # 1MB
                with open(path, 'rb') as f:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                        return bytes(mmapped)
            else:
                return path.read_bytes()
                
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return None
    
    def _store_in_partition(self, entry: CacheEntry, content: bytes, partition_id: str):
        """Store content in partition database"""
        with self._get_db_connection(partition_id) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO partition_cache 
                (path, content, compressed, size, checksum)
                VALUES (?, ?, ?, ?, ?)
            ''', (entry.path, content, entry.compressed, entry.size, entry.checksum))
            conn.commit()
    
    def _update_index(self, entry: CacheEntry):
        """Update main index with cache entry"""
        with self._get_db_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO security_cache 
                (path, checksum, size, modified_time, cached_time, compressed,
                 access_count, last_accessed, content_path, file_type, git_sha,
                 security_score, vulnerabilities, metadata, partition_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.path, entry.checksum, entry.size, entry.modified_time,
                entry.cached_time, entry.compressed, entry.access_count,
                entry.last_accessed, entry.content_path, entry.file_type.value,
                entry.git_sha, entry.security_score,
                json.dumps(entry.vulnerabilities), json.dumps(entry.metadata),
                entry.partition_key
            ))
            conn.commit()
    
    def _store_vulnerabilities(self, file_path: str, vulnerabilities: List[Dict[str, Any]]):
        """Store detected vulnerabilities"""
        with self._get_db_connection() as conn:
            for vuln in vulnerabilities:
                conn.execute('''
                    INSERT INTO vulnerabilities 
                    (file_path, vulnerability_type, severity, line_number, detected_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    file_path, vuln['type'], vuln['severity'], 
                    vuln.get('line_number', -1), time.time()
                ))
            conn.commit()
    
    def update_from_git(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD"):
        """Update cache based on git changes"""
        if not self.git_integration:
            logger.warning("Git integration not configured")
            return
        
        changes = self.git_integration.get_changed_files(base_ref, target_ref)
        
        for change in changes:
            if change.change_type == 'deleted':
                self._remove_from_cache(change.file_path)
            else:
                self.cache_file_enhanced(change.file_path, force=True)
        
        logger.info(f"Updated cache for {len(changes)} changed files")
    
    def warm_cache_parallel(self, patterns: List[str], max_workers: int = None) -> Dict[str, Any]:
        """Parallel cache warming for large codebases"""
        start_time = time.time()
        max_workers = max_workers or self.config.get("parallel_workers", 8)
        
        # Collect all files matching patterns
        all_files = []
        for pattern in patterns:
            all_files.extend(glob.glob(pattern, recursive=True))
        
        # Remove duplicates and filter
        all_files = list(set(all_files))
        all_files = [f for f in all_files if self._should_cache_file(f)]
        
        # Parallel caching
        cached_count = 0
        error_count = 0
        total_size = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.cache_file_enhanced, file_path): file_path
                for file_path in all_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    entry = future.result()
                    if entry:
                        cached_count += 1
                        total_size += entry.size
                except Exception as e:
                    logger.error(f"Error caching {file_path}: {e}")
                    error_count += 1
        
        duration = time.time() - start_time
        
        return {
            "files_processed": len(all_files),
            "files_cached": cached_count,
            "errors": error_count,
            "total_size_mb": total_size / 1024 / 1024,
            "duration_seconds": duration,
            "files_per_second": cached_count / duration if duration > 0 else 0
        }
    
    def _should_cache_file(self, file_path: str) -> bool:
        """Check if file should be cached"""
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return False
            
            # Check extension
            ext = path.suffix.lower()
            allowed_extensions = self.config.get("allowed_extensions", [])
            if ext not in allowed_extensions:
                return False
            
            # Check size
            max_size = self.config.get("max_file_size_mb", 50) * 1024 * 1024
            if path.stat().st_size > max_size:
                return False
            
            # Check if in allowed directories
            return self._validate_path(str(path))
            
        except Exception:
            return False
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        with self._get_db_connection() as conn:
            # Overall statistics
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_files,
                    AVG(security_score) as avg_security_score,
                    COUNT(CASE WHEN security_score < 50 THEN 1 END) as high_risk_files
                FROM security_cache
            ''')
            stats = dict(cursor.fetchone())
            
            # Vulnerability breakdown
            cursor = conn.execute('''
                SELECT 
                    severity,
                    vulnerability_type,
                    COUNT(*) as count
                FROM vulnerabilities
                WHERE resolved = 0
                GROUP BY severity, vulnerability_type
                ORDER BY severity, count DESC
            ''')
            vulnerabilities = [dict(row) for row in cursor.fetchall()]
            
            # Most vulnerable files
            cursor = conn.execute('''
                SELECT 
                    path,
                    security_score,
                    vulnerabilities
                FROM security_cache
                WHERE security_score < 70
                ORDER BY security_score ASC
                LIMIT 20
            ''')
            vulnerable_files = [dict(row) for row in cursor.fetchall()]
            
            return {
                "summary": stats,
                "vulnerabilities": vulnerabilities,
                "vulnerable_files": vulnerable_files,
                "generated_at": datetime.now().isoformat()
            }
    
    def scan_all_vulnerabilities(self):
        """Scan all cached files for vulnerabilities"""
        with self._get_db_connection() as conn:
            cursor = conn.execute('SELECT path FROM security_cache WHERE file_type = ?', 
                                (FileType.SOURCE_CODE.value,))
            files = [row[0] for row in cursor.fetchall()]
        
        updated_count = 0
        for file_path in files:
            try:
                content = self.get_cached_content(file_path)
                if content:
                    score, vulns = self.security_analyzer.analyze_content(
                        content.decode('utf-8', errors='ignore'),
                        file_path
                    )
                    
                    # Update security score
                    with self._get_db_connection() as conn:
                        conn.execute('''
                            UPDATE security_cache 
                            SET security_score = ?, vulnerabilities = ?
                            WHERE path = ?
                        ''', (score, json.dumps(vulns), file_path))
                        conn.commit()
                    
                    # Update vulnerabilities table
                    if vulns:
                        self._store_vulnerabilities(file_path, vulns)
                    
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
        
        logger.info(f"Vulnerability scan completed: {updated_count} files scanned")
    
    def get_cached_content(self, file_path: str) -> Optional[bytes]:
        """Retrieve cached content"""
        # Check memory caches first
        with self._db_lock:
            if file_path in self._memory_cache:
                entry = self._memory_cache[file_path]
                return self._read_cached_content(entry)
            
            if file_path in self._ttl_cache:
                entry = self._ttl_cache[file_path]
                self._memory_cache[file_path] = entry  # Promote to hot cache
                return self._read_cached_content(entry)
        
        # Check database
        entry = self._get_cache_entry(file_path)
        if entry:
            return self._read_cached_content(entry)
        
        return None
    
    def _read_cached_content(self, entry: CacheEntry) -> Optional[bytes]:
        """Read content from partition"""
        try:
            with self._get_db_connection(entry.partition_key) as conn:
                cursor = conn.execute(
                    'SELECT content, compressed FROM partition_cache WHERE path = ?',
                    (entry.path,)
                )
                row = cursor.fetchone()
                
                if row:
                    content = row['content']
                    if row['compressed']:
                        content = gzip.decompress(content)
                    return content
                    
        except Exception as e:
            logger.error(f"Error reading cached content: {e}")
        
        return None
    
    def _get_cache_entry(self, file_path: str) -> Optional[CacheEntry]:
        """Get cache entry from database"""
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM security_cache WHERE path = ?',
                (file_path,)
            )
            row = cursor.fetchone()
            
            if row:
                return CacheEntry(
                    path=row['path'],
                    checksum=row['checksum'],
                    size=row['size'],
                    modified_time=row['modified_time'],
                    cached_time=row['cached_time'],
                    compressed=bool(row['compressed']),
                    access_count=row['access_count'],
                    last_accessed=row['last_accessed'],
                    content_path=row['content_path'],
                    file_type=FileType(row['file_type']),
                    git_sha=row['git_sha'],
                    security_score=row['security_score'],
                    vulnerabilities=json.loads(row['vulnerabilities'] or '[]'),
                    metadata=json.loads(row['metadata'] or '{}'),
                    partition_key=row['partition_key']
                )
        
        return None
    
    def _update_access_stats(self, file_path: str):
        """Update access statistics"""
        with self._get_db_connection() as conn:
            conn.execute('''
                UPDATE security_cache 
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE path = ?
            ''', (time.time(), file_path))
            conn.commit()
        
        self.stats['cache_hits'] += 1
    
    def _rebalance_partitions(self):
        """Rebalance partitions for optimal performance"""
        # Analyze partition sizes
        partition_stats = {}
        
        for partition_id, partition in self.partitions.items():
            with self._get_db_connection(partition_id) as conn:
                cursor = conn.execute('SELECT COUNT(*) as count, SUM(size) as total_size FROM partition_cache')
                row = cursor.fetchone()
                partition_stats[partition_id] = {
                    'count': row['count'] or 0,
                    'size': row['total_size'] or 0
                }
        
        # Check if rebalancing is needed
        sizes = [stats['size'] for stats in partition_stats.values()]
        if not sizes or max(sizes) / (min(sizes) + 1) < 2:
            return  # Partitions are reasonably balanced
        
        logger.info("Starting partition rebalancing...")
        
        # TODO: Implement actual rebalancing logic
        # This would involve moving files between partitions
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        with self._stats_lock:
            hit_rate = (self.stats['cache_hits'] / 
                       (self.stats['cache_hits'] + self.stats.get('cache_misses', 1))) * 100
            
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Partition balance
            partition_sizes = {}
            for partition_id in self.partitions:
                with self._get_db_connection(partition_id) as conn:
                    cursor = conn.execute('SELECT COUNT(*) as count FROM partition_cache')
                    partition_sizes[partition_id] = cursor.fetchone()['count']
            
            metrics = {
                "cache_hits": self.stats['cache_hits'],
                "cache_misses": self.stats.get('cache_misses', 0),
                "hit_rate_percent": hit_rate,
                "cached_files": self.stats.get('cached_files', 0),
                "total_operations": sum(self.stats.values()),
                "errors": self.stats.get('errors', 0),
                "memory_usage_mb": memory_info.rss / 1024 / 1024,
                "memory_cache_size": len(self._memory_cache),
                "ttl_cache_size": len(self._ttl_cache),
                "partition_balance": partition_sizes,
                "io_threads": self._io_executor._threads,
                "cpu_workers": self._cpu_executor._max_workers
            }
            
            # Store metrics
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO performance_metrics
                    (timestamp, cache_hits, cache_misses, avg_response_time_ms, 
                     memory_usage_mb, partition_balance)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    time.time(), metrics['cache_hits'], metrics['cache_misses'],
                    0, metrics['memory_usage_mb'], json.dumps(partition_sizes)
                ))
                conn.commit()
            
            return metrics
    
    def _validate_path(self, file_path: str) -> bool:
        """Validate that path is within allowed directories"""
        try:
            resolved_path = Path(file_path).resolve()
            
            for allowed_dir in self.allowed_dirs:
                allowed_path = Path(allowed_dir).resolve()
                try:
                    resolved_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def _remove_from_cache(self, file_path: str):
        """Remove file from cache"""
        entry = self._get_cache_entry(file_path)
        if not entry:
            return
        
        # Remove from partition
        with self._get_db_connection(entry.partition_key) as conn:
            conn.execute('DELETE FROM partition_cache WHERE path = ?', (file_path,))
            conn.commit()
        
        # Remove from main index
        with self._get_db_connection() as conn:
            conn.execute('DELETE FROM security_cache WHERE path = ?', (file_path,))
            conn.execute('DELETE FROM vulnerabilities WHERE file_path = ?', (file_path,))
            conn.commit()
        
        # Remove from memory caches
        with self._db_lock:
            self._memory_cache.pop(file_path, None)
            self._ttl_cache.pop(file_path, None)
    
    def cleanup(self):
        """Cleanup resources"""
        self._io_executor.shutdown(wait=True)
        self._cpu_executor.shutdown(wait=True)
        
        for conn in self._db_pools.values():
            conn.close()


# CLI Interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Cache Security Enhanced")
    parser.add_argument("command", choices=["warm", "scan", "report", "metrics"])
    parser.add_argument("--patterns", nargs="+", help="File patterns to cache")
    parser.add_argument("--repo", help="Git repository path")
    
    args = parser.parse_args()
    
    cache = ClaudeCacheSecurityEnhanced()
    
    if args.command == "warm":
        if args.patterns:
            result = cache.warm_cache_parallel(args.patterns)
            print(json.dumps(result, indent=2))
    
    elif args.command == "scan":
        cache.scan_all_vulnerabilities()
        print("Vulnerability scan completed")
    
    elif args.command == "report":
        report = cache.get_security_report()
        print(json.dumps(report, indent=2))
    
    elif args.command == "metrics":
        metrics = cache.get_performance_metrics()
        print(json.dumps(metrics, indent=2))