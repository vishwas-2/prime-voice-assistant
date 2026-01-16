"""
Error handling and user-friendly error messages for PRIME Voice Assistant.

This module provides centralized error handling with helpful error messages
and solution suggestions for common errors.
"""

from typing import Optional, Dict, List
from enum import Enum
import traceback


class ErrorCategory(Enum):
    """Categories of errors that can occur in PRIME."""
    VOICE_INPUT = "voice_input"
    VOICE_OUTPUT = "voice_output"
    COMMAND_EXECUTION = "command_execution"
    FILE_SYSTEM = "file_system"
    PROCESS_MANAGEMENT = "process_management"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class PRIMEError(Exception):
    """Base exception class for PRIME errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        suggestions: Optional[List[str]] = None,
        technical_details: Optional[str] = None
    ):
        """
        Initialize PRIME error.
        
        Args:
            message: User-friendly error message
            category: Category of the error
            suggestions: List of suggested solutions
            technical_details: Technical error details for debugging
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.suggestions = suggestions or []
        self.technical_details = technical_details


class ErrorMessageTemplate:
    """Templates for user-friendly error messages."""
    
    # Voice Input Errors
    MICROPHONE_NOT_FOUND = {
        "message": "No microphone detected",
        "category": ErrorCategory.VOICE_INPUT,
        "suggestions": [
            "Check that your microphone is connected",
            "Grant microphone permissions to your terminal",
            "Test your microphone with: prime --test-microphone",
            "Try restarting PRIME"
        ]
    }
    
    SPEECH_RECOGNITION_FAILED = {
        "message": "Could not understand audio",
        "category": ErrorCategory.VOICE_INPUT,
        "suggestions": [
            "Speak more clearly and at a normal pace",
            "Reduce background noise",
            "Move closer to the microphone",
            "Check microphone volume settings"
        ]
    }
    
    SPEECH_RECOGNITION_TIMEOUT = {
        "message": "Speech recognition took too long",
        "category": ErrorCategory.VOICE_INPUT,
        "suggestions": [
            "Check your internet connection (if using online service)",
            "Try offline mode: prime --offline",
            "Reduce background noise",
            "Speak more clearly"
        ]
    }
    
    # Voice Output Errors
    AUDIO_PLAYBACK_FAILED = {
        "message": "Could not play audio",
        "category": ErrorCategory.VOICE_OUTPUT,
        "suggestions": [
            "Check that speakers/headphones are connected",
            "Verify audio output device is working",
            "Check system volume settings",
            "Try restarting PRIME"
        ]
    }
    
    TTS_ENGINE_FAILED = {
        "message": "Text-to-speech engine failed",
        "category": ErrorCategory.VOICE_OUTPUT,
        "suggestions": [
            "Check TTS engine is installed",
            "Try a different voice profile",
            "Restart PRIME",
            "Check system audio settings"
        ]
    }
    
    # Command Execution Errors
    APPLICATION_NOT_FOUND = {
        "message": "Application not found: {app_name}",
        "category": ErrorCategory.COMMAND_EXECUTION,
        "suggestions": [
            "Check the application name is correct",
            "Verify the application is installed",
            "Try using the full application name",
            "Use absolute path: /path/to/application"
        ]
    }
    
    COMMAND_FAILED = {
        "message": "Command execution failed: {command}",
        "category": ErrorCategory.COMMAND_EXECUTION,
        "suggestions": [
            "Check the command syntax",
            "Verify you have necessary permissions",
            "Try running with elevated privileges if needed",
            "Check system logs for more details"
        ]
    }
    
    # File System Errors
    FILE_NOT_FOUND = {
        "message": "File not found: {file_path}",
        "category": ErrorCategory.FILE_SYSTEM,
        "suggestions": [
            "Check the file path is correct",
            "Verify the file exists",
            "Check file permissions",
            "Try using absolute path"
        ]
    }
    
    PERMISSION_DENIED = {
        "message": "Permission denied: {path}",
        "category": ErrorCategory.PERMISSION,
        "suggestions": [
            "Check file/directory permissions",
            "Run PRIME with appropriate permissions",
            "Verify you own the file/directory",
            "Use sudo if necessary (with caution)"
        ]
    }
    
    DISK_FULL = {
        "message": "Not enough disk space",
        "category": ErrorCategory.FILE_SYSTEM,
        "suggestions": [
            "Free up disk space",
            "Delete unnecessary files",
            "Clear PRIME cache: prime --cleanup",
            "Move files to external storage"
        ]
    }
    
    # Process Management Errors
    PROCESS_NOT_FOUND = {
        "message": "Process not found: {process}",
        "category": ErrorCategory.PROCESS_MANAGEMENT,
        "suggestions": [
            "Check the process name or PID is correct",
            "Verify the process is running",
            "List all processes: prime show processes",
            "Try searching by partial name"
        ]
    }
    
    PROCESS_TERMINATION_FAILED = {
        "message": "Could not terminate process: {process}",
        "category": ErrorCategory.PROCESS_MANAGEMENT,
        "suggestions": [
            "Check you have permission to terminate the process",
            "Try force termination (use with caution)",
            "Verify the process still exists",
            "Check if process is protected by system"
        ]
    }
    
    # Network Errors
    NETWORK_UNAVAILABLE = {
        "message": "Network connection unavailable",
        "category": ErrorCategory.NETWORK,
        "suggestions": [
            "Check your internet connection",
            "Verify WiFi/Ethernet is connected",
            "Try reconnecting to network",
            "Use offline mode if available"
        ]
    }
    
    WIFI_CONNECTION_FAILED = {
        "message": "Could not connect to WiFi: {network}",
        "category": ErrorCategory.NETWORK,
        "suggestions": [
            "Check the network name is correct",
            "Verify the password is correct",
            "Check WiFi is enabled",
            "Move closer to the router"
        ]
    }
    
    # Resource Errors
    MEMORY_LIMIT_EXCEEDED = {
        "message": "Memory limit exceeded",
        "category": ErrorCategory.RESOURCE,
        "suggestions": [
            "Close unnecessary applications",
            "Clear PRIME cache: prime --cleanup",
            "Reduce session retention period",
            "Restart PRIME"
        ]
    }
    
    CPU_LIMIT_EXCEEDED = {
        "message": "CPU usage too high",
        "category": ErrorCategory.RESOURCE,
        "suggestions": [
            "Close resource-intensive applications",
            "Wait for current operations to complete",
            "Reduce automation complexity",
            "Check for runaway processes"
        ]
    }
    
    # Configuration Errors
    CONFIG_FILE_INVALID = {
        "message": "Configuration file is invalid",
        "category": ErrorCategory.CONFIGURATION,
        "suggestions": [
            "Check configuration file syntax",
            "Restore default configuration: prime --reset-config",
            "Verify JSON/YAML format is correct",
            "Check for missing required fields"
        ]
    }
    
    MISSING_DEPENDENCY = {
        "message": "Missing required dependency: {dependency}",
        "category": ErrorCategory.CONFIGURATION,
        "suggestions": [
            "Install missing dependency: pip install {dependency}",
            "Run: pip install -r requirements.txt",
            "Check Python version compatibility",
            "Verify virtual environment is activated"
        ]
    }


class ErrorHandler:
    """
    Centralized error handler for PRIME.
    
    Provides user-friendly error messages with helpful suggestions
    for resolving common issues.
    """
    
    @staticmethod
    def format_error(
        error: Exception,
        context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Format an error into a user-friendly message.
        
        Args:
            error: The exception that occurred
            context: Optional context information (e.g., command, file path)
        
        Returns:
            Dictionary containing:
                - message: User-friendly error message
                - category: Error category
                - suggestions: List of suggested solutions
                - technical_details: Technical error information
        
        **Validates: Requirements 14.1, 14.2**
        """
        context = context or {}
        
        # If it's already a PRIMEError, use its information
        if isinstance(error, PRIMEError):
            return {
                "message": error.message,
                "category": error.category.value,
                "suggestions": error.suggestions,
                "technical_details": error.technical_details or str(error)
            }
        
        # Map common exceptions to templates
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Determine template based on error type and message
        template = ErrorHandler._get_template(error_type, error_message, context)
        
        # Format message with context
        message = template["message"]
        if context:
            try:
                message = message.format(**context)
            except KeyError:
                pass  # Use message as-is if formatting fails
        
        return {
            "message": message,
            "category": template["category"].value,
            "suggestions": template["suggestions"],
            "technical_details": f"{error_type}: {str(error)}"
        }
    
    @staticmethod
    def _get_template(
        error_type: str,
        error_message: str,
        context: Dict
    ) -> Dict:
        """
        Get appropriate error template based on error type and message.
        
        Args:
            error_type: Type of exception
            error_message: Error message (lowercase)
            context: Context information
        
        Returns:
            Error template dictionary
        """
        # Microphone/audio input errors
        if "microphone" in error_message or "audio source" in error_message:
            return ErrorMessageTemplate.MICROPHONE_NOT_FOUND
        
        if "could not understand" in error_message or "unknown value" in error_message:
            return ErrorMessageTemplate.SPEECH_RECOGNITION_FAILED
        
        if "timeout" in error_message and "speech" in error_message:
            return ErrorMessageTemplate.SPEECH_RECOGNITION_TIMEOUT
        
        # File system errors
        if error_type == "FileNotFoundError" or "no such file" in error_message:
            return ErrorMessageTemplate.FILE_NOT_FOUND
        
        if error_type == "PermissionError" or "permission denied" in error_message:
            return ErrorMessageTemplate.PERMISSION_DENIED
        
        if "disk" in error_message and "full" in error_message:
            return ErrorMessageTemplate.DISK_FULL
        
        # Process errors
        if "process" in error_message and "not found" in error_message:
            return ErrorMessageTemplate.PROCESS_NOT_FOUND
        
        # Network errors
        if "network" in error_message or "connection" in error_message:
            return ErrorMessageTemplate.NETWORK_UNAVAILABLE
        
        # Resource errors
        if "memory" in error_message and "limit" in error_message:
            return ErrorMessageTemplate.MEMORY_LIMIT_EXCEEDED
        
        if "cpu" in error_message and "limit" in error_message:
            return ErrorMessageTemplate.CPU_LIMIT_EXCEEDED
        
        # Configuration errors
        if "dependency" in error_message or "module" in error_message:
            return ErrorMessageTemplate.MISSING_DEPENDENCY
        
        # Default template
        return {
            "message": f"An error occurred: {error_message}",
            "category": ErrorCategory.UNKNOWN,
            "suggestions": [
                "Check the error details below",
                "Try the operation again",
                "Check PRIME logs: ~/.prime/logs/prime.log",
                "Report this issue if it persists"
            ]
        }
    
    @staticmethod
    def create_error(
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        suggestions: Optional[List[str]] = None,
        technical_details: Optional[str] = None
    ) -> PRIMEError:
        """
        Create a PRIME error with user-friendly message.
        
        Args:
            message: User-friendly error message
            category: Error category
            suggestions: List of suggested solutions
            technical_details: Technical error details
        
        Returns:
            PRIMEError instance
        """
        return PRIMEError(
            message=message,
            category=category,
            suggestions=suggestions,
            technical_details=technical_details
        )
    
    @staticmethod
    def print_error(error_info: Dict) -> None:
        """
        Print formatted error message to console.
        
        Args:
            error_info: Error information dictionary from format_error()
        """
        print("\n" + "=" * 60)
        print(f"ERROR: {error_info['message']}")
        print("=" * 60)
        
        if error_info.get('suggestions'):
            print("\nSuggested Solutions:")
            for i, suggestion in enumerate(error_info['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
        if error_info.get('technical_details'):
            print(f"\nTechnical Details: {error_info['technical_details']}")
        
        print("=" * 60 + "\n")


def handle_error(
    error: Exception,
    context: Optional[Dict] = None,
    print_to_console: bool = True
) -> Dict[str, any]:
    """
    Handle an error with user-friendly messaging.
    
    Args:
        error: The exception that occurred
        context: Optional context information
        print_to_console: Whether to print error to console
    
    Returns:
        Formatted error information
    
    **Validates: Requirements 14.1, 14.2, 14.3**
    """
    handler = ErrorHandler()
    error_info = handler.format_error(error, context)
    
    if print_to_console:
        handler.print_error(error_info)
    
    return error_info
