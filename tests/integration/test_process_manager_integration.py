"""
Integration tests for Process Manager.

Tests the Process Manager with real system processes to verify
end-to-end functionality.
"""

import pytest
import os
import time
import subprocess
import sys
from prime.system.process_manager import ProcessManager
from prime.models.data_models import Process


class TestProcessManagerIntegration:
    """Integration tests for ProcessManager with real processes."""
    
    @pytest.fixture
    def process_manager(self):
        """Create a ProcessManager instance for testing."""
        return ProcessManager()
    
    @pytest.fixture
    def test_process(self):
        """Create a test process that we can monitor and terminate."""
        # Start a simple Python process that sleeps
        process = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(60)'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        yield process
        
        # Cleanup: ensure process is terminated
        try:
            process.terminate()
            process.wait(timeout=3)
        except:
            try:
                process.kill()
            except:
                pass
    
    def test_list_processes_includes_test_process(self, process_manager, test_process):
        """Test that list_processes includes our test process."""
        # Give the process a moment to start
        time.sleep(0.5)
        
        processes = process_manager.list_processes()
        pids = [proc.pid for proc in processes]
        
        assert test_process.pid in pids
    
    def test_get_process_info_for_test_process(self, process_manager, test_process):
        """Test getting info for our test process."""
        # Give the process a moment to start
        time.sleep(0.5)
        
        process_info = process_manager.get_process_info(test_process.pid)
        
        assert process_info.pid == test_process.pid
        assert isinstance(process_info.name, str)
        assert process_info.cpu_percent >= 0.0
        assert process_info.memory_mb > 0.0
        assert process_info.status in ['running', 'sleeping', 'disk-sleep']
    
    def test_monitor_resources_for_test_process(self, process_manager, test_process):
        """Test monitoring resources for our test process."""
        # Give the process a moment to start
        time.sleep(0.5)
        
        resources = process_manager.monitor_resources(test_process.pid)
        
        assert 'cpu_percent' in resources
        assert 'memory_mb' in resources
        assert 'memory_percent' in resources
        assert resources['cpu_percent'] >= 0.0
        assert resources['memory_mb'] > 0.0
        assert resources['memory_percent'] >= 0.0
    
    def test_terminate_test_process(self, process_manager, test_process):
        """Test terminating our test process."""
        # Give the process a moment to start
        time.sleep(0.5)
        
        # Verify process is running
        assert test_process.poll() is None
        
        # Terminate the process
        process_manager.terminate_process(test_process.pid)
        
        # Wait a moment for termination
        time.sleep(1)
        
        # Verify process is no longer running
        assert test_process.poll() is not None
    
    def test_alert_callback_integration(self, process_manager, test_process):
        """Test that alert callback is triggered when monitoring a process."""
        # Give the process a moment to start
        time.sleep(0.5)
        
        # Track alerts
        alerts = []
        
        def alert_callback(resource, process):
            alerts.append((resource, process))
        
        process_manager.set_alert_callback(alert_callback)
        
        # Set very low thresholds to trigger alerts
        process_manager.set_alert_threshold('cpu', 0.0)
        process_manager.set_alert_threshold('memory', 0.0)
        
        # Monitor the process
        process_manager.monitor_resources(test_process.pid)
        
        # Should have triggered at least one alert (memory should always be > 0)
        assert len(alerts) > 0
        
        # Verify alert structure
        for resource, process in alerts:
            assert resource in ['cpu', 'memory', 'disk_io']
            assert isinstance(process, Process)
            assert process.pid == test_process.pid
    
    def test_process_lifecycle(self, process_manager):
        """Test monitoring a process through its entire lifecycle."""
        # Start a short-lived process
        process = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(2)'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Give the process more time to start and be registered
            time.sleep(1.0)
            
            # Process should be in the list
            processes = process_manager.list_processes()
            pids = [proc.pid for proc in processes]
            
            # The process might have already completed if system is slow
            # So we check if it's either in the list or already finished
            if process.poll() is None:
                # Process still running, should be in list
                assert process.pid in pids, f"Process {process.pid} not found in process list"
            
            # Try to get process info if still running
            if process.poll() is None:
                info = process_manager.get_process_info(process.pid)
                assert info.pid == process.pid
                
                # Monitor resources if still running
                resources = process_manager.monitor_resources(process.pid)
                assert resources['memory_mb'] >= 0
            
            # Wait for process to complete naturally
            process.wait(timeout=5)
            
            # Process should no longer be accessible
            time.sleep(0.5)
            with pytest.raises(Exception):  # Could be NoSuchProcess or similar
                process_manager.get_process_info(process.pid)
        
        finally:
            # Cleanup
            try:
                process.terminate()
            except:
                pass
    
    def test_multiple_processes_monitoring(self, process_manager):
        """Test monitoring multiple processes simultaneously."""
        # Start multiple test processes
        processes = []
        for i in range(3):
            proc = subprocess.Popen(
                [sys.executable, '-c', 'import time; time.sleep(60)'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append(proc)
        
        try:
            # Give processes time to start
            time.sleep(0.5)
            
            # Monitor all processes
            for proc in processes:
                info = process_manager.get_process_info(proc.pid)
                assert info.pid == proc.pid
                
                resources = process_manager.monitor_resources(proc.pid)
                assert resources['memory_mb'] > 0
        
        finally:
            # Cleanup all processes
            for proc in processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except:
                    try:
                        proc.kill()
                    except:
                        pass
    
    def test_resource_threshold_alerts(self, process_manager, test_process):
        """Test that resource thresholds work correctly."""
        # Give the process a moment to start
        time.sleep(0.5)
        
        alerts = []
        
        def alert_callback(resource, process):
            alerts.append(resource)
        
        process_manager.set_alert_callback(alert_callback)
        
        # Set high thresholds - should not trigger
        process_manager.set_alert_threshold('cpu', 999.0)
        process_manager.set_alert_threshold('memory', 999.0)
        process_manager.set_alert_threshold('disk_io', 999999.0)
        
        process_manager.monitor_resources(test_process.pid)
        assert len(alerts) == 0
        
        # Set low thresholds - should trigger
        process_manager.set_alert_threshold('memory', 0.0)
        
        process_manager.monitor_resources(test_process.pid)
        assert 'memory' in alerts
