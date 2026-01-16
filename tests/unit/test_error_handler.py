"""
Unit tests for Error Handler.

Tests error formatting, message templates, and solution suggestions.
"""

import pytest
from prime.utils.error_handler import (
    ErrorHandler,
    ErrorCategory,
    PRIMEError,
    ErrorMessageTemplate,
    handle_error
)


class TestPRIMEError:
    """Test PRIMEError exception class."""
    
    def test_prime_error_creation(self):
        """Test creating PRIMEError."""
        error = PRIMEError(
            message="Test error",
            category=ErrorCategory.VOICE_INPUT,
            suggestions=["Try this", "Or that"],
            technical_details="Technical info"
        )
        
        assert error.message == "Test error"
        assert error.category == ErrorCategory.VOICE_INPUT
        assert len(error.suggestions) == 2
        assert error.technical_details == "Technical info"
    
    def test_prime_error_defaults(self):
        """Test PRIMEError with default values."""
        error = PRIMEError("Simple error")
        
        assert error.message == "Simple error"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.suggestions == []
        assert error.technical_details is None


class TestErrorMessageTemplates:
    """Test error message templates."""
    
    def test_microphone_not_found_template(self):
        """Test microphone not found template."""
        template = ErrorMessageTemplate.MICROPHONE_NOT_FOUND
        
        assert "microphone" in template["message"].lower()
        assert template["category"] == ErrorCategory.VOICE_INPUT
        assert len(template["suggestions"]) > 0
    
    def test_file_not_found_template(self):
        """Test file not found template."""
        template = ErrorMessageTemplate.FILE_NOT_FOUND
        
        assert "file not found" in template["message"].lower()
        assert template["category"] == ErrorCategory.FILE_SYSTEM
        assert len(template["suggestions"]) > 0
    
    def test_permission_denied_template(self):
        """Test permission denied template."""
        template = ErrorMessageTemplate.PERMISSION_DENIED
        
        assert "permission" in template["message"].lower()
        assert template["category"] == ErrorCategory.PERMISSION
        assert len(template["suggestions"]) > 0


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_format_prime_error(self):
        """Test formatting PRIMEError."""
        error = PRIMEError(
            message="Test error",
            category=ErrorCategory.VOICE_INPUT,
            suggestions=["Solution 1"],
            technical_details="Details"
        )
        
        result = ErrorHandler.format_error(error)
        
        assert result["message"] == "Test error"
        assert result["category"] == "voice_input"
        assert result["suggestions"] == ["Solution 1"]
        assert result["technical_details"] == "Details"
    
    def test_format_file_not_found_error(self):
        """Test formatting FileNotFoundError."""
        error = FileNotFoundError("test.txt not found")
        context = {"file_path": "test.txt"}
        
        result = ErrorHandler.format_error(error, context)
        
        assert "file not found" in result["message"].lower()
        assert result["category"] == "file_system"
        assert len(result["suggestions"]) > 0
        assert "FileNotFoundError" in result["technical_details"]
    
    def test_format_permission_error(self):
        """Test formatting PermissionError."""
        error = PermissionError("Permission denied")
        
        result = ErrorHandler.format_error(error)
        
        assert "permission" in result["message"].lower()
        assert result["category"] == "permission"
        assert len(result["suggestions"]) > 0
    
    def test_format_with_context(self):
        """Test formatting error with context."""
        error = FileNotFoundError("File not found")
        context = {"file_path": "/path/to/file.txt"}
        
        result = ErrorHandler.format_error(error, context)
        
        assert result["message"] is not None
        assert len(result["suggestions"]) > 0
    
    def test_format_unknown_error(self):
        """Test formatting unknown error type."""
        error = ValueError("Some random error")
        
        result = ErrorHandler.format_error(error)
        
        assert result["message"] is not None
        assert result["category"] == "unknown"
        assert len(result["suggestions"]) > 0
    
    def test_create_error(self):
        """Test creating error with ErrorHandler."""
        error = ErrorHandler.create_error(
            message="Custom error",
            category=ErrorCategory.COMMAND_EXECUTION,
            suggestions=["Fix it"],
            technical_details="Tech info"
        )
        
        assert isinstance(error, PRIMEError)
        assert error.message == "Custom error"
        assert error.category == ErrorCategory.COMMAND_EXECUTION


class TestErrorTemplateMatching:
    """Test error template matching logic."""
    
    def test_microphone_error_matching(self):
        """Test matching microphone errors."""
        error = RuntimeError("No microphone detected")
        
        result = ErrorHandler.format_error(error)
        
        assert "microphone" in result["message"].lower()
        assert result["category"] == "voice_input"
    
    def test_speech_recognition_error_matching(self):
        """Test matching speech recognition errors."""
        error = RuntimeError("Could not understand audio")
        
        result = ErrorHandler.format_error(error)
        
        assert "understand" in result["message"].lower()
        assert result["category"] == "voice_input"
    
    def test_timeout_error_matching(self):
        """Test matching timeout errors."""
        error = RuntimeError("Speech recognition timeout exceeded")
        
        result = ErrorHandler.format_error(error)
        
        assert "timeout" in result["message"].lower() or "took too long" in result["message"].lower()
    
    def test_network_error_matching(self):
        """Test matching network errors."""
        error = ConnectionError("Network connection unavailable")
        
        result = ErrorHandler.format_error(error)
        
        assert "network" in result["message"].lower() or "connection" in result["message"].lower()
    
    def test_memory_error_matching(self):
        """Test matching memory errors."""
        error = MemoryError("Memory limit exceeded")
        
        result = ErrorHandler.format_error(error)
        
        assert "memory" in result["message"].lower()


class TestSuggestions:
    """Test error suggestions."""
    
    def test_suggestions_not_empty(self):
        """Test that all templates have suggestions."""
        templates = [
            ErrorMessageTemplate.MICROPHONE_NOT_FOUND,
            ErrorMessageTemplate.FILE_NOT_FOUND,
            ErrorMessageTemplate.PERMISSION_DENIED,
            ErrorMessageTemplate.APPLICATION_NOT_FOUND,
            ErrorMessageTemplate.NETWORK_UNAVAILABLE
        ]
        
        for template in templates:
            assert len(template["suggestions"]) > 0
    
    def test_suggestions_are_helpful(self):
        """Test that suggestions are actionable."""
        error = FileNotFoundError("test.txt")
        
        result = ErrorHandler.format_error(error)
        
        # Suggestions should be strings
        assert all(isinstance(s, str) for s in result["suggestions"])
        
        # Suggestions should not be empty
        assert all(len(s) > 0 for s in result["suggestions"])
    
    def test_multiple_suggestions(self):
        """Test that errors have multiple suggestions."""
        error = PermissionError("Access denied")
        
        result = ErrorHandler.format_error(error)
        
        # Should have at least 2 suggestions
        assert len(result["suggestions"]) >= 2


class TestHandleError:
    """Test handle_error convenience function."""
    
    def test_handle_error_basic(self):
        """Test basic error handling."""
        error = ValueError("Test error")
        
        result = handle_error(error, print_to_console=False)
        
        assert "message" in result
        assert "category" in result
        assert "suggestions" in result
        assert "technical_details" in result
    
    def test_handle_error_with_context(self):
        """Test error handling with context."""
        error = FileNotFoundError("File not found")
        context = {"file_path": "test.txt"}
        
        result = handle_error(error, context, print_to_console=False)
        
        assert result["message"] is not None
        assert len(result["suggestions"]) > 0
    
    def test_handle_error_print_to_console(self, capsys):
        """Test error printing to console."""
        error = ValueError("Test error")
        
        handle_error(error, print_to_console=True)
        
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Test error" in captured.out or "error occurred" in captured.out.lower()


class TestErrorCategories:
    """Test error categorization."""
    
    def test_voice_input_category(self):
        """Test voice input errors are categorized correctly."""
        error = RuntimeError("Microphone not found")
        
        result = ErrorHandler.format_error(error)
        
        assert result["category"] == "voice_input"
    
    def test_file_system_category(self):
        """Test file system errors are categorized correctly."""
        error = FileNotFoundError("File not found")
        
        result = ErrorHandler.format_error(error)
        
        assert result["category"] == "file_system"
    
    def test_permission_category(self):
        """Test permission errors are categorized correctly."""
        error = PermissionError("Permission denied")
        
        result = ErrorHandler.format_error(error)
        
        assert result["category"] == "permission"
    
    def test_unknown_category(self):
        """Test unknown errors get unknown category."""
        error = Exception("Random error")
        
        result = ErrorHandler.format_error(error)
        
        assert result["category"] == "unknown"


class TestTechnicalDetails:
    """Test technical details in error messages."""
    
    def test_technical_details_included(self):
        """Test that technical details are included."""
        error = ValueError("Test error")
        
        result = ErrorHandler.format_error(error)
        
        assert result["technical_details"] is not None
        assert "ValueError" in result["technical_details"]
    
    def test_technical_details_for_prime_error(self):
        """Test technical details for PRIMEError."""
        error = PRIMEError(
            message="User message",
            technical_details="Technical info"
        )
        
        result = ErrorHandler.format_error(error)
        
        assert result["technical_details"] == "Technical info"


class TestErrorFormatting:
    """Test error message formatting."""
    
    def test_message_formatting_with_placeholders(self):
        """Test message formatting with context placeholders."""
        # This tests the internal formatting logic
        template = ErrorMessageTemplate.APPLICATION_NOT_FOUND
        context = {"app_name": "Firefox"}
        
        message = template["message"].format(**context)
        
        assert "Firefox" in message
    
    def test_message_without_context(self):
        """Test message formatting without context."""
        error = FileNotFoundError("File not found")
        
        result = ErrorHandler.format_error(error)
        
        # Should still have a valid message
        assert result["message"] is not None
        assert len(result["message"]) > 0


class TestPrintError:
    """Test error printing functionality."""
    
    def test_print_error_format(self, capsys):
        """Test error printing format."""
        error_info = {
            "message": "Test error message",
            "category": "test",
            "suggestions": ["Solution 1", "Solution 2"],
            "technical_details": "Technical info"
        }
        
        ErrorHandler.print_error(error_info)
        
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Test error message" in captured.out
        assert "Solution 1" in captured.out
        assert "Solution 2" in captured.out
        assert "Technical info" in captured.out
    
    def test_print_error_without_suggestions(self, capsys):
        """Test printing error without suggestions."""
        error_info = {
            "message": "Simple error",
            "category": "test",
            "suggestions": [],
            "technical_details": None
        }
        
        ErrorHandler.print_error(error_info)
        
        captured = capsys.readouterr()
        assert "Simple error" in captured.out
