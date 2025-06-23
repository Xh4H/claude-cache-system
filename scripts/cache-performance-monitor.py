#!/usr/bin/env python3
"""
Claude Code Cache Performance Monitor
Real-time performance analytics and optimization suggestions
"""

import os
import sys
import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import argparse

@dataclass
class PerformanceMetrics:
    """Performance metrics for cache analysis"""
    timestamp: float
    hit_rate: float
    avg_response_time: float
    cache_size: int
    total_operations: int
    memory_usage: int
    effectiveness_score: float

class CachePerformanceMonitor:
    """Monitor and analyze cache performance"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.claude/cache"))
        self.db_file = self.cache_dir / "files" / "index.db"
        self.metrics_file = self.cache_dir / "performance_metrics.json"
        self.config_file = self.cache_dir / "config" / "cache.json"
        
        # Load configuration
        self.config = self._load_config()
        
        # Performance tracking
        self.metrics_history = self._load_metrics_history()
    
    def _load_config(self) -> Dict:
        """Load cache configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _load_metrics_history(self) -> List[PerformanceMetrics]:
        """Load historical performance metrics"""
        try:
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
                return [PerformanceMetrics(**item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_metrics_history(self):
        """Save metrics history to file"""
        data = [vars(metric) for metric in self.metrics_history]
        with open(self.metrics_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def collect_current_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        timestamp = time.time()
        
        # Database statistics
        if not self.db_file.exists():
            return PerformanceMetrics(
                timestamp=timestamp,
                hit_rate=0.0,
                avg_response_time=0.0,
                cache_size=0,
                total_operations=0,
                memory_usage=0,
                effectiveness_score=0.0
            )
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Get cache statistics
        cursor.execute('SELECT COUNT(*) FROM cache_entries')
        total_files = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(size) FROM cache_entries')
        cache_size = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(access_count) FROM cache_entries')
        total_accesses = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(access_count) FROM cache_entries WHERE access_count > 0')
        avg_access = cursor.fetchone()[0] or 0
        
        # Calculate hit rate approximation
        hit_rate = min(1.0, avg_access / 2.0) if avg_access > 0 else 0.0
        
        # Response time estimation (based on cache vs file system)
        avg_response_time = self._estimate_response_time()
        
        # Memory usage (rough estimate)
        memory_usage = self._estimate_memory_usage()
        
        # Effectiveness score (composite metric)
        effectiveness_score = self._calculate_effectiveness_score(
            hit_rate, total_files, cache_size, avg_response_time
        )
        
        conn.close()
        
        return PerformanceMetrics(
            timestamp=timestamp,
            hit_rate=hit_rate,
            avg_response_time=avg_response_time,
            cache_size=cache_size,
            total_operations=total_accesses,
            memory_usage=memory_usage,
            effectiveness_score=effectiveness_score
        )
    
    def _estimate_response_time(self) -> float:
        """Estimate average response time"""
        # Simple benchmark with test file
        test_file = self.cache_dir.parent / "CLAUDE.md"
        if not test_file.exists():
            return 0.0
        
        try:
            # Time file system read
            start = time.time()
            with open(test_file, 'r') as f:
                f.read()
            fs_time = time.time() - start
            
            # Time cache read (if available)
            sys.path.insert(0, str(self.cache_dir))
            from claude_cache import get_cache
            cache = get_cache()
            
            start = time.time()
            cache.get_file(str(test_file))
            cache_time = time.time() - start
            
            return cache_time
            
        except Exception:
            return 0.001  # Default estimate
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage of cache"""
        try:
            cache_dir_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file())
            return cache_dir_size
        except Exception:
            return 0
    
    def _calculate_effectiveness_score(self, hit_rate: float, total_files: int, 
                                     cache_size: int, response_time: float) -> float:
        """Calculate composite effectiveness score (0-1)"""
        # Weighted scoring
        hit_score = hit_rate * 0.4
        size_score = min(1.0, total_files / 100) * 0.2  # More files = better
        speed_score = max(0.0, 1.0 - response_time) * 0.3  # Faster = better
        efficiency_score = min(1.0, 1000000 / max(1, cache_size / max(1, total_files))) * 0.1
        
        return hit_score + size_score + speed_score + efficiency_score
    
    def record_metrics(self):
        """Record current metrics"""
        current = self.collect_current_metrics()
        self.metrics_history.append(current)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        self._save_metrics_history()
    
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Generate performance report for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available for specified period"}
        
        # Calculate trends
        hit_rates = [m.hit_rate for m in recent_metrics]
        response_times = [m.avg_response_time for m in recent_metrics]
        effectiveness_scores = [m.effectiveness_score for m in recent_metrics]
        
        current = recent_metrics[-1] if recent_metrics else None
        
        report = {
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "current": {
                "hit_rate": current.hit_rate if current else 0,
                "response_time": current.avg_response_time if current else 0,
                "cache_size_mb": (current.cache_size / 1024 / 1024) if current else 0,
                "effectiveness_score": current.effectiveness_score if current else 0,
                "total_operations": current.total_operations if current else 0
            },
            "averages": {
                "hit_rate": sum(hit_rates) / len(hit_rates),
                "response_time": sum(response_times) / len(response_times),
                "effectiveness": sum(effectiveness_scores) / len(effectiveness_scores)
            },
            "trends": {
                "hit_rate_trend": self._calculate_trend(hit_rates),
                "response_time_trend": self._calculate_trend(response_times),
                "effectiveness_trend": self._calculate_trend(effectiveness_scores)
            },
            "recommendations": self._generate_recommendations(recent_metrics)
        }
        
        return report
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change = (second_avg - first_avg) / first_avg if first_avg > 0 else 0
        
        if change > 0.05:
            return "improving"
        elif change < -0.05:
            return "declining" 
        else:
            return "stable"
    
    def _generate_recommendations(self, metrics: List[PerformanceMetrics]) -> List[str]:
        """Generate optimization recommendations"""
        if not metrics:
            return []
        
        current = metrics[-1]
        recommendations = []
        
        # Hit rate recommendations
        if current.hit_rate < 0.6:
            recommendations.append("Low hit rate - consider warming cache for frequently accessed files")
        
        # Response time recommendations
        if current.avg_response_time > 0.01:
            recommendations.append("High response time - check cache configuration and disk performance")
        
        # Cache size recommendations
        cache_size_mb = current.cache_size / 1024 / 1024
        if cache_size_mb > 500:
            recommendations.append("Large cache size - consider clearing old entries")
        elif cache_size_mb < 10:
            recommendations.append("Small cache size - cache may not be working effectively")
        
        # Effectiveness recommendations
        if current.effectiveness_score < 0.5:
            recommendations.append("Low effectiveness - review cache policies and file patterns")
        
        # Trend-based recommendations
        hit_rates = [m.hit_rate for m in metrics]
        if self._calculate_trend(hit_rates) == "declining":
            recommendations.append("Hit rate declining - check for file changes or cache invalidation issues")
        
        if not recommendations:
            recommendations.append("Cache performing well - no immediate optimizations needed")
        
        return recommendations
    
    def print_live_dashboard(self):
        """Print live performance dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🚀 Claude Code Cache Performance Dashboard")
        print("=" * 50)
        print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Current metrics
        current = self.collect_current_metrics()
        
        print("📊 Current Performance:")
        print(f"  Hit Rate: {current.hit_rate:.1%}")
        print(f"  Response Time: {current.avg_response_time*1000:.1f}ms")
        print(f"  Cache Size: {current.cache_size/1024/1024:.1f}MB")
        print(f"  Total Operations: {current.total_operations}")
        print(f"  Effectiveness Score: {current.effectiveness_score:.2f}/1.0")
        print()
        
        # Recent report
        report = self.get_performance_report(24)
        if "error" not in report:
            print("📈 24-Hour Trends:")
            trends = report["trends"]
            print(f"  Hit Rate: {trends['hit_rate_trend'].title()}")
            print(f"  Response Time: {trends['response_time_trend'].title()}")
            print(f"  Effectiveness: {trends['effectiveness_trend'].title()}")
            print()
            
            print("💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"][:3], 1):
                print(f"  {i}. {rec}")
        
        print()
        print("Press Ctrl+C to exit")

def main():
    parser = argparse.ArgumentParser(description="Claude Code Cache Performance Monitor")
    parser.add_argument("command", choices=["report", "record", "dashboard", "analyze"], 
                       help="Command to execute")
    parser.add_argument("--hours", type=int, default=24, 
                       help="Hours to analyze for report (default: 24)")
    parser.add_argument("--cache-dir", type=str, 
                       help="Cache directory path")
    
    args = parser.parse_args()
    
    monitor = CachePerformanceMonitor(args.cache_dir)
    
    if args.command == "record":
        monitor.record_metrics()
        print("✅ Metrics recorded")
        
    elif args.command == "report":
        report = monitor.get_performance_report(args.hours)
        print(json.dumps(report, indent=2))
        
    elif args.command == "analyze":
        report = monitor.get_performance_report(args.hours)
        if "error" in report:
            print(f"Error: {report['error']}")
            return
        
        print(f"📊 Cache Performance Analysis ({args.hours}h)")
        print("=" * 50)
        print()
        
        current = report["current"]
        averages = report["averages"]
        trends = report["trends"]
        
        print(f"Current Status:")
        print(f"  Hit Rate: {current['hit_rate']:.1%}")
        print(f"  Cache Size: {current['cache_size_mb']:.1f}MB")
        print(f"  Effectiveness: {current['effectiveness_score']:.2f}/1.0")
        print()
        
        print(f"Average Performance:")
        print(f"  Hit Rate: {averages['hit_rate']:.1%}")
        print(f"  Response Time: {averages['response_time']*1000:.1f}ms")
        print(f"  Effectiveness: {averages['effectiveness']:.2f}/1.0")
        print()
        
        print("Trends:")
        print(f"  Hit Rate: {trends['hit_rate_trend'].title()}")
        print(f"  Response Time: {trends['response_time_trend'].title()}")
        print(f"  Effectiveness: {trends['effectiveness_trend'].title()}")
        print()
        
        print("Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
    elif args.command == "dashboard":
        try:
            while True:
                monitor.print_live_dashboard()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")

if __name__ == "__main__":
    main()