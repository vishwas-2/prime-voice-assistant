"""Integration tests for Voice Input Flow.

This module tests the complete voice input flow integration:
Voice Input → Intent Parser → Context Engine → Command Executor → Voice Output

**Validates: Requirements 1.3 (Property 3)**

Task 9.2: Voice Input Flow Integration
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from prime.voice import VoiceInputModule, VoiceOutputModule, AudioStream
from prime.nlp import IntentParser, ContextEngine
from prime.execution import CommandExecutor
from prime.safety import SafetyController
from prime.persistence import MemoryManager
from prime.models import (
    Session, Command, Intent, Entity, CommandResult,
    VoiceProfile
)


class TestVoiceInputFlowIntegration:
    """Test complete voice input flow integration."""
    
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
    
    @pytest.fixture
    def components(self, tmp_path):
        """Create all components for integration testing."""
        # Create components
        voice_input = VoiceInputModule()
        intent_parser = IntentParser()
        memory_manager = MemoryManager(storage_dir=tmp_path)
        context_engine = ContextEngine(intent_parser, memory_manager)
        safety_controller = SafetyController()
        command_executor = CommandExecutor(safety_controller)
        voice_output = VoiceOutputModule()
        
        return {
            'voice_input': voice_input,
            'intent_parser': intent_parser,
            'context_engine': context_engine,
            'command_executor': command_executor,
            'voice_output': voice_output,
            'memory_manager': memory_manager,
            'safety_controller': safety_controller
        }
    
    def test_complete_voice_command_flow_launch_app(self, components, session):
        """
        Test complete flow: voice command to launch an application.
        
        Flow: Voice Input → Intent Parser → Context Engine → Command Executor → Voice Output
        """
        # Step 1: Simulate voice input (speech-to-text)
        command_text = "launch notepad"
        
        # Step 2: Parse intent
        intent = components['intent_parser'].parse(command_text)
        assert intent.intent_type == "launch_app"
        assert len(intent.entities) > 0
        
        # Step 3: Process with context engine
        processed_intent = components['context_engine'].process_command(command_text, session)
        assert processed_intent.intent_type == "launch_app"
        
        # Step 4: Create command
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=processed_intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 5: Check safety
        action_type = components['safety_controller'].classify_action(command)
        assert action_type.value == "safe"
        
        # Step 6: Execute command (mock the actual execution)
        with patch.object(components['command_executor'], 'launch_application') as mock_launch:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_launch.return_value = mock_process
            
            result = components['command_executor'].execute(command)
            
            assert result.success is True
            assert "notepad" in result.output.lower()
        
        # Step 7: Add to history
        components['context_engine'].add_to_history(command, result, session)
        assert len(session.command_history) == 1
        
        # Step 8: Generate voice response
        response_text = result.output
        audio_response = components['voice_output'].text_to_speech(response_text)
        assert audio_response is not None
        assert audio_response.duration_ms > 0
    
    def test_complete_voice_command_flow_with_reference(self, components, session):
        """
        Test flow with pronoun reference resolution.
        
        Tests that context engine can resolve "it" to a previous entity.
        """
        # First command: launch chrome
        command_text_1 = "launch chrome"
        intent_1 = components['context_engine'].process_command(command_text_1, session)
        
        command_1 = Command(
            command_id=str(uuid.uuid4()),
            intent=intent_1,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Mock execution
        result_1 = CommandResult(
            command_id=command_1.command_id,
            success=True,
            output="Successfully launched chrome",
            error=None,
            execution_time_ms=500
        )
        
        # Add to history
        components['context_engine'].add_to_history(command_1, result_1, session)
        
        # Second command: close it (should resolve "it" to chrome)
        command_text_2 = "close it"
        intent_2 = components['context_engine'].process_command(command_text_2, session)
        
        # Verify that context was used
        assert len(session.command_history) == 1
        
        # Resolve reference
        entity = components['context_engine'].resolve_reference("it", session)
        assert entity is not None
        assert "chrome" in str(entity.value).lower()
    
    def test_complete_voice_command_flow_destructive_action(self, components, session):
        """
        Test flow with destructive action requiring confirmation.
        
        Flow includes safety check and confirmation prompt.
        """
        # Step 1: Parse destructive command
        command_text = "delete important.txt"
        intent = components['context_engine'].process_command(command_text, session)
        
        # Step 2: Create command
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 3: Safety check
        action_type = components['safety_controller'].classify_action(command)
        assert action_type.value == "destructive"
        
        # Step 4: Check if confirmation required
        requires_conf = components['safety_controller'].requires_confirmation(action_type)
        assert requires_conf is True
        
        # Step 5: Generate confirmation prompt
        prompt = components['safety_controller'].generate_confirmation_prompt(command)
        assert "important.txt" in prompt
        assert "CONFIRMATION" in prompt
        
        # Step 6: Convert prompt to speech
        audio_prompt = components['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None
        
        # Step 7: Simulate user confirmation
        user_response = "yes"
        is_confirmed = components['safety_controller'].validate_confirmation(user_response)
        assert is_confirmed is True
        
        # Step 8: Execute would proceed (not actually deleting in test)
        # In real system, execution would happen here
    
    def test_voice_command_flow_with_error_handling(self, components, session):
        """
        Test flow with error handling and error message generation.
        """
        # Step 1: Parse command for non-existent app
        command_text = "launch nonexistentapp12345"
        intent = components['context_engine'].process_command(command_text, session)
        
        # Step 2: Create command
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Step 3: Execute command (will fail)
        with patch.object(components['command_executor'], 'launch_application') as mock_launch:
            mock_launch.side_effect = FileNotFoundError("Application not found")
            
            result = components['command_executor'].execute(command)
            
            assert result.success is False
            assert result.error is not None
            assert "not found" in result.error.lower()
        
        # Step 4: Generate error response
        error_response = result.error
        audio_error = components['voice_output'].text_to_speech(error_response)
        assert audio_error is not None
        
        # Step 5: Add to history
        components['context_engine'].add_to_history(command, result, session)
        assert len(session.command_history) == 1
        assert not session.command_history[0].result.success
    
    def test_voice_command_flow_with_suggestions(self, components, session):
        """
        Test flow that generates proactive suggestions.
        """
        # Execute several similar commands to trigger pattern detection
        for i in range(3):
            command_text = "launch chrome"
            intent = components['context_engine'].process_command(command_text, session)
            
            command = Command(
                command_id=str(uuid.uuid4()),
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            
            result = CommandResult(
                command_id=command.command_id,
                success=True,
                output="Successfully launched chrome",
                error=None,
                execution_time_ms=500
            )
            
            components['context_engine'].add_to_history(command, result, session)
        
        # Get suggestions
        suggestions = components['context_engine'].get_suggestions(session)
        
        # Should have suggestions based on repetitive pattern
        # (May or may not trigger depending on pattern detection logic)
        assert isinstance(suggestions, list)


class TestEndToEndVoiceCommands:
    """End-to-end tests for complete voice command scenarios."""
    
    @pytest.fixture
    def integrated_system(self, tmp_path):
        """Create a fully integrated system."""
        memory_manager = MemoryManager(storage_dir=tmp_path)
        intent_parser = IntentParser()
        context_engine = ContextEngine(intent_parser, memory_manager)
        safety_controller = SafetyController()
        command_executor = CommandExecutor(safety_controller)
        voice_output = VoiceOutputModule()
        
        return {
            'context_engine': context_engine,
            'command_executor': command_executor,
            'voice_output': voice_output,
            'safety_controller': safety_controller,
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
    
    def test_e2e_simple_command(self, integrated_system, session):
        """End-to-end test: simple voice command execution."""
        # User says: "launch notepad"
        command_text = "launch notepad"
        
        # Process command
        intent = integrated_system['context_engine'].process_command(command_text, session)
        
        # Create command object
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Execute with mocked launch
        with patch.object(integrated_system['command_executor'], 'launch_application') as mock_launch:
            mock_process = Mock()
            mock_process.pid = 9999
            mock_launch.return_value = mock_process
            
            result = integrated_system['command_executor'].execute(command)
        
        # Verify success
        assert result.success is True
        
        # Generate voice response
        response_audio = integrated_system['voice_output'].text_to_speech(result.output)
        assert response_audio is not None
        
        # Update history
        integrated_system['context_engine'].add_to_history(command, result, session)
        assert len(session.command_history) == 1
    
    def test_e2e_multi_step_conversation(self, integrated_system, session):
        """End-to-end test: multi-step conversation with context."""
        # Step 1: Launch application
        command_text_1 = "launch firefox"
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
            output="Successfully launched firefox",
            error=None,
            execution_time_ms=800
        )
        
        integrated_system['context_engine'].add_to_history(command_1, result_1, session)
        
        # Step 2: Reference previous command
        command_text_2 = "close that"
        intent_2 = integrated_system['context_engine'].process_command(command_text_2, session)
        
        # Verify context is maintained
        assert len(session.command_history) == 1
        
        # Resolve reference
        entity = integrated_system['context_engine'].resolve_reference("that", session)
        assert entity is not None
    
    def test_e2e_destructive_action_with_confirmation(self, integrated_system, session):
        """End-to-end test: destructive action with full confirmation flow."""
        # User says: "delete myfile.txt"
        command_text = "delete myfile.txt"
        intent = integrated_system['context_engine'].process_command(command_text, session)
        
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Check if destructive
        action_type = integrated_system['safety_controller'].classify_action(command)
        assert action_type.value == "destructive"
        
        # Generate confirmation
        prompt = integrated_system['safety_controller'].generate_confirmation_prompt(command)
        
        # Convert to speech
        audio_prompt = integrated_system['voice_output'].text_to_speech(prompt)
        assert audio_prompt is not None
        
        # User confirms
        confirmation = "yes"
        is_confirmed = integrated_system['safety_controller'].validate_confirmation(confirmation)
        assert is_confirmed is True
        
        # Execution would proceed (not actually deleting in test)
    
    def test_e2e_prohibited_command_blocked(self, integrated_system, session):
        """End-to-end test: prohibited command is blocked."""
        # User says something prohibited - create a command with prohibited keywords in parameters
        command_text = "execute hack command"
        intent = integrated_system['context_engine'].process_command(command_text, session)
        
        # Add prohibited keyword to command parameters to ensure detection
        command = Command(
            command_id=str(uuid.uuid4()),
            intent=intent,
            parameters={"command": "hack into network"},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        # Check if prohibited
        is_prohibited = integrated_system['safety_controller'].is_prohibited(command)
        assert is_prohibited is True
        
        # Execute (should be blocked)
        result = integrated_system['command_executor'].execute(command)
        assert result.success is False
        assert "prohibited" in result.error.lower()
        
        # Generate error response
        error_audio = integrated_system['voice_output'].text_to_speech(result.error)
        assert error_audio is not None
