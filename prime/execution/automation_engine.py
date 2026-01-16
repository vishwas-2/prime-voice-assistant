"""
Automation Engine for PRIME Voice Assistant.

This module provides task automation capabilities including recording action sequences,
executing keyboard and mouse automation, and managing saved automation workflows.
"""

import time
import uuid
import json
import pyautogui
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from prime.models.data_models import AutomationSequence, Action


class RecordingSession:
    """Represents an active automation recording session."""
    
    def __init__(self, session_id: str):
        """
        Initialize a recording session.
        
        Args:
            session_id: Unique identifier for this recording session
        """
        self.session_id = session_id
        self.start_time = datetime.now()
        self.actions: List[Action] = []
        self.last_action_time: Optional[float] = None
    
    def add_action(self, action: Action) -> None:
        """
        Add an action to the recording.
        
        Args:
            action: The Action to record
        """
        self.actions.append(action)
        self.last_action_time = time.time()


class AutomationEngine:
    """
    Automation engine for recording and executing action sequences.
    
    This engine provides:
    - Recording of keyboard and mouse actions
    - Playback of recorded sequences
    - Saving and loading automation sequences
    - Keyboard and mouse simulation
    
    Attributes:
        _storage_path: Path to directory for storing automation sequences
        _current_recording: Currently active recording session (if any)
        _sequences: Cache of loaded automation sequences
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the Automation Engine.
        
        Args:
            storage_path: Optional path to directory for storing sequences.
                         Defaults to './automation_sequences'
        """
        self._storage_path = Path(storage_path or './automation_sequences')
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._current_recording: Optional[RecordingSession] = None
        self._sequences: Dict[str, AutomationSequence] = {}
        
        # Configure pyautogui safety settings
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small pause between actions
    
    def start_recording(self) -> RecordingSession:
        """
        Start recording an automation sequence.
        
        Creates a new recording session that will capture subsequent actions.
        
        Returns:
            RecordingSession object representing the active recording
        
        Raises:
            RuntimeError: If a recording is already in progress
        
        **Validates: Requirements 9.1**
        """
        if self._current_recording is not None:
            raise RuntimeError("Recording already in progress")
        
        session_id = str(uuid.uuid4())
        self._current_recording = RecordingSession(session_id)
        return self._current_recording
    
    def stop_recording(self, session: RecordingSession) -> AutomationSequence:
        """
        Stop recording and return the captured automation sequence.
        
        Args:
            session: The RecordingSession to stop
        
        Returns:
            AutomationSequence containing all recorded actions
        
        Raises:
            ValueError: If the provided session is not the current recording
            RuntimeError: If no recording is in progress
        
        **Validates: Requirements 9.1**
        """
        if self._current_recording is None:
            raise RuntimeError("No recording in progress")
        
        if session.session_id != self._current_recording.session_id:
            raise ValueError("Provided session is not the current recording")
        
        # Create automation sequence from recorded actions
        sequence = AutomationSequence(
            sequence_id=session.session_id,
            name=f"Recording_{session.start_time.strftime('%Y%m%d_%H%M%S')}",
            actions=session.actions,
            created_at=session.start_time
        )
        
        self._current_recording = None
        return sequence
    
    def execute_sequence(self, sequence: AutomationSequence) -> Dict[str, any]:
        """
        Execute an automation sequence.
        
        Plays back all actions in the sequence with appropriate delays.
        
        Args:
            sequence: The AutomationSequence to execute
        
        Returns:
            Dictionary containing execution results:
                - success: bool indicating if execution completed
                - actions_executed: int number of actions executed
                - execution_time_ms: float total execution time
                - error: Optional error message if execution failed
        
        Raises:
            ValueError: If sequence is invalid
        
        **Validates: Requirements 9.2, 9.3**
        """
        if not sequence or not sequence.actions:
            raise ValueError("Cannot execute empty sequence")
        
        start_time = time.time()
        actions_executed = 0
        
        try:
            for action in sequence.actions:
                # Apply delay before action
                if action.delay_ms > 0:
                    time.sleep(action.delay_ms / 1000.0)
                
                # Execute action based on type
                if action.action_type == "keyboard":
                    self._execute_keyboard_action(action)
                elif action.action_type == "mouse":
                    self._execute_mouse_action(action)
                elif action.action_type == "command":
                    self._execute_command_action(action)
                else:
                    raise ValueError(f"Unknown action type: {action.action_type}")
                
                actions_executed += 1
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "actions_executed": actions_executed,
                "execution_time_ms": execution_time_ms,
                "error": None
            }
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "actions_executed": actions_executed,
                "execution_time_ms": execution_time_ms,
                "error": str(e)
            }
    
    def _execute_keyboard_action(self, action: Action) -> None:
        """Execute a keyboard action."""
        keys = action.parameters.get("keys", "")
        if not keys:
            raise ValueError("Keyboard action missing 'keys' parameter")
        
        self.simulate_keyboard(keys)
    
    def _execute_mouse_action(self, action: Action) -> None:
        """Execute a mouse action."""
        mouse_action = action.parameters.get("action")
        x = action.parameters.get("x")
        y = action.parameters.get("y")
        
        if not mouse_action:
            raise ValueError("Mouse action missing 'action' parameter")
        
        from prime.models.data_models import Coordinates
        coords = Coordinates(x=x or 0, y=y or 0)
        self.simulate_mouse(mouse_action, coords)
    
    def _execute_command_action(self, action: Action) -> None:
        """Execute a command action."""
        # Command actions would integrate with CommandExecutor
        # For now, we'll just log them
        command = action.parameters.get("command", "")
        if not command:
            raise ValueError("Command action missing 'command' parameter")
        
        # In a full implementation, this would call CommandExecutor
        pass
    
    def save_sequence(self, name: str, sequence: AutomationSequence) -> None:
        """
        Save an automation sequence to persistent storage.
        
        Args:
            name: Name to save the sequence under
            sequence: The AutomationSequence to save
        
        Raises:
            ValueError: If name is empty or sequence is invalid
        
        **Validates: Requirements 9.4**
        """
        if not name or not name.strip():
            raise ValueError("Sequence name cannot be empty")
        
        if not sequence or not sequence.actions:
            raise ValueError("Cannot save empty sequence")
        
        # Update sequence name
        sequence.name = name
        
        # Convert to dictionary for JSON serialization
        sequence_dict = {
            "sequence_id": sequence.sequence_id,
            "name": sequence.name,
            "created_at": sequence.created_at.isoformat(),
            "actions": [
                {
                    "action_type": action.action_type,
                    "parameters": action.parameters,
                    "delay_ms": action.delay_ms
                }
                for action in sequence.actions
            ]
        }
        
        # Save to file
        file_path = self._storage_path / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(sequence_dict, f, indent=2)
        
        # Cache the sequence
        self._sequences[name] = sequence
    
    def load_sequence(self, name: str) -> AutomationSequence:
        """
        Load an automation sequence from persistent storage.
        
        Args:
            name: Name of the sequence to load
        
        Returns:
            The loaded AutomationSequence
        
        Raises:
            FileNotFoundError: If sequence with given name doesn't exist
            ValueError: If sequence file is corrupted
        
        **Validates: Requirements 9.5**
        """
        if not name or not name.strip():
            raise ValueError("Sequence name cannot be empty")
        
        # Check cache first
        if name in self._sequences:
            return self._sequences[name]
        
        # Load from file
        file_path = self._storage_path / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Sequence '{name}' not found")
        
        try:
            with open(file_path, 'r') as f:
                sequence_dict = json.load(f)
            
            # Reconstruct AutomationSequence
            actions = [
                Action(
                    action_type=action_data["action_type"],
                    parameters=action_data["parameters"],
                    delay_ms=action_data["delay_ms"]
                )
                for action_data in sequence_dict["actions"]
            ]
            
            sequence = AutomationSequence(
                sequence_id=sequence_dict["sequence_id"],
                name=sequence_dict["name"],
                actions=actions,
                created_at=datetime.fromisoformat(sequence_dict["created_at"])
            )
            
            # Cache the sequence
            self._sequences[name] = sequence
            return sequence
        
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Corrupted sequence file: {e}")
    
    def simulate_keyboard(self, keys: str) -> None:
        """
        Simulate keyboard input.
        
        Args:
            keys: String representing keys to type or key combination
                 Examples: "hello", "ctrl+c", "alt+tab"
        
        Raises:
            ValueError: If keys string is empty
        
        **Validates: Requirements 9.2**
        """
        if not keys or not keys.strip():
            raise ValueError("Keys string cannot be empty")
        
        # Check if it's a key combination (contains +)
        if '+' in keys:
            # Handle key combinations like "ctrl+c"
            key_parts = [k.strip() for k in keys.split('+')]
            pyautogui.hotkey(*key_parts)
        else:
            # Regular typing
            pyautogui.write(keys, interval=0.05)
    
    def simulate_mouse(self, action: str, coordinates: 'Coordinates') -> None:
        """
        Simulate mouse action.
        
        Args:
            action: Type of mouse action ("click", "double_click", "right_click", "move")
            coordinates: Coordinates for the mouse action
        
        Raises:
            ValueError: If action type is invalid
        
        **Validates: Requirements 9.2**
        """
        if not action or not action.strip():
            raise ValueError("Mouse action cannot be empty")
        
        action = action.lower().strip()
        
        if action == "click":
            pyautogui.click(coordinates.x, coordinates.y)
        elif action == "double_click":
            pyautogui.doubleClick(coordinates.x, coordinates.y)
        elif action == "right_click":
            pyautogui.rightClick(coordinates.x, coordinates.y)
        elif action == "move":
            pyautogui.moveTo(coordinates.x, coordinates.y)
        else:
            raise ValueError(f"Unknown mouse action: {action}")
    
    def is_recording(self) -> bool:
        """
        Check if a recording is currently in progress.
        
        Returns:
            True if recording is active, False otherwise
        """
        return self._current_recording is not None
    
    def get_current_recording(self) -> Optional[RecordingSession]:
        """
        Get the current recording session if one is active.
        
        Returns:
            Current RecordingSession or None if not recording
        """
        return self._current_recording
    
    def list_saved_sequences(self) -> List[str]:
        """
        List all saved automation sequences.
        
        Returns:
            List of sequence names
        """
        return [f.stem for f in self._storage_path.glob("*.json")]
    
    def delete_sequence(self, name: str) -> None:
        """
        Delete a saved automation sequence.
        
        Args:
            name: Name of the sequence to delete
        
        Raises:
            FileNotFoundError: If sequence doesn't exist
        """
        file_path = self._storage_path / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Sequence '{name}' not found")
        
        file_path.unlink()
        
        # Remove from cache
        if name in self._sequences:
            del self._sequences[name]
