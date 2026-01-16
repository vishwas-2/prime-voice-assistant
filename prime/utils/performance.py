"""
Performance optimization utilities for PRIME Voice Assistant.

This module provides caching, profiling, and optimization utilities to improve
PRIME's performance.
"""

import time
import functools
from typing import Any, Callable, Dict, Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
import threading


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    
    Provides fast caching with automatic eviction of least recently used items
    when the cache reaches its maximum size.
    """
    
    def __init__(self, max_size: int = 128):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
    
    def get(self, key: Any) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None
    
    def put(self, key: Any, value: Any) -> None:
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            if key in self.cache:
                # Update existing item
                self.cache.move_to_end(key)
            else:
                # Add new item
                if len(self.cache) >= self.max_size:
                    # Remove least recently used item
                    self.cache.popitem(last=False)
            
            self.cache[key] = value
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats (hits, misses, size, hit_rate)
        """
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate
            }


class TTLCache:
    """
    Time-To-Live (TTL) cache implementation.
    
    Cached items expire after a specified time period.
    """
    
    def __init__(self, ttl_seconds: float = 300.0):
        """
        Initialize TTL cache.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default: 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[Any, Tuple[Any, datetime]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: Any) -> Optional[Any]:
        """
        Get item from cache if not expired.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                
                # Check if expired
                if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                    return value
                else:
                    # Remove expired item
                    del self.cache[key]
            
            return None
    
    def put(self, key: Any, value: Any) -> None:
        """
        Put item in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self.cache[key] = (value, datetime.now())
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired items from cache.
        
        Returns:
            Number of items removed
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if now - timestamp >= timedelta(seconds=self.ttl_seconds)
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)


def cached(max_size: int = 128):
    """
    Decorator to cache function results using LRU cache.
    
    Args:
        max_size: Maximum cache size
    
    Returns:
        Decorated function with caching
    
    Example:
        @cached(max_size=256)
        def expensive_function(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(max_size=max_size)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = (args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result
        
        # Attach cache to function for inspection
        wrapper.cache = cache
        return wrapper
    
    return decorator


def timed(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to time
    
    Returns:
        Decorated function that prints execution time
    
    Example:
        @timed
        def slow_function():
            time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        print(f"{func.__name__} took {elapsed_time:.4f} seconds")
        return result
    
    return wrapper


class PerformanceProfiler:
    """
    Simple performance profiler for tracking function execution times.
    
    Tracks execution times for different operations to identify bottlenecks.
    """
    
    def __init__(self):
        """Initialize performance profiler."""
        self.timings: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def record(self, operation: str, duration: float) -> None:
        """
        Record execution time for an operation.
        
        Args:
            operation: Name of the operation
            duration: Execution time in seconds
        """
        with self._lock:
            if operation not in self.timings:
                self.timings[operation] = []
            self.timings[operation].append(duration)
    
    def get_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for an operation.
        
        Args:
            operation: Name of the operation
        
        Returns:
            Dictionary with min, max, avg, total times, or None if not found
        """
        with self._lock:
            if operation not in self.timings or not self.timings[operation]:
                return None
            
            times = self.timings[operation]
            return {
                "count": len(times),
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "total": sum(times)
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all operations.
        
        Returns:
            Dictionary mapping operation names to their statistics
        """
        with self._lock:
            return {
                operation: self.get_stats(operation)
                for operation in self.timings.keys()
            }
    
    def clear(self) -> None:
        """Clear all recorded timings."""
        with self._lock:
            self.timings.clear()
    
    def profile(self, operation: str) -> Callable:
        """
        Decorator to profile a function.
        
        Args:
            operation: Name of the operation
        
        Returns:
            Decorator function
        
        Example:
            profiler = PerformanceProfiler()
            
            @profiler.profile("speech_to_text")
            def convert_speech(audio):
                # ... conversion logic
                pass
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                self.record(operation, duration)
                return result
            return wrapper
        return decorator


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """
    Get the global performance profiler instance.
    
    Returns:
        Global PerformanceProfiler instance
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def profile(operation: str) -> Callable:
    """
    Decorator to profile a function using global profiler.
    
    Args:
        operation: Name of the operation
    
    Returns:
        Decorator function
    
    Example:
        @profile("command_execution")
        def execute_command(cmd):
            # ... execution logic
            pass
    """
    profiler = get_profiler()
    return profiler.profile(operation)


def get_performance_stats() -> Dict[str, Dict[str, float]]:
    """
    Get performance statistics from global profiler.
    
    Returns:
        Dictionary with all operation statistics
    """
    profiler = get_profiler()
    return profiler.get_all_stats()


def clear_performance_stats() -> None:
    """Clear all performance statistics."""
    profiler = get_profiler()
    profiler.clear()


class BatchProcessor:
    """
    Batch processor for optimizing bulk operations.
    
    Collects items and processes them in batches to reduce overhead.
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        flush_interval: float = 1.0,
        processor: Optional[Callable] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items to collect before processing
            flush_interval: Time in seconds before auto-flushing
            processor: Function to process batches
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.processor = processor
        self.batch: list = []
        self.last_flush = time.time()
        self._lock = threading.Lock()
    
    def add(self, item: Any) -> None:
        """
        Add item to batch.
        
        Args:
            item: Item to add
        """
        with self._lock:
            self.batch.append(item)
            
            # Check if batch is full or flush interval exceeded
            if (len(self.batch) >= self.batch_size or
                time.time() - self.last_flush >= self.flush_interval):
                self.flush()
    
    def flush(self) -> None:
        """Process and clear current batch."""
        with self._lock:
            if self.batch and self.processor:
                self.processor(self.batch)
            self.batch.clear()
            self.last_flush = time.time()
    
    def get_batch_size(self) -> int:
        """
        Get current batch size.
        
        Returns:
            Number of items in current batch
        """
        with self._lock:
            return len(self.batch)


def optimize_imports():
    """
    Optimize module imports by preloading commonly used modules.
    
    This can reduce startup time for frequently used operations.
    """
    # Preload commonly used modules
    import json
    import os
    import sys
    import datetime
    import pathlib
    
    # Return loaded modules for potential use
    return {
        'json': json,
        'os': os,
        'sys': sys,
        'datetime': datetime,
        'pathlib': pathlib
    }
