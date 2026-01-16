"""Integration tests for Safety Controller.

This module tests the Safety Controller in realistic scenarios,
verifying the complete workflow from command classification through
confirmation to execution decision.
"""

import pytest
from datetime import datetime
from prime.safety import SafetyController
from prime.safety.safety_controller import ActionType, SecurityEvent
from prime.models import Command, Intent, Entity


class TestSafetyWorkflow:
    """Test complete safety workflow scenarios."""
    
    def test_destructive_action_workflow(self):
        """Test complete workflow for a destructive action."""
        # Create a file deletion command
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
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Step 1: Classify the action
        action_type = controller.classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE
        
        # Step 2: Check if confirmation is required
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is True
        
        # Step 3: Generate confirmation prompt
        prompt = controller.generate_confirmation_prompt(command)
        assert "important.txt" in prompt
        assert "CONFIRMATION" in prompt
        
        # Step 4: User confirms
        user_response = "yes"
        is_confirmed = controller.validate_confirmation(user_response)
        assert is_confirmed is True
        
        # Step 5: Log the event
        event = SecurityEvent(
            event_type="destructive_action_confirmed",
            command_id=command.command_id,
            description=f"User confirmed deletion of important.txt",
            timestamp=datetime.now(),
            severity="warning"
        )
        controller.log_security_event(event)
        
        # Workflow complete - action would proceed
    
    def test_destructive_action_aborted(self):
        """Test workflow when user aborts a destructive action."""
        # Create a shutdown command
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
        
        # Step 1: Classify the action
        action_type = controller.classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE
        
        # Step 2: Check if confirmation is required
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is True
        
        # Step 3: Generate confirmation prompt
        prompt = controller.generate_confirmation_prompt(command)
        assert "shut down" in prompt.lower() or "shutdown" in prompt.lower()
        
        # Step 4: User aborts
        user_response = "no"
        is_confirmed = controller.validate_confirmation(user_response)
        is_aborted = controller.is_abortion(user_response)
        assert is_confirmed is False
        assert is_aborted is True
        
        # Step 5: Log the abortion
        event = SecurityEvent(
            event_type="destructive_action_aborted",
            command_id=command.command_id,
            description="User aborted shutdown command",
            timestamp=datetime.now(),
            severity="info"
        )
        controller.log_security_event(event)
        
        # Workflow complete - action would NOT proceed
    
    def test_prohibited_action_blocked(self):
        """Test workflow when a prohibited action is attempted."""
        # Create a hacking command
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "hack into network", 0.9)],
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
        
        # Step 1: Classify the action
        action_type = controller.classify_action(command)
        assert action_type == ActionType.PROHIBITED
        
        # Step 2: Check if it's prohibited
        is_prohibited = controller.is_prohibited(command)
        assert is_prohibited is True
        
        # Step 3: Confirmation should not be required (it's blocked entirely)
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is False
        
        # Step 4: Log the security violation
        event = SecurityEvent(
            event_type="prohibited_command_blocked",
            command_id=command.command_id,
            description="User attempted prohibited hacking command",
            timestamp=datetime.now(),
            severity="critical"
        )
        controller.log_security_event(event)
        
        # Workflow complete - action is BLOCKED, no confirmation needed
    
    def test_safe_action_no_confirmation(self):
        """Test workflow for a safe action that doesn't need confirmation."""
        # Create a launch app command
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "chrome", 0.9)],
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
        
        # Step 1: Classify the action
        action_type = controller.classify_action(command)
        assert action_type == ActionType.SAFE
        
        # Step 2: Check if confirmation is required
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is False
        
        # Step 3: No confirmation needed, action proceeds directly
        # (No prompt generation or validation needed)
        
        # Workflow complete - action proceeds without confirmation
    
    def test_process_termination_workflow(self):
        """Test workflow for process termination (Requirement 10.4)."""
        # Create a process termination command
        intent = Intent(
            intent_type="terminate_process",
            entities=[Entity("process_name", "chrome", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd-005",
            intent=intent,
            parameters={"pid": 1234},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Step 1: Classify the action
        action_type = controller.classify_action(command)
        assert action_type == ActionType.DESTRUCTIVE
        
        # Step 2: Check if confirmation is required
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is True
        
        # Step 3: Generate confirmation prompt
        prompt = controller.generate_confirmation_prompt(command)
        assert "chrome" in prompt.lower() or "process" in prompt.lower()
        
        # Step 4: User confirms with "proceed"
        user_response = "proceed"
        is_confirmed = controller.validate_confirmation(user_response)
        assert is_confirmed is True
        
        # Workflow complete - process termination would proceed


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_command_classification(self):
        """Test classification of command with no entities."""
        intent = Intent(
            intent_type="unknown",
            entities=[],
            confidence=0.5,
            requires_clarification=True
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
        
        # Should default to SAFE for unknown commands
        assert action_type == ActionType.SAFE
    
    def test_mixed_case_confirmation(self):
        """Test confirmation with mixed case input."""
        controller = SafetyController()
        
        # Various mixed case confirmations
        assert controller.validate_confirmation("YeS") is True
        assert controller.validate_confirmation("CoNfIrM") is True
        assert controller.validate_confirmation("pRoCeEd") is True
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in responses."""
        controller = SafetyController()
        
        # Leading/trailing whitespace
        assert controller.validate_confirmation("  yes  ") is True
        assert controller.is_abortion("  no  ") is True
        
        # Tabs and newlines
        assert controller.validate_confirmation("\tconfirm\n") is True
        assert controller.is_abortion("\tcancel\n") is True
    
    def test_multiple_destructive_keywords(self):
        """Test command with multiple destructive keywords."""
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", "delete and remove files", 0.9)],
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
        
        # Should be classified as destructive
        assert action_type == ActionType.DESTRUCTIVE
    
    def test_prohibited_overrides_destructive(self):
        """Test that prohibited classification takes precedence."""
        intent = Intent(
            intent_type="delete_file",  # Normally destructive
            entities=[Entity("command", "hack and delete", 0.9)],  # But also prohibited
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
        
        # Should be classified as prohibited (higher priority)
        assert action_type == ActionType.PROHIBITED
