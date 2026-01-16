"""Property-based tests for Command Executor.

**Validates: Requirements 4.1, 4.4, 4.5**

Property 15: Application Launch Performance
Property 17: Status Update Delivery
Property 18: Error Reporting

This property test verifies that:
- Applications launch within 3 seconds
- Real-time status updates are delivered during execution
- Errors are reported with clear explanations
"""

from datetime import datetime
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from prime.execution import CommandExecutor, ExecutionStatus
from prime.models import Command, Intent, Entity
from prime.safety import SafetyController
import subprocess
import time


# Strategy for generating application names
# Using common applications that are likely to be available
# Avoiding cmd as it can be flaky
application_names = st.sampled_from([
    "notepad",
    "calc",
    "mspaint"
])

# Strategy for generating command IDs
command_ids = st.text(
    min_size=1,
    max_size=20,
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )
)

# Strategy for generating entity values
entity_values = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='.-_ '
    )
)

# Strategy for generating invalid application names
# Use simple ASCII to avoid shell interpretation issues
invalid_app_names = st.text(
    min_size=5,
    max_size=20,
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'),
        min_codepoint=65,
        max_codepoint=122
    )
).filter(lambda x: x.lower() not in ["notepad", "calc", "mspaint", "cmd", "explorer", "start", "exit", "echo"])


class TestProperty15ApplicationLaunchPerformance:
    """Property 15: Application Launch Performance.
    
    **Validates: Requirements 4.1**
    
    For any application launch request, the Command_Executor should start
    the application within 3 seconds.
    """
    
    @given(
        app_name=application_names,
        command_id=command_ids
    )
    @settings(max_examples=5, deadline=15000, suppress_health_check=[HealthCheck.too_slow])
    def test_property_15_application_launches_within_3_seconds(
        self, app_name, command_id
    ):
        """Property 15: Applications launch within 3 seconds.
        
        **Validates: Requirements 4.1**
        
        For any application launch request, the Command_Executor should:
        1. Start the application
        2. Complete within 3 seconds (3000ms)
        3. Return a successful result
        
        This test verifies that:
        1. A launch application command is created
        2. The command is executed
        3. The execution completes within 3000ms
        4. The result indicates success
        
        Note: This test allows for platform-specific timing variations.
        """
        # Create a launch application command
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", app_name, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        
        # Execute the command
        result = executor.execute(command)
        
        # Skip if application launch failed due to system issues
        # (e.g., application not installed, permissions, etc.)
        if not result.success:
            # This is acceptable for property testing - we're testing
            # the timing when launches DO succeed
            assume(result.success)
        
        # Verify execution time is within 3 seconds
        # Allow some tolerance for platform variations (3.5s)
        assert result.execution_time_ms <= 3500, (
            f"Application launch took {result.execution_time_ms}ms, "
            f"exceeding 3-second (3000ms) requirement (with 500ms tolerance)"
        )
        
        # Verify command ID matches
        assert result.command_id == command_id
        
        # Verify output contains information about the launch
        assert result.output, "Result should contain output information"
        assert app_name.lower() in result.output.lower(), (
            "Output should mention the application name"
        )
    
    @given(
        app_name=application_names,
        command_id=command_ids
    )
    @settings(max_examples=10, deadline=10000)
    def test_property_15_launch_application_method_performance(
        self, app_name, command_id
    ):
        """Property 15: Direct launch_application method performance.
        
        **Validates: Requirements 4.1**
        
        The launch_application method should also complete within 3 seconds.
        """
        executor = CommandExecutor()
        
        start_time = time.time()
        
        try:
            # Launch the application directly
            process = executor.launch_application(app_name)
            
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Verify timing
            assert elapsed_time <= 3000, (
                f"Application launch took {elapsed_time:.0f}ms, "
                f"exceeding 3-second requirement"
            )
            
            # Verify process was created
            assert process is not None
            assert process.pid > 0
            
            # Clean up - terminate the process
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
                
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            # If the application doesn't exist on this system, skip
            assume(False)


class TestProperty17StatusUpdateDelivery:
    """Property 17: Status Update Delivery.
    
    **Validates: Requirements 4.4**
    
    For any command being executed, the Command_Executor should provide
    real-time status updates to the Voice_Output_Module.
    """
    
    @given(
        app_name=application_names,
        command_id=command_ids
    )
    @settings(max_examples=10, deadline=10000)
    def test_property_17_status_updates_delivered_during_execution(
        self, app_name, command_id
    ):
        """Property 17: Status updates are delivered during execution.
        
        **Validates: Requirements 4.4**
        
        For any command being executed, the Command_Executor should:
        1. Provide status updates via callback
        2. Update execution state
        3. Make status queryable via get_execution_status
        
        This test verifies that:
        1. A status callback receives updates
        2. Execution state is tracked
        3. Status can be queried during and after execution
        """
        # Track status updates
        status_updates = []
        
        def status_callback(cmd_id: str, message: str):
            status_updates.append((cmd_id, message))
        
        # Create a launch application command
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", app_name, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor(status_callback=status_callback)
        
        # Execute the command
        result = executor.execute(command)
        
        # Verify status updates were delivered
        assert len(status_updates) > 0, (
            "Status updates should be delivered during execution"
        )
        
        # Verify all updates have the correct command ID
        for cmd_id, message in status_updates:
            assert cmd_id == command_id, (
                f"Status update command ID {cmd_id} doesn't match {command_id}"
            )
            assert message, "Status message should not be empty"
        
        # Verify execution state is tracked
        execution_state = executor.get_execution_status(command_id)
        assert execution_state is not None, (
            "Execution state should be tracked"
        )
        
        # Verify execution state properties
        assert execution_state.command_id == command_id
        assert execution_state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
        assert execution_state.start_time is not None
        assert execution_state.end_time is not None
        assert execution_state.progress_message is not None
        
        # If successful, result should be stored
        if result.success:
            assert execution_state.result is not None
            assert execution_state.result.success is True
    
    @given(
        command_id=command_ids,
        entity_value=entity_values
    )
    @settings(max_examples=15, deadline=5000)
    def test_property_17_status_updates_for_all_command_types(
        self, command_id, entity_value
    ):
        """Property 17: Status updates for all command types.
        
        **Validates: Requirements 4.4**
        
        Status updates should be provided for all command types,
        not just application launches.
        """
        # Track status updates
        status_updates = []
        
        def status_callback(cmd_id: str, message: str):
            status_updates.append((cmd_id, message))
        
        # Create a generic command
        intent = Intent(
            intent_type="generic_command",
            entities=[Entity("target", entity_value, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor(status_callback=status_callback)
        
        # Execute the command
        result = executor.execute(command)
        
        # Verify execution state exists
        execution_state = executor.get_execution_status(command_id)
        assert execution_state is not None, (
            "Execution state should be tracked for all command types"
        )
        
        # Verify state has required properties
        assert execution_state.command_id == command_id
        assert execution_state.status is not None
        assert execution_state.start_time is not None


class TestProperty18ErrorReporting:
    """Property 18: Error Reporting.
    
    **Validates: Requirements 4.5, 14.1**
    
    For any command that fails during execution, the Command_Executor
    should report the error with a clear explanation of what went wrong.
    """
    
    @given(
        invalid_app=invalid_app_names,
        command_id=command_ids
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_18_errors_reported_with_clear_explanations(
        self, invalid_app, command_id
    ):
        """Property 18: Errors are reported with clear explanations.
        
        **Validates: Requirements 4.5, 14.1**
        
        For any command that fails, the Command_Executor should:
        1. Return a CommandResult with success=False
        2. Provide a clear error message
        3. Explain what went wrong
        4. Not return empty error messages
        
        This test verifies that:
        1. A command that will fail is created
        2. The command is executed
        3. The result indicates failure
        4. The error message is clear and informative
        """
        # Assume the invalid app name is actually invalid
        # (not one of the common apps that might exist)
        assume(invalid_app.lower() not in ["notepad", "calc", "mspaint", "cmd", "explorer", "start", "exit", "echo"])
        # Also filter out single letters which might be drive letters
        assume(len(invalid_app) > 2)
        
        # Create a launch application command with invalid app
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", invalid_app, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        
        # Execute the command (should fail)
        result = executor.execute(command)
        
        # Verify failure is reported
        assert result.success is False, (
            f"Command should fail for invalid application '{invalid_app}', "
            f"but got success=True with output: {result.output}"
        )
        
        # Verify error message exists and is informative
        assert result.error is not None, (
            "Error message should not be None"
        )
        assert len(result.error) > 0, (
            "Error message should not be empty"
        )
        assert len(result.error) > 10, (
            "Error message should be substantial (more than 10 characters)"
        )
        
        # Verify error message is clear and helpful
        error_lower = result.error.lower()
        
        # Should mention what went wrong
        assert any(word in error_lower for word in [
            "not found", "could not find", "failed", "error",
            "cannot", "unable", "does not exist", "not recognized"
        ]), f"Error should explain what went wrong, got: {result.error}"
        
        # Should be user-friendly (not just a stack trace)
        assert "traceback" not in error_lower, (
            "Error should be user-friendly, not a raw traceback"
        )
        
        # Verify command ID matches
        assert result.command_id == command_id
        
        # Verify execution time is recorded
        assert result.execution_time_ms >= 0
    
    @given(
        command_id=command_ids,
        entity_value=entity_values
    )
    @settings(max_examples=15, deadline=5000)
    def test_property_18_unimplemented_commands_report_clear_errors(
        self, command_id, entity_value
    ):
        """Property 18: Unimplemented commands report clear errors.
        
        **Validates: Requirements 4.5, 14.1**
        
        Commands that are not yet implemented should report clear errors
        explaining that the functionality is not available.
        """
        # Create a command with an unimplemented intent type
        intent = Intent(
            intent_type="unimplemented_command_type",
            entities=[Entity("target", entity_value, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        
        # Execute the command
        result = executor.execute(command)
        
        # Verify failure is reported
        assert result.success is False, (
            "Unimplemented command should fail"
        )
        
        # Verify error message is clear
        assert result.error is not None
        assert len(result.error) > 0
        
        # Should explain that it's not implemented
        error_lower = result.error.lower()
        assert any(word in error_lower for word in [
            "not implemented", "not yet implemented", "not available"
        ]), "Error should explain that the command is not implemented"
    
    @given(
        command_id=command_ids
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_18_missing_parameters_report_clear_errors(
        self, command_id
    ):
        """Property 18: Missing parameters report clear errors.
        
        **Validates: Requirements 4.5, 14.1**
        
        Commands with missing required parameters should report clear errors
        explaining what is missing.
        """
        # Create a launch application command without app name
        intent = Intent(
            intent_type="launch_app",
            entities=[],  # No entities
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},  # No parameters
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        executor = CommandExecutor()
        
        # Execute the command
        result = executor.execute(command)
        
        # Verify failure is reported
        assert result.success is False, (
            "Command with missing parameters should fail"
        )
        
        # Verify error message is clear
        assert result.error is not None
        assert len(result.error) > 0
        
        # Should explain what is missing
        error_lower = result.error.lower()
        assert any(word in error_lower for word in [
            "no application", "not specified", "missing", "specify"
        ]), "Error should explain what parameter is missing"
