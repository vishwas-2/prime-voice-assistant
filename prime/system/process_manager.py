"""
Process Manager for PRIME Voice Assistant.

This module provides process monitoring and management capabilities including
listing processes, monitoring resource usage, terminating processes, and
alerting on resource thresholds.

Validates Requirements:
- 10.1: List running processes with resource usage
- 10.2: Monitor CPU usage, memory usage, and disk I/O
- 10.3: Alert when process consumes excessive resources
- 10.4: Confirm before terminating process (handled by Safety Controller)
- 10.5: Provide process details including PID, name, and resource consumption
"""

import psutil
from typing import List, Dict, Optional, Callable
from prime.models.data_models import Process


class ProcessManager:
    """
    Provides process monitoring and management capabilities for PRIME Voice Assistant.
    
    This class handles process listing, resource monitoring, process termination,
    and resource threshold alerts. It uses the psutil library for cross-platform
    process management.
    """
    
    def __init__(self):
        """
        Initialize the Process Manager.
        
        Sets up resource alert thresholds and callback handlers.
        """
        # Resource alert thresholds (percentage)
        self._alert_thresholds: Dict[str, float] = {
            'cpu': 80.0,      # CPU usage percentage
            'memory': 80.0,   # Memory usage percentage
            'disk_io': 100.0  # Disk I/O MB/s
        }
        
        # Alert callback function (can be set by external components)
        self._alert_callback: Optional[Callable[[str, Process], None]] = None
    
    def list_processes(self) -> List[Process]:
        """
        List all running processes with their resource usage.
        
        Returns a list of Process objects containing PID, name, CPU usage,
        memory usage, and status for each running process.
        
        Returns:
            List of Process objects representing running processes
        
        Raises:
            psutil.Error: If there's an error accessing process information
        
        Validates: Requirements 10.1, 10.5
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                # Get process info
                pid = proc.info['pid']
                name = proc.info['name']
                status = proc.info['status']
                
                # Get CPU and memory usage
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_info = proc.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
                
                process = Process(
                    pid=pid,
                    name=name,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    status=status
                )
                
                processes.append(process)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes we can't access or that no longer exist
                continue
        
        return processes
    
    def get_process_info(self, pid: int) -> Process:
        """
        Get detailed information about a specific process.
        
        Args:
            pid: Process ID to query
        
        Returns:
            Process object with detailed information
        
        Raises:
            psutil.NoSuchProcess: If the process doesn't exist
            psutil.AccessDenied: If lacking permission to access the process
            psutil.ZombieProcess: If the process is a zombie
        
        Validates: Requirements 10.5
        """
        try:
            proc = psutil.Process(pid)
            
            # Get process information
            name = proc.name()
            status = proc.status()
            cpu_percent = proc.cpu_percent(interval=0.1)
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
            
            return Process(
                pid=pid,
                name=name,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                status=status
            )
            
        except psutil.NoSuchProcess:
            raise psutil.NoSuchProcess(pid, name=None, msg=f"Process with PID {pid} does not exist")
        except psutil.AccessDenied:
            raise psutil.AccessDenied(pid, name=None, msg=f"Access denied to process with PID {pid}")
        except psutil.ZombieProcess:
            raise psutil.ZombieProcess(pid, name=None, msg=f"Process with PID {pid} is a zombie")
    
    def monitor_resources(self, pid: int) -> Dict[str, float]:
        """
        Monitor resource usage for a specific process.
        
        Returns CPU usage, memory usage, and disk I/O statistics for the
        specified process. Checks against alert thresholds and triggers
        alerts if thresholds are exceeded.
        
        Args:
            pid: Process ID to monitor
        
        Returns:
            Dictionary containing resource usage metrics:
            - cpu_percent: CPU usage percentage
            - memory_mb: Memory usage in megabytes
            - memory_percent: Memory usage percentage
            - disk_read_mb: Disk read in megabytes
            - disk_write_mb: Disk write in megabytes
            - disk_io_mb_per_sec: Total disk I/O rate in MB/s
        
        Raises:
            psutil.NoSuchProcess: If the process doesn't exist
            psutil.AccessDenied: If lacking permission to access the process
            psutil.ZombieProcess: If the process is a zombie
        
        Validates: Requirements 10.2, 10.3
        """
        try:
            proc = psutil.Process(pid)
            
            # Get CPU usage
            cpu_percent = proc.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
            memory_percent = proc.memory_percent()
            
            # Get disk I/O statistics
            try:
                io_counters = proc.io_counters()
                disk_read_mb = io_counters.read_bytes / (1024 * 1024)
                disk_write_mb = io_counters.write_bytes / (1024 * 1024)
                # Approximate I/O rate (this is cumulative, not per-second)
                disk_io_mb_per_sec = (disk_read_mb + disk_write_mb) / max(proc.create_time(), 1)
            except (psutil.AccessDenied, AttributeError):
                # Some platforms don't support I/O counters or we lack permission
                disk_read_mb = 0.0
                disk_write_mb = 0.0
                disk_io_mb_per_sec = 0.0
            
            resources = {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'memory_percent': memory_percent,
                'disk_read_mb': disk_read_mb,
                'disk_write_mb': disk_write_mb,
                'disk_io_mb_per_sec': disk_io_mb_per_sec
            }
            
            # Check thresholds and trigger alerts
            self._check_thresholds(pid, resources)
            
            return resources
            
        except psutil.NoSuchProcess:
            raise psutil.NoSuchProcess(pid, name=None, msg=f"Process with PID {pid} does not exist")
        except psutil.AccessDenied:
            raise psutil.AccessDenied(pid, name=None, msg=f"Access denied to process with PID {pid}")
        except psutil.ZombieProcess:
            raise psutil.ZombieProcess(pid, name=None, msg=f"Process with PID {pid} is a zombie")
    
    def terminate_process(self, pid: int) -> None:
        """
        Terminate a process.
        
        This is a destructive operation and should be confirmed by the
        Safety Controller before execution.
        
        Args:
            pid: Process ID to terminate
        
        Raises:
            psutil.NoSuchProcess: If the process doesn't exist
            psutil.AccessDenied: If lacking permission to terminate the process
            psutil.TimeoutExpired: If the process doesn't terminate within timeout
        
        Validates: Requirements 10.4
        """
        try:
            proc = psutil.Process(pid)
            
            # Try graceful termination first
            proc.terminate()
            
            # Wait up to 3 seconds for the process to terminate
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                # If graceful termination fails, force kill
                proc.kill()
                proc.wait(timeout=3)
                
        except psutil.NoSuchProcess:
            raise psutil.NoSuchProcess(pid, name=None, msg=f"Process with PID {pid} does not exist")
        except psutil.AccessDenied:
            raise psutil.AccessDenied(pid, name=None, msg=f"Access denied to terminate process with PID {pid}")
    
    def set_alert_threshold(self, resource: str, threshold: float) -> None:
        """
        Set the alert threshold for a specific resource type.
        
        When a process exceeds this threshold during monitoring, an alert
        will be triggered if an alert callback is registered.
        
        Args:
            resource: Resource type ('cpu', 'memory', or 'disk_io')
            threshold: Threshold value (percentage for cpu/memory, MB/s for disk_io)
        
        Raises:
            ValueError: If the resource type is invalid or threshold is negative
        
        Validates: Requirements 10.3
        """
        valid_resources = ['cpu', 'memory', 'disk_io']
        
        if resource not in valid_resources:
            raise ValueError(
                f"Invalid resource type: {resource}. "
                f"Must be one of {valid_resources}"
            )
        
        if threshold < 0:
            raise ValueError(f"Threshold must be non-negative, got {threshold}")
        
        self._alert_thresholds[resource] = threshold
    
    def set_alert_callback(self, callback: Callable[[str, Process], None]) -> None:
        """
        Set a callback function to be called when resource thresholds are exceeded.
        
        The callback will be called with two arguments:
        - resource: The resource type that exceeded the threshold
        - process: The Process object that exceeded the threshold
        
        Args:
            callback: Function to call when alerts are triggered
        """
        self._alert_callback = callback
    
    def _check_thresholds(self, pid: int, resources: Dict[str, float]) -> None:
        """
        Check if resource usage exceeds thresholds and trigger alerts.
        
        Args:
            pid: Process ID being monitored
            resources: Dictionary of resource usage metrics
        """
        if self._alert_callback is None:
            return
        
        # Check CPU threshold
        if resources['cpu_percent'] > self._alert_thresholds['cpu']:
            process = self.get_process_info(pid)
            self._alert_callback('cpu', process)
        
        # Check memory threshold
        if resources['memory_percent'] > self._alert_thresholds['memory']:
            process = self.get_process_info(pid)
            self._alert_callback('memory', process)
        
        # Check disk I/O threshold
        if resources['disk_io_mb_per_sec'] > self._alert_thresholds['disk_io']:
            process = self.get_process_info(pid)
            self._alert_callback('disk_io', process)
