"""Property-based tests for Context Engine.

**Validates: Requirements 3.1, 3.3**

Property 9: Context Awareness
For any command issued during a session, the Context_Engine should consider
previous commands from the same session when processing.

Property 11: Reference Resolution
For any pronoun reference ("it", "that", "the previous one") in a command,
the Context_Engine should resolve it to a specific entity from conversation history.

This property test verifies that:
- Commands are processed with awareness of session history
- References are resolved to entities from previous commands
- Context improves intent parsing accuracy
- Multiple references can be resolved in sequence
"""

import tempfile
import shutil
from datetime import datetime
from hypothesis import given, strategies as st, settings
from prime.nlp import IntentParser, ContextEngine
from prime.persistence import MemoryManager
from prime.models import (
    Session, Command, CommandResult, Intent, Entity,
    CommandRecord
)


# Strategy for generating valid entity types
entity_types = st.sampled_from([
    "application", "file_name", "file_path", "process_name",
    "network_name", "device_name", "quoted_string"
])


# Strategy for generating intent types
intent_types = st.sampled_from([
    "launch_app", "adjust_volume", "search_files", "create_file",
    "delete_file", "move_file", "terminate_process", "read_screen"
])


# Strategy for generating reference words
reference_words = st.sampled_from([
    "it", "that", "this", "the previous one", "the last one"
])


class TestProperty9ContextAwareness:
    """Property 9: Context Awareness.
    
    **Validates: Requirements 3.1**
    
    For any command issued during a session, the Context_Engine should
    consider previous commands from the same session when processing.
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        intent_type=intent_types,
        num_history_commands=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=15)
    def test_property_9_context_considers_history(
        self, user_id, session_id, intent_type, num_history_commands
    ):
        """Property 9: Commands are processed with session history context.
        
        **Validates: Requirements 3.1**
        
        For any command issued during a session, the Context_Engine should
        consider previous commands in the current session.
        
        This test verifies that:
        1. A session with command history is created
        2. A new command is processed
        3. The context engine has access to the history
        4. Processing completes successfully with context
        """
        # Create temporary storage
        temp_storage = tempfile.mkdtemp()
        
        try:
            # Create context engine
            memory_manager = MemoryManager(storage_dir=temp_storage)
            intent_parser = IntentParser()
            context_engine = ContextEngine(intent_parser, memory_manager)
            
            # Create session with history
            session = Session(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={}
            )
            
            # Add commands to history
            for i in range(num_history_commands):
                intent = Intent(
                    intent_type=intent_type,
                    entities=[Entity("application", f"App{i}", 0.9)],
                    confidence=0.9,
                    requires_clarification=False
                )
                command = Command(
                    command_id=f"cmd-{i:03d}",
                    intent=intent,
                    parameters={},
                    timestamp=datetime.now(),
                    requires_confirmation=False
                )
                result = CommandResult(
                    command_id=f"cmd-{i:03d}",
                    success=True,
                    output=f"Success {i}",
                    error=None,
                    execution_time_ms=100
                )
                
                context_engine.add_to_history(command, result, session)
            
            # Process a new command with context
            text = "open Chrome"
            intent = context_engine.process_command(text, session)
            
            # Verify processing succeeded
            assert intent is not None
            assert isinstance(intent, Intent)
            
            # Verify history was considered (session has commands)
            assert len(session.command_history) == num_history_commands
        finally:
            # Cleanup
            shutil.rmtree(temp_storage, ignore_errors=True)
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=10)
    def test_property_9_empty_history_still_processes(
        self, user_id, session_id
    ):
        """Property 9: Commands process correctly even with empty history.
        
        **Validates: Requirements 3.1**
        
        The Context_Engine should handle sessions with no history gracefully.
        """
        # Create temporary storage
        temp_storage = tempfile.mkdtemp()
        
        try:
            # Create context engine
            memory_manager = MemoryManager(storage_dir=temp_storage)
            intent_parser = IntentParser()
            context_engine = ContextEngine(intent_parser, memory_manager)
            
            # Create session with no history
            session = Session(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={}
            )
            
            # Process a command
            text = "open Chrome"
            intent = context_engine.process_command(text, session)
            
            # Verify processing succeeded
            assert intent is not None
            assert isinstance(intent, Intent)
            assert intent.intent_type == "launch_app"
        finally:
            # Cleanup
            shutil.rmtree(temp_storage, ignore_errors=True)


class TestProperty11ReferenceResolution:
    """Property 11: Reference Resolution.
    
    **Validates: Requirements 3.3**
    
    For any pronoun reference ("it", "that", "the previous one") in a command,
    the Context_Engine should resolve it to a specific entity from conversation history.
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        entity_type=entity_types,
        entity_value=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='.-_'
        )),
        reference=reference_words
    )
    @settings(max_examples=20)
    def test_property_11_reference_resolves_to_entity(
        self, user_id, session_id, entity_type,
        entity_value, reference
    ):
        """Property 11: References resolve to entities from history.
        
        **Validates: Requirements 3.3**
        
        For any pronoun reference in a command, the Context_Engine should
        resolve it to a specific entity from conversation history.
        
        This test verifies that:
        1. A command with an entity is added to history
        2. A reference is resolved
        3. The resolved entity matches the historical entity
        """
        # Create temporary storage
        temp_storage = tempfile.mkdtemp()
        
        try:
            # Create context engine
            memory_manager = MemoryManager(storage_dir=temp_storage)
            intent_parser = IntentParser()
            context_engine = ContextEngine(intent_parser, memory_manager)
            
            # Create session
            session = Session(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={}
            )
            
            # Add a command with an entity to history
            intent = Intent(
                intent_type="search_files",
                entities=[Entity(entity_type, entity_value, 0.9)],
                confidence=0.9,
                requires_clarification=False
            )
            command = Command(
                command_id="cmd-001",
                intent=intent,
                parameters={},
                timestamp=datetime.now(),
                requires_confirmation=False
            )
            result = CommandResult(
                command_id="cmd-001",
                success=True,
                output=f"Found {entity_value}",
                error=None,
                execution_time_ms=50
            )
            
            context_engine.add_to_history(command, result, session)
            
            # Resolve the reference
            resolved_entity = context_engine.resolve_reference(reference, session)
            
            # Verify resolution succeeded
            assert resolved_entity is not None
            assert isinstance(resolved_entity, Entity)
            
            # Verify the resolved entity relates to the historical entity
            # (either the entity itself or the output)
            assert (
                entity_value in str(resolved_entity.value) or
                str(resolved_entity.value) in entity_value or
                f"Found {entity_value}" in str(resolved_entity.value)
            )
        finally:
            # Cleanup
            shutil.rmtree(temp_storage, ignore_errors=True)
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        reference=reference_words
    )
    @settings(max_examples=10)
    def test_property_11_reference_with_no_history_returns_none(
        self, user_id, session_id, reference
    ):
        """Property 11: References with no history return None.
        
        **Validates: Requirements 3.3**
        
        When there is no conversation history, reference resolution
        should return None gracefully.
        """
        # Create temporary storage
        temp_storage = tempfile.mkdtemp()
        
        try:
            # Create context engine
            memory_manager = MemoryManager(storage_dir=temp_storage)
            intent_parser = IntentParser()
            context_engine = ContextEngine(intent_parser, memory_manager)
            
            # Create session with no history
            session = Session(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={}
            )
            
            # Try to resolve reference
            resolved_entity = context_engine.resolve_reference(reference, session)
            
            # Should return None
            assert resolved_entity is None
        finally:
            # Cleanup
            shutil.rmtree(temp_storage, ignore_errors=True)
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        num_entities=st.integers(min_value=2, max_value=5),
        reference=reference_words
    )
    @settings(max_examples=10)
    def test_property_11_reference_resolves_to_most_recent(
        self, user_id, session_id, num_entities, reference
    ):
        """Property 11: References resolve to most recent entity.
        
        **Validates: Requirements 3.3**
        
        When multiple entities exist in history, references should
        resolve to the most recent relevant entity.
        """
        # Create temporary storage
        temp_storage = tempfile.mkdtemp()
        
        try:
            # Create context engine
            memory_manager = MemoryManager(storage_dir=temp_storage)
            intent_parser = IntentParser()
            context_engine = ContextEngine(intent_parser, memory_manager)
            
            # Create session
            session = Session(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                end_time=None,
                command_history=[],
                context_state={}
            )
            
            # Add multiple commands with entities
            entity_values = []
            for i in range(num_entities):
                entity_value = f"Entity{i}"
                entity_values.append(entity_value)
                
                intent = Intent(
                    intent_type="search_files",
                    entities=[Entity("file_name", entity_value, 0.9)],
                    confidence=0.9,
                    requires_clarification=False
                )
                command = Command(
                    command_id=f"cmd-{i:03d}",
                    intent=intent,
                    parameters={},
                    timestamp=datetime.now(),
                    requires_confirmation=False
                )
                result = CommandResult(
                    command_id=f"cmd-{i:03d}",
                    success=True,
                    output=f"Found {entity_value}",
                    error=None,
                    execution_time_ms=50
                )
                
                context_engine.add_to_history(command, result, session)
            
            # Resolve reference
            resolved_entity = context_engine.resolve_reference(reference, session)
            
            # Should resolve to most recent entity
            assert resolved_entity is not None
            most_recent_value = entity_values[-1]
            assert (
                most_recent_value in str(resolved_entity.value) or
                f"Found {most_recent_value}" in str(resolved_entity.value)
            )
        finally:
            # Cleanup
            shutil.rmtree(temp_storage, ignore_errors=True)
