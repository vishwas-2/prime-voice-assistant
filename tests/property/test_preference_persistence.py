"""Property-based tests for preference persistence.

**Validates: Requirements 3.2**

Property 10: Preference Persistence Round-Trip
For any user preference stored by the Memory_Manager, retrieving it in a new
session should return the same value.

This property test verifies that:
- Any JSON-serializable value can be stored and retrieved
- Preferences persist across different manager instances (simulating sessions)
- The round-trip preserves the exact value and type
- Different users maintain separate preference spaces
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from prime.persistence import MemoryManager


# Strategy for generating valid JSON-serializable values
json_values = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1_000_000, max_value=1_000_000),
        st.floats(allow_nan=False, allow_infinity=False, width=32),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            children,
            max_size=10
        )
    ),
    max_leaves=20
)


class TestPreferencePersistenceProperty:
    """Property-based tests for preference persistence."""

    @given(
        user_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50),
        value=json_values
    )
    @settings(max_examples=20)
    def test_property_10_preference_persistence_round_trip(
        self, user_id, key, value
    ):
        """Property 10: Preference Persistence Round-Trip.
        
        **Validates: Requirements 3.2**
        
        For any user preference stored by the Memory_Manager, retrieving it
        in a new session should return the same value.
        
        This test verifies that:
        1. A preference can be stored with any valid JSON-serializable value
        2. Creating a new manager instance (simulating a new session)
        3. The retrieved value exactly matches the stored value
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create first manager instance (first session)
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            
            # Store the preference
            manager1.store_preference(key, value, user_id)
            
            # Create second manager instance (new session) with same key
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            
            # Retrieve the preference in the new session
            retrieved_value = manager2.get_preference(key, user_id)
            
            # Verify the value persists exactly
            assert retrieved_value == value
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        preferences=st.dictionaries(
            st.text(min_size=1, max_size=50),
            json_values,
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=10)
    def test_property_10_multiple_preferences_persist(
        self, user_id, preferences
    ):
        """Property 10: Multiple preferences persist across sessions.
        
        **Validates: Requirements 3.2**
        
        For any set of user preferences stored by the Memory_Manager,
        all preferences should be retrievable in a new session.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create first manager instance (first session)
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            
            # Store all preferences
            for key, value in preferences.items():
                manager1.store_preference(key, value, user_id)
            
            # Create second manager instance (new session)
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            
            # Verify all preferences persist
            for key, expected_value in preferences.items():
                retrieved_value = manager2.get_preference(key, user_id)
                assert retrieved_value == expected_value
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user1_id=st.text(min_size=1, max_size=50),
        user2_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50),
        value1=json_values,
        value2=json_values
    )
    @settings(max_examples=10)
    def test_property_10_different_users_separate_persistence(
        self, user1_id, user2_id, key, value1, value2
    ):
        """Property 10: Different users have separate persistent preferences.
        
        **Validates: Requirements 3.2**
        
        For any two different users, their preferences should persist
        independently across sessions.
        """
        # Ensure users are different
        assume(user1_id != user2_id)
        
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create first manager instance (first session)
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            
            # Store preferences for both users
            manager1.store_preference(key, value1, user1_id)
            manager1.store_preference(key, value2, user2_id)
            
            # Create second manager instance (new session)
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            
            # Verify each user's preference persists correctly
            assert manager2.get_preference(key, user1_id) == value1
            assert manager2.get_preference(key, user2_id) == value2
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50),
        initial_value=json_values,
        updated_value=json_values
    )
    @settings(max_examples=10)
    def test_property_10_preference_updates_persist(
        self, user_id, key, initial_value, updated_value
    ):
        """Property 10: Preference updates persist across sessions.
        
        **Validates: Requirements 3.2**
        
        When a preference is updated, the new value should persist
        in subsequent sessions.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create first manager instance
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            
            # Store initial preference
            manager1.store_preference(key, initial_value, user_id)
            
            # Update the preference
            manager1.store_preference(key, updated_value, user_id)
            
            # Create second manager instance (new session)
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            
            # Verify the updated value persists (not the initial value)
            retrieved_value = manager2.get_preference(key, user_id)
            assert retrieved_value == updated_value
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50),
        value=json_values
    )
    @settings(max_examples=10)
    def test_property_10_preference_survives_multiple_sessions(
        self, user_id, key, value
    ):
        """Property 10: Preferences survive multiple session transitions.
        
        **Validates: Requirements 3.2**
        
        A preference should remain accessible across multiple
        manager instance creations (multiple sessions).
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            encryption_key = None
            
            # Session 1: Store preference
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            manager1.store_preference(key, value, user_id)
            
            # Session 2: Verify persistence
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            assert manager2.get_preference(key, user_id) == value
            
            # Session 3: Verify persistence again
            manager3 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            assert manager3.get_preference(key, user_id) == value
            
            # Session 4: Verify persistence one more time
            manager4 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            assert manager4.get_preference(key, user_id) == value
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=10)
    def test_property_10_nonexistent_preference_returns_none(
        self, user_id, key
    ):
        """Property 10: Non-existent preferences return None consistently.
        
        **Validates: Requirements 3.2**
        
        For any preference that was never stored, get_preference
        should return None across all sessions.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            encryption_key = None
            
            # Session 1: Check non-existent preference
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            assert manager1.get_preference(key, user_id) is None
            
            # Session 2: Check again in new session
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            assert manager2.get_preference(key, user_id) is None
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50),
        value=json_values
    )
    @settings(max_examples=10)
    def test_property_10_preference_type_preservation(
        self, user_id, key, value
    ):
        """Property 10: Preference types are preserved across sessions.
        
        **Validates: Requirements 3.2**
        
        The type of a stored preference should be preserved exactly
        when retrieved in a new session.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create first manager instance
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            
            # Store preference
            manager1.store_preference(key, value, user_id)
            
            # Create second manager instance (new session)
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            
            # Retrieve preference
            retrieved_value = manager2.get_preference(key, user_id)
            
            # Verify type is preserved
            assert type(retrieved_value) == type(value)
            assert retrieved_value == value
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)
