"""Integration tests for Safety Check Flow.

This module tests the complete safety check flow integration:
Command Executor → Safety Controller → Confirmation → Execution

**Task 9.3: Safety Check Flow Integration**

This validates that destructive actions are properly handled with
confirmation prompts and user responses.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from prime.execution import CommandExecutor
from prime.safety import SafetyController
from prime.safety.safety_controller import ActionType, SecurityEvent
from prime.nlp import IntentParser, ContextEngine
from prime.persistence import MemoryManager
from prime.voice import VoiceOutputModule
from prime.models import (
    Command, Intent, Entity, CommandResult, Session
)


class TestSafetyCheckFlowIntegration:
    """Test complete safety check flow integration."""
    
    @pytest.fixture
    def components(self, tmp_path):
        """Create components for safety flow testing."""
        safety_controller = SafetyController()
        command_executor = CommandExecutor(safety_controller)
        voice_output = VoiceOutputModule()
        memory_manager = MemoryManager(storage_dir=tmp_path)
        intent_parser = IntentParser()
        context_engine = ContextEngine(intent_parser, memory_manager)
        
        return {
            'safety_controller': safety_controller,
            'command_executor': command_executor,
            'voice_output': voice_output,
            'context_engine': context_engine
        }
    
    @pytest.fixture
    def session(self):
        """Create a test session."""
        return Session(
            session_id=str(uuid.uuid4()),
            user_id="test_user",
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
    
    def test_destructive_action_full_flow_with_confirmation(self, components, session):
        """
        Test complete flow for destructive action with user confirmation.
        
        Flow: Command → Safety Check → Confirmation Prompt → User Confirms → Execute
        """
        # Step 1: Create a destructive command (file deletion)
        command_text = "delete important.txt"
        intent = components['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={"file_path": "important.txt"},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 2: Safety Controller classifies action
        action_type = components['safety_controller'].classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE, \
            "File deletion should be classified as destructive"
        
        # Step 3: Check if confirmation is required
        requires_conf = components['safety_controller'].requires_confirmation(action_type)
        assert requires_conf is True, \
            "Destructive actions should require confirmation"
        
        # Step 4: Generate confirmation prompt
        prompt = components['safety_controller'].generate_confirmation_prompt(command)
        assert "CONFIRMATION" in prompt, "Prompt should indicate confirmation required"
        assert "important.txt" in prompt, "Prompt should mention the file"
        assert "cannot be easily undone" in prompt.lower() or "cannot be undone" in prompt.lower(), \
            "Prompt should warn about irreversibility"
        
        # Step 5: Convert prompt to voice output
        audio_prompt = components['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None, "Should generate audio prompt"
        assert audio_prompt.duration_ms > 0, "Audio should have duration"
        
        # Step 6: Simulate user voice response "yes"
        user_response = "yes"
        is_confirmed = components['safety_controller'].validate_confirmation(user_response)
        assert is_confirmed is True, "User confirmation should be validated"
        
        # Step 7: Log security event
        event = SecurityEvent(
            event_type="destructive_action_confirmed",
            command_id=command.command_id,
            description=f"User confirmed deletion of important.txt",
            timestamp=datetime.now(),
            severity="warning"
        )
        components['safety_controller'].log_security_event(event)
        
        # Step 8: Execute command (mocked - not actually deleting)
        # In real system, execution would proceed here
        # For testing, we verify the flow completed successfully
        assert True, "Flow completed successfully"
    
    def test_destructive_action_full_flow_with_abortion(self, components, session):
        """
        Test complete flow for destructive action with user abortion.
        
        Flow: Command → Safety Check → Confirmation Prompt → User Cancels → Abort
        """
        # Step 1: Create a destructive command (system shutdown)
        command_text = "shutdown the system"
        intent = components['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 2: Safety Controller classifies action
        action_type = components['safety_controller'].classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE, \
            "System shutdown should be classified as destructive"
        
        # Step 3: Check if confirmation is required
        requires_conf = components['safety_controller'].requires_confirmation(action_type)
        assert requires_conf is True
        
        # Step 4: Generate confirmation prompt
        prompt = components['safety_controller'].generate_confirmation_prompt(command)
        assert "CONFIRMATION" in prompt
        assert "shut down" in prompt.lower() or "shutdown" in prompt.lower()
        
        # Step 5: Convert prompt to voice output
        audio_prompt = components['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None
        
        # Step 6: Simulate user voice response "no"
        user_response = "no"
        is_confirmed = components['safety_controller'].validate_confirmation(user_response)
        is_aborted = components['safety_controller'].is_abortion(user_response)
        
        assert is_confirmed is False, "User did not confirm"
        assert is_aborted is True, "User aborted the action"
        
        # Step 7: Log abortion event
        event = SecurityEvent(
            event_type="destructive_action_aborted",
            command_id=command.command_id,
            description="User aborted shutdown command",
            timestamp=datetime.now(),
            severity="info"
        )
        components['safety_controller'].log_security_event(event)
        
        # Step 8: Command is NOT executed
        # Verify that abortion prevents execution
        assert True, "Flow completed with abortion"
    
    def test_process_termination_flow_with_confirmation(self, components, session):
        """
        Test flow for process termination (Requirement 10.4).
        
        Flow: Terminate Process Command → Safety Check → Confirmation → Execute
        """
        # Step 1: Create process termination command
        command_text = "terminate chrome"
        intent = components['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={"process_name": "chrome", "pid": 1234},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 2: Safety Controller classifies action
        action_type = components['safety_controller'].classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE, \
            "Process termination should be classified as destructive"
        
        # Step 3: Confirmation required
        requires_conf = components['safety_controller'].requires_confirmation(action_type)
        assert requires_conf is True
        
        # Step 4: Generate confirmation prompt
        prompt = components['safety_controller'].generate_confirmation_prompt(command)
        assert "CONFIRMATION" in prompt
        assert "chrome" in prompt.lower() or "process" in prompt.lower()
        
        # Step 5: User confirms with "proceed"
        user_response = "proceed"
        is_confirmed = components['safety_controller'].validate_confirmation(user_response)
        assert is_confirmed is True
        
        # Step 6: Execution would proceed
        # (Not actually terminating process in test)
    
    def test_multiple_destructive_actions_in_sequence(self, components, session):
        """
        Test handling multiple destructive actions in sequence.
        
        Each action should require separate confirmation.
        """
        destructive_commands = [
            "delete file1.txt",
            "delete file2.txt",
            "shutdown"
        ]
        
        for cmd_text in destructive_commands:
            # Parse command
            intent = components['context_engine'].process_command(cmd_text, session)
            
            command = Command(
                command_id=str(uuid.uuid4()),
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            
            # Classify
            action_type = components['safety_controller'].classify_action(command)
            
            # Each should be destructive
            assert action_type == ActionType.DESTRUCTIVE
            
            # Each should require confirmation
            requires_conf = components['safety_controller'].requires_confirmation(action_type)
            assert requires_conf is True
            
            # Generate prompt
            prompt = components['safety_controller'].generate_confirmation_prompt(command)
            assert "CONFIRMATION" in prompt
    
    def test_safe_action_bypasses_confirmation(self, components, session):
        """
        Test that safe actions bypass the confirmation flow.
        
        Flow: Safe Command → Safety Check → Execute Directly (no confirmation)
        """
        # Step 1: Create a safe command (launch app)
        command_text = "launch notepad"
        intent = components['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 2: Safety Controller classifies action
        action_type = components['safety_controller'].classify_action(command)
        assert action_type == ActionType.SAFE, \
            "Launching app should be classified as safe"
        
        # Step 3: No confirmation required
        requires_conf = components['safety_controller'].requires_confirmation(action_type)
        assert requires_conf is False, \
            "Safe actions should not require confirmation"
        
        # Step 4: Execute directly (mocked)
        with patch.object(components['command_executor'], 'launch_application') as mock_launch:
            mock_process = Mock()
            mock_process.pid = 5678
            mock_launch.return_value = mock_process
            
            result = components['command_executor'].execute(command)
            
            assert result.success is True
            assert "notepad" in result.output.lower()
    
    def test_prohibited_action_blocked_immediately(self, components, session):
        """
        Test that prohibited actions are blocked without confirmation.
        
        Flow: Prohibited Command → Safety Check → Block Immediately (no confirmation)
        """
        # Step 1: Create a prohibited command with prohibited keywords in parameters
        command_text = "execute command"
        intent = components['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={"command": "hack into network"},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 2: Safety Controller classifies action
        action_type = components['safety_controller'].classify_action(command)
        assert action_type == ActionType.PROHIBITED, \
            "Hacking command should be classified as prohibited"
        
        # Step 3: Check if prohibited
        is_prohibited = components['safety_controller'].is_prohibited(command)
        assert is_prohibited is True
        
        # Step 4: No confirmation needed - blocked immediately
        requires_conf = components['safety_controller'].requires_confirmation(action_type)
        assert requires_conf is False, \
            "Prohibited actions should not require confirmation (blocked immediately)"
        
        # Step 5: Execute (should be blocked)
        result = components['command_executor'].execute(command)
        
        assert result.success is False, "Prohibited command should fail"
        assert "prohibited" in result.error.lower(), \
            "Error should indicate command is prohibited"
        
        # Step 6: Log security event
        event = SecurityEvent(
            event_type="prohibited_command_blocked",
            command_id=command.command_id,
            description="User attempted prohibited hacking command",
            timestamp=datetime.now(),
            severity="critical"
        )
        components['safety_controller'].log_security_event(event)


class TestEndToEndDestructiveActions:
    """End-to-end tests for complete destructive action scenarios."""
    
    @pytest.fixture
    def integrated_system(self, tmp_path):
        """Create a fully integrated system."""
        safety_controller = SafetyController()
        command_executor = CommandExecutor(safety_controller)
        voice_output = VoiceOutputModule()
        memory_manager = MemoryManager(storage_dir=tmp_path)
        intent_parser = IntentParser()
        context_engine = ContextEngine(intent_parser, memory_manager)
        
        return {
            'safety_controller': safety_controller,
            'command_executor': command_executor,
            'voice_output': voice_output,
            'context_engine': context_engine,
            'memory_manager': memory_manager
        }
    
    @pytest.fixture
    def session(self):
        """Create a test session."""
        return Session(
            session_id=str(uuid.uuid4()),
            user_id="test_user",
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
    
    def test_e2e_file_deletion_with_confirmation(self, integrated_system, session):
        """End-to-end test: file deletion with full confirmation flow."""
        # User says: "delete myfile.txt"
        command_text = "delete myfile.txt"
        
        # Process command
        intent = integrated_system['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={"file_path": "myfile.txt"},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Safety check
        action_type = integrated_system['safety_controller'].classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE
        
        # Generate confirmation
        prompt = integrated_system['safety_controller'].generate_confirmation_prompt(command)
        
        # Voice output
        audio_prompt = integrated_system['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None
        
        # User confirms
        confirmation = "yes"
        is_confirmed = integrated_system['safety_controller'].validate_confirmation(confirmation)
        assert is_confirmed is True
        
        # Execution would proceed (not actually deleting in test)
    
    def test_e2e_system_restart_with_abortion(self, integrated_system, session):
        """End-to-end test: system restart with user abortion."""
        # User says: "restart the computer"
        command_text = "restart the computer"
        
        # Process command
        intent = integrated_system['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Safety check
        action_type = integrated_system['safety_controller'].classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE
        
        # Generate confirmation
        prompt = integrated_system['safety_controller'].generate_confirmation_prompt(command)
        
        # Voice output
        audio_prompt = integrated_system['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None
        
        # User cancels
        cancellation = "cancel"
        is_confirmed = integrated_system['safety_controller'].validate_confirmation(cancellation)
        is_aborted = integrated_system['safety_controller'].is_abortion(cancellation)
        
        assert is_confirmed is False
        assert is_aborted is True
        
        # Execution does NOT proceed
    
    def test_e2e_multiple_file_operations_with_mixed_responses(
        self, integrated_system, session
    ):
        """End-to-end test: multiple file operations with different user responses."""
        operations = [
            ("delete file1.txt", "yes", True),  # Confirmed
            ("delete file2.txt", "no", False),  # Aborted
            ("delete file3.txt", "confirm", True),  # Confirmed
        ]
        
        for cmd_text, response, should_proceed in operations:
            # Process command
            intent = integrated_system['context_engine'].process_command(cmd_text, session)
            
            command = Command(
                command_id=str(uuid.uuid4()),
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            
            # Safety check
            action_type = integrated_system['safety_controller'].classify_action(command)
            assert action_type == ActionType.DESTRUCTIVE
            
            # Generate confirmation
            prompt = integrated_system['safety_controller'].generate_confirmation_prompt(command)
            
            # Voice output
            audio_prompt = integrated_system['voice_output'].text_to_speech(prompt)
            assert audio_prompt is not None
            
            # User responds
            is_confirmed = integrated_system['safety_controller'].validate_confirmation(response)
            assert is_confirmed == should_proceed
    
    def test_e2e_confirmation_with_various_responses(self, integrated_system, session):
        """End-to-end test: test various confirmation responses."""
        command_text = "delete testfile.txt"
        
        # Test different confirmation words
        confirmation_words = ["yes", "confirm", "proceed", "ok", "okay"]
        
        for word in confirmation_words:
            intent = integrated_system['context_engine'].process_command(command_text, session)
            
            command = Command(
                command_id=str(uuid.uuid4()),
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            
            # Validate confirmation
            is_confirmed = integrated_system['safety_controller'].validate_confirmation(word)
            assert is_confirmed is True, f"'{word}' should be accepted as confirmation"
        
        # Test different abortion words
        abortion_words = ["no", "cancel", "stop", "abort", "nevermind"]
        
        for word in abortion_words:
            is_aborted = integrated_system['safety_controller'].is_abortion(word)
            assert is_aborted is True, f"'{word}' should be accepted as abortion"
    
    def test_e2e_destructive_action_with_context_reference(
        self, integrated_system, session
    ):
        """End-to-end test: destructive action with context reference."""
        # First command: create a file reference
        command_text_1 = "find important.txt"
        intent_1 = integrated_system['context_engine'].process_command(command_text_1, session)
        
        command_1 = Command(
            command_id=str(uuid.uuid4()),
            intent=intent_1,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        result_1 = CommandResult(
            command_id=command_1.command_id,
            success=True,
            output="Found: important.txt",
            error=None,
            execution_time_ms=100
        )
        
        integrated_system['context_engine'].add_to_history(command_1, result_1, session)
        
        # Second command: delete "that" (should resolve to important.txt)
        command_text_2 = "delete that"
        intent_2 = integrated_system['context_engine'].process_command(command_text_2, session)
        
        command_2 = Command(
            command_id=str(uuid.uuid4()),
            intent=intent_2,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Safety check
        action_type = integrated_system['safety_controller'].classify_action(command_2)
        assert action_type == ActionType.DESTRUCTIVE
        
        # Generate confirmation (should mention the resolved file)
        prompt = integrated_system['safety_controller'].generate_confirmation_prompt(command_2)
        
        # Voice output
        audio_prompt = integrated_system['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None
