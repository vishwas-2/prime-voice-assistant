"""
Unit tests for the Automation Engine.

Tests cover recording, playback, saving/loading sequences, and keyboard/mouse simulation.
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from prime.execution.automation_engine import AutomationEngine, RecordingSession
from prime.models.data_models import AutomationSequence, Action, Coordinates


class TestRecordingSession:
    """Test RecordingSession class."""
    
    def test_recording_session_initialization(self):
        """Test that recording session initializes correctly."""
        session = RecordingSession("test-session-id")
        
        assert session.session_id == "test-session-id"
        assert isinstance(session.start_time, datetime)
        assert session.actions == []
        assert session.last_action_time is None
    
    def test_add_action_to_recording(self):
        """Test adding actions to a recording session."""
        session = RecordingSession("test-session-id")
        
        action = Action(
            action_type="keyboard",
            parameters={"keys": "hello"},
            delay_ms=100
        )
        
        session.add_action(action)
        
        assert len(session.actions) == 1
        assert session.actions[0] == action
        assert session.last_action_time is not None


class TestAutomationEngineInitialization:
    """Test Automation Engine initialization."""
    
    def test_initialization_default_path(self, tmp_path):
        """Test initialization with default storage path."""
        with patch('prime.execution.automation_engine.Path') as mock_path:
            mock_path.return_value = tmp_path / 'automation_sequences'
            engine = AutomationEngine()
            
            assert engine._current_recording is None
            assert engine._sequences == {}
    
    def test_initialization_custom_path(self, tmp_path):
        """Test initialization with custom storage path."""
        custom_path = tmp_path / "custom_sequences"
        engine = AutomationEngine(storage_path=str(custom_path))
        
        assert engine._storage_path == custom_path
        assert custom_path.exists()


class TestRecordingManagement:
    """Test recording start/stop functionality."""
    
    def test_start_recording(self, tmp_path):
        """Test starting a recording session."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        session = engine.start_recording()
        
        assert isinstance(session, RecordingSession)
        assert engine.is_recording()
        assert engine.get_current_recording() == session
    
    def test_start_recording_when_already_recording(self, tmp_path):
        """Test that starting a recording when one is active raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        engine.start_recording()
        
        with pytest.raises(RuntimeError, match="Recording already in progress"):
            engine.start_recording()
    
    def test_stop_recording(self, tmp_path):
        """Test stopping a recording session."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        session = engine.start_recording()
        
        # Add some actions
        action = Action(action_type="keyboard", parameters={"keys": "test"}, delay_ms=0)
        session.add_action(action)
        
        sequence = engine.stop_recording(session)
        
        assert isinstance(sequence, AutomationSequence)
        assert len(sequence.actions) == 1
        assert not engine.is_recording()
        assert engine.get_current_recording() is None
    
    def test_stop_recording_no_active_recording(self, tmp_path):
        """Test stopping recording when none is active."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        session = RecordingSession("fake-session")
        
        with pytest.raises(RuntimeError, match="No recording in progress"):
            engine.stop_recording(session)
    
    def test_stop_recording_wrong_session(self, tmp_path):
        """Test stopping recording with wrong session."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        engine.start_recording()
        
        wrong_session = RecordingSession("wrong-session-id")
        
        with pytest.raises(ValueError, match="not the current recording"):
            engine.stop_recording(wrong_session)


class TestSequenceSaveLoad:
    """Test saving and loading automation sequences."""
    
    def test_save_sequence(self, tmp_path):
        """Test saving an automation sequence."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq-1",
            name="Test Sequence",
            actions=[
                Action(action_type="keyboard", parameters={"keys": "hello"}, delay_ms=100)
            ],
            created_at=datetime.now()
        )
        
        engine.save_sequence("test_sequence", sequence)
        
        # Check file was created
        file_path = tmp_path / "test_sequence.json"
        assert file_path.exists()
        
        # Check sequence is cached
        assert "test_sequence" in engine._sequences
    
    def test_save_sequence_empty_name(self, tmp_path):
        """Test that saving with empty name raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Test",
            actions=[Action(action_type="keyboard", parameters={"keys": "test"}, delay_ms=0)],
            created_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="name cannot be empty"):
            engine.save_sequence("", sequence)
    
    def test_save_sequence_empty_actions(self, tmp_path):
        """Test that saving empty sequence raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Test",
            actions=[],
            created_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Cannot save empty sequence"):
            engine.save_sequence("test", sequence)
    
    def test_load_sequence(self, tmp_path):
        """Test loading a saved sequence."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        # Save a sequence first
        original_sequence = AutomationSequence(
            sequence_id="test-seq-1",
            name="Test Sequence",
            actions=[
                Action(action_type="keyboard", parameters={"keys": "hello"}, delay_ms=100),
                Action(action_type="mouse", parameters={"action": "click", "x": 100, "y": 200}, delay_ms=50)
            ],
            created_at=datetime.now()
        )
        engine.save_sequence("test_load", original_sequence)
        
        # Clear cache to force loading from file
        engine._sequences.clear()
        
        # Load the sequence
        loaded_sequence = engine.load_sequence("test_load")
        
        assert loaded_sequence.sequence_id == original_sequence.sequence_id
        assert loaded_sequence.name == "test_load"  # Name is updated on save
        assert len(loaded_sequence.actions) == 2
        assert loaded_sequence.actions[0].action_type == "keyboard"
        assert loaded_sequence.actions[1].action_type == "mouse"
    
    def test_load_sequence_from_cache(self, tmp_path):
        """Test loading sequence from cache."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Test",
            actions=[Action(action_type="keyboard", parameters={"keys": "test"}, delay_ms=0)],
            created_at=datetime.now()
        )
        engine.save_sequence("cached_test", sequence)
        
        # Load should use cache
        loaded = engine.load_sequence("cached_test")
        assert loaded == sequence
    
    def test_load_nonexistent_sequence(self, tmp_path):
        """Test loading a sequence that doesn't exist."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        with pytest.raises(FileNotFoundError, match="not found"):
            engine.load_sequence("nonexistent")
    
    def test_load_sequence_empty_name(self, tmp_path):
        """Test loading with empty name raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        with pytest.raises(ValueError, match="name cannot be empty"):
            engine.load_sequence("")


class TestSequenceExecution:
    """Test automation sequence execution."""
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_execute_keyboard_sequence(self, mock_pyautogui, tmp_path):
        """Test executing a sequence with keyboard actions."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Keyboard Test",
            actions=[
                Action(action_type="keyboard", parameters={"keys": "hello"}, delay_ms=0)
            ],
            created_at=datetime.now()
        )
        
        result = engine.execute_sequence(sequence)
        
        assert result["success"] is True
        assert result["actions_executed"] == 1
        assert result["error"] is None
        mock_pyautogui.write.assert_called_once_with("hello", interval=0.05)
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_execute_mouse_sequence(self, mock_pyautogui, tmp_path):
        """Test executing a sequence with mouse actions."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Mouse Test",
            actions=[
                Action(action_type="mouse", parameters={"action": "click", "x": 100, "y": 200}, delay_ms=0)
            ],
            created_at=datetime.now()
        )
        
        result = engine.execute_sequence(sequence)
        
        assert result["success"] is True
        assert result["actions_executed"] == 1
        mock_pyautogui.click.assert_called_once_with(100, 200)
    
    def test_execute_empty_sequence(self, tmp_path):
        """Test executing an empty sequence raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Empty",
            actions=[],
            created_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Cannot execute empty sequence"):
            engine.execute_sequence(sequence)
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_execute_sequence_with_delays(self, mock_pyautogui, tmp_path):
        """Test that delays are applied during execution."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Delay Test",
            actions=[
                Action(action_type="keyboard", parameters={"keys": "a"}, delay_ms=100),
                Action(action_type="keyboard", parameters={"keys": "b"}, delay_ms=100)
            ],
            created_at=datetime.now()
        )
        
        start_time = time.time()
        result = engine.execute_sequence(sequence)
        elapsed_time = time.time() - start_time
        
        assert result["success"] is True
        assert result["actions_executed"] == 2
        # Should take at least 200ms for the delays
        assert elapsed_time >= 0.2
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_execute_sequence_with_error(self, mock_pyautogui, tmp_path):
        """Test execution error handling."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        mock_pyautogui.write.side_effect = Exception("Simulated error")
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Error Test",
            actions=[
                Action(action_type="keyboard", parameters={"keys": "test"}, delay_ms=0)
            ],
            created_at=datetime.now()
        )
        
        result = engine.execute_sequence(sequence)
        
        assert result["success"] is False
        assert result["actions_executed"] == 0
        assert "Simulated error" in result["error"]


class TestKeyboardSimulation:
    """Test keyboard simulation."""
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_simulate_keyboard_typing(self, mock_pyautogui, tmp_path):
        """Test simulating keyboard typing."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        engine.simulate_keyboard("hello world")
        
        mock_pyautogui.write.assert_called_once_with("hello world", interval=0.05)
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_simulate_keyboard_hotkey(self, mock_pyautogui, tmp_path):
        """Test simulating keyboard hotkey combination."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        engine.simulate_keyboard("ctrl+c")
        
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")
    
    def test_simulate_keyboard_empty_string(self, tmp_path):
        """Test that empty keys string raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        with pytest.raises(ValueError, match="Keys string cannot be empty"):
            engine.simulate_keyboard("")


class TestMouseSimulation:
    """Test mouse simulation."""
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_simulate_mouse_click(self, mock_pyautogui, tmp_path):
        """Test simulating mouse click."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        coords = Coordinates(x=100, y=200)
        
        engine.simulate_mouse("click", coords)
        
        mock_pyautogui.click.assert_called_once_with(100, 200)
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_simulate_mouse_double_click(self, mock_pyautogui, tmp_path):
        """Test simulating mouse double click."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        coords = Coordinates(x=150, y=250)
        
        engine.simulate_mouse("double_click", coords)
        
        mock_pyautogui.doubleClick.assert_called_once_with(150, 250)
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_simulate_mouse_right_click(self, mock_pyautogui, tmp_path):
        """Test simulating mouse right click."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        coords = Coordinates(x=300, y=400)
        
        engine.simulate_mouse("right_click", coords)
        
        mock_pyautogui.rightClick.assert_called_once_with(300, 400)
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_simulate_mouse_move(self, mock_pyautogui, tmp_path):
        """Test simulating mouse movement."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        coords = Coordinates(x=500, y=600)
        
        engine.simulate_mouse("move", coords)
        
        mock_pyautogui.moveTo.assert_called_once_with(500, 600)
    
    def test_simulate_mouse_invalid_action(self, tmp_path):
        """Test that invalid mouse action raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        coords = Coordinates(x=100, y=100)
        
        with pytest.raises(ValueError, match="Unknown mouse action"):
            engine.simulate_mouse("invalid_action", coords)
    
    def test_simulate_mouse_empty_action(self, tmp_path):
        """Test that empty mouse action raises error."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        coords = Coordinates(x=100, y=100)
        
        with pytest.raises(ValueError, match="Mouse action cannot be empty"):
            engine.simulate_mouse("", coords)


class TestSequenceManagement:
    """Test sequence management utilities."""
    
    def test_list_saved_sequences(self, tmp_path):
        """Test listing saved sequences."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        # Save multiple sequences
        for i in range(3):
            sequence = AutomationSequence(
                sequence_id=f"seq-{i}",
                name=f"Sequence {i}",
                actions=[Action(action_type="keyboard", parameters={"keys": f"test{i}"}, delay_ms=0)],
                created_at=datetime.now()
            )
            engine.save_sequence(f"sequence_{i}", sequence)
        
        sequences = engine.list_saved_sequences()
        
        assert len(sequences) == 3
        assert "sequence_0" in sequences
        assert "sequence_1" in sequences
        assert "sequence_2" in sequences
    
    def test_delete_sequence(self, tmp_path):
        """Test deleting a saved sequence."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        sequence = AutomationSequence(
            sequence_id="test-seq",
            name="Test",
            actions=[Action(action_type="keyboard", parameters={"keys": "test"}, delay_ms=0)],
            created_at=datetime.now()
        )
        engine.save_sequence("to_delete", sequence)
        
        # Verify it exists
        assert "to_delete" in engine.list_saved_sequences()
        
        # Delete it
        engine.delete_sequence("to_delete")
        
        # Verify it's gone
        assert "to_delete" not in engine.list_saved_sequences()
        assert "to_delete" not in engine._sequences
    
    def test_delete_nonexistent_sequence(self, tmp_path):
        """Test deleting a sequence that doesn't exist."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        with pytest.raises(FileNotFoundError, match="not found"):
            engine.delete_sequence("nonexistent")


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @patch('prime.execution.automation_engine.pyautogui')
    def test_complete_record_save_load_execute_workflow(self, mock_pyautogui, tmp_path):
        """Test complete workflow: record -> save -> load -> execute."""
        engine = AutomationEngine(storage_path=str(tmp_path))
        
        # Start recording
        session = engine.start_recording()
        
        # Add actions
        session.add_action(Action(action_type="keyboard", parameters={"keys": "hello"}, delay_ms=50))
        session.add_action(Action(action_type="mouse", parameters={"action": "click", "x": 100, "y": 200}, delay_ms=50))
        
        # Stop recording
        sequence = engine.stop_recording(session)
        
        # Save sequence
        engine.save_sequence("test_workflow", sequence)
        
        # Clear cache
        engine._sequences.clear()
        
        # Load sequence
        loaded_sequence = engine.load_sequence("test_workflow")
        
        # Execute sequence
        result = engine.execute_sequence(loaded_sequence)
        
        assert result["success"] is True
        assert result["actions_executed"] == 2
        assert mock_pyautogui.write.called
        assert mock_pyautogui.click.called
