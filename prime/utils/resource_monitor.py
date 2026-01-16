"""
Resource monitoring utilities for PRIME Voice Assistant.

This module provides resource monitoring and management capabilities to ensure
PRIME operates within defined resource limits.
"""

import psutil
import time
import threading
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResourceUsage:
    """Represents current resource usage statistics."""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    timestamp: datetime


class ResourceMonitor:
    """
    Monitors system resource usage for PRIME.
    
    Tracks CPU and memory usage to ensure PRIME operates within defined limits:
    - Memory: < 500MB during normal operation
    - CPU: < 5% when idle
    
    Attributes:
        _process: psutil Process object for current process
        _monitoring: Flag indicating if monitoring is active
        _monitor_thread: Background thread for monitoring
        _alert_callbacks: List of callback functions for alerts
        _memory_limit_mb: Memory limit in MB
        _cpu_limit_percent: CPU limit percentage
        _check_interval: Interval between checks in seconds
    """
    
    def __init__(
        self,
        memory_limit_mb: float = 500.0,
        cpu_limit_percent: float = 5.0,
        check_interval: float = 5.0
    ):
        """
        Initialize the Resource Monitor.
        
        Args:
            memory_limit_mb: Memory limit in MB (default: 500MB)
            cpu_limit_percent: CPU limit percentage when idle (default: 5%)
            check_interval: Interval between checks in seconds (default: 5s)
        """
        self._process = psutil.Process()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._alert_callbacks: list[Callable] = []
        self._memory_limit_mb = memory_limit_mb
        self._cpu_limit_percent = cpu_limit_percent
        self._check_interval = check_interval
        self._last_usage: Optional[ResourceUsage] = None
    
    def get_current_usage(self) -> ResourceUsage:
        """
        Get current resource usage.
        
        Returns:
            ResourceUsage object with current statistics
        
        **Validates: Requirements 18.1, 18.2**
        """
        # Get memory info
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        memory_percent = self._process.memory_percent()
        
        # Get CPU usage (averaged over 0.1 seconds)
        cpu_percent = self._process.cpu_percent(interval=0.1)
        
        usage = ResourceUsage(
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            timestamp=datetime.now()
        )
        
        self._last_usage = usage
        return usage
    
    def is_within_limits(self, usage: Optional[ResourceUsage] = None) -> Dict[str, bool]:
        """
        Check if resource usage is within defined limits.
        
        Args:
            usage: ResourceUsage to check (uses current if None)
        
        Returns:
            Dictionary with limit check results:
                - memory_ok: bool
                - cpu_ok: bool
                - overall_ok: bool
        
        **Validates: Requirements 18.1, 18.2**
        """
        if usage is None:
            usage = self.get_current_usage()
        
        memory_ok = usage.memory_mb < self._memory_limit_mb
        cpu_ok = usage.cpu_percent < self._cpu_limit_percent
        
        return {
            "memory_ok": memory_ok,
            "cpu_ok": cpu_ok,
            "overall_ok": memory_ok and cpu_ok,
            "memory_usage_mb": usage.memory_mb,
            "memory_limit_mb": self._memory_limit_mb,
            "cpu_usage_percent": usage.cpu_percent,
            "cpu_limit_percent": self._cpu_limit_percent
        }
    
    def start_monitoring(self) -> None:
        """
        Start continuous resource monitoring in background thread.
        
        Monitors resource usage at regular intervals and triggers alerts
        if limits are exceeded.
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop continuous resource monitoring."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self) -> None:
        """Internal monitoring loop (runs in background thread)."""
        while self._monitoring:
            try:
                usage = self.get_current_usage()
                limits = self.is_within_limits(usage)
                
                # Trigger alerts if limits exceeded
                if not limits["overall_ok"]:
                    self._trigger_alerts(usage, limits)
                
                time.sleep(self._check_interval)
            except Exception as e:
                # Log error but continue monitoring
                print(f"Resource monitoring error: {e}")
                time.sleep(self._check_interval)
    
    def add_alert_callback(self, callback: Callable[[ResourceUsage, Dict], None]) -> None:
        """
        Add a callback function to be called when resource limits are exceeded.
        
        Args:
            callback: Function that takes (usage, limits) as arguments
        """
        if callback not in self._alert_callbacks:
            self._alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable) -> None:
        """
        Remove an alert callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
    
    def _trigger_alerts(self, usage: ResourceUsage, limits: Dict) -> None:
        """
        Trigger all registered alert callbacks.
        
        Args:
            usage: Current resource usage
            limits: Limit check results
        """
        for callback in self._alert_callbacks:
            try:
                callback(usage, limits)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    def cleanup_resources(self) -> None:
        """
        Perform resource cleanup operations.
        
        This method can be called when PRIME is idle to free up resources.
        
        **Validates: Requirements 18.5**
        """
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Additional cleanup operations can be added here
        # For example:
        # - Clear caches
        # - Close unused connections
        # - Flush buffers
    
    def get_system_info(self) -> Dict[str, any]:
        """
        Get overall system resource information.
        
        Returns:
            Dictionary with system-wide resource statistics
        """
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_total_mb": psutil.virtual_memory().total / (1024 * 1024),
            "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
    
    def get_last_usage(self) -> Optional[ResourceUsage]:
        """
        Get the last recorded resource usage.
        
        Returns:
            Last ResourceUsage or None if no measurements taken
        """
        return self._last_usage
    
    def is_monitoring(self) -> bool:
        """
        Check if monitoring is currently active.
        
        Returns:
            True if monitoring is active, False otherwise
        """
        return self._monitoring


# Global resource monitor instance
_global_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """
    Get the global resource monitor instance.
    
    Returns:
        Global ResourceMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
    return _global_monitor


def start_resource_monitoring() -> None:
    """Start global resource monitoring."""
    monitor = get_resource_monitor()
    monitor.start_monitoring()


def stop_resource_monitoring() -> None:
    """Stop global resource monitoring."""
    monitor = get_resource_monitor()
    monitor.stop_monitoring()


def get_current_resource_usage() -> ResourceUsage:
    """
    Get current resource usage from global monitor.
    
    Returns:
        Current ResourceUsage
    """
    monitor = get_resource_monitor()
    return monitor.get_current_usage()


def check_resource_limits() -> Dict[str, bool]:
    """
    Check if current resource usage is within limits.
    
    Returns:
        Dictionary with limit check results
    """
    monitor = get_resource_monitor()
    return monitor.is_within_limits()
