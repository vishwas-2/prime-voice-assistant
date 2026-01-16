"""
Shared pytest fixtures and configuration for PRIME Voice Assistant tests.

This file contains fixtures that are automatically available to all tests
without needing to import them explicitly.
"""

import pytest
from datetime import datetime, timedelta
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


# ============================================================================
# Basic Data Fixtures
# ============================================================================

@pytest.fixture
def sample_coordinates():
    """Provide sample coordinates for testing."""
    return Coordinates(x=100, y=200)


@pytest.fixture
def sample_size():
    """Provide sample size for testing."""
    return Size(width=800, height=600)


@pytest.fixture
def sample_entity():
    """Provide a sample entity for testing."""
    return Entity(
        entity_type="application",
        value="chrome",
        confidence=0.95
    )


@pytest.fixture
def sample_intent(sample_entity):
    """Provide a sample intent for testing."""
    return Intent(
        intent_type="launch_app",
        entities=[sample_entity],
        confidence=0.9,
        requires_clarification=False
    )


@pytest.fixture
def sample_command(sample_intent):
    """Provide a sample command for testing."""
    return Command(
        command_id="cmd_001",
        intent=sample_intent,
        parameters={"app_name": "chrome"},
        timestamp=datetime.now(),
        requires_confirmation=False
    )


@pytest.fixture
def sample_command_result():
    """Provide a sample successful command result."""
    return CommandResult(
        command_id="cmd_001",
        success=True,
        output="Application launched successfully",
        error=None,
        execution_time_ms=150
    )


@pytest.fixture
def sample_failed_command_result():
    """Provide a sample failed command result."""
    return CommandResult(
        command_id="cmd_002",
        success=False,
        output="",
        error="Application not found",
        execution_time_ms=50
    )


@pytest.fixture
def sample_session():
    """Provide a sample session for testing."""
    return Session(
        session_id="sess_001",
        user_id="user_123",
        start_time=datetime.now(),
        end_time=None
    )


@pytest.fixture
def sample_session_with_history(sample_command, sample_command_result):
    """Provide a session with command history."""
    record = CommandRecord(
        command=sample_command,
        result=sample_command_result,
        timestamp=datetime.now()
    )
    return Session(
        session_id="sess_001",
        user_id="user_123",
        start_time=datetime.now(),
        end_time=None,
        command_history=[record],
        context_state={"last_app": "chrome"}
    )


@pytest.fixture
def sample_voice_profile():
    """Provide a sample voice profile for testing."""
    return VoiceProfile(
        profile_id="voice_001",
        voice_name="en-US-Neural",
        speech_rate=1.0,
        pitch=1.0,
        volume=0.8
    )


@pytest.fixture
def sample_note():
    """Provide a sample note for testing."""
    return Note(
        note_id="note_001",
        content="Remember to buy groceries",
        tags=["personal", "shopping"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_reminder():
    """Provide a sample reminder for testing."""
    return Reminder(
        reminder_id="rem_001",
        content="Team meeting at 3 PM",
        due_time=datetime.now() + timedelta(hours=2),
        is_completed=False
    )


@pytest.fixture
def sample_action():
    """Provide a sample action for testing."""
    return Action(
        action_type="keyboard",
        parameters={"keys": "ctrl+c"},
        delay_ms=100
    )


@pytest.fixture
def sample_automation_sequence(sample_action):
    """Provide a sample automation sequence for testing."""
    action1 = sample_action
    action2 = Action(
        action_type="keyboard",
        parameters={"keys": "ctrl+v"},
        delay_ms=100
    )
    return AutomationSequence(
        sequence_id="seq_001",
        name="Copy and Paste",
        actions=[action1, action2],
        created_at=datetime.now()
    )


@pytest.fixture
def sample_process():
    """Provide a sample process for testing."""
    return Process(
        pid=1234,
        name="chrome.exe",
        cpu_percent=15.5,
        memory_mb=512.0,
        status="running"
    )


@pytest.fixture
def sample_ui_element(sample_coordinates, sample_size):
    """Provide a sample UI element for testing."""
    return UIElement(
        element_type="button",
        text="Submit",
        coordinates=sample_coordinates,
        size=sample_size
    )


# ============================================================================
# Time-related Fixtures
# ============================================================================

@pytest.fixture
def current_time():
    """Provide current timestamp for testing."""
    return datetime.now()


@pytest.fixture
def past_time():
    """Provide a timestamp from 1 hour ago."""
    return datetime.now() - timedelta(hours=1)


@pytest.fixture
def future_time():
    """Provide a timestamp 1 hour in the future."""
    return datetime.now() + timedelta(hours=1)


# ============================================================================
# Test Data Collections
# ============================================================================

@pytest.fixture
def sample_command_history(sample_command, sample_command_result):
    """Provide a list of command records for testing."""
    records = []
    for i in range(3):
        command = Command(
            command_id=f"cmd_{i:03d}",
            intent=sample_command.intent,
            parameters=sample_command.parameters,
            timestamp=datetime.now() - timedelta(minutes=i),
            requires_confirmation=False
        )
        result = CommandResult(
            command_id=f"cmd_{i:03d}",
            success=True,
            output=f"Command {i} executed",
            error=None,
            execution_time_ms=100 + i * 10
        )
        records.append(CommandRecord(
            command=command,
            result=result,
            timestamp=datetime.now() - timedelta(minutes=i)
        ))
    return records


@pytest.fixture
def sample_notes_list():
    """Provide a list of notes for testing."""
    return [
        Note(
            note_id=f"note_{i:03d}",
            content=f"Note content {i}",
            tags=["test", f"tag{i}"],
            created_at=datetime.now() - timedelta(days=i),
            updated_at=datetime.now() - timedelta(days=i)
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_reminders_list():
    """Provide a list of reminders for testing."""
    return [
        Reminder(
            reminder_id=f"rem_{i:03d}",
            content=f"Reminder {i}",
            due_time=datetime.now() + timedelta(hours=i),
            is_completed=False
        )
        for i in range(5)
    ]


# ============================================================================
# Hypothesis Strategies (for property-based testing)
# ============================================================================

# Note: Hypothesis strategies are typically defined in the test files themselves,
# but you can define reusable strategies here if needed.

# Example:
# from hypothesis import strategies as st
# 
# @st.composite
# def entity_strategy(draw):
#     """Generate random Entity instances."""
#     return Entity(
#         entity_type=draw(st.text(min_size=1, max_size=50)),
#         value=draw(st.text(max_size=100)),
#         confidence=draw(st.floats(min_value=0.0, max_value=1.0))
#     )


# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "property: Property-based tests using Hypothesis"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "voice: Tests requiring voice input/output"
    )
    config.addinivalue_line(
        "markers", "system: Tests requiring system access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests in property/ directory
        if "property" in str(item.fspath):
            item.add_marker(pytest.mark.property)
        # Auto-mark tests in unit/ directory
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Auto-mark tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
