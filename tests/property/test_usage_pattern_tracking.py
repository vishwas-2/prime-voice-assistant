"""Property-based tests for usage pattern tracking.

**Validates: Requirements 3.4**

Property 12: Usage Pattern Tracking
For any application launched by a user, the Memory_Manager should record the
usage and make it retrievable.

This property test verifies that:
- Any application launch is recorded with accurate metadata
- Usage data persists across different manager instances (simulating sessions)
- Launch counts are accurately incremented
- Timestamps are properly maintained
- Different users maintain separate usage patterns
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings
from prime.persistence import MemoryManager
from prime.models.data_models import ApplicationUsage


class TestUsagePatternTrackingProperty:
    """Property-based tests for usage pattern tracking."""

    @given(
        user_id=st.text(min_size=1, max_size=50),
        application_name=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=20)
    def test_property_12_application_usage_recorded_and_retrievable(
        self, user_id, application_name
    ):
        """Property 12: Application usage is recorded and retrievable.
        
        **Validates: Requirements 3.4**
        
        For any application launched by a user, the Memory_Manager should
        record the usage and make it retrievable.
        
        This test verifies that:
        1. An application launch can be recorded
        2. The usage data can be retrieved
        3. The retrieved data matches the recorded application
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record application usage
            manager.record_application_usage(application_name, user_id)
            
            # Retrieve the usage data
            usage = manager.get_application_usage(application_name, user_id)
            
            # Verify usage was recorded and is retrievable
            assert usage is not None
            assert isinstance(usage, ApplicationUsage)
            assert usage.application_name == application_name
            assert usage.launch_count == 1
            assert isinstance(usage.first_launched, datetime)
            assert isinstance(usage.last_launched, datetime)
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        application_name=st.text(min_size=1, max_size=100),
        launch_count=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=20)
    def test_property_12_launch_count_increments_correctly(
        self, user_id, application_name, launch_count
    ):
        """Property 12: Launch count increments correctly for multiple launches.
        
        **Validates: Requirements 3.4**
        
        For any number of application launches, the Memory_Manager should
        accurately track the count.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record multiple application launches
            for _ in range(launch_count):
                manager.record_application_usage(application_name, user_id)
            
            # Retrieve the usage data
            usage = manager.get_application_usage(application_name, user_id)
            
            # Verify launch count is correct
            assert usage is not None
            assert usage.launch_count == launch_count
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        application_name=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=20)
    def test_property_12_usage_persists_across_sessions(
        self, user_id, application_name
    ):
        """Property 12: Usage data persists across manager instances (sessions).
        
        **Validates: Requirements 3.4**
        
        For any application usage recorded, the data should persist when
        a new manager instance is created (simulating a new session).
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Session 1: Record usage
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            manager1.record_application_usage(application_name, user_id)
            
            # Get usage from first session
            usage1 = manager1.get_application_usage(application_name, user_id)
            assert usage1 is not None
            
            # Session 2: Verify persistence
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            usage2 = manager2.get_application_usage(application_name, user_id)
            
            # Verify usage persists
            assert usage2 is not None
            assert usage2.application_name == usage1.application_name
            assert usage2.launch_count == usage1.launch_count
            assert usage2.first_launched == usage1.first_launched
            assert usage2.last_launched == usage1.last_launched
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        application_name=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=15)
    def test_property_12_timestamps_maintained_correctly(
        self, user_id, application_name
    ):
        """Property 12: First and last launch timestamps are maintained correctly.
        
        **Validates: Requirements 3.4**
        
        For any application usage, first_launched should remain constant
        while last_launched should update with each launch.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record first launch
            before_first = datetime.now()
            manager.record_application_usage(application_name, user_id)
            after_first = datetime.now()
            
            usage1 = manager.get_application_usage(application_name, user_id)
            assert usage1 is not None
            
            # Verify first launch timestamp is within expected range
            assert before_first <= usage1.first_launched <= after_first
            assert before_first <= usage1.last_launched <= after_first
            assert usage1.first_launched == usage1.last_launched
            
            # Small delay to ensure different timestamp
            import time
            time.sleep(0.01)
            
            # Record second launch
            before_second = datetime.now()
            manager.record_application_usage(application_name, user_id)
            after_second = datetime.now()
            
            usage2 = manager.get_application_usage(application_name, user_id)
            assert usage2 is not None
            
            # Verify first_launched stayed the same
            assert usage2.first_launched == usage1.first_launched
            
            # Verify last_launched was updated
            assert usage2.last_launched > usage1.last_launched
            assert before_second <= usage2.last_launched <= after_second
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user1_id=st.text(min_size=1, max_size=50),
        user2_id=st.text(min_size=1, max_size=50),
        application_name=st.text(min_size=1, max_size=100),
        user1_launches=st.integers(min_value=1, max_value=50),
        user2_launches=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=15)
    def test_property_12_different_users_separate_usage_tracking(
        self, user1_id, user2_id, application_name, user1_launches, user2_launches
    ):
        """Property 12: Different users have separate usage tracking.
        
        **Validates: Requirements 3.4**
        
        For any two different users, their application usage should be
        tracked independently.
        """
        # Ensure users are different
        assume(user1_id != user2_id)
        
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage for user 1
            for _ in range(user1_launches):
                manager.record_application_usage(application_name, user1_id)
            
            # Record usage for user 2
            for _ in range(user2_launches):
                manager.record_application_usage(application_name, user2_id)
            
            # Retrieve usage for both users
            usage1 = manager.get_application_usage(application_name, user1_id)
            usage2 = manager.get_application_usage(application_name, user2_id)
            
            # Verify separate tracking
            assert usage1 is not None
            assert usage2 is not None
            assert usage1.launch_count == user1_launches
            assert usage2.launch_count == user2_launches
            
            # Verify timestamps are independent
            assert usage1.first_launched != usage2.first_launched or user1_launches == user2_launches == 1
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        applications=st.lists(
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=15)
    def test_property_12_multiple_applications_tracked_independently(
        self, user_id, applications
    ):
        """Property 12: Multiple applications are tracked independently.
        
        **Validates: Requirements 3.4**
        
        For any set of different applications, each should have
        independent usage tracking.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage for each application (different number of launches)
            expected_counts = {}
            for i, app_name in enumerate(applications):
                launch_count = i + 1  # 1, 2, 3, ...
                expected_counts[app_name] = launch_count
                for _ in range(launch_count):
                    manager.record_application_usage(app_name, user_id)
            
            # Verify each application has correct independent count
            for app_name, expected_count in expected_counts.items():
                usage = manager.get_application_usage(app_name, user_id)
                assert usage is not None
                assert usage.application_name == app_name
                assert usage.launch_count == expected_count
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        application_name=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10)
    def test_property_12_nonexistent_usage_returns_none(
        self, user_id, application_name
    ):
        """Property 12: Non-existent usage data returns None.
        
        **Validates: Requirements 3.4**
        
        For any application that was never launched, get_application_usage
        should return None.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Try to retrieve usage for application that was never launched
            usage = manager.get_application_usage(application_name, user_id)
            
            # Verify None is returned
            assert usage is None
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        applications=st.lists(
            st.text(min_size=1, max_size=100),
            min_size=2,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=10)
    def test_property_12_get_all_usage_returns_all_applications(
        self, user_id, applications
    ):
        """Property 12: get_all_application_usage returns all tracked applications.
        
        **Validates: Requirements 3.4**
        
        For any set of applications launched by a user, get_all_application_usage
        should return usage data for all of them.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage for each application
            for app_name in applications:
                manager.record_application_usage(app_name, user_id)
            
            # Get all usage data
            all_usage = manager.get_all_application_usage(user_id)
            
            # Verify all applications are returned
            assert len(all_usage) == len(applications)
            returned_app_names = {usage.application_name for usage in all_usage}
            assert returned_app_names == set(applications)
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    @given(
        user_id=st.text(min_size=1, max_size=50),
        applications=st.lists(
            st.text(min_size=1, max_size=100),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=10)
    def test_property_12_get_all_usage_sorted_by_launch_count(
        self, user_id, applications
    ):
        """Property 12: get_all_application_usage returns sorted by launch count.
        
        **Validates: Requirements 3.4**
        
        For any set of applications with different launch counts,
        get_all_application_usage should return them sorted by most used first.
        """
        # Create temporary storage directory
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # Create manager instance
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage with increasing counts
            for i, app_name in enumerate(applications):
                launch_count = i + 1
                for _ in range(launch_count):
                    manager.record_application_usage(app_name, user_id)
            
            # Get all usage data
            all_usage = manager.get_all_application_usage(user_id)
            
            # Verify sorted by launch_count (descending)
            assert len(all_usage) == len(applications)
            for i in range(len(all_usage) - 1):
                assert all_usage[i].launch_count >= all_usage[i + 1].launch_count
        finally:
            # Cleanup
            shutil.rmtree(temp_storage_dir, ignore_errors=True)
