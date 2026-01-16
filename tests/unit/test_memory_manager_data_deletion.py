"""Unit tests for Memory Manager data deletion.

Tests the delete_user_data method to ensure:
- All user data is properly deleted
- Preferences are deleted
- Sessions are deleted
- Notes are deleted
- Reminders are deleted
- Usage patterns are deleted
- Other users' data is not affected
- Deletion works even when some data types don't exist
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from prime.persistence import MemoryManager
from prime.models.data_models import (
    Session, Note, Reminder, CommandRecord, Command, CommandResult,
    Intent, Entity
)


class TestDataDeletion:
    """Test data deletion functionality."""

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

    def test_delete_user_preferences(self, manager, temp_storage_dir):
        """Test that user preferences are deleted."""
        user_id = "user1"
        
        # Store some preferences
        manager.store_preference("theme", "dark", user_id)
        manager.store_preference("volume", 75, user_id)
        
        # Verify preferences exist
        assert manager.get_preference("theme", user_id) == "dark"
        assert manager.get_preference("volume", user_id) == 75
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify preferences are deleted
        assert manager.get_preference("theme", user_id) is None
        assert manager.get_preference("volume", user_id) is None

    def test_delete_user_notes(self, manager, temp_storage_dir):
        """Test that user notes are deleted."""
        user_id = "user1"
        
        # Create and store notes
        note1 = Note(
            note_id="note1",
            content="Test note 1",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        note2 = Note(
            note_id="note2",
            content="Test note 2",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        manager.store_note(note1, user_id)
        manager.store_note(note2, user_id)
        
        # Verify notes exist
        notes = manager.search_notes("Test", user_id)
        assert len(notes) == 2
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify notes are deleted
        notes = manager.search_notes("Test", user_id)
        assert len(notes) == 0

    def test_delete_user_reminders(self, manager, temp_storage_dir):
        """Test that user reminders are deleted."""
        user_id = "user1"
        
        # Create and store reminders
        reminder1 = Reminder(
            reminder_id="reminder1",
            content="Test reminder 1",
            due_time=datetime.now() - timedelta(hours=1),
            is_completed=False
        )
        reminder2 = Reminder(
            reminder_id="reminder2",
            content="Test reminder 2",
            due_time=datetime.now() - timedelta(hours=2),
            is_completed=False
        )
        
        manager.create_reminder(reminder1, user_id)
        manager.create_reminder(reminder2, user_id)
        
        # Verify reminders exist
        reminders = manager.get_due_reminders(user_id)
        assert len(reminders) == 2
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify reminders are deleted
        reminders = manager.get_due_reminders(user_id)
        assert len(reminders) == 0

    def test_delete_user_sessions(self, manager, temp_storage_dir):
        """Test that user sessions are deleted."""
        user_id = "user1"
        
        # Create and store sessions
        session1 = Session(
            session_id="session1",
            user_id=user_id,
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        session2 = Session(
            session_id="session2",
            user_id=user_id,
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        
        manager.save_session(session1)
        manager.save_session(session2)
        
        # Verify sessions exist
        loaded_session1 = manager.load_session("session1")
        loaded_session2 = manager.load_session("session2")
        assert loaded_session1.user_id == user_id
        assert loaded_session2.user_id == user_id
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify sessions are deleted
        with pytest.raises(FileNotFoundError):
            manager.load_session("session1")
        with pytest.raises(FileNotFoundError):
            manager.load_session("session2")

    def test_delete_user_usage_patterns(self, manager, temp_storage_dir):
        """Test that user usage patterns are deleted."""
        user_id = "user1"
        
        # Record application usage
        manager.record_application_usage("chrome", user_id)
        manager.record_application_usage("vscode", user_id)
        manager.record_application_usage("chrome", user_id)
        
        # Verify usage patterns exist
        usage = manager.get_application_usage("chrome", user_id)
        assert usage is not None
        assert usage.launch_count == 2
        
        all_usage = manager.get_all_application_usage(user_id)
        assert len(all_usage) == 2
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify usage patterns are deleted
        usage = manager.get_application_usage("chrome", user_id)
        assert usage is None
        
        all_usage = manager.get_all_application_usage(user_id)
        assert len(all_usage) == 0

    def test_delete_all_user_data_types(self, manager, temp_storage_dir):
        """Test deleting all data types for a user at once."""
        user_id = "user1"
        
        # Store all types of data
        # 1. Preferences
        manager.store_preference("theme", "dark", user_id)
        
        # 2. Notes
        note = Note(
            note_id="note1",
            content="Test note",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        manager.store_note(note, user_id)
        
        # 3. Reminders
        reminder = Reminder(
            reminder_id="reminder1",
            content="Test reminder",
            due_time=datetime.now() - timedelta(hours=1),
            is_completed=False
        )
        manager.create_reminder(reminder, user_id)
        
        # 4. Sessions
        session = Session(
            session_id="session1",
            user_id=user_id,
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        manager.save_session(session)
        
        # 5. Usage patterns
        manager.record_application_usage("chrome", user_id)
        
        # Verify all data exists
        assert manager.get_preference("theme", user_id) == "dark"
        assert len(manager.search_notes("Test", user_id)) == 1
        assert len(manager.get_due_reminders(user_id)) == 1
        assert manager.load_session("session1").user_id == user_id
        assert manager.get_application_usage("chrome", user_id) is not None
        
        # Delete all user data
        manager.delete_user_data(user_id)
        
        # Verify all data is deleted
        assert manager.get_preference("theme", user_id) is None
        assert len(manager.search_notes("Test", user_id)) == 0
        assert len(manager.get_due_reminders(user_id)) == 0
        with pytest.raises(FileNotFoundError):
            manager.load_session("session1")
        assert manager.get_application_usage("chrome", user_id) is None

    def test_delete_user_data_does_not_affect_other_users(self, manager, temp_storage_dir):
        """Test that deleting one user's data doesn't affect other users."""
        user1_id = "user1"
        user2_id = "user2"
        
        # Store data for both users
        # Preferences
        manager.store_preference("theme", "dark", user1_id)
        manager.store_preference("theme", "light", user2_id)
        
        # Notes
        note1 = Note(
            note_id="note1",
            content="User 1 note",
            tags=["user1"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        note2 = Note(
            note_id="note2",
            content="User 2 note",
            tags=["user2"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        manager.store_note(note1, user1_id)
        manager.store_note(note2, user2_id)
        
        # Sessions
        session1 = Session(
            session_id="session1",
            user_id=user1_id,
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        session2 = Session(
            session_id="session2",
            user_id=user2_id,
            start_time=datetime.now(),
            end_time=None,
            command_history=[],
            context_state={}
        )
        manager.save_session(session1)
        manager.save_session(session2)
        
        # Usage patterns
        manager.record_application_usage("chrome", user1_id)
        manager.record_application_usage("firefox", user2_id)
        
        # Delete user1's data
        manager.delete_user_data(user1_id)
        
        # Verify user1's data is deleted
        assert manager.get_preference("theme", user1_id) is None
        assert len(manager.search_notes("User 1", user1_id)) == 0
        with pytest.raises(FileNotFoundError):
            manager.load_session("session1")
        assert manager.get_application_usage("chrome", user1_id) is None
        
        # Verify user2's data still exists
        assert manager.get_preference("theme", user2_id) == "light"
        assert len(manager.search_notes("User 2", user2_id)) == 1
        assert manager.load_session("session2").user_id == user2_id
        assert manager.get_application_usage("firefox", user2_id) is not None

    def test_delete_user_data_when_no_data_exists(self, manager, temp_storage_dir):
        """Test deleting data for a user that has no data."""
        user_id = "nonexistent_user"
        
        # This should not raise an error
        manager.delete_user_data(user_id)
        
        # Verify no data exists (should return None/empty)
        assert manager.get_preference("any_key", user_id) is None
        assert len(manager.search_notes("any", user_id)) == 0
        assert len(manager.get_due_reminders(user_id)) == 0
        assert manager.get_application_usage("any_app", user_id) is None

    def test_delete_user_data_with_partial_data(self, manager, temp_storage_dir):
        """Test deleting data when user has only some data types."""
        user_id = "user1"
        
        # Store only preferences and notes (no reminders, sessions, or usage)
        manager.store_preference("theme", "dark", user_id)
        note = Note(
            note_id="note1",
            content="Test note",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        manager.store_note(note, user_id)
        
        # Verify data exists
        assert manager.get_preference("theme", user_id) == "dark"
        assert len(manager.search_notes("Test", user_id)) == 1
        
        # Delete user data (should not raise error for missing data types)
        manager.delete_user_data(user_id)
        
        # Verify data is deleted
        assert manager.get_preference("theme", user_id) is None
        assert len(manager.search_notes("Test", user_id)) == 0

    def test_delete_user_data_with_special_characters_in_user_id(self, manager, temp_storage_dir):
        """Test deleting data for users with special characters in ID."""
        user_id = "user@example.com"
        
        # Store data
        manager.store_preference("email", "test@example.com", user_id)
        note = Note(
            note_id="note1",
            content="Email note",
            tags=["email"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        manager.store_note(note, user_id)
        
        # Verify data exists
        assert manager.get_preference("email", user_id) == "test@example.com"
        assert len(manager.search_notes("Email", user_id)) == 1
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify data is deleted
        assert manager.get_preference("email", user_id) is None
        assert len(manager.search_notes("Email", user_id)) == 0

    def test_delete_user_data_multiple_times(self, manager, temp_storage_dir):
        """Test that deleting user data multiple times doesn't cause errors."""
        user_id = "user1"
        
        # Store some data
        manager.store_preference("theme", "dark", user_id)
        
        # Delete once
        manager.delete_user_data(user_id)
        assert manager.get_preference("theme", user_id) is None
        
        # Delete again (should not raise error)
        manager.delete_user_data(user_id)
        assert manager.get_preference("theme", user_id) is None

    def test_delete_user_data_with_multiple_sessions(self, manager, temp_storage_dir):
        """Test deleting multiple sessions for a user."""
        user_id = "user1"
        
        # Create multiple sessions
        for i in range(5):
            session = Session(
                session_id=f"session{i}",
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={}
            )
            manager.save_session(session)
        
        # Verify all sessions exist
        for i in range(5):
            assert manager.load_session(f"session{i}").user_id == user_id
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify all sessions are deleted
        for i in range(5):
            with pytest.raises(FileNotFoundError):
                manager.load_session(f"session{i}")

    def test_delete_user_data_with_multiple_notes(self, manager, temp_storage_dir):
        """Test deleting multiple notes for a user."""
        user_id = "user1"
        
        # Create multiple notes
        for i in range(10):
            note = Note(
                note_id=f"note{i}",
                content=f"Test note {i}",
                tags=["test"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            manager.store_note(note, user_id)
        
        # Verify all notes exist
        notes = manager.search_notes("Test", user_id)
        assert len(notes) == 10
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify all notes are deleted
        notes = manager.search_notes("Test", user_id)
        assert len(notes) == 0

    def test_delete_user_data_with_multiple_reminders(self, manager, temp_storage_dir):
        """Test deleting multiple reminders for a user."""
        user_id = "user1"
        
        # Create multiple reminders
        for i in range(10):
            reminder = Reminder(
                reminder_id=f"reminder{i}",
                content=f"Test reminder {i}",
                due_time=datetime.now() - timedelta(hours=i),
                is_completed=False
            )
            manager.create_reminder(reminder, user_id)
        
        # Verify all reminders exist
        reminders = manager.get_due_reminders(user_id)
        assert len(reminders) == 10
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify all reminders are deleted
        reminders = manager.get_due_reminders(user_id)
        assert len(reminders) == 0

    def test_delete_user_data_with_multiple_usage_patterns(self, manager, temp_storage_dir):
        """Test deleting multiple usage patterns for a user."""
        user_id = "user1"
        
        # Record usage for multiple applications
        apps = ["chrome", "vscode", "firefox", "terminal", "slack"]
        for app in apps:
            manager.record_application_usage(app, user_id)
        
        # Verify all usage patterns exist
        all_usage = manager.get_all_application_usage(user_id)
        assert len(all_usage) == 5
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify all usage patterns are deleted
        all_usage = manager.get_all_application_usage(user_id)
        assert len(all_usage) == 0
        
        for app in apps:
            assert manager.get_application_usage(app, user_id) is None

    def test_delete_user_data_directory_structure(self, manager, temp_storage_dir):
        """Test that user-specific directories are removed after deletion."""
        user_id = "user1"
        
        # Store data to create directories
        note = Note(
            note_id="note1",
            content="Test note",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        manager.store_note(note, user_id)
        
        reminder = Reminder(
            reminder_id="reminder1",
            content="Test reminder",
            due_time=datetime.now(),
            is_completed=False
        )
        manager.create_reminder(reminder, user_id)
        
        manager.record_application_usage("chrome", user_id)
        
        # Get sanitized user_id
        import hashlib
        safe_user_id = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        
        # Verify directories exist
        notes_dir = Path(temp_storage_dir) / 'notes' / safe_user_id
        reminders_dir = Path(temp_storage_dir) / 'reminders' / safe_user_id
        usage_dir = Path(temp_storage_dir) / 'usage_patterns' / safe_user_id
        
        assert notes_dir.exists()
        assert reminders_dir.exists()
        assert usage_dir.exists()
        
        # Delete user data
        manager.delete_user_data(user_id)
        
        # Verify directories are removed
        assert not notes_dir.exists()
        assert not reminders_dir.exists()
        assert not usage_dir.exists()
