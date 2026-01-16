"""Unit tests for Safety Controller.

This module tests the basic functionality of the Safety Controller,
including action classification, confirmation prompt generation,
and validation logic.
"""

import pytest
from datetime import datetime
from prime.safety import SafetyController
from prime.safety.safety_controller import ActionType, SecurityEvent
from prime.models import Command, Intent, Entity


class TestActionClassification:
    """Test action classification logic."""
    
    def test_classify_delete_file_as_destructive(self):
        """Delete file commands should be classified as destructive."""
        intent = Intent(
            intent_type="delete_file",
            entities=[Entity("file_name", "test.txt", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-001",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.DESTRUCTIVE
    
    def test_classify_shutdown_as_destructive(self):
        """Shutdown commands should be classified as destructive."""
        intent = Intent(
            intent_type="shutdown",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-002",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.DESTRUCTIVE
    
    def test_classify_terminate_process_as_destructive(self):
        """Process termination should be classified as destructive."""
        intent = Intent(
            intent_type="terminate_process",
            entities=[Entity("process_name", "chrome", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-003",
            intent=intent,
            parameters={"pid": 1234},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.DESTRUCTIVE
    
    def test_classify_modify_setting_as_destructive(self):
        """Setting modifications should be classified as destructive."""
        intent = Intent(
            intent_type="modify_setting",
            entities=[Entity("setting_name", "network", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-004",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.DESTRUCTIVE
    
    def test_classify_launch_app_as_safe(self):
        """Launching applications should be classified as safe."""
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "chrome", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-005",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.SAFE
    
    def test_classify_hacking_as_prohibited(self):
        """Hacking-related commands should be classified as prohibited."""
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "hack into system", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-006",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.PROHIBITED
    
    def test_classify_surveillance_as_prohibited(self):
        """Unauthorized surveillance should be classified as prohibited."""
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "unauthorized surveillance", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-007",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        action_type = controller.classify_action(command)
        
        assert action_type == ActionType.PROHIBITED


class TestConfirmationRequirement:
    """Test confirmation requirement logic."""
    
    def test_destructive_requires_confirmation(self):
        """Destructive actions should require confirmation."""
        controller = SafetyController()
        assert controller.requires_confirmation(ActionType.DESTRUCTIVE) is True
    
    def test_safe_does_not_require_confirmation(self):
        """Safe actions should not require confirmation."""
        controller = SafetyController()
        assert controller.requires_confirmation(ActionType.SAFE) is False
    
    def test_prohibited_does_not_require_confirmation(self):
        """Prohibited actions should not require confirmation (they're blocked)."""
        controller = SafetyController()
        assert controller.requires_confirmation(ActionType.PROHIBITED) is False


class TestConfirmationPrompt:
    """Test confirmation prompt generation."""
    
    def test_generate_prompt_for_delete_file(self):
        """Confirmation prompt should describe file deletion clearly."""
        intent = Intent(
            intent_type="delete_file",
            entities=[Entity("file_name", "important.txt", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-001",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=True
        )
        
        controller = SafetyController()
        prompt = controller.generate_confirmation_prompt(command)
        
        # Check that prompt contains key elements
        assert "CONFIRMATION REQUIRED" in prompt
        assert "important.txt" in prompt
        assert "cannot be easily undone" in prompt or "cannot be recovered" in prompt
        assert "yes" in prompt.lower()
        assert "no" in prompt.lower()
    
    def test_generate_prompt_for_shutdown(self):
        """Confirmation prompt should describe shutdown consequences."""
        intent = Intent(
            intent_type="shutdown",
            entities=[],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-002",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=True
        )
        
        controller = SafetyController()
        prompt = controller.generate_confirmation_prompt(command)
        
        assert "CONFIRMATION REQUIRED" in prompt
        assert "shut down" in prompt.lower() or "shutdown" in prompt.lower()
        assert "unsaved work" in prompt.lower() or "lost" in prompt.lower()
    
    def test_generate_prompt_for_terminate_process(self):
        """Confirmation prompt should describe process termination."""
        intent = Intent(
            intent_type="terminate_process",
            entities=[Entity("process_name", "chrome", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-003",
            intent=intent,
            parameters={"pid": 1234},
            timestamp=datetime.now(),
            requires_confirmation=True
        )
        
        controller = SafetyController()
        prompt = controller.generate_confirmation_prompt(command)
        
        assert "CONFIRMATION REQUIRED" in prompt
        assert "chrome" in prompt.lower()
        assert "process" in prompt.lower()


class TestConfirmationValidation:
    """Test confirmation response validation."""
    
    def test_validate_yes(self):
        """'yes' should be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("yes") is True
    
    def test_validate_confirm(self):
        """'confirm' should be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("confirm") is True
    
    def test_validate_proceed(self):
        """'proceed' should be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("proceed") is True
    
    def test_validate_case_insensitive(self):
        """Confirmation should be case-insensitive."""
        controller = SafetyController()
        assert controller.validate_confirmation("YES") is True
        assert controller.validate_confirmation("Confirm") is True
        assert controller.validate_confirmation("PROCEED") is True
    
    def test_validate_with_whitespace(self):
        """Confirmation should handle whitespace."""
        controller = SafetyController()
        assert controller.validate_confirmation("  yes  ") is True
        assert controller.validate_confirmation("\tconfirm\n") is True
    
    def test_validate_no_rejects(self):
        """'no' should not be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("no") is False
    
    def test_validate_cancel_rejects(self):
        """'cancel' should not be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("cancel") is False
    
    def test_validate_empty_rejects(self):
        """Empty string should not be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("") is False
    
    def test_validate_random_text_rejects(self):
        """Random text should not be accepted as confirmation."""
        controller = SafetyController()
        assert controller.validate_confirmation("maybe") is False
        assert controller.validate_confirmation("I don't know") is False


class TestAbortion:
    """Test abortion response detection."""
    
    def test_is_abortion_no(self):
        """'no' should be detected as abortion."""
        controller = SafetyController()
        assert controller.is_abortion("no") is True
    
    def test_is_abortion_cancel(self):
        """'cancel' should be detected as abortion."""
        controller = SafetyController()
        assert controller.is_abortion("cancel") is True
    
    def test_is_abortion_stop(self):
        """'stop' should be detected as abortion."""
        controller = SafetyController()
        assert controller.is_abortion("stop") is True
    
    def test_is_abortion_case_insensitive(self):
        """Abortion detection should be case-insensitive."""
        controller = SafetyController()
        assert controller.is_abortion("NO") is True
        assert controller.is_abortion("Cancel") is True
        assert controller.is_abortion("STOP") is True
    
    def test_is_abortion_yes_returns_false(self):
        """'yes' should not be detected as abortion."""
        controller = SafetyController()
        assert controller.is_abortion("yes") is False


class TestProhibitedCommands:
    """Test prohibited command detection."""
    
    def test_is_prohibited_hack(self):
        """Commands with 'hack' should be prohibited."""
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "hack the system", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-001",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        assert controller.is_prohibited(command) is True
    
    def test_is_prohibited_bypass_security(self):
        """Commands with 'bypass security' should be prohibited."""
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "bypass security", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-002",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        assert controller.is_prohibited(command) is True
    
    def test_is_prohibited_safe_command(self):
        """Safe commands should not be prohibited."""
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "chrome", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-003",
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        assert controller.is_prohibited(command) is False


class TestSecurityEventLogging:
    """Test security event logging."""
    
    def test_log_security_event_info(self):
        """Info events should be logged."""
        controller = SafetyController()
        event = SecurityEvent(
            event_type="confirmation_required",
            command_id="cmd-001",
            description="User requested file deletion",
            timestamp=datetime.now(),
            severity="info"
        )
        
        # Should not raise an exception
        controller.log_security_event(event)
    
    def test_log_security_event_warning(self):
        """Warning events should be logged."""
        controller = SafetyController()
        event = SecurityEvent(
            event_type="suspicious_command",
            command_id="cmd-002",
            description="Command contains suspicious keywords",
            timestamp=datetime.now(),
            severity="warning"
        )
        
        # Should not raise an exception
        controller.log_security_event(event)
    
    def test_log_security_event_critical(self):
        """Critical events should be logged."""
        controller = SafetyController()
        event = SecurityEvent(
            event_type="prohibited_command",
            command_id="cmd-003",
            description="User attempted prohibited action",
            timestamp=datetime.now(),
            severity="critical"
        )
        
        # Should not raise an exception
        controller.log_security_event(event)
