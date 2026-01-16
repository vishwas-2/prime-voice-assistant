"""Unit tests for Memory Manager notes and reminders functionality."""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from prime.persistence.memory_manager import MemoryManager
from prime.models.data_models import Note, Reminder


class TestMemoryManagerNotes:
    """Test suite for note storage and retrieval."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_manager(self, temp_storage):
        """Create a MemoryManager instance with temporary storage."""
        return MemoryManager(storage_dir=temp_storage)

    def test_store_note_creates_file(self, memory_manager, temp_storage):
        """Test that storing a note creates an encrypted file."""
        note = Note(
            note_id="note_001",
            content="This is a test note",
            tags=["test", "example"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        user_id = "test_user"
        
        memory_manager.store_note(note, user_id)
        
        # Verify the note file was created
        notes_dir = Path(temp_storage) / 'notes'
        assert notes_dir.exists()
        
        # Check that user-specific directory exists
        user_notes = list(notes_dir.iterdir())
        assert len(user_notes) == 1
        
        # Check that note file exists
        note_files = list(user_notes[0].glob("*.json"))
        assert len(note_files) == 1
        assert note_files[0].name == "note_001.json"

    def test_store_note_encrypts_data(self, memory_manager, temp_storage):
        """Test that stored notes are encrypted."""
        note = Note(
            note_id="note_002",
            content="Secret note content",
            tags=["secret"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        user_id = "test_user"
        
        memory_manager.store_note(note, user_id)
        
        # Read the raw file content
        notes_dir = Path(temp_storage) / 'notes'
        user_notes_dir = list(notes_dir.iterdir())[0]
        note_file = user_notes_dir / "note_002.json"
        raw_content = note_file.read_bytes()
        
        # Verify content is encrypted (not plain text)
        assert b"Secret note content" not in raw_content
        assert b"secret" not in raw_content

    def test_store_note_invalid_type(self, memory_manager):
        """Test that storing a non-Note object raises TypeError."""
        with pytest.raises(TypeError, match="Expected Note object"):
            memory_manager.store_note("not a note", "test_user")

    def test_search_notes_by_content(self, memory_manager):
        """Test searching notes by content."""
        user_id = "test_user"
        
        # Create and store multiple notes
        note1 = Note(
            note_id="note_001",
            content="Python programming tips",
            tags=["programming"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        note2 = Note(
            note_id="note_002",
            content="JavaScript best practices",
            tags=["programming"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        note3 = Note(
            note_id="note_003",
            content="Grocery shopping list",
            tags=["personal"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        memory_manager.store_note(note1, user_id)
        memory_manager.store_note(note2, user_id)
        memory_manager.store_note(note3, user_id)
        
        # Search for "Python"
        results = memory_manager.search_notes("Python", user_id)
        assert len(results) == 1
        assert results[0].note_id == "note_001"
        assert results[0].content == "Python programming tips"

    def test_search_notes_by_tag(self, memory_manager):
        """Test searching notes by tag."""
        user_id = "test_user"
        
        # Create and store notes with different tags
        note1 = Note(
            note_id="note_001",
            content="Meeting notes",
            tags=["work", "meeting"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        note2 = Note(
            note_id="note_002",
            content="Project ideas",
            tags=["work", "ideas"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        note3 = Note(
            note_id="note_003",
            content="Personal thoughts",
            tags=["personal"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        memory_manager.store_note(note1, user_id)
        memory_manager.store_note(note2, user_id)
        memory_manager.store_note(note3, user_id)
        
        # Search for "work" tag
        results = memory_manager.search_notes("work", user_id)
        assert len(results) == 2
        note_ids = {note.note_id for note in results}
        assert note_ids == {"note_001", "note_002"}

    def test_search_notes_case_insensitive(self, memory_manager):
        """Test that note search is case-insensitive."""
        user_id = "test_user"
        
        note = Note(
            note_id="note_001",
            content="Important REMINDER",
            tags=["URGENT"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        memory_manager.store_note(note, user_id)
        
        # Search with different cases
        results_lower = memory_manager.search_notes("reminder", user_id)
        results_upper = memory_manager.search_notes("REMINDER", user_id)
        results_mixed = memory_manager.search_notes("ReMiNdEr", user_id)
        
        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    def test_search_notes_empty_results(self, memory_manager):
        """Test searching for non-existent content returns empty list."""
        user_id = "test_user"
        
        note = Note(
            note_id="note_001",
            content="Test content",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        memory_manager.store_note(note, user_id)
        
        # Search for non-existent content
        results = memory_manager.search_notes("nonexistent", user_id)
        assert len(results) == 0

    def test_search_notes_no_user_data(self, memory_manager):
        """Test searching notes for user with no data returns empty list."""
        results = memory_manager.search_notes("anything", "nonexistent_user")
        assert len(results) == 0

    def test_search_notes_sorted_by_updated_at(self, memory_manager):
        """Test that search results are sorted by updated_at (most recent first)."""
        user_id = "test_user"
        
        # Create notes with different update times
        now = datetime.now()
        note1 = Note(
            note_id="note_001",
            content="Test note",
            tags=["test"],
            created_at=now - timedelta(hours=3),
            updated_at=now - timedelta(hours=3)
        )
        note2 = Note(
            note_id="note_002",
            content="Test note",
            tags=["test"],
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=1)  # Most recent
        )
        note3 = Note(
            note_id="note_003",
            content="Test note",
            tags=["test"],
            created_at=now - timedelta(hours=1),
            updated_at=now - timedelta(hours=2)
        )
        
        memory_manager.store_note(note1, user_id)
        memory_manager.store_note(note2, user_id)
        memory_manager.store_note(note3, user_id)
        
        # Search for all notes
        results = memory_manager.search_notes("test", user_id)
        
        # Verify sorting (most recent first)
        assert len(results) == 3
        assert results[0].note_id == "note_002"
        assert results[1].note_id == "note_003"
        assert results[2].note_id == "note_001"

    def test_store_note_updates_existing(self, memory_manager):
        """Test that storing a note with same ID updates the existing note."""
        user_id = "test_user"
        
        # Store initial note
        note1 = Note(
            note_id="note_001",
            content="Original content",
            tags=["original"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memory_manager.store_note(note1, user_id)
        
        # Update the note
        note2 = Note(
            note_id="note_001",
            content="Updated content",
            tags=["updated"],
            created_at=note1.created_at,
            updated_at=datetime.now()
        )
        memory_manager.store_note(note2, user_id)
        
        # Search and verify updated content
        results = memory_manager.search_notes("Updated", user_id)
        assert len(results) == 1
        assert results[0].content == "Updated content"
        assert results[0].tags == ["updated"]


class TestMemoryManagerReminders:
    """Test suite for reminder creation and retrieval."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_manager(self, temp_storage):
        """Create a MemoryManager instance with temporary storage."""
        return MemoryManager(storage_dir=temp_storage)

    def test_create_reminder_creates_file(self, memory_manager, temp_storage):
        """Test that creating a reminder creates an encrypted file."""
        reminder = Reminder(
            reminder_id="reminder_001",
            content="Test reminder",
            due_time=datetime.now() + timedelta(hours=1),
            is_completed=False
        )
        user_id = "test_user"
        
        memory_manager.create_reminder(reminder, user_id)
        
        # Verify the reminder file was created
        reminders_dir = Path(temp_storage) / 'reminders'
        assert reminders_dir.exists()
        
        # Check that user-specific directory exists
        user_reminders = list(reminders_dir.iterdir())
        assert len(user_reminders) == 1
        
        # Check that reminder file exists
        reminder_files = list(user_reminders[0].glob("*.json"))
        assert len(reminder_files) == 1
        assert reminder_files[0].name == "reminder_001.json"

    def test_create_reminder_encrypts_data(self, memory_manager, temp_storage):
        """Test that stored reminders are encrypted."""
        reminder = Reminder(
            reminder_id="reminder_002",
            content="Secret reminder",
            due_time=datetime.now() + timedelta(hours=1),
            is_completed=False
        )
        user_id = "test_user"
        
        memory_manager.create_reminder(reminder, user_id)
        
        # Read the raw file content
        reminders_dir = Path(temp_storage) / 'reminders'
        user_reminders_dir = list(reminders_dir.iterdir())[0]
        reminder_file = user_reminders_dir / "reminder_002.json"
        raw_content = reminder_file.read_bytes()
        
        # Verify content is encrypted (not plain text)
        assert b"Secret reminder" not in raw_content

    def test_create_reminder_invalid_type(self, memory_manager):
        """Test that creating a non-Reminder object raises TypeError."""
        with pytest.raises(TypeError, match="Expected Reminder object"):
            memory_manager.create_reminder("not a reminder", "test_user")

    def test_get_due_reminders_returns_due_only(self, memory_manager):
        """Test that get_due_reminders returns only reminders that are due."""
        user_id = "test_user"
        now = datetime.now()
        
        # Create reminders with different due times
        reminder1 = Reminder(
            reminder_id="reminder_001",
            content="Past reminder",
            due_time=now - timedelta(hours=1),  # Past
            is_completed=False
        )
        reminder2 = Reminder(
            reminder_id="reminder_002",
            content="Current reminder",
            due_time=now,  # Now
            is_completed=False
        )
        reminder3 = Reminder(
            reminder_id="reminder_003",
            content="Future reminder",
            due_time=now + timedelta(hours=1),  # Future
            is_completed=False
        )
        
        memory_manager.create_reminder(reminder1, user_id)
        memory_manager.create_reminder(reminder2, user_id)
        memory_manager.create_reminder(reminder3, user_id)
        
        # Get due reminders
        due_reminders = memory_manager.get_due_reminders(user_id)
        
        # Should return past and current, but not future
        assert len(due_reminders) == 2
        reminder_ids = {r.reminder_id for r in due_reminders}
        assert reminder_ids == {"reminder_001", "reminder_002"}

    def test_get_due_reminders_excludes_completed(self, memory_manager):
        """Test that get_due_reminders excludes completed reminders."""
        user_id = "test_user"
        now = datetime.now()
        
        # Create completed and incomplete reminders
        reminder1 = Reminder(
            reminder_id="reminder_001",
            content="Completed reminder",
            due_time=now - timedelta(hours=1),
            is_completed=True  # Completed
        )
        reminder2 = Reminder(
            reminder_id="reminder_002",
            content="Incomplete reminder",
            due_time=now - timedelta(hours=1),
            is_completed=False  # Not completed
        )
        
        memory_manager.create_reminder(reminder1, user_id)
        memory_manager.create_reminder(reminder2, user_id)
        
        # Get due reminders
        due_reminders = memory_manager.get_due_reminders(user_id)
        
        # Should only return incomplete reminder
        assert len(due_reminders) == 1
        assert due_reminders[0].reminder_id == "reminder_002"

    def test_get_due_reminders_sorted_by_due_time(self, memory_manager):
        """Test that due reminders are sorted by due_time (earliest first)."""
        user_id = "test_user"
        now = datetime.now()
        
        # Create reminders with different due times
        reminder1 = Reminder(
            reminder_id="reminder_001",
            content="Third",
            due_time=now - timedelta(hours=1),
            is_completed=False
        )
        reminder2 = Reminder(
            reminder_id="reminder_002",
            content="First",
            due_time=now - timedelta(hours=3),  # Earliest
            is_completed=False
        )
        reminder3 = Reminder(
            reminder_id="reminder_003",
            content="Second",
            due_time=now - timedelta(hours=2),
            is_completed=False
        )
        
        memory_manager.create_reminder(reminder1, user_id)
        memory_manager.create_reminder(reminder2, user_id)
        memory_manager.create_reminder(reminder3, user_id)
        
        # Get due reminders
        due_reminders = memory_manager.get_due_reminders(user_id)
        
        # Verify sorting (earliest first)
        assert len(due_reminders) == 3
        assert due_reminders[0].reminder_id == "reminder_002"
        assert due_reminders[1].reminder_id == "reminder_003"
        assert due_reminders[2].reminder_id == "reminder_001"

    def test_get_due_reminders_no_user_data(self, memory_manager):
        """Test getting reminders for user with no data returns empty list."""
        due_reminders = memory_manager.get_due_reminders("nonexistent_user")
        assert len(due_reminders) == 0

    def test_get_due_reminders_empty_when_all_future(self, memory_manager):
        """Test that get_due_reminders returns empty list when all reminders are future."""
        user_id = "test_user"
        now = datetime.now()
        
        # Create only future reminders
        reminder1 = Reminder(
            reminder_id="reminder_001",
            content="Future reminder 1",
            due_time=now + timedelta(hours=1),
            is_completed=False
        )
        reminder2 = Reminder(
            reminder_id="reminder_002",
            content="Future reminder 2",
            due_time=now + timedelta(hours=2),
            is_completed=False
        )
        
        memory_manager.create_reminder(reminder1, user_id)
        memory_manager.create_reminder(reminder2, user_id)
        
        # Get due reminders
        due_reminders = memory_manager.get_due_reminders(user_id)
        
        # Should return empty list
        assert len(due_reminders) == 0

    def test_create_reminder_updates_existing(self, memory_manager):
        """Test that creating a reminder with same ID updates the existing reminder."""
        user_id = "test_user"
        now = datetime.now()
        
        # Create initial reminder
        reminder1 = Reminder(
            reminder_id="reminder_001",
            content="Original content",
            due_time=now + timedelta(hours=1),
            is_completed=False
        )
        memory_manager.create_reminder(reminder1, user_id)
        
        # Update the reminder (mark as completed)
        reminder2 = Reminder(
            reminder_id="reminder_001",
            content="Updated content",
            due_time=now - timedelta(hours=1),  # Now in the past
            is_completed=True  # Completed
        )
        memory_manager.create_reminder(reminder2, user_id)
        
        # Get due reminders - should be empty since it's completed
        due_reminders = memory_manager.get_due_reminders(user_id)
        assert len(due_reminders) == 0


class TestMemoryManagerNotesRemindersIntegration:
    """Integration tests for notes and reminders working together."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_manager(self, temp_storage):
        """Create a MemoryManager instance with temporary storage."""
        return MemoryManager(storage_dir=temp_storage)

    def test_notes_and_reminders_separate_storage(self, memory_manager):
        """Test that notes and reminders are stored separately."""
        user_id = "test_user"
        
        # Create a note
        note = Note(
            note_id="note_001",
            content="Test note",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memory_manager.store_note(note, user_id)
        
        # Create a reminder
        reminder = Reminder(
            reminder_id="reminder_001",
            content="Test reminder",
            due_time=datetime.now() + timedelta(hours=1),
            is_completed=False
        )
        memory_manager.create_reminder(reminder, user_id)
        
        # Verify both exist independently
        notes = memory_manager.search_notes("test", user_id)
        reminders = memory_manager.get_due_reminders(user_id)
        
        assert len(notes) == 1
        # Reminder is in the future, so should not be due yet
        assert len(reminders) == 0

    def test_multiple_users_isolated_data(self, memory_manager):
        """Test that notes and reminders are isolated between users."""
        user1 = "user_one"
        user2 = "user_two"
        
        # Create note for user1
        note1 = Note(
            note_id="note_001",
            content="User 1 note",
            tags=["user1"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memory_manager.store_note(note1, user1)
        
        # Create note for user2
        note2 = Note(
            note_id="note_002",
            content="User 2 note",
            tags=["user2"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        memory_manager.store_note(note2, user2)
        
        # Create reminder for user1
        reminder1 = Reminder(
            reminder_id="reminder_001",
            content="User 1 reminder",
            due_time=datetime.now() - timedelta(hours=1),
            is_completed=False
        )
        memory_manager.create_reminder(reminder1, user1)
        
        # Verify isolation
        user1_notes = memory_manager.search_notes("note", user1)
        user2_notes = memory_manager.search_notes("note", user2)
        user1_reminders = memory_manager.get_due_reminders(user1)
        user2_reminders = memory_manager.get_due_reminders(user2)
        
        assert len(user1_notes) == 1
        assert user1_notes[0].content == "User 1 note"
        
        assert len(user2_notes) == 1
        assert user2_notes[0].content == "User 2 note"
        
        assert len(user1_reminders) == 1
        assert user1_reminders[0].content == "User 1 reminder"
        
        assert len(user2_reminders) == 0
