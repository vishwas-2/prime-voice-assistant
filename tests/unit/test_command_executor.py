"""Unit tests for Command Executor.

**Validates: Requirements 4.1, 4.4, 4.5**

This module contains unit tests for the CommandExecutor class,
testing specific scenarios and edge cases.
"""

import pytest
import subprocess
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from prime.execution import CommandExecutor, ExecutionStatus, ExecutionState
from prime.models import Command, Intent, Entity, CommandResult
from prime.safety import SafetyController


class TestCommandExecutorBasicOperations:
    """Test basic operations of the Command Executor."""
    
    def test_executor_initialization(self):
        """Test that CommandExecutor initializes correctly."""
        executor = CommandExecutor()
        
        assert executor is not None
        assert executor.safety_controller is not None
        assert executor.logger is not None
        assert isinstance(executor._execution_states, dict)
        assert len(executor._execution_states) == 0
    
    def test_executor_with_custom_safety_controller(self):
        """Test initialization with custom SafetyController."""
        custom_controller = SafetyController()
        executor = CommandExecutor(safety_controller=custom_controller)
        
        assert executor.safety_controller is custom_controller
    
    def test_executor_with_status_callback(self):
        """Test initialization with status callback."""
        callback_called = []
        
        def callback(cmd_id, message):
            callback_called.append((cmd_id, message))
        
        executor = CommandExecutor(status_callback=callback)
        
        # Create and execute a simple command
        intent = Intent(
            intent_type="test_command",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="test-123",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor.execute(command)
        
        # Verify callback was called
        assert len(callback_called) > 0
        assert any(cmd_id == "test-123" for cmd_id, _ in callback_called)


class TestCommandExecutorLaunchApplication:
    """Test application launching functionality."""
    
    def test_launch_notepad_success(self):
        """Test launching notepad successfully."""
        executor = CommandExecutor()
        
        try:
            process = executor.launch_application("notepad")
            
            assert process is not None
            assert process.pid > 0
            assert process.poll() is None  # Process should still be running
            
            # Clean up
            process.terminate()
            process.wait(timeout=2)
        except Exception as e:
            pytest.skip(f"Notepad not available: {e}")
    
    def test_launch_invalid_application_raises_error(self):
        """Test that launching an invalid application raises an error."""
        executor = CommandExecutor()
        
        with pytest.raises((FileNotFoundError, subprocess.SubprocessError)):
            executor.launch_application("nonexistent_app_xyz123")
    
    def test_launch_application_command(self):
        """Test launching application via execute command."""
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "notepad", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="launch-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        result = executor.execute(command)
        
        # If notepad is available, should succeed
        if result.success:
            assert result.command_id == "launch-test-1"
            assert result.execution_time_ms >= 0
            assert "notepad" in result.output.lower()
            assert result.error is None
        else:
            # If not available, should have clear error
            assert result.error is not None
            assert len(result.error) > 0
    
    def test_launch_application_without_app_name(self):
        """Test launching application without specifying app name."""
        intent = Intent(
            intent_type="launch_app",
            entities=[],  # No entities
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="launch-test-2",
            intent=intent,
            parameters={},  # No parameters
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        result = executor.execute(command)
        
        assert result.success is False
        assert result.error is not None
        assert "no application" in result.error.lower() or "not specified" in result.error.lower()


class TestCommandExecutorExecutionStatus:
    """Test execution status tracking."""
    
    def test_get_execution_status_for_executed_command(self):
        """Test getting execution status for a command."""
        intent = Intent(
            intent_type="test_command",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="status-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        result = executor.execute(command)
        
        # Get execution status
        status = executor.get_execution_status("status-test-1")
        
        assert status is not None
        assert status.command_id == "status-test-1"
        assert status.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
        assert status.start_time is not None
        assert status.end_time is not None
        assert status.progress_message is not None
    
    def test_get_execution_status_for_nonexistent_command(self):
        """Test getting execution status for a command that doesn't exist."""
        executor = CommandExecutor()
        
        status = executor.get_execution_status("nonexistent-command")
        
        assert status is None
    
    def test_execution_state_tracks_result(self):
        """Test that execution state tracks the result."""
        intent = Intent(
            intent_type="test_command",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="result-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        result = executor.execute(command)
        
        status = executor.get_execution_status("result-test-1")
        
        assert status.result is not None
        assert status.result.command_id == result.command_id
        assert status.result.success == result.success


class TestCommandExecutorErrorHandling:
    """Test error handling and reporting."""
    
    def test_prohibited_command_blocked(self):
        """Test that prohibited commands are blocked."""
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "hack the system", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="prohibited-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        result = executor.execute(command)
        
        assert result.success is False
        assert result.error is not None
        assert "prohibited" in result.error.lower()
    
    def test_unimplemented_command_reports_error(self):
        """Test that unimplemented commands report clear errors."""
        intent = Intent(
            intent_type="unimplemented_feature",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="unimpl-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        result = executor.execute(command)
        
        assert result.success is False
        assert result.error is not None
        assert "not implemented" in result.error.lower() or "not yet implemented" in result.error.lower()
    
    def test_error_explanation_generation(self):
        """Test that error explanations are generated correctly."""
        executor = CommandExecutor()
        
        intent = Intent(
            intent_type="test_command",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="error-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Test FileNotFoundError
        error = FileNotFoundError("test.txt not found")
        explanation = executor._generate_error_explanation(command, error)
        
        assert "could not find" in explanation.lower()
        assert len(explanation) > 20
        
        # Test PermissionError
        error = PermissionError("Access denied")
        explanation = executor._generate_error_explanation(command, error)
        
        assert "permission" in explanation.lower()
        assert len(explanation) > 20
        
        # Test generic error
        error = ValueError("Invalid value")
        explanation = executor._generate_error_explanation(command, error)
        
        assert "unexpected error" in explanation.lower()
        assert len(explanation) > 20


class TestCommandExecutorStatusUpdates:
    """Test status update functionality."""
    
    def test_status_updates_sent_via_callback(self):
        """Test that status updates are sent via callback."""
        updates = []
        
        def callback(cmd_id, message):
            updates.append((cmd_id, message))
        
        intent = Intent(
            intent_type="test_command",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="callback-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor(status_callback=callback)
        executor.execute(command)
        
        # Verify updates were sent
        assert len(updates) > 0
        
        # Verify all updates have correct command ID
        for cmd_id, message in updates:
            assert cmd_id == "callback-test-1"
            assert isinstance(message, str)
            assert len(message) > 0
    
    def test_status_callback_error_handled_gracefully(self):
        """Test that errors in status callback don't break execution."""
        def bad_callback(cmd_id, message):
            raise Exception("Callback error")
        
        intent = Intent(
            intent_type="test_command",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="callback-error-test",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor(status_callback=bad_callback)
        
        # Should not raise exception
        result = executor.execute(command)
        
        # Execution should still complete
        assert result is not None
        assert result.command_id == "callback-error-test"


class TestCommandExecutorIntegration:
    """Integration tests for Command Executor."""
    
    def test_full_execution_flow(self):
        """Test the full execution flow from command to result."""
        updates = []
        
        def callback(cmd_id, message):
            updates.append((cmd_id, message))
        
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "notepad", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="integration-test-1",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor(status_callback=callback)
        result = executor.execute(command)
        
        # Verify result
        assert result is not None
        assert result.command_id == "integration-test-1"
        assert result.execution_time_ms >= 0
        
        # Verify status updates were sent
        assert len(updates) > 0
        
        # Verify execution state is tracked
        status = executor.get_execution_status("integration-test-1")
        assert status is not None
        assert status.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
        
        # If successful, verify result details
        if result.success:
            assert result.output
            assert result.error is None
            assert status.result.success is True
        else:
            # If failed, verify error details
            assert result.error is not None
            assert len(result.error) > 0
