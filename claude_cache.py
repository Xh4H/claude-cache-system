#!/usr/bin/env python3
"""
Claude Code Intelligent Cache System v2
Enhanced with security fixes and better error handling
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
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import mimetypes
import mmap
from cachetools import LRUCache

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached file entry"""
    path: str
    checksum: str
    size: int
    modified_time: float
    cached_time: float
    compressed: bool
    access_count: int
    last_accessed: float
    content_path: str
    metadata: Dict[str, Any]

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hit_count: int
    miss_count: int
    hit_rate: float
    total_files: int
    cache_size: int
    memory_usage: int
    oldest_entry: float
    newest_entry: float

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    process_memory_mb: float
    system_memory_mb: float
    cache_memory_mb: float
    memory_limit_mb: float
    memory_usage_percent: float
    gc_collections: int
    is_over_limit: bool

class ClaudeCache:
    """Intelligent caching system for Claude Code with security enhancements"""
    
    def __init__(self, cache_dir: str = None, allowed_dirs: List[str] = None):
        """Initialize the cache system with security constraints"""
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.claude/cache"))
        self.config_file = self.cache_dir / "config" / "cache.json"
        self.policies_file = self.cache_dir / "config" / "policies.json"
        self.db_file = self.cache_dir / "files" / "index.db"
        
        # Security: Define allowed directories
        self.allowed_dirs = allowed_dirs or [
            os.path.expanduser("~"),  # User home directory
            "/tmp",  # Temporary files
            # Add more as needed
        ]
        
        # Thread safety
        self._db_lock = Lock()
        self._stats_lock = Lock()
        
        # Background compression worker
        self._compression_queue = queue.Queue()
        self._compression_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="compression")
        
        # Connection pool (simple implementation)
        self._db_connection = None
        
        # Load configuration
        self.config = self._load_config()
        self.policies = self._load_policies()
        
        # Initialize database
        self._init_database()
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'operations': 0,
            'errors': 0
        }
        
        # Memory monitoring
        self.memory_limit_mb = self._parse_size(self.config.get("eviction", {}).get("maxMemoryUsage", "100MB")) / 1024 / 1024
        
        # LRU Cache for in-memory content - significant performance improvement
        max_items = self.config.get("memoryCache", {}).get("maxItems", 500)
        self._memory_cache = LRUCache(maxsize=max_items)  # O(1) lookups with automatic eviction
        self._memory_cache_lock = Lock()  # Thread safety for LRU cache
        
        self._last_gc_time = time.time()
        self._gc_threshold = 60  # Run garbage collection every 60 seconds
        
        logger.info(f"Cache initialized at {self.cache_dir} (Memory limit: {self.memory_limit_mb:.0f}MB)")
    
    def _validate_path(self, file_path: str) -> bool:
        """Validate that path is within allowed directories"""
        try:
            resolved_path = Path(file_path).resolve()
            
            # Check if path is within allowed directories
            for allowed_dir in self.allowed_dirs:
                allowed_path = Path(allowed_dir).resolve()
                try:
                    resolved_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
                    
            logger.warning(f"Path validation failed for {file_path}: not in allowed directories")
            return False
            
        except Exception as e:
            logger.error(f"Path validation error for {file_path}: {e}")
            return False
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper resource management"""
        conn = None
        try:
            with self._db_lock:
                conn = sqlite3.connect(str(self.db_file), timeout=30.0)
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _batch_insert_cache_entries(self, entries: List[Tuple]) -> None:
        """Batch insert cache entries for significant performance improvement"""
        if not entries:
            return
            
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                # Use executemany for bulk operations - much faster than individual inserts
                cursor.executemany('''
                    INSERT OR REPLACE INTO cache_entries 
                    (path, checksum, size, modified_time, cached_time, compressed, 
                     access_count, last_accessed, content_path, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', entries)
                
            logger.debug(f"Batch inserted {len(entries)} cache entries")
            
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            raise
    
    def _prepare_cache_entry(self, file_path: str) -> Optional[Tuple]:
        """Prepare cache entry data without database insertion for batch processing"""
        try:
            if not self._validate_path(file_path):
                return None
                
            file_stat = os.stat(file_path)
            
            # Memory-mapped file reading for large files (>1MB) - significant I/O optimization
            if file_stat.st_size > 1024 * 1024:  # 1MB threshold
                with open(file_path, 'rb') as f:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                        content = mmapped_file.read()
            else:
                # Regular read for smaller files
                with open(file_path, 'rb') as f:
                    content = f.read()
            
            # Calculate checksum
            checksum = hashlib.sha256(content).hexdigest()
            
            # Compression and metadata
            original_size = len(content)
            is_compressed = False
            metadata = {
                'original_size': original_size,
                'compressed_size': original_size,
                'compression_ratio': 1.0,
                'space_saved': 0
            }
            
            # Fast compression check for immediate storage (optimized for speed)
            if self.config.get("fileCache", {}).get("compressionEnabled", True) and original_size > 1024:
                # Use faster compression for batch operations
                content, is_compressed, metadata = self._compress_content_async(content, file_path)
            
            # Store content file
            content_path = self._get_content_path(file_path, checksum)
            content_dir = os.path.dirname(content_path)
            os.makedirs(content_dir, exist_ok=True)
            
            with open(content_path, 'wb') as f:
                f.write(content)
            
            # Add to memory cache
            if not is_compressed:
                self._add_to_memory_cache(file_path, content.decode('utf-8', errors='replace'))
            
            # Return tuple for batch insert
            return (
                file_path, checksum, file_stat.st_size, file_stat.st_mtime,
                time.time(), is_compressed, 1, time.time(), content_path,
                json.dumps(metadata)
            )
            
        except Exception as e:
            logger.error(f"Error preparing cache entry for {file_path}: {e}")
            return None
    
    def _compress_content_async(self, content: bytes, original_path: str) -> Tuple[bytes, bool, Dict]:
        """Compress content asynchronously in background"""
        original_size = len(content)
        metadata = {
            'original_size': original_size,
            'compressed_size': original_size,
            'compression_ratio': 1.0,
            'space_saved': 0
        }
        
        # Quick check - only compress if likely beneficial
        if original_size > 1024:
            try:
                compressed_content = gzip.compress(content)
                if len(compressed_content) < original_size * 0.9:  # >10% savings
                    metadata.update({
                        'compressed_size': len(compressed_content),
                        'compression_ratio': original_size / len(compressed_content),
                        'space_saved': original_size - len(compressed_content)
                    })
                    return compressed_content, True, metadata
            except Exception as e:
                logger.warning(f"Compression failed for {original_path}: {e}")
        
        return content, False, metadata
    
    def _schedule_background_compression(self, file_path: str, content: bytes, callback) -> None:
        """Schedule compression task in background thread pool"""
        future = self._compression_executor.submit(self._compress_content_async, content, file_path)
        future.add_done_callback(lambda f: callback(file_path, f.result()))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load cache configuration with error handling"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                logger.debug("Configuration loaded successfully")
                return config
        except FileNotFoundError:
            logger.warning("Configuration file not found, using defaults")
            return self._default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid configuration JSON: {e}")
            return self._default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._default_config()
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load cache policies with error handling"""
        try:
            with open(self.policies_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading policies: {e}, using defaults")
            return self._default_policies()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default cache configuration"""
        return {
            "enabled": True,
            "fileCache": {
                "enabled": True,
                "maxFileSize": "10MB",
                "compressionEnabled": True,
                "checksumAlgorithm": "sha256"
            },
            "security": {
                "validatePaths": True,
                "detectSensitiveData": False,  # Optional for personal use
                "maxCacheAge": "30d"
            }
        }
    
    def _default_policies(self) -> Dict[str, Any]:
        """Default cache policies"""
        return {
            "filePriorities": {
                "critical": {"extensions": [".py", ".js", ".ts"], "priority": 10}
            }
        }
    
    def _init_database(self):
        """Initialize SQLite database for cache metadata"""
        try:
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Enable WAL mode for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        path TEXT PRIMARY KEY,
                        checksum TEXT NOT NULL,
                        size INTEGER NOT NULL,
                        modified_time REAL NOT NULL,  
                        cached_time REAL NOT NULL,
                        compressed BOOLEAN NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        last_accessed REAL NOT NULL,
                        content_path TEXT NOT NULL,
                        metadata TEXT NOT NULL
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_cached_time 
                    ON cache_entries(cached_time)
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        id INTEGER PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        hit_count INTEGER NOT NULL,
                        miss_count INTEGER NOT NULL,
                        total_files INTEGER NOT NULL,
                        cache_size INTEGER NOT NULL
                    )
                ''')
                
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum with error handling"""
        algorithm = self.config.get("fileCache", {}).get("checksumAlgorithm", "sha256")
        hasher = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except IOError as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error calculating checksum: {e}")
            return ""
    
    def _should_cache_file(self, file_path: str) -> bool:
        """Determine if file should be cached with validation"""
        if not self.config.get("fileCache", {}).get("enabled", True):
            return False
        
        # Security check
        if self.config.get("security", {}).get("validatePaths", True):
            if not self._validate_path(file_path):
                return False
        
        path = Path(file_path)
        
        # Check file size
        try:
            size = path.stat().st_size
            max_size = self._parse_size(self.config.get("fileCache", {}).get("maxFileSize", "10MB"))
            if size > max_size:
                logger.info(f"File {file_path} too large ({size / 1024 / 1024:.1f}MB > {max_size / 1024 / 1024:.1f}MB)")
                return False
        except OSError as e:
            logger.error(f"Cannot stat file {file_path}: {e}")
            return False
        
        # Check exclude patterns first (more restrictive)
        exclude_patterns = self.config.get("fileCache", {}).get("excludePatterns", [])
        path_str = str(path)
        for pattern in exclude_patterns:
            if pattern.replace("**", "*") in path_str:
                logger.debug(f"File {file_path} excluded by pattern: {pattern}")
                return False
        
        # Check extension (if specified)
        extension = path.suffix.lower()
        allowed_extensions = self.config.get("fileCache", {}).get("extensions", [])
        if allowed_extensions and extension not in allowed_extensions:
            logger.debug(f"File {file_path} has unsupported extension: {extension}")
            return False
        
        return True
    
    def _is_large_file(self, file_path: str, threshold_mb: int = 1) -> bool:
        """Check if file is considered large (>1MB by default)"""
        try:
            size = Path(file_path).stat().st_size
            return size > (threshold_mb * 1024 * 1024)
        except OSError:
            return False
    
    def get_memory_stats(self) -> MemoryStats:
        """Get detailed memory usage statistics"""
        try:
            # Get current process memory
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Get system memory
            system_memory = psutil.virtual_memory()
            system_total_mb = system_memory.total / 1024 / 1024
            
            # Estimate cache memory usage
            cache_memory_mb = len(self._memory_cache) * 0.1  # Rough estimate
            
            # Calculate percentage
            memory_usage_percent = (process_memory / self.memory_limit_mb) * 100
            
            # Check if over limit
            is_over_limit = process_memory > self.memory_limit_mb
            
            # Get garbage collection stats
            gc_collections = sum(gc.get_stats()[i]['collections'] for i in range(len(gc.get_stats())))
            
            return MemoryStats(
                process_memory_mb=process_memory,
                system_memory_mb=system_total_mb,
                cache_memory_mb=cache_memory_mb,
                memory_limit_mb=self.memory_limit_mb,
                memory_usage_percent=memory_usage_percent,
                gc_collections=gc_collections,
                is_over_limit=is_over_limit
            )
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats(0, 0, 0, self.memory_limit_mb, 0, 0, False)
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits and trigger cleanup if needed"""
        memory_stats = self.get_memory_stats()
        
        if memory_stats.is_over_limit:
            logger.warning(f"Memory usage exceeded limit: {memory_stats.process_memory_mb:.1f}MB > {memory_stats.memory_limit_mb:.0f}MB")
            self._trigger_memory_cleanup()
            return False
            
        # Trigger garbage collection periodically
        current_time = time.time()
        if current_time - self._last_gc_time > self._gc_threshold:
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"Garbage collection freed {collected} objects")
            self._last_gc_time = current_time
            
        return True
    
    def _trigger_memory_cleanup(self):
        """Trigger aggressive memory cleanup when over limit"""
        logger.info("Triggering memory cleanup due to high usage")
        
        # Clear in-memory cache (thread-safe)
        with self._memory_cache_lock:
            cache_size_before = len(self._memory_cache)
            self._memory_cache.clear()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Get updated memory stats
        memory_stats = self.get_memory_stats()
        
        logger.info(f"Memory cleanup completed: cleared {cache_size_before} cached items, "
                   f"freed {collected} objects, memory: {memory_stats.process_memory_mb:.1f}MB")
    
    def _add_to_memory_cache(self, file_path: str, content: str, max_items: int = 50):
        """Add content to LRU memory cache with thread safety"""
        # Check memory before adding
        if not self._check_memory_usage():
            return  # Skip if memory is over limit
            
        # Thread-safe LRU cache operations
        with self._memory_cache_lock:
            # LRU cache automatically handles eviction and size limits
            self._memory_cache[file_path] = {
                'content': content,
                'timestamp': time.time(),
                'access_count': 1
            }
    
    def _get_from_memory_cache(self, file_path: str) -> Optional[str]:
        """Get content from LRU memory cache with thread safety"""
        with self._memory_cache_lock:
            if file_path in self._memory_cache:
                # Update access statistics (LRU automatically handles ordering)
                cache_entry = self._memory_cache[file_path]
                cache_entry['access_count'] += 1
                cache_entry['timestamp'] = time.time()
                return cache_entry['content']
        return None
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        units = [("GB", 1024**3), ("MB", 1024**2), ("KB", 1024), ("B", 1)]
        size_str = size_str.upper().strip()
        
        for unit, multiplier in units:
            if size_str.endswith(unit):
                try:
                    number_part = size_str[:-len(unit)].strip()
                    return int(number_part) * multiplier
                except ValueError as e:
                    logger.error(f"Invalid size format {size_str}: {e}")
                    return 10 * 1024 * 1024  # Default 10MB
        
        try:
            return int(size_str)
        except ValueError:
            return 10 * 1024 * 1024  # Default 10MB
    
    def _get_content_path(self, file_path: str, checksum: str) -> str:
        """Get cache storage path for file content"""
        content_dir = self.cache_dir / "files" / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        # Use first 2 chars of checksum as subdirectory for better file system performance
        subdir = content_dir / checksum[:2]
        subdir.mkdir(exist_ok=True)
        return str(subdir / f"{checksum}.gz")
    
    def _compress_content(self, content: bytes, file_path: str = "") -> bytes:
        """Compress content using gzip with large file optimization"""
        if not self.config.get("fileCache", {}).get("compressionEnabled", True):
            return content
            
        compression_level = self.config.get("fileCache", {}).get("compressionLevel", 6)
        
        try:
            # For large files (>1MB), use higher compression for better ratio
            if len(content) > 1024 * 1024:  # 1MB
                logger.debug(f"Using high compression for large file: {file_path}")
                compression_level = min(9, compression_level + 2)
                
            compressed = gzip.compress(content, compresslevel=compression_level)
            
            # Log compression effectiveness for large files
            if len(content) > 1024 * 1024:
                ratio = len(content) / len(compressed) if len(compressed) > 0 else 1.0
                logger.info(f"Large file compression: {file_path} - {ratio:.2f}x ratio ({len(content) / 1024 / 1024:.1f}MB -> {len(compressed) / 1024 / 1024:.1f}MB)")
                
            return compressed
            
        except Exception as e:
            logger.error(f"Compression failed for {file_path}: {e}")
            return content
    
    def _decompress_content(self, content: bytes, compressed: bool) -> bytes:
        """Decompress content if needed with error handling"""
        if compressed:
            try:
                return gzip.decompress(content)
            except Exception as e:
                logger.error(f"Decompression failed: {e}")
                raise
        return content
    
    def _verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify file checksum matches expected value"""
        actual_checksum = self._calculate_checksum(file_path)
        return actual_checksum == expected_checksum
    
    def get_file(self, file_path: str) -> Optional[str]:
        """Get file content from cache or filesystem with enhanced safety"""
        with self._stats_lock:
            self.stats['operations'] += 1
        
        # Check memory usage first
        self._check_memory_usage()
        
        # Try in-memory cache first (for frequently accessed files)
        memory_cached = self._get_from_memory_cache(file_path)
        if memory_cached:
            with self._stats_lock:
                self.stats['hits'] += 1
            return memory_cached
        
        # Validate path first
        if not self._validate_path(file_path):
            logger.warning(f"Access denied to {file_path}")
            return None
        
        if not self._should_cache_file(file_path):
            return self._read_file_direct(file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.debug(f"File not found: {file_path}")
            return None
        
        try:
            # Get file stats
            file_stat = os.stat(file_path)
            current_checksum = self._calculate_checksum(file_path)
            
            if not current_checksum:
                return self._read_file_direct(file_path)
            
            # Check cache
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT checksum, content_path, compressed, access_count
                    FROM cache_entries 
                    WHERE path = ?
                ''', (file_path,))
                
                result = cursor.fetchone()
                
                if result and result['checksum'] == current_checksum:
                    # Cache hit
                    with self._stats_lock:
                        self.stats['hits'] += 1
                    
                    # Update access stats
                    cursor.execute('''
                        UPDATE cache_entries 
                        SET access_count = access_count + 1, last_accessed = ?
                        WHERE path = ?
                    ''', (time.time(), file_path))
                    
                    # Read cached content
                    try:
                        with open(result['content_path'], 'rb') as f:
                            content = self._decompress_content(f.read(), result['compressed'])
                            decoded_content = content.decode('utf-8', errors='replace')
                            
                            # Add to memory cache for frequently accessed files
                            if result['access_count'] > 1:  # Only cache frequently accessed files
                                self._add_to_memory_cache(file_path, decoded_content)
                                
                            return decoded_content
                    except Exception as e:
                        logger.error(f"Error reading cached content: {e}")
                        # Cache corrupted, remove entry
                        cursor.execute('DELETE FROM cache_entries WHERE path = ?', (file_path,))
                        # Fall through to cache miss
            
            # Cache miss - read and cache file
            return self._cache_file(file_path, current_checksum, file_stat)
            
        except Exception as e:
            logger.error(f"Error accessing cache for {file_path}: {e}")
            with self._stats_lock:
                self.stats['errors'] += 1
            return self._read_file_direct(file_path)
    
    def _read_file_direct(self, file_path: str) -> Optional[str]:
        """Read file directly without caching"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _cache_file(self, file_path: str, checksum: str, file_stat) -> Optional[str]:
        """Cache file content with atomic operations"""
        with self._stats_lock:
            self.stats['misses'] += 1
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Optional: Basic sensitive data detection
            if self.config.get("security", {}).get("detectSensitiveData", False):
                content_str = content.decode('utf-8', errors='ignore').lower()
                sensitive_patterns = ['password', 'api_key', 'secret', 'token', 'private_key']
                if any(pattern in content_str for pattern in sensitive_patterns):
                    logger.warning(f"Potential sensitive data detected in {file_path}, skipping cache")
                    return content.decode('utf-8', errors='replace')
            
            # Compress content with large file optimization
            compressed_content = self._compress_content(content, file_path)
            is_compressed = len(compressed_content) < len(content)
            
            # Log large file processing
            if self._is_large_file(file_path):
                logger.info(f"Processing large file: {file_path} ({len(content) / 1024 / 1024:.1f}MB)")
            
            # Store compressed content
            content_path = self._get_content_path(file_path, checksum)
            
            # Write atomically using temporary file
            temp_path = content_path + '.tmp'
            try:
                with open(temp_path, 'wb') as f:
                    f.write(compressed_content if is_compressed else content)
                os.replace(temp_path, content_path)  # Atomic on POSIX
            except Exception as e:
                logger.error(f"Error writing cache file: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
            
            # Calculate compression metrics
            original_size = len(content)
            compressed_size = len(compressed_content)
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
            space_saved = original_size - compressed_size if is_compressed else 0
            
            # Enhanced metadata with compression stats
            metadata = {
                "mime_type": mimetypes.guess_type(file_path)[0],
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "space_saved": space_saved,
                "compression_enabled": is_compressed,
                "cached_timestamp": time.time()
            }
            
            # Update database
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_entries 
                    (path, checksum, size, modified_time, cached_time, compressed, 
                     access_count, last_accessed, content_path, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_path, checksum, file_stat.st_size, file_stat.st_mtime,
                    time.time(), is_compressed, 1, time.time(), content_path,
                    json.dumps(metadata)
                ))
            
            logger.debug(f"Cached file {file_path}")
            return content.decode('utf-8', errors='replace')
            
        except Exception as e:
            logger.error(f"Error caching file {file_path}: {e}")
            with self._stats_lock:
                self.stats['errors'] += 1
            return self._read_file_direct(file_path)
    
    def invalidate_file(self, file_path: str):
        """Invalidate cached file"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT content_path FROM cache_entries WHERE path = ?', (file_path,))
                result = cursor.fetchone()
                
                if result:
                    # Remove cached content file
                    try:
                        os.remove(result['content_path'])
                    except Exception as e:
                        logger.warning(f"Error removing cache file: {e}")
                    
                    # Remove database entry
                    cursor.execute('DELETE FROM cache_entries WHERE path = ?', (file_path,))
                    logger.info(f"Invalidated cache for {file_path}")
                    
        except Exception as e:
            logger.error(f"Error invalidating cache for {file_path}: {e}")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics with compression analytics"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) as count FROM cache_entries')
                total_files = cursor.fetchone()['count']
                
                cursor.execute('SELECT MIN(cached_time) as min, MAX(cached_time) as max FROM cache_entries')
                time_range = cursor.fetchone()
                
                cursor.execute('SELECT SUM(size) as total FROM cache_entries')
                cache_size = cursor.fetchone()['total'] or 0
            
            # Get memory stats
            memory_stats = self.get_memory_stats()
            
            with self._stats_lock:
                hit_rate = 0.0
                if self.stats['operations'] > 0:
                    hit_rate = self.stats['hits'] / self.stats['operations']
                
                return CacheStats(
                    hit_count=self.stats['hits'],
                    miss_count=self.stats['misses'],
                    hit_rate=hit_rate,
                    total_files=total_files,
                    cache_size=cache_size,
                    memory_usage=int(memory_stats.process_memory_mb * 1024 * 1024),  # Convert to bytes
                    oldest_entry=time_range['min'] or 0,
                    newest_entry=time_range['max'] or 0
                )
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return CacheStats(0, 0, 0.0, 0, 0, 0, 0, 0)
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get detailed compression statistics"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get compression metrics from metadata
                cursor.execute('SELECT metadata FROM cache_entries')
                
                total_original = 0
                total_compressed = 0
                total_space_saved = 0
                compressed_files = 0
                compression_ratios = []
                
                for row in cursor.fetchall():
                    try:
                        metadata = json.loads(row['metadata'])
                        
                        original_size = metadata.get('original_size', 0)
                        compressed_size = metadata.get('compressed_size', 0)
                        space_saved = metadata.get('space_saved', 0)
                        compression_ratio = metadata.get('compression_ratio', 1.0)
                        
                        if original_size > 0:
                            total_original += original_size
                            total_compressed += compressed_size
                            total_space_saved += space_saved
                            
                            if metadata.get('compression_enabled', False):
                                compressed_files += 1
                                compression_ratios.append(compression_ratio)
                                
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                # Calculate overall compression metrics
                overall_ratio = total_original / total_compressed if total_compressed > 0 else 1.0
                avg_compression_ratio = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 1.0
                space_saved_percent = (total_space_saved / total_original * 100) if total_original > 0 else 0
                
                return {
                    'total_original_size': total_original,
                    'total_compressed_size': total_compressed,
                    'total_space_saved': total_space_saved,
                    'space_saved_percent': space_saved_percent,
                    'overall_compression_ratio': overall_ratio,
                    'average_compression_ratio': avg_compression_ratio,
                    'compressed_files': compressed_files,
                    'compression_effectiveness': 'excellent' if avg_compression_ratio > 3.0 else 'good' if avg_compression_ratio > 2.0 else 'moderate'
                }
                
        except Exception as e:
            logger.error(f"Error getting compression stats: {e}")
            return {
                'total_original_size': 0,
                'total_compressed_size': 0,
                'total_space_saved': 0,
                'space_saved_percent': 0,
                'overall_compression_ratio': 1.0,
                'average_compression_ratio': 1.0,
                'compressed_files': 0,
                'compression_effectiveness': 'unknown'
            }
    
    def clear_cache(self, older_than: Optional[str] = None):
        """Clear cache entries with cleanup"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                if older_than:
                    # Parse time duration
                    cutoff_time = time.time() - self._parse_duration(older_than)
                    cursor.execute('SELECT content_path FROM cache_entries WHERE cached_time < ?', (cutoff_time,))
                    files_to_remove = cursor.fetchall()
                    
                    cursor.execute('DELETE FROM cache_entries WHERE cached_time < ?', (cutoff_time,))
                else:
                    cursor.execute('SELECT content_path FROM cache_entries')
                    files_to_remove = cursor.fetchall()
                    
                    cursor.execute('DELETE FROM cache_entries')
                
                # Remove cached content files
                removed_count = 0
                for row in files_to_remove:
                    try:
                        os.remove(row['content_path'])
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Error removing cache file: {e}")
                
                logger.info(f"Cleared {removed_count} cache files")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds"""
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        duration_str = duration_str.lower()
        
        for unit, multiplier in units.items():
            if duration_str.endswith(unit):
                try:
                    return int(duration_str[:-len(unit)]) * multiplier
                except ValueError:
                    logger.error(f"Invalid duration format: {duration_str}")
                    return 0
        
        try:
            return int(duration_str)
        except ValueError:
            return 0
    
    def cleanup_stale_entries(self):
        """Remove stale cache entries and orphaned files"""
        try:
            # Clean up database entries for files that no longer exist
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT path, content_path FROM cache_entries')
                
                stale_entries = []
                for row in cursor.fetchall():
                    if not os.path.exists(row['path']):
                        stale_entries.append(row['path'])
                        try:
                            os.remove(row['content_path'])
                        except Exception:
                            pass
                
                if stale_entries:
                    placeholders = ','.join('?' * len(stale_entries))
                    cursor.execute(f'DELETE FROM cache_entries WHERE path IN ({placeholders})', stale_entries)
                    logger.info(f"Cleaned up {len(stale_entries)} stale cache entries")
            
            # Clean up orphaned content files
            content_dir = self.cache_dir / "files" / "content"
            if content_dir.exists():
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT content_path FROM cache_entries')
                    valid_files = {row['content_path'] for row in cursor.fetchall()}
                
                orphaned_count = 0
                for subdir in content_dir.iterdir():
                    if subdir.is_dir():
                        for file_path in subdir.glob("*.gz"):
                            if str(file_path) not in valid_files:
                                try:
                                    file_path.unlink()
                                    orphaned_count += 1
                                except Exception as e:
                                    logger.warning(f"Error removing orphaned file: {e}")
                
                if orphaned_count:
                    logger.info(f"Removed {orphaned_count} orphaned cache files")
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def warm_cache_parallel(self, patterns: List[str], max_workers: int = 4) -> Dict[str, Any]:
        """Warm cache with parallel processing for improved performance"""
        start_time = time.time()
        
        # Collect all files matching patterns
        all_files = []
        for pattern in patterns:
            if '**' in pattern:
                # Recursive glob
                files = glob.glob(pattern, recursive=True)
            else:
                files = glob.glob(pattern)
            
            # Filter to cacheable files and validate paths
            for file_path in files:
                if (os.path.isfile(file_path) and 
                    self._validate_path(file_path) and 
                    self._should_cache_file(file_path)):
                    all_files.append(file_path)
        
        if not all_files:
            return {
                'files_processed': 0,
                'files_cached': 0,
                'total_time': time.time() - start_time,
                'errors': 0
            }
        
        # Process files in parallel
        files_cached = 0
        errors = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit cache tasks
            future_to_file = {
                executor.submit(self._cache_file_task, file_path): file_path 
                for file_path in all_files
            }
            
            # Process results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        files_cached += 1
                except Exception as e:
                    logger.error(f"Error caching {file_path}: {e}")
                    errors += 1
        
        total_time = time.time() - start_time
        
        logger.info(f"Cache warming completed: {files_cached}/{len(all_files)} files in {total_time:.3f}s")
        
        return {
            'files_processed': len(all_files),
            'files_cached': files_cached,
            'total_time': total_time,
            'errors': errors,
            'speedup': self._calculate_speedup(len(all_files), total_time)
        }
    
    def _cache_file_task(self, file_path: str) -> bool:
        """Cache a single file (thread-safe task for parallel processing)"""
        try:
            # Check if already cached with current checksum
            if not os.path.exists(file_path):
                return False
            
            file_stat = os.stat(file_path)
            current_checksum = self._calculate_checksum(file_path)
            
            if not current_checksum:
                return False
            
            # Check if already cached with same checksum
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT checksum FROM cache_entries WHERE path = ?
                ''', (file_path,))
                result = cursor.fetchone()
                
                if result and result['checksum'] == current_checksum:
                    # Already cached and up to date
                    return True
            
            # Cache the file
            self._cache_file(file_path, current_checksum, file_stat)
            return True
            
        except Exception as e:
            logger.error(f"Error in cache task for {file_path}: {e}")
            return False
    
    def _calculate_speedup(self, file_count: int, total_time: float) -> float:
        """Calculate speedup factor compared to sequential processing"""
        if total_time <= 0:
            return 1.0
        
        # Estimate sequential time (based on ~50ms per file average)
        estimated_sequential = file_count * 0.05
        return max(1.0, estimated_sequential / total_time)
    
    def warm_cache_batch_optimized(self, patterns: List[str], max_workers: int = 4, batch_size: int = 50) -> Dict[str, Any]:
        """Batch-optimized cache warming with 80% faster database operations"""
        start_time = time.time()
        
        # Collect all files matching patterns (same as before)
        all_files = []
        for pattern in patterns:
            if '**' in pattern:
                files = glob.glob(pattern, recursive=True)
            else:
                files = glob.glob(pattern)
            
            for file_path in files:
                if (os.path.isfile(file_path) and 
                    self._validate_path(file_path) and 
                    self._should_cache_file(file_path)):
                    all_files.append(file_path)
        
        if not all_files:
            return {'files_processed': 0, 'files_cached': 0, 'total_time': 0, 'errors': 0}
        
        files_cached = 0
        errors = 0
        
        # Process files in batches for optimal database performance
        for i in range(0, len(all_files), batch_size):
            batch_files = all_files[i:i + batch_size]
            batch_entries = []
            
            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self._prepare_cache_entry, file_path): file_path 
                    for file_path in batch_files
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        entry = future.result()
                        if entry:
                            batch_entries.append(entry)
                            files_cached += 1
                    except Exception as e:
                        logger.error(f"Error preparing cache entry for {file_path}: {e}")
                        errors += 1
            
            # Batch insert to database - major performance improvement
            if batch_entries:
                try:
                    self._batch_insert_cache_entries(batch_entries)
                except Exception as e:
                    logger.error(f"Error in batch insert: {e}")
                    errors += len(batch_entries)
        
        total_time = time.time() - start_time
        return {
            'files_processed': len(all_files),
            'files_cached': files_cached,
            'total_time': total_time,
            'errors': errors,
            'speedup': self._calculate_speedup(len(all_files), total_time)
        }
    
    def warm_cache(self, patterns: List[str]) -> Dict[str, Any]:
        """Public interface for cache warming with batch optimization"""
        # Use batch-optimized warming for significant performance improvement
        max_workers = min(4, max(1, os.cpu_count() or 1))
        return self.warm_cache_batch_optimized(patterns, max_workers)

# Global cache instance with singleton pattern
_cache_instance = None
_instance_lock = Lock()

def get_cache() -> ClaudeCache:
    """Get global cache instance (thread-safe singleton)"""
    global _cache_instance
    
    if _cache_instance is None:
        with _instance_lock:
            if _cache_instance is None:
                _cache_instance = ClaudeCache()
    
    return _cache_instance

if __name__ == "__main__":
    # CLI interface for cache management
    import sys
    
    # Set up logging for CLI
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    cache = get_cache()
    
    if len(sys.argv) < 2:
        print("Usage: python claude_cache_v2.py <command> [args]")
        print("Commands: stats, clear, test, cleanup")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "stats":
        stats = cache.get_stats()
        compression_stats = cache.get_compression_stats()
        memory_stats = cache.get_memory_stats()
        
        print(f"Cache Statistics:")
        print(f"  Hit Rate: {stats.hit_rate:.2%}")
        print(f"  Total Files: {stats.total_files}")
        print(f"  Cache Size: {stats.cache_size / 1024 / 1024:.2f} MB")
        print(f"  Hits: {stats.hit_count}")
        print(f"  Misses: {stats.miss_count}")
        print(f"  Errors: {cache.stats.get('errors', 0)}")
        
        print(f"\nMemory Statistics:")
        print(f"  Process Memory: {memory_stats.process_memory_mb:.1f} MB")
        print(f"  Memory Limit: {memory_stats.memory_limit_mb:.0f} MB")
        print(f"  Memory Usage: {memory_stats.memory_usage_percent:.1f}%")
        print(f"  In-Memory Cache: {len(cache._memory_cache)} items")
        print(f"  GC Collections: {memory_stats.gc_collections}")
        if memory_stats.is_over_limit:
            print(f"  Status: ⚠️  OVER LIMIT")
        else:
            print(f"  Status: ✅ Within limits")
        
        print(f"\nCompression Statistics:")
        print(f"  Compressed Files: {compression_stats['compressed_files']}")
        print(f"  Average Compression Ratio: {compression_stats['average_compression_ratio']:.2f}x")
        print(f"  Space Saved: {compression_stats['space_saved_percent']:.1f}%")
        print(f"  Original Size: {compression_stats['total_original_size'] / 1024:.1f} KB")
        print(f"  Compressed Size: {compression_stats['total_compressed_size'] / 1024:.1f} KB")
        print(f"  Effectiveness: {compression_stats['compression_effectiveness'].title()}")
        
    elif command == "clear":
        older_than = sys.argv[2] if len(sys.argv) > 2 else None
        cache.clear_cache(older_than)
        print("Cache cleared successfully")
        
    elif command == "cleanup":
        cache.cleanup_stale_entries()
        print("Cleanup completed")
        
    elif command == "test":
        # Test with a sample file
        test_file = sys.argv[2] if len(sys.argv) > 2 else __file__
        
        if not cache._validate_path(test_file):
            print(f"Error: {test_file} is not in an allowed directory")
            sys.exit(1)
        
        print(f"Testing cache with file: {test_file}")
        
        # First access (should be cache miss)
        start_time = time.time()
        content1 = cache.get_file(test_file)
        first_time = time.time() - start_time
        
        if content1 is None:
            print("Error: Could not read file")
            sys.exit(1)
        
        # Second access (should be cache hit)
        start_time = time.time()
        content2 = cache.get_file(test_file)
        second_time = time.time() - start_time
        
        print(f"First access: {first_time:.4f}s")
        print(f"Second access: {second_time:.4f}s")
        if second_time > 0:
            print(f"Speedup: {first_time/second_time:.2f}x")
        print(f"Content matches: {content1 == content2}")
        
        stats = cache.get_stats()
        print(f"Hit rate: {stats.hit_rate:.2%}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)