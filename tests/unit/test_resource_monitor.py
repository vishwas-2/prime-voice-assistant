"""
Unit tests for Resource Monitor.

Tests resource monitoring, limit checking, and cleanup functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from prime.utils.resource_monitor import (
    ResourceMonitor,
    ResourceUsage,
    get_resource_monitor,
    start_resource_monitoring,
    stop_resource_monitoring,
    get_current_resource_usage,
    check_resource_limits
)


class TestResourceUsage:
    """Test ResourceUsage dataclass."""
    
    def test_resource_usage_creation(self):
        """Test creating ResourceUsage object."""
        from datetime import datetime
        
        usage = ResourceUsage(
            cpu_percent=2.5,
            memory_mb=250.0,
            memory_percent=5.0,
            timestamp=datetime.now()
        )
        
        assert usage.cpu_percent == 2.5
        assert usage.memory_mb == 250.0
        assert usage.memory_percent == 5.0
        assert isinstance(usage.timestamp, datetime)


class TestResourceMonitorInitialization:
    """Test ResourceMonitor initialization."""
    
    def test_default_initialization(self):
        """Test initialization with default parameters."""
        monitor = ResourceMonitor()
        
        assert monitor._memory_limit_mb == 500.0
        assert monitor._cpu_limit_percent == 5.0
        assert monitor._check_interval == 5.0
        assert not monitor.is_monitoring()
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        monitor = ResourceMonitor(
            memory_limit_mb=1000.0,
            cpu_limit_percent=10.0,
            check_interval=2.0
        )
        
        assert monitor._memory_limit_mb == 1000.0
        assert monitor._cpu_limit_percent == 10.0
        assert monitor._check_interval == 2.0


class TestResourceMonitoring:
    """Test resource monitoring functionality."""
    
    def test_get_current_usage(self):
        """Test getting current resource usage."""
        monitor = ResourceMonitor()
        
        usage = monitor.get_current_usage()
        
        assert isinstance(usage, ResourceUsage)
        assert usage.cpu_percent >= 0
        assert usage.memory_mb > 0
        assert usage.memory_percent >= 0
    
    def test_is_within_limits_success(self):
        """Test limit checking when within limits."""
        monitor = ResourceMonitor(
            memory_limit_mb=1000.0,
            cpu_limit_percent=50.0
        )
        
        # Current usage should be well within these generous limits
        limits = monitor.is_within_limits()
        
        assert "memory_ok" in limits
        assert "cpu_ok" in limits
        assert "overall_ok" in limits
        assert isinstance(limits["memory_ok"], bool)
        assert isinstance(limits["cpu_ok"], bool)
    
    def test_is_within_limits_with_provided_usage(self):
        """Test limit checking with provided usage."""
        from datetime import datetime
        
        monitor = ResourceMonitor(
            memory_limit_mb=500.0,
            cpu_limit_percent=5.0
        )
        
        # Create usage within limits
        usage = ResourceUsage(
            cpu_percent=2.0,
            memory_mb=250.0,
            memory_percent=5.0,
            timestamp=datetime.now()
        )
        
        limits = monitor.is_within_limits(usage)
        
        assert limits["memory_ok"] is True
        assert limits["cpu_ok"] is True
        assert limits["overall_ok"] is True
    
    def test_is_within_limits_memory_exceeded(self):
        """Test limit checking when memory limit exceeded."""
        from datetime import datetime
        
        monitor = ResourceMonitor(
            memory_limit_mb=100.0,  # Very low limit
            cpu_limit_percent=50.0
        )
        
        usage = ResourceUsage(
            cpu_percent=2.0,
            memory_mb=200.0,  # Exceeds limit
            memory_percent=10.0,
            timestamp=datetime.now()
        )
        
        limits = monitor.is_within_limits(usage)
        
        assert limits["memory_ok"] is False
        assert limits["overall_ok"] is False
    
    def test_is_within_limits_cpu_exceeded(self):
        """Test limit checking when CPU limit exceeded."""
        from datetime import datetime
        
        monitor = ResourceMonitor(
            memory_limit_mb=1000.0,
            cpu_limit_percent=1.0  # Very low limit
        )
        
        usage = ResourceUsage(
            cpu_percent=5.0,  # Exceeds limit
            memory_mb=200.0,
            memory_percent=5.0,
            timestamp=datetime.now()
        )
        
        limits = monitor.is_within_limits(usage)
        
        assert limits["cpu_ok"] is False
        assert limits["overall_ok"] is False


class TestMonitoringControl:
    """Test monitoring start/stop functionality."""
    
    def test_start_monitoring(self):
        """Test starting monitoring."""
        monitor = ResourceMonitor(check_interval=0.1)
        
        monitor.start_monitoring()
        
        assert monitor.is_monitoring()
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()
        
        # Cleanup
        monitor.stop_monitoring()
    
    def test_stop_monitoring(self):
        """Test stopping monitoring."""
        monitor = ResourceMonitor(check_interval=0.1)
        
        monitor.start_monitoring()
        time.sleep(0.2)  # Let it run briefly
        monitor.stop_monitoring()
        
        assert not monitor.is_monitoring()
    
    def test_start_monitoring_idempotent(self):
        """Test that starting monitoring multiple times is safe."""
        monitor = ResourceMonitor(check_interval=0.1)
        
        monitor.start_monitoring()
        thread1 = monitor._monitor_thread
        
        monitor.start_monitoring()  # Should not create new thread
        thread2 = monitor._monitor_thread
        
        assert thread1 is thread2
        
        # Cleanup
        monitor.stop_monitoring()


class TestAlertCallbacks:
    """Test alert callback functionality."""
    
    def test_add_alert_callback(self):
        """Test adding alert callback."""
        monitor = ResourceMonitor()
        callback = Mock()
        
        monitor.add_alert_callback(callback)
        
        assert callback in monitor._alert_callbacks
    
    def test_remove_alert_callback(self):
        """Test removing alert callback."""
        monitor = ResourceMonitor()
        callback = Mock()
        
        monitor.add_alert_callback(callback)
        monitor.remove_alert_callback(callback)
        
        assert callback not in monitor._alert_callbacks
    
    def test_alert_callback_triggered(self):
        """Test that alert callback is triggered when limits exceeded."""
        from datetime import datetime
        
        monitor = ResourceMonitor(
            memory_limit_mb=100.0,  # Very low limit
            check_interval=0.1
        )
        
        callback = Mock()
        monitor.add_alert_callback(callback)
        
        # Create usage that exceeds limits
        usage = ResourceUsage(
            cpu_percent=2.0,
            memory_mb=200.0,  # Exceeds limit
            memory_percent=10.0,
            timestamp=datetime.now()
        )
        
        limits = monitor.is_within_limits(usage)
        monitor._trigger_alerts(usage, limits)
        
        callback.assert_called_once()
        args = callback.call_args[0]
        assert isinstance(args[0], ResourceUsage)
        assert isinstance(args[1], dict)


class TestResourceCleanup:
    """Test resource cleanup functionality."""
    
    def test_cleanup_resources(self):
        """Test cleanup resources method."""
        monitor = ResourceMonitor()
        
        # Should not raise any errors
        monitor.cleanup_resources()
    
    @patch('gc.collect')
    def test_cleanup_calls_gc(self, mock_gc):
        """Test that cleanup calls garbage collection."""
        monitor = ResourceMonitor()
        
        monitor.cleanup_resources()
        
        mock_gc.assert_called_once()


class TestSystemInfo:
    """Test system information retrieval."""
    
    def test_get_system_info(self):
        """Test getting system information."""
        monitor = ResourceMonitor()
        
        info = monitor.get_system_info()
        
        assert "cpu_count" in info
        assert "cpu_percent" in info
        assert "memory_total_mb" in info
        assert "memory_available_mb" in info
        assert "memory_percent" in info
        assert "disk_usage_percent" in info
        
        assert info["cpu_count"] > 0
        assert info["memory_total_mb"] > 0


class TestLastUsage:
    """Test last usage tracking."""
    
    def test_get_last_usage_initially_none(self):
        """Test that last usage is None initially."""
        monitor = ResourceMonitor()
        
        assert monitor.get_last_usage() is None
    
    def test_get_last_usage_after_measurement(self):
        """Test that last usage is stored after measurement."""
        monitor = ResourceMonitor()
        
        usage = monitor.get_current_usage()
        last_usage = monitor.get_last_usage()
        
        assert last_usage is not None
        assert last_usage == usage


class TestGlobalMonitor:
    """Test global monitor functions."""
    
    def test_get_resource_monitor(self):
        """Test getting global monitor instance."""
        monitor1 = get_resource_monitor()
        monitor2 = get_resource_monitor()
        
        assert monitor1 is monitor2  # Should be same instance
    
    def test_start_resource_monitoring(self):
        """Test starting global monitoring."""
        start_resource_monitoring()
        
        monitor = get_resource_monitor()
        assert monitor.is_monitoring()
        
        # Cleanup
        stop_resource_monitoring()
    
    def test_stop_resource_monitoring(self):
        """Test stopping global monitoring."""
        start_resource_monitoring()
        stop_resource_monitoring()
        
        monitor = get_resource_monitor()
        assert not monitor.is_monitoring()
    
    def test_get_current_resource_usage(self):
        """Test getting current usage from global monitor."""
        usage = get_current_resource_usage()
        
        assert isinstance(usage, ResourceUsage)
        assert usage.cpu_percent >= 0
        assert usage.memory_mb > 0
    
    def test_check_resource_limits(self):
        """Test checking limits from global monitor."""
        limits = check_resource_limits()
        
        assert "memory_ok" in limits
        assert "cpu_ok" in limits
        assert "overall_ok" in limits


class TestIntegration:
    """Integration tests for resource monitoring."""
    
    def test_continuous_monitoring(self):
        """Test continuous monitoring over time."""
        monitor = ResourceMonitor(check_interval=0.1)
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Let it run for a bit
        time.sleep(0.5)
        
        # Should have recorded usage
        last_usage = monitor.get_last_usage()
        assert last_usage is not None
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        assert not monitor.is_monitoring()
    
    def test_monitoring_with_callback(self):
        """Test monitoring with alert callback."""
        callback_called = []
        
        def alert_callback(usage, limits):
            callback_called.append((usage, limits))
        
        monitor = ResourceMonitor(
            memory_limit_mb=1.0,  # Impossibly low limit to trigger alert
            check_interval=0.1
        )
        
        monitor.add_alert_callback(alert_callback)
        monitor.start_monitoring()
        
        # Let it run and trigger alerts
        time.sleep(0.3)
        
        monitor.stop_monitoring()
        
        # Should have triggered at least one alert
        assert len(callback_called) > 0
