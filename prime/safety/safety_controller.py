"""Safety Controller for PRIME Voice Assistant.

This module implements the Safety Controller component that validates and
confirms potentially destructive operations, blocks prohibited commands,
and logs security-relevant events.

**Validates: Requirements 5.1-5.6, 10.4**
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from prime.models import Command


class ActionType(Enum):
    """Classification of command actions by safety level."""
    SAFE = "safe"
    DESTRUCTIVE = "destructive"
    PROHIBITED = "prohibited"


@dataclass
class SecurityEvent:
    """Represents a security-relevant event."""
    event_type: str
    command_id: str
    description: str
    timestamp: datetime
    severity: str  # "info", "warning", "critical"


class SafetyController:
    """Controls safety and security for command execution.
    
    The Safety Controller is responsible for:
    - Classifying actions as safe, destructive, or prohibited
    - Requiring confirmation for destructive actions
    - Validating user confirmations
    - Blocking prohibited operations
    - Logging security events
    
    **Validates: Requirements 5.1-5.6, 10.4**
    """
    
    # Keywords that indicate destructive actions
    DESTRUCTIVE_KEYWORDS = {
        'delete', 'remove', 'rm', 'erase', 'wipe', 'clear',
        'shutdown', 'restart', 'reboot', 'power off',
        'terminate', 'kill', 'stop process', 'end process',
        'format', 'modify setting', 'change setting', 'update setting',
        'uninstall', 'purge'
    }
    
    # Keywords that indicate prohibited actions
    PROHIBITED_KEYWORDS = {
        'hack', 'crack', 'exploit', 'breach', 'bypass security',
        'unauthorized', 'surveillance', 'spy', 'keylog',
        'steal', 'illegal', 'malware', 'virus', 'trojan',
        'ddos', 'attack', 'penetrate', 'brute force'
    }
    
    # Confirmation words that allow execution
    CONFIRMATION_WORDS = {'yes', 'confirm', 'proceed', 'continue', 'ok', 'okay'}
    
    # Abortion words that cancel execution
    ABORTION_WORDS = {'no', 'cancel', 'stop', 'abort', 'nevermind', 'never mind'}
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Safety Controller.
        
        Args:
            logger: Optional logger instance. If not provided, creates a new one.
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def classify_action(self, command: Command) -> ActionType:
        """Classify a command as safe, destructive, or prohibited.
        
        **Validates: Requirements 5.2, 5.6**
        
        Classification rules:
        - PROHIBITED: Commands related to hacking, security bypass, unauthorized
          surveillance, or illegal activities
        - DESTRUCTIVE: File deletion, system shutdown, restart, process termination,
          and setting modifications
        - SAFE: All other commands
        
        Args:
            command: The command to classify
            
        Returns:
            ActionType indicating the safety classification
        """
        # First check if prohibited
        if self.is_prohibited(command):
            return ActionType.PROHIBITED
        
        # Check if destructive
        intent_type = command.intent.intent_type.lower()
        
        # Check intent type for destructive actions
        destructive_intents = {
            'delete_file', 'remove_file', 'shutdown', 'restart',
            'terminate_process', 'kill_process', 'modify_setting',
            'change_setting', 'update_setting', 'format_disk',
            'uninstall_app'
        }
        
        if intent_type in destructive_intents:
            return ActionType.DESTRUCTIVE
        
        # Check command parameters and entities for destructive keywords
        command_text = self._extract_command_text(command)
        command_lower = command_text.lower()
        
        for keyword in self.DESTRUCTIVE_KEYWORDS:
            if keyword in command_lower:
                return ActionType.DESTRUCTIVE
        
        return ActionType.SAFE
    
    def requires_confirmation(self, action: ActionType) -> bool:
        """Determine if an action requires user confirmation.
        
        **Validates: Requirements 5.1**
        
        Args:
            action: The action type to check
            
        Returns:
            True if confirmation is required, False otherwise
        """
        return action == ActionType.DESTRUCTIVE
    
    def generate_confirmation_prompt(self, command: Command) -> str:
        """Generate a confirmation prompt for a destructive action.
        
        **Validates: Requirements 5.3**
        
        The prompt clearly describes:
        - What action will be performed
        - What the consequences are
        - How to confirm or cancel
        
        Args:
            command: The command requiring confirmation
            
        Returns:
            A clear confirmation prompt string
        """
        intent_type = command.intent.intent_type
        
        # Extract relevant information from the command
        action_description = self._describe_action(command)
        consequences = self._describe_consequences(command)
        
        prompt = (
            f"⚠️  CONFIRMATION REQUIRED\n\n"
            f"Action: {action_description}\n"
            f"Consequences: {consequences}\n\n"
            f"This action cannot be easily undone.\n"
            f"Please confirm by saying 'yes', 'confirm', or 'proceed'.\n"
            f"To cancel, say 'no', 'cancel', or 'stop'."
        )
        
        return prompt
    
    def validate_confirmation(self, response: str) -> bool:
        """Validate a user's confirmation response.
        
        **Validates: Requirements 5.4**
        
        Accepts: "yes", "confirm", "proceed" (case-insensitive)
        
        Args:
            response: The user's response to the confirmation prompt
            
        Returns:
            True if the response confirms the action, False otherwise
        """
        if not response:
            return False
        
        response_lower = response.strip().lower()
        
        # Check for confirmation words
        return response_lower in self.CONFIRMATION_WORDS
    
    def is_abortion(self, response: str) -> bool:
        """Check if a response indicates the user wants to abort.
        
        **Validates: Requirements 5.5**
        
        Abortion words: "no", "cancel", "stop" (case-insensitive)
        
        Args:
            response: The user's response
            
        Returns:
            True if the response indicates abortion, False otherwise
        """
        if not response:
            return False
        
        response_lower = response.strip().lower()
        
        # Check for abortion words
        return response_lower in self.ABORTION_WORDS
    
    def is_prohibited(self, command: Command) -> bool:
        """Check if a command is prohibited.
        
        **Validates: Requirements 5.6**
        
        Prohibited commands include those related to:
        - Hacking
        - Security bypass
        - Unauthorized surveillance
        - Illegal activities
        
        Args:
            command: The command to check
            
        Returns:
            True if the command is prohibited, False otherwise
        """
        command_text = self._extract_command_text(command)
        command_lower = command_text.lower()
        
        # Check for prohibited keywords
        for keyword in self.PROHIBITED_KEYWORDS:
            if keyword in command_lower:
                return True
        
        return False
    
    def log_security_event(self, event: SecurityEvent) -> None:
        """Log a security-relevant event.
        
        **Validates: Requirements 5.6, 15.4**
        
        Events are logged with appropriate severity levels:
        - info: Normal security checks
        - warning: Suspicious or potentially dangerous actions
        - critical: Prohibited actions or security violations
        
        Args:
            event: The security event to log
        """
        log_message = (
            f"Security Event [{event.severity.upper()}] - "
            f"{event.event_type}: {event.description} "
            f"(Command ID: {event.command_id}, Time: {event.timestamp})"
        )
        
        if event.severity == "critical":
            self.logger.critical(log_message)
        elif event.severity == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _extract_command_text(self, command: Command) -> str:
        """Extract a text representation of the command for analysis.
        
        Args:
            command: The command to extract text from
            
        Returns:
            A string representation of the command
        """
        parts = [command.intent.intent_type]
        
        # Add entity values
        for entity in command.intent.entities:
            parts.append(str(entity.value))
        
        # Add parameter values
        for key, value in command.parameters.items():
            parts.append(f"{key}={value}")
        
        return " ".join(parts)
    
    def _describe_action(self, command: Command) -> str:
        """Generate a human-readable description of the action.
        
        Args:
            command: The command to describe
            
        Returns:
            A description of what the command will do
        """
        intent_type = command.intent.intent_type
        
        # Map intent types to descriptions
        descriptions = {
            'delete_file': 'Delete file(s)',
            'remove_file': 'Remove file(s)',
            'shutdown': 'Shut down the system',
            'restart': 'Restart the system',
            'reboot': 'Reboot the system',
            'terminate_process': 'Terminate process',
            'kill_process': 'Kill process',
            'modify_setting': 'Modify system setting',
            'change_setting': 'Change system setting',
            'update_setting': 'Update system setting',
            'format_disk': 'Format disk',
            'uninstall_app': 'Uninstall application'
        }
        
        base_description = descriptions.get(intent_type, intent_type.replace('_', ' ').title())
        
        # Add entity information if available
        if command.intent.entities:
            entity_values = [str(e.value) for e in command.intent.entities]
            if entity_values:
                base_description += f": {', '.join(entity_values)}"
        
        return base_description
    
    def _describe_consequences(self, command: Command) -> str:
        """Generate a description of the consequences of the action.
        
        Args:
            command: The command to describe consequences for
            
        Returns:
            A description of what will happen if the command executes
        """
        intent_type = command.intent.intent_type
        
        # Map intent types to consequences
        consequences = {
            'delete_file': 'The file(s) will be permanently deleted and cannot be recovered',
            'remove_file': 'The file(s) will be permanently removed and cannot be recovered',
            'shutdown': 'The system will shut down and all unsaved work will be lost',
            'restart': 'The system will restart and all unsaved work will be lost',
            'reboot': 'The system will reboot and all unsaved work will be lost',
            'terminate_process': 'The process will be forcefully terminated and may lose unsaved data',
            'kill_process': 'The process will be forcefully killed and may lose unsaved data',
            'modify_setting': 'System settings will be changed, which may affect system behavior',
            'change_setting': 'System settings will be changed, which may affect system behavior',
            'update_setting': 'System settings will be updated, which may affect system behavior',
            'format_disk': 'All data on the disk will be permanently erased',
            'uninstall_app': 'The application and its data will be removed from the system'
        }
        
        return consequences.get(
            intent_type,
            'This action may modify or delete data and cannot be easily undone'
        )
