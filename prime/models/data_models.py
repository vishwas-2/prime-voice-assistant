"""
Core data models for PRIME Voice Assistant.

This module defines all the dataclasses used throughout the PRIME system,
including session management, command processing, voice profiles, notes,
reminders, automation, and system monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Coordinates:
    """Represents x, y coordinates on the screen."""
    x: int
    y: int


@dataclass
class Size:
    """Represents width and height dimensions."""
    width: int
    height: int


@dataclass
class Entity:
    """Represents an extracted entity from a command."""
    entity_type: str  # e.g., "application", "file", "setting"
    value: Any
    confidence: float


@dataclass
class Intent:
    """Represents the parsed intent of a user command."""
    intent_type: str  # e.g., "launch_app", "adjust_volume", "search_files"
    entities: List[Entity]
    confidence: float
    requires_clarification: bool


@dataclass
class Command:
    """Represents a command to be executed."""
    command_id: str
    intent: Intent
    parameters: Dict[str, Any]
    timestamp: datetime
    requires_confirmation: bool


@dataclass
class CommandResult:
    """Represents the result of a command execution."""
    command_id: str
    success: bool
    output: str
    error: Optional[str]
    execution_time_ms: int


@dataclass
class CommandRecord:
    """Represents a command and its result in history."""
    command: Command
    result: CommandResult
    timestamp: datetime


@dataclass
class Session:
    """Represents a user session with PRIME."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    command_history: List[CommandRecord] = field(default_factory=list)
    context_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceProfile:
    """Represents a voice configuration profile."""
    profile_id: str
    voice_name: str
    speech_rate: float
    pitch: float
    volume: float


@dataclass
class Note:
    """Represents a user note."""
    note_id: str
    content: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class Reminder:
    """Represents a time-based reminder."""
    reminder_id: str
    content: str
    due_time: datetime
    is_completed: bool


@dataclass
class Action:
    """Represents a single action in an automation sequence."""
    action_type: str  # "keyboard", "mouse", "command"
    parameters: Dict[str, Any]
    delay_ms: int


@dataclass
class AutomationSequence:
    """Represents a sequence of automated actions."""
    sequence_id: str
    name: str
    actions: List[Action]
    created_at: datetime


@dataclass
class Process:
    """Represents a system process with resource usage information."""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str


@dataclass
class UIElement:
    """Represents a UI element identified on the screen."""
    element_type: str  # "button", "text_field", "menu", etc.
    text: str
    coordinates: Coordinates
    size: Size


@dataclass
class ApplicationUsage:
    """Represents usage pattern data for an application."""
    application_name: str
    launch_count: int
    last_launched: datetime
    first_launched: datetime


@dataclass
class FileMetadata:
    """Represents metadata information about a file."""
    path: str
    name: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    is_directory: bool
    extension: Optional[str]
    permissions: str
