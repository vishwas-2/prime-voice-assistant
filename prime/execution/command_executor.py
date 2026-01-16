"""Command Executor for PRIME Voice Assistant.

This module implements the Command Executor component that executes system
commands, launches applications, adjusts system settings, and manages command
execution status.

**Validates: Requirements 4.1, 4.2, 4.4, 4.5**
"""

import logging
import subprocess
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Callable
from dataclasses import dataclass

from prime.models import Command, CommandResult
from prime.safety import SafetyController


class ExecutionStatus(Enum):
    """Status of command execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionState:
    """Represents the current state of a command execution."""
    command_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    progress_message: Optional[str]
    result: Optional[CommandResult]


class CommandExecutor:
    """Executes system commands and operations.
    
    The Command Executor is responsible for:
    - Executing system commands
    - Launching applications
    - Providing real-time status updates
    - Reporting errors with clear explanations
    - Integrating with Safety Controller for destructive actions
    
    **Validates: Requirements 4.1, 4.2, 4.4, 4.5**
    """
    
    def __init__(
        self,
        safety_controller: Optional[SafetyController] = None,
        logger: Optional[logging.Logger] = None,
        status_callback: Optional[Callable[[str, str], None]] = None
    ):
        """Initialize the Command Executor.
        
        Args:
            safety_controller: Optional SafetyController instance for safety checks
            logger: Optional logger instance
            status_callback: Optional callback for status updates (command_id, message)
        """
        self.safety_controller = safety_controller or SafetyController()
        self.logger = logger or logging.getLogger(__name__)
        self.status_callback = status_callback
        
        # Track execution states
        self._execution_states: Dict[str, ExecutionState] = {}
    
    def execute(self, command: Command) -> CommandResult:
        """Execute a command and return the result.
        
        **Validates: Requirements 4.4, 4.5**
        
        This method:
        1. Validates the command with Safety Controller
        2. Executes the appropriate handler based on intent type
        3. Provides real-time status updates
        4. Returns a CommandResult with success/error information
        
        Args:
            command: The command to execute
            
        Returns:
            CommandResult with execution outcome
        """
        start_time = datetime.now()
        
        # Initialize execution state
        self._update_execution_state(
            command.command_id,
            ExecutionStatus.PENDING,
            start_time,
            "Command received, preparing to execute"
        )
        
        try:
            # Check if command is prohibited
            if self.safety_controller.is_prohibited(command):
                error_msg = (
                    "This command is prohibited for security reasons. "
                    "PRIME cannot execute commands related to hacking, "
                    "security bypass, unauthorized surveillance, or illegal activities."
                )
                self.logger.warning(f"Prohibited command blocked: {command.command_id}")
                
                self._update_execution_state(
                    command.command_id,
                    ExecutionStatus.FAILED,
                    start_time,
                    "Command blocked by safety controller",
                    end_time=datetime.now()
                )
                
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                return CommandResult(
                    command_id=command.command_id,
                    success=False,
                    output="",
                    error=error_msg,
                    execution_time_ms=execution_time
                )
            
            # Update status to in progress
            self._update_execution_state(
                command.command_id,
                ExecutionStatus.IN_PROGRESS,
                start_time,
                "Executing command"
            )
            
            # Route to appropriate handler based on intent type
            intent_type = command.intent.intent_type
            
            if intent_type == "launch_app" or intent_type == "launch_application":
                result = self._handle_launch_application(command, start_time)
            else:
                # Generic command execution
                result = self._handle_generic_command(command, start_time)
            
            # Update final state
            status = ExecutionStatus.COMPLETED if result.success else ExecutionStatus.FAILED
            self._update_execution_state(
                command.command_id,
                status,
                start_time,
                "Command completed" if result.success else "Command failed",
                end_time=datetime.now(),
                result=result
            )
            
            return result
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = self._generate_error_explanation(command, e)
            self.logger.error(f"Error executing command {command.command_id}: {e}", exc_info=True)
            
            self._update_execution_state(
                command.command_id,
                ExecutionStatus.FAILED,
                start_time,
                f"Error: {str(e)}",
                end_time=datetime.now()
            )
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return CommandResult(
                command_id=command.command_id,
                success=False,
                output="",
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def launch_application(self, app_name: str) -> subprocess.Popen:
        """Launch an application by name.
        
        **Validates: Requirements 4.1**
        
        This method launches an application and returns a process handle.
        The application should start within 3 seconds.
        
        Args:
            app_name: Name or path of the application to launch
            
        Returns:
            Process handle for the launched application
            
        Raises:
            FileNotFoundError: If the application cannot be found
            subprocess.SubprocessError: If the application fails to launch
        """
        self.logger.info(f"Launching application: {app_name}")
        
        try:
            # Try to launch the application
            # Use shell=True to allow launching by name (e.g., "notepad", "firefox")
            process = subprocess.Popen(
                app_name,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL  # Prevent interactive prompts
            )
            
            # Give it a moment to start and check for immediate failures
            time.sleep(0.2)
            
            # Check if process started successfully
            poll_result = process.poll()
            if poll_result is not None:
                # Process already terminated, likely an error
                try:
                    _, stderr = process.communicate(timeout=0.5)
                    error_msg = stderr.decode('utf-8', errors='ignore').strip()
                except:
                    error_msg = "Unknown error"
                
                # Check if it's a "not recognized" error (command not found)
                if "not recognized" in error_msg.lower() or "not found" in error_msg.lower():
                    raise FileNotFoundError(
                        f"Could not find application '{app_name}'. "
                        f"Please check the application name and try again."
                    )
                
                raise subprocess.SubprocessError(
                    f"Application failed to start: {error_msg or 'Unknown error'}"
                )
            
            self.logger.info(f"Application launched successfully: {app_name} (PID: {process.pid})")
            return process
            
        except FileNotFoundError:
            self.logger.error(f"Application not found: {app_name}")
            raise
        except subprocess.SubprocessError:
            self.logger.error(f"Failed to launch application {app_name}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to launch application {app_name}: {e}")
            raise subprocess.SubprocessError(
                f"Failed to launch application: {str(e)}"
            )
    
    def get_execution_status(self, command_id: str) -> Optional[ExecutionState]:
        """Get the current execution status of a command.
        
        **Validates: Requirements 4.4**
        
        This method provides real-time status updates for command execution.
        
        Args:
            command_id: The ID of the command to check
            
        Returns:
            ExecutionState if the command is being tracked, None otherwise
        """
        return self._execution_states.get(command_id)
    
    def _handle_launch_application(self, command: Command, start_time: datetime) -> CommandResult:
        """Handle application launch commands.
        
        Args:
            command: The launch application command
            start_time: When execution started
            
        Returns:
            CommandResult with launch outcome
        """
        # Extract application name from entities or parameters
        app_name = None
        
        for entity in command.intent.entities:
            if entity.entity_type in ["application", "app", "program"]:
                app_name = entity.value
                break
        
        if not app_name:
            app_name = command.parameters.get("app_name") or command.parameters.get("application")
        
        if not app_name:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return CommandResult(
                command_id=command.command_id,
                success=False,
                output="",
                error="No application name specified. Please specify which application to launch.",
                execution_time_ms=execution_time
            )
        
        try:
            # Update status
            self._send_status_update(
                command.command_id,
                f"Launching {app_name}..."
            )
            
            # Launch the application
            process = self.launch_application(app_name)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Check if we met the 3-second requirement
            if execution_time > 3000:
                self.logger.warning(
                    f"Application launch took {execution_time}ms, "
                    f"exceeding 3-second requirement"
                )
            
            return CommandResult(
                command_id=command.command_id,
                success=True,
                output=f"Successfully launched {app_name} (PID: {process.pid})",
                error=None,
                execution_time_ms=execution_time
            )
            
        except FileNotFoundError as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return CommandResult(
                command_id=command.command_id,
                success=False,
                output="",
                error=str(e),
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = (
                f"Failed to launch {app_name}: {str(e)}. "
                f"Please check that the application is installed and accessible."
            )
            return CommandResult(
                command_id=command.command_id,
                success=False,
                output="",
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _handle_generic_command(self, command: Command, start_time: datetime) -> CommandResult:
        """Handle generic commands that don't have specific handlers.
        
        Args:
            command: The command to execute
            start_time: When execution started
            
        Returns:
            CommandResult with execution outcome
        """
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # For now, return a not implemented result
        return CommandResult(
            command_id=command.command_id,
            success=False,
            output="",
            error=f"Command type '{command.intent.intent_type}' is not yet implemented.",
            execution_time_ms=execution_time
        )
    
    def _update_execution_state(
        self,
        command_id: str,
        status: ExecutionStatus,
        start_time: datetime,
        progress_message: str,
        end_time: Optional[datetime] = None,
        result: Optional[CommandResult] = None
    ) -> None:
        """Update the execution state for a command.
        
        Args:
            command_id: The command ID
            status: Current execution status
            start_time: When execution started
            progress_message: Progress message
            end_time: When execution ended (if completed)
            result: Final result (if completed)
        """
        state = ExecutionState(
            command_id=command_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            progress_message=progress_message,
            result=result
        )
        
        self._execution_states[command_id] = state
        
        # Send status update if callback is registered
        self._send_status_update(command_id, progress_message)
    
    def _send_status_update(self, command_id: str, message: str) -> None:
        """Send a status update via the callback if registered.
        
        **Validates: Requirements 4.4**
        
        Args:
            command_id: The command ID
            message: Status message
        """
        if self.status_callback:
            try:
                self.status_callback(command_id, message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def _generate_error_explanation(self, command: Command, error: Exception) -> str:
        """Generate a clear error explanation for the user.
        
        **Validates: Requirements 4.5**
        
        Args:
            command: The command that failed
            error: The exception that occurred
            
        Returns:
            A clear, user-friendly error message
        """
        intent_type = command.intent.intent_type
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Generate context-specific error messages
        if isinstance(error, FileNotFoundError):
            return (
                f"Could not find the requested resource. "
                f"Please check that the file or application exists and try again. "
                f"Details: {error_msg}"
            )
        elif isinstance(error, PermissionError):
            return (
                f"Permission denied. PRIME does not have the necessary permissions "
                f"to perform this action. You may need to run PRIME with elevated "
                f"privileges or check file permissions. Details: {error_msg}"
            )
        elif isinstance(error, subprocess.SubprocessError):
            return (
                f"Failed to execute the command. The system reported an error: {error_msg}. "
                f"Please check that all required programs are installed and accessible."
            )
        else:
            return (
                f"An unexpected error occurred while executing the command: {error_msg}. "
                f"Error type: {error_type}. Please try again or contact support if "
                f"the problem persists."
            )
