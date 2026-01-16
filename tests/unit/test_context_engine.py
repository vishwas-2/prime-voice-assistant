"""Unit tests for Context Engine.

This module tests the core functionality of the Context Engine including:
- Command processing with context
- Reference resolution
- History management
- Suggestion generation
- Learning from corrections
- Pattern detection
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from prime.nlp import IntentParser, ContextEngine, Suggestion, Pattern
from prime.persistence import MemoryManager
from prime.models import (
    Session, Command, CommandResult, Intent, Entity,
    CommandRecord
)


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def memory_manager(temp_storage):
    """Create a MemoryManager instance for tests."""
    return MemoryManager(storage_dir=temp_storage)


@pytest.fixture
def intent_parser():
    """Create an IntentParser instance for tests."""
    return IntentParser()


@pytest.fixture
def context_engine(intent_parser, memory_manager):
    """Create a ContextEngine instance for tests."""
    return ContextEngine(intent_parser, memory_manager)


@pytest.fixture
def sample_session():
    """Create a sample session for tests."""
    return Session(
        session_id="test-session-001",
        user_id="test-user",
        start_time=datetime.now(),
        end_time=None,
        command_history=[],
        context_state={}
    )


class TestProcessCommand:
    """Tests for process_command method."""
    
    def test_process_simple_command(self, context_engine, sample_session):
        """Test processing a simple command without context."""
        text = "open Chrome"
        intent = context_engine.process_command(text, sample_session)
        
        assert intent.intent_type == "launch_app"
        assert len(intent.entities) > 0
        assert any(e.entity_type == "application" for e in intent.entities)
    
    def test_process_command_with_history(self, context_engine, sample_session):
        """Test that command processing considers session history."""
        # Add some history
        past_intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "Chrome", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        past_command = Command(
            command_id="cmd-001",
            intent=past_intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        past_result = CommandResult(
            command_id="cmd-001",
            success=True,
            output="Chrome launched",
            error=None,
            execution_time_ms=100
        )
        
        sample_session.command_history.append(
            CommandRecord(past_command, past_result, datetime.now())
        )
        
        # Process a similar command
        text = "open Firefox"
        intent = context_engine.process_command(text, sample_session)
        
        assert intent.intent_type == "launch_app"
        # Confidence should be boosted due to recent similar command
        assert intent.confidence >= 0.6
    
    def test_process_command_with_correction(
        self, context_engine, sample_session
    ):
        """Test that learned corrections are applied."""
        # Teach a correction
        context_engine.learn_from_correction(
            "opn Chrome", "open Chrome", sample_session
        )
        
        # Process the misspelled command
        text = "opn Chrome"
        intent = context_engine.process_command(text, sample_session)
        
        # Should be corrected and parsed correctly
        assert intent.intent_type == "launch_app"


class TestResolveReference:
    """Tests for resolve_reference method."""
    
    def test_resolve_it_reference(self, context_engine, sample_session):
        """Test resolving 'it' reference."""
        # Add a command with an entity to history
        past_intent = Intent(
            intent_type="search_files",
            entities=[Entity("file_name", "document.txt", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        past_command = Command(
            command_id="cmd-001",
            intent=past_intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        past_result = CommandResult(
            command_id="cmd-001",
            success=True,
            output="/home/user/document.txt",
            error=None,
            execution_time_ms=50
        )
        
        sample_session.command_history.append(
            CommandRecord(past_command, past_result, datetime.now())
        )
        
        # Resolve "it"
        entity = context_engine.resolve_reference("it", sample_session)
        
        assert entity is not None
        assert entity.value in ["document.txt", "/home/user/document.txt"]
    
    def test_resolve_that_reference(self, context_engine, sample_session):
        """Test resolving 'that' reference."""
        # Add a command with an application entity
        past_intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "Firefox", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        past_command = Command(
            command_id="cmd-001",
            intent=past_intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        past_result = CommandResult(
            command_id="cmd-001",
            success=True,
            output="Firefox launched",
            error=None,
            execution_time_ms=100
        )
        
        sample_session.command_history.append(
            CommandRecord(past_command, past_result, datetime.now())
        )
        
        # Resolve "that"
        entity = context_engine.resolve_reference("that", sample_session)
        
        assert entity is not None
        assert "Firefox" in str(entity.value)
    
    def test_resolve_previous_one_reference(
        self, context_engine, sample_session
    ):
        """Test resolving 'the previous one' reference."""
        # Add multiple commands
        for i in range(3):
            intent = Intent(
                intent_type="search_files",
                entities=[Entity("file_name", f"file{i}.txt", 0.9)],
                confidence=0.9,
                requires_clarification=False
            )
            command = Command(
                command_id=f"cmd-{i:03d}",
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            result = CommandResult(
                command_id=f"cmd-{i:03d}",
                success=True,
                output=f"/home/user/file{i}.txt",
                error=None,
                execution_time_ms=50
            )
            
            sample_session.command_history.append(
                CommandRecord(command, result, datetime.now())
            )
        
        # Resolve "the previous one"
        entity = context_engine.resolve_reference(
            "the previous one", sample_session
        )
        
        assert entity is not None
        # Should resolve to the most recent file
        assert "file2.txt" in str(entity.value) or "/home/user/file2.txt" in str(entity.value)
    
    def test_resolve_reference_no_history(
        self, context_engine, sample_session
    ):
        """Test resolving reference with no history."""
        entity = context_engine.resolve_reference("it", sample_session)
        
        assert entity is None
    
    def test_resolve_non_reference(self, context_engine, sample_session):
        """Test that non-references return None."""
        entity = context_engine.resolve_reference("Chrome", sample_session)
        
        assert entity is None


class TestAddToHistory:
    """Tests for add_to_history method."""
    
    def test_add_command_to_history(
        self, context_engine, sample_session, memory_manager
    ):
        """Test adding a command to history."""
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity("application", "Chrome", 0.9)],
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
        result = CommandResult(
            command_id="cmd-001",
            success=True,
            output="Chrome launched",
            error=None,
            execution_time_ms=100
        )
        
        # Add to history
        context_engine.add_to_history(command, result, sample_session)
        
        # Verify it was added
        assert len(sample_session.command_history) == 1
        assert sample_session.command_history[0].command.command_id == "cmd-001"
    
    def test_add_multiple_commands(
        self, context_engine, sample_session
    ):
        """Test adding multiple commands to history."""
        for i in range(5):
            intent = Intent(
                intent_type="launch_app",
                entities=[Entity("application", f"App{i}", 0.9)],
                confidence=0.9,
                requires_clarification=False
            )
            command = Command(
                command_id=f"cmd-{i:03d}",
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            result = CommandResult(
                command_id=f"cmd-{i:03d}",
                success=True,
                output=f"App{i} launched",
                error=None,
                execution_time_ms=100
            )
            
            context_engine.add_to_history(command, result, sample_session)
        
        assert len(sample_session.command_history) == 5


class TestGetSuggestions:
    """Tests for get_suggestions method."""
    
    def test_get_suggestions_empty_history(
        self, context_engine, sample_session
    ):
        """Test getting suggestions with empty history."""
        suggestions = context_engine.get_suggestions(sample_session)
        
        # Should return a list (may be empty)
        assert isinstance(suggestions, list)
    
    def test_get_suggestions_with_pattern(
        self, context_engine, sample_session
    ):
        """Test getting suggestions when a pattern is detected."""
        # Add repetitive commands
        for _ in range(4):
            for intent_type in ["launch_app", "adjust_volume"]:
                intent = Intent(
                    intent_type=intent_type,
                    entities=[],
                    confidence=0.9,
                    requires_clarification=False
                )
                command = Command(
                    command_id=f"cmd-{datetime.now().timestamp()}",
                    intent=intent,
                    parameters={},
                    timestamp=datetime.now(),
                    requires_confirmation=False
                )
                result = CommandResult(
                    command_id=command.command_id,
                    success=True,
                    output="Success",
                    error=None,
                    execution_time_ms=100
                )
                
                context_engine.add_to_history(command, result, sample_session)
        
        suggestions = context_engine.get_suggestions(sample_session)
        
        # Should suggest automation
        assert len(suggestions) > 0
        assert any(s.suggestion_type == "automation" for s in suggestions)
    
    def test_get_suggestions_after_error(
        self, context_engine, sample_session
    ):
        """Test getting suggestions after a failed command."""
        intent = Intent(
            intent_type="search_files",
            entities=[],
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
        result = CommandResult(
            command_id="cmd-001",
            success=False,
            output="",
            error="File not found",
            execution_time_ms=50
        )
        
        context_engine.add_to_history(command, result, sample_session)
        
        suggestions = context_engine.get_suggestions(sample_session)
        
        # Should suggest alternatives
        assert len(suggestions) > 0
        assert any(s.suggestion_type == "alternative" for s in suggestions)


class TestLearnFromCorrection:
    """Tests for learn_from_correction method."""
    
    def test_learn_simple_correction(
        self, context_engine, sample_session
    ):
        """Test learning from a simple correction."""
        original = "opn Chrome"
        corrected = "open Chrome"
        
        context_engine.learn_from_correction(
            original, corrected, sample_session
        )
        
        # Verify correction was stored
        assert sample_session.user_id in context_engine._corrections
        assert len(context_engine._corrections[sample_session.user_id]) == 1
    
    def test_learn_multiple_corrections(
        self, context_engine, sample_session
    ):
        """Test learning from multiple corrections."""
        corrections = [
            ("opn", "open"),
            ("clos", "close"),
            ("serch", "search")
        ]
        
        for original, corrected in corrections:
            context_engine.learn_from_correction(
                original, corrected, sample_session
            )
        
        assert len(context_engine._corrections[sample_session.user_id]) == 3
    
    def test_correction_persistence(
        self, context_engine, sample_session, memory_manager
    ):
        """Test that corrections are persisted."""
        original = "opn Chrome"
        corrected = "open Chrome"
        
        context_engine.learn_from_correction(
            original, corrected, sample_session
        )
        
        # Verify it was saved to memory manager
        stored = memory_manager.get_preference(
            "command_corrections", sample_session.user_id
        )
        
        assert stored is not None
        assert len(stored) == 1


class TestDetectRepetitivePattern:
    """Tests for detect_repetitive_pattern method."""
    
    def test_detect_no_pattern_insufficient_data(
        self, context_engine, sample_session
    ):
        """Test that no pattern is detected with insufficient data."""
        # Add only 3 commands
        for i in range(3):
            intent = Intent(
                intent_type="launch_app",
                entities=[],
                confidence=0.9,
                requires_clarification=False
            )
            command = Command(
                command_id=f"cmd-{i:03d}",
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            result = CommandResult(
                command_id=f"cmd-{i:03d}",
                success=True,
                output="Success",
                error=None,
                execution_time_ms=100
            )
            
            context_engine.add_to_history(command, result, sample_session)
        
        pattern = context_engine.detect_repetitive_pattern(sample_session)
        
        assert pattern is None
    
    def test_detect_simple_pattern(
        self, context_engine, sample_session
    ):
        """Test detecting a simple repetitive pattern."""
        # Add a repeating sequence: launch_app, adjust_volume
        for _ in range(4):
            for intent_type in ["launch_app", "adjust_volume"]:
                intent = Intent(
                    intent_type=intent_type,
                    entities=[],
                    confidence=0.9,
                    requires_clarification=False
                )
                command = Command(
                    command_id=f"cmd-{datetime.now().timestamp()}",
                    intent=intent,
                    parameters={},
                    timestamp=datetime.now(),
                    requires_confirmation=False
                )
                result = CommandResult(
                    command_id=command.command_id,
                    success=True,
                    output="Success",
                    error=None,
                    execution_time_ms=100
                )
                
                context_engine.add_to_history(command, result, sample_session)
        
        pattern = context_engine.detect_repetitive_pattern(sample_session)
        
        assert pattern is not None
        assert pattern.pattern_type == "command_sequence"
        assert pattern.frequency >= 3
        assert len(pattern.commands) >= 2
    
    def test_detect_no_pattern_random_commands(
        self, context_engine, sample_session
    ):
        """Test that no pattern is detected with random commands."""
        intent_types = [
            "launch_app", "adjust_volume", "search_files",
            "create_file", "delete_file", "shutdown_system"
        ]
        
        # Add random commands
        for i, intent_type in enumerate(intent_types):
            intent = Intent(
                intent_type=intent_type,
                entities=[],
                confidence=0.9,
                requires_clarification=False
            )
            command = Command(
                command_id=f"cmd-{i:03d}",
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            result = CommandResult(
                command_id=f"cmd-{i:03d}",
                success=True,
                output="Success",
                error=None,
                execution_time_ms=100
            )
            
            context_engine.add_to_history(command, result, sample_session)
        
        pattern = context_engine.detect_repetitive_pattern(sample_session)
        
        # Should not detect a pattern with random commands
        assert pattern is None


class TestContextIntegration:
    """Integration tests for Context Engine."""
    
    def test_full_workflow(
        self, context_engine, sample_session
    ):
        """Test a complete workflow with context."""
        # 1. Process a command
        text1 = "open Chrome"
        intent1 = context_engine.process_command(text1, sample_session)
        
        command1 = Command(
            command_id="cmd-001",
            intent=intent1,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        result1 = CommandResult(
            command_id="cmd-001",
            success=True,
            output="Chrome launched",
            error=None,
            execution_time_ms=100
        )
        
        # 2. Add to history
        context_engine.add_to_history(command1, result1, sample_session)
        
        # 3. Process a command with reference
        text2 = "close it"
        intent2 = context_engine.process_command(text2, sample_session)
        
        # Should resolve "it" to Chrome
        assert intent2 is not None
        
        # 4. Get suggestions
        suggestions = context_engine.get_suggestions(sample_session)
        assert isinstance(suggestions, list)
    
    def test_reference_resolution_in_command(
        self, context_engine, sample_session
    ):
        """Test that references are resolved during command processing."""
        # Add a file search to history
        intent1 = Intent(
            intent_type="search_files",
            entities=[Entity("file_name", "document.txt", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command1 = Command(
            command_id="cmd-001",
            intent=intent1,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        result1 = CommandResult(
            command_id="cmd-001",
            success=True,
            output="/home/user/document.txt",
            error=None,
            execution_time_ms=50
        )
        
        context_engine.add_to_history(command1, result1, sample_session)
        
        # Process a command that references "it"
        text2 = "delete it"
        intent2 = context_engine.process_command(text2, sample_session)
        
        # Should be parsed as delete command
        assert intent2.intent_type == "delete_file"
