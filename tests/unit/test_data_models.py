"""
Unit tests for core data models.

Tests verify that all dataclasses can be instantiated correctly
and that their fields are properly typed and accessible.
"""

import pytest
from datetime import datetime
from prime.models import (
    Action,
    AutomationSequence,
    Command,
    CommandRecord,
    CommandResult,
    Coordinates,
    Entity,
    Intent,
    Note,
    Process,
    Reminder,
    Session,
    Size,
    UIElement,
    VoiceProfile,
)


class TestCoordinates:
    """Tests for Coordinates dataclass."""
    
    def test_coordinates_creation(self):
        coords = Coordinates(x=100, y=200)
        assert coords.x == 100
        assert coords.y == 200


class TestSize:
    """Tests for Size dataclass."""
    
    def test_size_creation(self):
        size = Size(width=800, height=600)
        assert size.width == 800
        assert size.height == 600


class TestEntity:
    """Tests for Entity dataclass."""
    
    def test_entity_creation(self):
        entity = Entity(
            entity_type="application",
            value="chrome",
            confidence=0.95
        )
        assert entity.entity_type == "application"
        assert entity.value == "chrome"
        assert entity.confidence == 0.95



class TestIntent:
    """Tests for Intent dataclass."""
    
    def test_intent_creation(self):
        entity = Entity(entity_type="application", value="chrome", confidence=0.95)
        intent = Intent(
            intent_type="launch_app",
            entities=[entity],
            confidence=0.9,
            requires_clarification=False
        )
        assert intent.intent_type == "launch_app"
        assert len(intent.entities) == 1
        assert intent.entities[0].value == "chrome"
        assert intent.confidence == 0.9
        assert intent.requires_clarification is False


class TestCommand:
    """Tests for Command dataclass."""
    
    def test_command_creation(self):
        entity = Entity(entity_type="application", value="chrome", confidence=0.95)
        intent = Intent(
            intent_type="launch_app",
            entities=[entity],
            confidence=0.9,
            requires_clarification=False
        )
        timestamp = datetime.now()
        command = Command(
            command_id="cmd_001",
            intent=intent,
            parameters={"app_name": "chrome"},
            timestamp=timestamp,
            requires_confirmation=False
        )
        assert command.command_id == "cmd_001"
        assert command.intent.intent_type == "launch_app"
        assert command.parameters["app_name"] == "chrome"
        assert command.timestamp == timestamp
        assert command.requires_confirmation is False


class TestCommandResult:
    """Tests for CommandResult dataclass."""
    
    def test_command_result_success(self):
        result = CommandResult(
            command_id="cmd_001",
            success=True,
            output="Application launched successfully",
            error=None,
            execution_time_ms=150
        )
        assert result.command_id == "cmd_001"
        assert result.success is True
        assert result.output == "Application launched successfully"
        assert result.error is None
        assert result.execution_time_ms == 150
    
    def test_command_result_failure(self):
        result = CommandResult(
            command_id="cmd_002",
            success=False,
            output="",
            error="Application not found",
            execution_time_ms=50
        )
        assert result.success is False
        assert result.error == "Application not found"



class TestSession:
    """Tests for Session dataclass."""
    
    def test_session_creation(self):
        start_time = datetime.now()
        session = Session(
            session_id="sess_001",
            user_id="user_123",
            start_time=start_time,
            end_time=None
        )
        assert session.session_id == "sess_001"
        assert session.user_id == "user_123"
        assert session.start_time == start_time
        assert session.end_time is None
        assert session.command_history == []
        assert session.context_state == {}
    
    def test_session_with_history(self):
        start_time = datetime.now()
        entity = Entity(entity_type="application", value="chrome", confidence=0.95)
        intent = Intent(
            intent_type="launch_app",
            entities=[entity],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id="cmd_001",
            intent=intent,
            parameters={},
            timestamp=start_time,
            requires_confirmation=False
        )
        result = CommandResult(
            command_id="cmd_001",
            success=True,
            output="Success",
            error=None,
            execution_time_ms=100
        )
        record = CommandRecord(
            command=command,
            result=result,
            timestamp=start_time
        )
        
        session = Session(
            session_id="sess_001",
            user_id="user_123",
            start_time=start_time,
            end_time=None,
            command_history=[record],
            context_state={"last_app": "chrome"}
        )
        assert len(session.command_history) == 1
        assert session.context_state["last_app"] == "chrome"


class TestVoiceProfile:
    """Tests for VoiceProfile dataclass."""
    
    def test_voice_profile_creation(self):
        profile = VoiceProfile(
            profile_id="voice_001",
            voice_name="en-US-Neural",
            speech_rate=1.0,
            pitch=1.0,
            volume=0.8
        )
        assert profile.profile_id == "voice_001"
        assert profile.voice_name == "en-US-Neural"
        assert profile.speech_rate == 1.0
        assert profile.pitch == 1.0
        assert profile.volume == 0.8



class TestNote:
    """Tests for Note dataclass."""
    
    def test_note_creation(self):
        created = datetime.now()
        updated = datetime.now()
        note = Note(
            note_id="note_001",
            content="Remember to buy groceries",
            tags=["personal", "shopping"],
            created_at=created,
            updated_at=updated
        )
        assert note.note_id == "note_001"
        assert note.content == "Remember to buy groceries"
        assert len(note.tags) == 2
        assert "personal" in note.tags
        assert note.created_at == created
        assert note.updated_at == updated


class TestReminder:
    """Tests for Reminder dataclass."""
    
    def test_reminder_creation(self):
        due_time = datetime(2024, 12, 31, 15, 30)
        reminder = Reminder(
            reminder_id="rem_001",
            content="Team meeting at 3 PM",
            due_time=due_time,
            is_completed=False
        )
        assert reminder.reminder_id == "rem_001"
        assert reminder.content == "Team meeting at 3 PM"
        assert reminder.due_time == due_time
        assert reminder.is_completed is False


class TestAction:
    """Tests for Action dataclass."""
    
    def test_action_creation(self):
        action = Action(
            action_type="keyboard",
            parameters={"keys": "ctrl+c"},
            delay_ms=100
        )
        assert action.action_type == "keyboard"
        assert action.parameters["keys"] == "ctrl+c"
        assert action.delay_ms == 100


class TestAutomationSequence:
    """Tests for AutomationSequence dataclass."""
    
    def test_automation_sequence_creation(self):
        action1 = Action(action_type="keyboard", parameters={"keys": "ctrl+c"}, delay_ms=100)
        action2 = Action(action_type="keyboard", parameters={"keys": "ctrl+v"}, delay_ms=100)
        created = datetime.now()
        
        sequence = AutomationSequence(
            sequence_id="seq_001",
            name="Copy and Paste",
            actions=[action1, action2],
            created_at=created
        )
        assert sequence.sequence_id == "seq_001"
        assert sequence.name == "Copy and Paste"
        assert len(sequence.actions) == 2
        assert sequence.actions[0].action_type == "keyboard"
        assert sequence.created_at == created



class TestProcess:
    """Tests for Process dataclass."""
    
    def test_process_creation(self):
        process = Process(
            pid=1234,
            name="chrome.exe",
            cpu_percent=15.5,
            memory_mb=512.0,
            status="running"
        )
        assert process.pid == 1234
        assert process.name == "chrome.exe"
        assert process.cpu_percent == 15.5
        assert process.memory_mb == 512.0
        assert process.status == "running"


class TestUIElement:
    """Tests for UIElement dataclass."""
    
    def test_ui_element_creation(self):
        coords = Coordinates(x=100, y=200)
        size = Size(width=150, height=40)
        element = UIElement(
            element_type="button",
            text="Submit",
            coordinates=coords,
            size=size
        )
        assert element.element_type == "button"
        assert element.text == "Submit"
        assert element.coordinates.x == 100
        assert element.coordinates.y == 200
        assert element.size.width == 150
        assert element.size.height == 40
