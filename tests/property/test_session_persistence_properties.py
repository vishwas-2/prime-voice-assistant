"""Property-based tests for session persistence.

**Validates: Requirements 3.5, 3.6**

Property 13: Session Persistence Timing
For any session that ends, the Memory_Manager should save the session context
to persistent storage within 5 seconds.

Property 14: Session Retention Duration
For any session saved by the Memory_Manager, it should remain retrievable
for at least 30 days.

These property tests verify that:
- Sessions are saved quickly (within 5 seconds)
- Sessions persist for the required retention period
- Session data remains intact over time
"""

import pytest
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from prime.persistence import MemoryManager
from prime.models.data_models import (
    Session, CommandRecord, Command, CommandResult,
    Intent, Entity
)


# Strategy for generating valid session IDs
session_id_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    ),
    min_size=1,
    max_size=50
)

# Strategy for generating valid user IDs
user_id_strategy = st.text(min_size=1, max_size=50)

# Strategy for generating context state
context_state_strategy = st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, width=32),
        st.text(max_size=50)
    ),
    max_size=5
)


def create_simple_session(session_id: str, user_id: str, context_state: dict) -> Session:
    """Create a simple session for testing.
    
    Args:
        session_id: The session identifier
        user_id: The user identifier
        context_state: The context state dictionary
        
    Returns:
        A Session object
    """
    return Session(
        session_id=session_id,
        user_id=user_id,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(minutes=30),
        command_history=[],
        context_state=context_state
    )


class TestSessionPersistenceTimingProperty:
    """Property-based tests for session persistence timing (Property 13)."""

    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        context_state=context_state_strategy
    )
    @settings(max_examples=20)
    def test_property_13_session_persistence_timing(
        self, session_id, user_id, context_state
    ):
        """Property 13: Session Persistence Timing.
        
        **Validates: Requirements 3.5**
        
        For any session that ends, the Memory_Manager should save the session
        context to persistent storage within 5 seconds.
        
        This test verifies that:
        1. A session can be saved
        2. The save operation completes within 5 seconds
        3. The saved session can be immediately retrieved
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Create a session
            session = create_simple_session(session_id, user_id, context_state)
            
            # Measure save time
            start_time = time.time()
            manager.save_session(session)
            end_time = time.time()
            
            # Verify save completed within 5 seconds
            save_duration = end_time - start_time
            assert save_duration < 5.0, f"Session save took {save_duration:.3f}s, exceeds 5s limit"
            
            # Verify the session was actually saved and can be retrieved
            loaded_session = manager.load_session(session_id)
            assert loaded_session is not None
            assert loaded_session.session_id == session_id
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        context_state=context_state_strategy
    )
    @settings(max_examples=10)
    def test_property_13_session_persistence_timing_with_command_history(
        self, session_id, user_id, context_state
    ):
        """Property 13: Session persistence timing with command history.
        
        **Validates: Requirements 3.5**
        
        Even with command history, session save should complete within 5 seconds.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Create a session with command history
            session = create_simple_session(session_id, user_id, context_state)
            
            # Add some command records
            for i in range(5):
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
                    timestamp=datetime.now(),
                    requires_confirmation=False
                )
                
                result = CommandResult(
                    command_id=f"cmd_{i}",
                    success=True,
                    output=f"App{i} launched",
                    error=None,
                    execution_time_ms=100
                )
                
                record = CommandRecord(
                    command=command,
                    result=result,
                    timestamp=datetime.now()
                )
                
                session.command_history.append(record)
            
            # Measure save time
            start_time = time.time()
            manager.save_session(session)
            end_time = time.time()
            
            # Verify save completed within 5 seconds
            save_duration = end_time - start_time
            assert save_duration < 5.0, f"Session save took {save_duration:.3f}s, exceeds 5s limit"
            
            # Verify the session was saved correctly
            loaded_session = manager.load_session(session_id)
            assert len(loaded_session.command_history) == 5
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        session_ids=st.lists(session_id_strategy, min_size=1, max_size=10, unique=True),
        user_id=user_id_strategy
    )
    @settings(max_examples=5)
    def test_property_13_multiple_sessions_save_within_time_limit(
        self, session_ids, user_id
    ):
        """Property 13: Multiple sessions can be saved within time limit.
        
        **Validates: Requirements 3.5**
        
        Each session save operation should complete within 5 seconds,
        even when saving multiple sessions.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Save multiple sessions, each within time limit
            for session_id in session_ids:
                session = create_simple_session(session_id, user_id, {})
                
                start_time = time.time()
                manager.save_session(session)
                end_time = time.time()
                
                save_duration = end_time - start_time
                assert save_duration < 5.0, f"Session save took {save_duration:.3f}s, exceeds 5s limit"
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)


class TestSessionRetentionDurationProperty:
    """Property-based tests for session retention duration (Property 14)."""

    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        context_state=context_state_strategy
    )
    @settings(max_examples=20)
    def test_property_14_session_retention_duration(
        self, session_id, user_id, context_state
    ):
        """Property 14: Session Retention Duration.
        
        **Validates: Requirements 3.6**
        
        For any session saved by the Memory_Manager, it should remain
        retrievable for at least 30 days.
        
        This test verifies that:
        1. A session can be saved
        2. The session file exists on disk
        3. The session can be retrieved after being saved
        4. The session data remains intact
        
        Note: We simulate the 30-day retention by verifying the session
        persists on disk and can be loaded. In a real system, this would
        involve checking file timestamps and retention policies.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Create and save a session
            session = create_simple_session(session_id, user_id, context_state)
            manager.save_session(session)
            
            # Verify the session file exists
            session_file = Path(temp_storage_dir) / 'sessions' / f'{session_id}.json'
            assert session_file.exists(), "Session file should exist on disk"
            
            # Verify the session can be loaded
            loaded_session = manager.load_session(session_id)
            assert loaded_session is not None
            assert loaded_session.session_id == session_id
            assert loaded_session.user_id == user_id
            assert loaded_session.context_state == context_state
            
            # Verify the session persists across manager instances
            # (simulating a new session/day)
            manager2 = MemoryManager(
                encryption_key=manager.encryption_key,
                storage_dir=temp_storage_dir
            )
            loaded_session2 = manager2.load_session(session_id)
            assert loaded_session2 is not None
            assert loaded_session2.session_id == session_id
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        days_old=st.integers(min_value=0, max_value=30)
    )
    @settings(max_examples=10)
    def test_property_14_session_retention_with_old_timestamps(
        self, session_id, user_id, days_old
    ):
        """Property 14: Sessions with old timestamps remain retrievable.
        
        **Validates: Requirements 3.6**
        
        Sessions created in the past (up to 30 days) should remain
        retrievable.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Create a session with an old timestamp
            old_start_time = datetime.now() - timedelta(days=days_old)
            old_end_time = old_start_time + timedelta(minutes=30)
            
            session = Session(
                session_id=session_id,
                user_id=user_id,
                start_time=old_start_time,
                end_time=old_end_time,
                command_history=[],
                context_state={"days_old": days_old}
            )
            
            # Save the session
            manager.save_session(session)
            
            # Verify the session can be loaded
            loaded_session = manager.load_session(session_id)
            assert loaded_session is not None
            assert loaded_session.session_id == session_id
            assert loaded_session.start_time == old_start_time
            assert loaded_session.end_time == old_end_time
            
            # Verify the session file exists
            session_file = Path(temp_storage_dir) / 'sessions' / f'{session_id}.json'
            assert session_file.exists()
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        session_ids=st.lists(session_id_strategy, min_size=1, max_size=10, unique=True),
        user_id=user_id_strategy
    )
    @settings(max_examples=5)
    def test_property_14_multiple_sessions_retention(
        self, session_ids, user_id
    ):
        """Property 14: Multiple sessions are retained.
        
        **Validates: Requirements 3.6**
        
        All saved sessions should remain retrievable, not just the most recent.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Save multiple sessions
            for session_id in session_ids:
                session = create_simple_session(session_id, user_id, {"id": session_id})
                manager.save_session(session)
            
            # Verify all sessions can be loaded
            for session_id in session_ids:
                loaded_session = manager.load_session(session_id)
                assert loaded_session is not None
                assert loaded_session.session_id == session_id
                assert loaded_session.context_state["id"] == session_id
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        context_state=context_state_strategy
    )
    @settings(max_examples=10)
    def test_property_14_session_data_integrity_over_time(
        self, session_id, user_id, context_state
    ):
        """Property 14: Session data integrity is maintained over time.
        
        **Validates: Requirements 3.6**
        
        Session data should remain intact and uncorrupted over the
        retention period.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Create and save a session
            session = create_simple_session(session_id, user_id, context_state)
            manager.save_session(session)
            
            # Load the session multiple times (simulating access over time)
            for _ in range(5):
                loaded_session = manager.load_session(session_id)
                
                # Verify data integrity
                assert loaded_session.session_id == session_id
                assert loaded_session.user_id == user_id
                assert loaded_session.context_state == context_state
                assert loaded_session.start_time == session.start_time
                assert loaded_session.end_time == session.end_time
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy
    )
    @settings(max_examples=10)
    def test_property_14_session_with_command_history_retention(
        self, session_id, user_id
    ):
        """Property 14: Sessions with command history are retained.
        
        **Validates: Requirements 3.6**
        
        Sessions with complex command history should remain retrievable
        with all data intact.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Create a session with command history
            session = create_simple_session(session_id, user_id, {})
            
            # Add command records
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
                    timestamp=datetime.now(),
                    requires_confirmation=False
                )
                
                result = CommandResult(
                    command_id=f"cmd_{i}",
                    success=True,
                    output=f"App{i} launched",
                    error=None,
                    execution_time_ms=100
                )
                
                record = CommandRecord(
                    command=command,
                    result=result,
                    timestamp=datetime.now()
                )
                
                session.command_history.append(record)
            
            # Save the session
            manager.save_session(session)
            
            # Verify the session can be loaded with all command history
            loaded_session = manager.load_session(session_id)
            assert loaded_session is not None
            assert len(loaded_session.command_history) == 3
            
            # Verify command history details
            for i, record in enumerate(loaded_session.command_history):
                assert record.command.command_id == f"cmd_{i}"
                assert record.result.output == f"App{i} launched"
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)
