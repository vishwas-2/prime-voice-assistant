"""
Demonstration of using shared fixtures from conftest.py.

This file shows how to use the fixtures defined in conftest.py
for writing tests efficiently.
"""

import pytest
from datetime import datetime


class TestFixtureUsage:
    """Demonstrate using fixtures from conftest.py."""
    
    def test_sample_session_fixture(self, sample_session):
        """Test using the sample_session fixture."""
        assert sample_session.session_id == "sess_001"
        assert sample_session.user_id == "user_123"
        assert sample_session.start_time is not None
        assert sample_session.end_time is None
        assert sample_session.command_history == []
        assert sample_session.context_state == {}
    
    def test_sample_entity_fixture(self, sample_entity):
        """Test using the sample_entity fixture."""
        assert sample_entity.entity_type == "application"
        assert sample_entity.value == "chrome"
        assert sample_entity.confidence == 0.95
    
    def test_sample_command_fixture(self, sample_command):
        """Test using the sample_command fixture."""
        assert sample_command.command_id == "cmd_001"
        assert sample_command.intent.intent_type == "launch_app"
        assert sample_command.parameters["app_name"] == "chrome"
        assert sample_command.requires_confirmation is False
    
    def test_sample_command_result_fixture(self, sample_command_result):
        """Test using the sample_command_result fixture."""
        assert sample_command_result.command_id == "cmd_001"
        assert sample_command_result.success is True
        assert sample_command_result.error is None
        assert sample_command_result.execution_time_ms == 150
    
    def test_sample_voice_profile_fixture(self, sample_voice_profile):
        """Test using the sample_voice_profile fixture."""
        assert sample_voice_profile.profile_id == "voice_001"
        assert sample_voice_profile.voice_name == "en-US-Neural"
        assert sample_voice_profile.speech_rate == 1.0
        assert sample_voice_profile.pitch == 1.0
        assert sample_voice_profile.volume == 0.8


class TestMultipleFixtures:
    """Demonstrate using multiple fixtures together."""
    
    def test_session_with_history(self, sample_session_with_history):
        """Test using a session that has command history."""
        assert len(sample_session_with_history.command_history) == 1
        assert sample_session_with_history.context_state["last_app"] == "chrome"
        
        # Verify the command record
        record = sample_session_with_history.command_history[0]
        assert record.command.command_id == "cmd_001"
        assert record.result.success is True
    
    def test_ui_element_with_coordinates(self, sample_ui_element):
        """Test using a UI element with coordinates and size."""
        assert sample_ui_element.element_type == "button"
        assert sample_ui_element.text == "Submit"
        assert sample_ui_element.coordinates.x == 100
        assert sample_ui_element.coordinates.y == 200
        assert sample_ui_element.size.width == 800
        assert sample_ui_element.size.height == 600
    
    def test_automation_sequence_with_actions(self, sample_automation_sequence):
        """Test using an automation sequence with multiple actions."""
        assert sample_automation_sequence.sequence_id == "seq_001"
        assert sample_automation_sequence.name == "Copy and Paste"
        assert len(sample_automation_sequence.actions) == 2
        assert sample_automation_sequence.actions[0].action_type == "keyboard"
        assert sample_automation_sequence.actions[1].action_type == "keyboard"


class TestCollectionFixtures:
    """Demonstrate using collection fixtures."""
    
    def test_command_history_list(self, sample_command_history):
        """Test using a list of command records."""
        assert len(sample_command_history) == 3
        
        # Verify all records are valid
        for record in sample_command_history:
            assert record.command.command_id.startswith("cmd_")
            assert record.result.success is True
            assert record.timestamp is not None
    
    def test_notes_list(self, sample_notes_list):
        """Test using a list of notes."""
        assert len(sample_notes_list) == 5
        
        # Verify all notes are valid
        for note in sample_notes_list:
            assert note.note_id.startswith("note_")
            assert "test" in note.tags
            assert note.content.startswith("Note content")
    
    def test_reminders_list(self, sample_reminders_list):
        """Test using a list of reminders."""
        assert len(sample_reminders_list) == 5
        
        # Verify all reminders are valid
        for reminder in sample_reminders_list:
            assert reminder.reminder_id.startswith("rem_")
            assert reminder.is_completed is False
            assert isinstance(reminder.due_time, datetime)


class TestTimeFixtures:
    """Demonstrate using time-related fixtures."""
    
    def test_current_time_fixture(self, current_time):
        """Test using the current_time fixture."""
        assert isinstance(current_time, datetime)
        # Should be very recent (within last minute)
        time_diff = (datetime.now() - current_time).total_seconds()
        assert abs(time_diff) < 60
    
    def test_past_time_fixture(self, past_time):
        """Test using the past_time fixture."""
        assert isinstance(past_time, datetime)
        assert past_time < datetime.now()
    
    def test_future_time_fixture(self, future_time):
        """Test using the future_time fixture."""
        assert isinstance(future_time, datetime)
        assert future_time > datetime.now()
    
    def test_time_ordering(self, past_time, current_time, future_time):
        """Test that time fixtures are properly ordered."""
        assert past_time < current_time < future_time


@pytest.mark.unit
class TestFixtureWithMarker:
    """Demonstrate using fixtures with test markers."""
    
    def test_marked_test_with_fixture(self, sample_process):
        """Test that fixtures work with marked tests."""
        assert sample_process.pid == 1234
        assert sample_process.name == "chrome.exe"
        assert sample_process.cpu_percent == 15.5
        assert sample_process.memory_mb == 512.0
        assert sample_process.status == "running"


if __name__ == "__main__":
    # Allow running this file directly
    pytest.main([__file__, "-v"])
