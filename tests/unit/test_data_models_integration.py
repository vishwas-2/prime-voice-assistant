"""
Integration tests for data models.

Tests verify that data models work together correctly in realistic scenarios.
"""

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
    Session,
    Size,
    UIElement,
)


class TestDataModelIntegration:
    """Tests for data model integration scenarios."""
    
    def test_complete_command_flow(self):
        """Test a complete command flow from intent to result."""
        # Create an entity
        entity = Entity(
            entity_type="application",
            value="notepad",
            confidence=0.95
        )
        
        # Create an intent with the entity
        intent = Intent(
            intent_type="launch_app",
            entities=[entity],
            confidence=0.9,
            requires_clarification=False
        )
        
        # Create a command with the intent
        timestamp = datetime.now()
        command = Command(
            command_id="cmd_001",
            intent=intent,
            parameters={"app_name": "notepad"},
            timestamp=timestamp,
            requires_confirmation=False
        )
        
        # Create a command result
        result = CommandResult(
            command_id="cmd_001",
            success=True,
            output="Notepad launched successfully",
            error=None,
            execution_time_ms=250
        )
        
        # Create a command record
        record = CommandRecord(
            command=command,
            result=result,
            timestamp=timestamp
        )
        
        # Verify the complete flow
        assert record.command.intent.entities[0].value == "notepad"
        assert record.result.success is True
        assert record.result.execution_time_ms == 250
    
    def test_session_with_multiple_commands(self):
        """Test a session with multiple command records."""
        start_time = datetime.now()
        
        # Create first command
        entity1 = Entity(entity_type="application", value="chrome", confidence=0.95)
        intent1 = Intent(
            intent_type="launch_app",
            entities=[entity1],
            confidence=0.9,
            requires_clarification=False
        )
        command1 = Command(
            command_id="cmd_001",
            intent=intent1,
            parameters={},
            timestamp=start_time,
            requires_confirmation=False
        )
        result1 = CommandResult(
            command_id="cmd_001",
            success=True,
            output="Chrome launched",
            error=None,
            execution_time_ms=300
        )
        record1 = CommandRecord(command=command1, result=result1, timestamp=start_time)
        
        # Create second command
        entity2 = Entity(entity_type="setting", value="volume", confidence=0.9)
        intent2 = Intent(
            intent_type="adjust_volume",
            entities=[entity2],
            confidence=0.85,
            requires_clarification=False
        )
        command2 = Command(
            command_id="cmd_002",
            intent=intent2,
            parameters={"level": 50},
            timestamp=start_time,
            requires_confirmation=False
        )
        result2 = CommandResult(
            command_id="cmd_002",
            success=True,
            output="Volume set to 50%",
            error=None,
            execution_time_ms=100
        )
        record2 = CommandRecord(command=command2, result=result2, timestamp=start_time)
        
        # Create session with both commands
        session = Session(
            session_id="sess_001",
            user_id="user_123",
            start_time=start_time,
            end_time=None,
            command_history=[record1, record2],
            context_state={"last_app": "chrome", "current_volume": 50}
        )
        
        # Verify session state
        assert len(session.command_history) == 2
        assert session.command_history[0].command.intent.intent_type == "launch_app"
        assert session.command_history[1].command.intent.intent_type == "adjust_volume"
        assert session.context_state["last_app"] == "chrome"
        assert session.context_state["current_volume"] == 50
    
    def test_automation_sequence_with_ui_elements(self):
        """Test automation sequence interacting with UI elements."""
        # Create UI element
        coords = Coordinates(x=500, y=300)
        size = Size(width=100, height=40)
        button = UIElement(
            element_type="button",
            text="Submit",
            coordinates=coords,
            size=size
        )
        
        # Create actions that interact with the UI element
        action1 = Action(
            action_type="mouse",
            parameters={
                "action": "click",
                "x": button.coordinates.x,
                "y": button.coordinates.y
            },
            delay_ms=500
        )
        
        action2 = Action(
            action_type="keyboard",
            parameters={"keys": "enter"},
            delay_ms=100
        )
        
        # Create automation sequence
        sequence = AutomationSequence(
            sequence_id="seq_001",
            name="Click Submit Button",
            actions=[action1, action2],
            created_at=datetime.now()
        )
        
        # Verify the sequence
        assert len(sequence.actions) == 2
        assert sequence.actions[0].parameters["x"] == button.coordinates.x
        assert sequence.actions[0].parameters["y"] == button.coordinates.y
        assert sequence.actions[1].action_type == "keyboard"
