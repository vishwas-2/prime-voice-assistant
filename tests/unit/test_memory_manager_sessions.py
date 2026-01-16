"""Unit tests for Memory Manager session persistence.

Tests the save_session and load_session methods to ensure:
- Sessions can be saved and loaded correctly
- Session data is preserved accurately
- Sessions persist across manager instances
- Session files are encrypted on disk
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from prime.persistence import MemoryManager
from prime.models.data_models import (
    Session, CommandRecord, Command, CommandResult,
    Intent, Entity
)


class TestSessionPersistence:
    """Test session storage and retrieval functionality."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_storage_dir):
        """Create a MemoryManager instance with temporary storage."""
        return MemoryManager(storage_dir=temp_storage_dir)

    @pytest.fixture
    def simple_session(self):
        """Create a simple session for testing."""
        return Session(
            session_id="test_session_1",
            user_id="user1",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 30, 0),
            command_history=[],
            context_state={"last_app": "chrome"}
        )

    @pytest.fixture
    def complex_session(self):
        """Create a session with command history for testing."""
        # Create an entity
        entity = Entity(
            entity_type="application",
            value="chrome",
            confidence=0.95
        )
        
        # Create an intent
        intent = Intent(
            intent_type="launch_app",
            entities=[entity],
            confidence=0.95,
            requires_clarification=False
        )
        
        # Create a command
        command = Command(
            command_id="cmd_1",
            intent=intent,
            parameters={"app_name": "chrome"},
            timestamp=datetime(2024, 1, 1, 10, 5, 0),
            requires_confirmation=False
        )
        
        # Create a command result
        result = CommandResult(
            command_id="cmd_1",
            success=True,
            output="Chrome launched successfully",
            error=None,
            execution_time_ms=150
        )
        
        # Create a command record
        record = CommandRecord(
            command=command,
            result=result,
            timestamp=datetime(2024, 1, 1, 10, 5, 0)
        )
        
        # Create session with command history
        return Session(
            session_id="test_session_2",
            user_id="user1",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 30, 0),
            command_history=[record],
            context_state={"last_app": "chrome", "volume": 75}
        )

    def test_save_simple_session(self, manager, simple_session):
        """Test saving a simple session without command history."""
        # Should not raise any exceptions
        manager.save_session(simple_session)
        
        # Verify file was created
        session_file = Path(manager._sessions_dir) / f"{simple_session.session_id}.json"
        assert session_file.exists()

    def test_load_simple_session(self, manager, simple_session):
        """Test loading a simple session."""
        # Save the session
        manager.save_session(simple_session)
        
        # Load the session
        loaded_session = manager.load_session(simple_session.session_id)
        
        # Verify all fields match
        assert loaded_session.session_id == simple_session.session_id
        assert loaded_session.user_id == simple_session.user_id
        assert loaded_session.start_time == simple_session.start_time
        assert loaded_session.end_time == simple_session.end_time
        assert loaded_session.command_history == simple_session.command_history
        assert loaded_session.context_state == simple_session.context_state

    def test_save_and_load_complex_session(self, manager, complex_session):
        """Test saving and loading a session with command history."""
        # Save the session
        manager.save_session(complex_session)
        
        # Load the session
        loaded_session = manager.load_session(complex_session.session_id)
        
        # Verify basic fields
        assert loaded_session.session_id == complex_session.session_id
        assert loaded_session.user_id == complex_session.user_id
        assert loaded_session.start_time == complex_session.start_time
        assert loaded_session.end_time == complex_session.end_time
        assert loaded_session.context_state == complex_session.context_state
        
        # Verify command history
        assert len(loaded_session.command_history) == 1
        
        # Verify command record
        loaded_record = loaded_session.command_history[0]
        original_record = complex_session.command_history[0]
        
        assert loaded_record.timestamp == original_record.timestamp
        
        # Verify command
        assert loaded_record.command.command_id == original_record.command.command_id
        assert loaded_record.command.parameters == original_record.command.parameters
        assert loaded_record.command.timestamp == original_record.command.timestamp
        assert loaded_record.command.requires_confirmation == original_record.command.requires_confirmation
        
        # Verify intent
        assert loaded_record.command.intent.intent_type == original_record.command.intent.intent_type
        assert loaded_record.command.intent.confidence == original_record.command.intent.confidence
        assert loaded_record.command.intent.requires_clarification == original_record.command.intent.requires_clarification
        
        # Verify entities
        assert len(loaded_record.command.intent.entities) == 1
        loaded_entity = loaded_record.command.intent.entities[0]
        original_entity = original_record.command.intent.entities[0]
        assert loaded_entity.entity_type == original_entity.entity_type
        assert loaded_entity.value == original_entity.value
        assert loaded_entity.confidence == original_entity.confidence
        
        # Verify result
        assert loaded_record.result.command_id == original_record.result.command_id
        assert loaded_record.result.success == original_record.result.success
        assert loaded_record.result.output == original_record.result.output
        assert loaded_record.result.error == original_record.result.error
        assert loaded_record.result.execution_time_ms == original_record.result.execution_time_ms

    def test_load_nonexistent_session_raises_error(self, manager):
        """Test that loading a non-existent session raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            manager.load_session("nonexistent_session")

    def test_session_persists_across_manager_instances(self, temp_storage_dir, simple_session):
        """Test that sessions persist when creating a new manager instance."""
        # Create first manager and save session
        manager1 = MemoryManager(storage_dir=temp_storage_dir)
        encryption_key = manager1.encryption_key
        manager1.save_session(simple_session)
        
        # Create second manager with same key and storage dir
        manager2 = MemoryManager(encryption_key=encryption_key, storage_dir=temp_storage_dir)
        loaded_session = manager2.load_session(simple_session.session_id)
        
        # Verify session data matches
        assert loaded_session.session_id == simple_session.session_id
        assert loaded_session.user_id == simple_session.user_id
        assert loaded_session.start_time == simple_session.start_time
        assert loaded_session.end_time == simple_session.end_time

    def test_session_files_are_encrypted(self, manager, simple_session, temp_storage_dir):
        """Test that session files are encrypted on disk."""
        manager.save_session(simple_session)
        
        # Read the raw file content
        session_file = Path(temp_storage_dir) / 'sessions' / f'{simple_session.session_id}.json'
        raw_content = session_file.read_bytes()
        
        # Verify the raw content doesn't contain plaintext data
        assert b"test_session_1" not in raw_content
        assert b"user1" not in raw_content
        assert b"chrome" not in raw_content

    def test_save_session_with_none_end_time(self, manager):
        """Test saving a session with None end_time (active session)."""
        session = Session(
            session_id="active_session",
            user_id="user1",
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        
        manager.save_session(session)
        loaded_session = manager.load_session(session.session_id)
        
        assert loaded_session.end_time is None

    def test_save_session_with_empty_context_state(self, manager):
        """Test saving a session with empty context state."""
        session = Session(
            session_id="empty_context_session",
            user_id="user1",
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        
        manager.save_session(session)
        loaded_session = manager.load_session(session.session_id)
        
        assert loaded_session.context_state == {}

    def test_save_session_with_complex_context_state(self, manager):
        """Test saving a session with complex nested context state."""
        session = Session(
            session_id="complex_context_session",
            user_id="user1",
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={
                "preferences": {
                    "theme": "dark",
                    "volume": 75
                },
                "recent_apps": ["chrome", "vscode", "terminal"],
                "last_command": "launch chrome"
            }
        )
        
        manager.save_session(session)
        loaded_session = manager.load_session(session.session_id)
        
        assert loaded_session.context_state == session.context_state

    def test_save_multiple_sessions(self, manager):
        """Test saving multiple different sessions."""
        sessions = [
            Session(
                session_id=f"session_{i}",
                user_id=f"user{i}",
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={"session_num": i}
            )
            for i in range(5)
        ]
        
        # Save all sessions
        for session in sessions:
            manager.save_session(session)
        
        # Load and verify all sessions
        for session in sessions:
            loaded = manager.load_session(session.session_id)
            assert loaded.session_id == session.session_id
            assert loaded.user_id == session.user_id
            assert loaded.context_state == session.context_state

    def test_update_session(self, manager, simple_session):
        """Test updating an existing session."""
        # Save initial session
        manager.save_session(simple_session)
        
        # Modify the session
        simple_session.end_time = datetime(2024, 1, 1, 11, 0, 0)
        simple_session.context_state["new_key"] = "new_value"
        
        # Save updated session
        manager.save_session(simple_session)
        
        # Load and verify updates
        loaded_session = manager.load_session(simple_session.session_id)
        assert loaded_session.end_time == simple_session.end_time
        assert loaded_session.context_state["new_key"] == "new_value"

    def test_save_session_with_invalid_type_raises_error(self, manager):
        """Test that saving a non-Session object raises TypeError."""
        with pytest.raises(TypeError):
            manager.save_session({"not": "a session"})

    def test_save_session_with_multiple_command_records(self, manager):
        """Test saving a session with multiple command records."""
        # Create multiple command records
        records = []
        for i in range(3):
            entity = Entity(
                entity_type="application",
                value=f"app{i}",
                confidence=0.9
            )
            
            intent = Intent(
                intent_type="launch_app",
                entities=[entity],
                confidence=0.9,
                requires_clarification=False
            )
            
            command = Command(
                command_id=f"cmd_{i}",
                intent=intent,
                parameters={"app_name": f"app{i}"},
                timestamp=datetime(2024, 1, 1, 10, i, 0),
                requires_confirmation=False
            )
            
            result = CommandResult(
                command_id=f"cmd_{i}",
                success=True,
                output=f"App{i} launched",
                error=None,
                execution_time_ms=100 + i * 10
            )
            
            record = CommandRecord(
                command=command,
                result=result,
                timestamp=datetime(2024, 1, 1, 10, i, 0)
            )
            
            records.append(record)
        
        # Create session with multiple records
        session = Session(
            session_id="multi_command_session",
            user_id="user1",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=None,
            command_history=records,
            context_state={}
        )
        
        # Save and load
        manager.save_session(session)
        loaded_session = manager.load_session(session.session_id)
        
        # Verify all command records
        assert len(loaded_session.command_history) == 3
        for i, record in enumerate(loaded_session.command_history):
            assert record.command.command_id == f"cmd_{i}"
            assert record.result.output == f"App{i} launched"
