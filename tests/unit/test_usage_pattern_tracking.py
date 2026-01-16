"""Unit tests for usage pattern tracking functionality.

These tests complement the property-based tests by testing specific
edge cases and error conditions for the usage pattern tracking feature.
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from prime.persistence import MemoryManager
from prime.models.data_models import ApplicationUsage


class TestUsagePatternTracking:
    """Unit tests for usage pattern tracking."""

    def test_record_application_usage_creates_new_entry(self):
        """Test that recording usage for a new application creates an entry."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage
            manager.record_application_usage("Chrome", "user1")
            
            # Verify entry was created
            usage = manager.get_application_usage("Chrome", "user1")
            assert usage is not None
            assert usage.application_name == "Chrome"
            assert usage.launch_count == 1
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_record_application_usage_increments_existing_entry(self):
        """Test that recording usage for existing application increments count."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage multiple times
            manager.record_application_usage("Chrome", "user1")
            manager.record_application_usage("Chrome", "user1")
            manager.record_application_usage("Chrome", "user1")
            
            # Verify count was incremented
            usage = manager.get_application_usage("Chrome", "user1")
            assert usage is not None
            assert usage.launch_count == 3
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_get_application_usage_returns_none_for_nonexistent(self):
        """Test that getting usage for non-existent application returns None."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Try to get usage for application that was never launched
            usage = manager.get_application_usage("NonExistent", "user1")
            
            # Verify None is returned
            assert usage is None
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_get_application_usage_returns_none_for_nonexistent_user(self):
        """Test that getting usage for non-existent user returns None."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage for user1
            manager.record_application_usage("Chrome", "user1")
            
            # Try to get usage for different user
            usage = manager.get_application_usage("Chrome", "user2")
            
            # Verify None is returned
            assert usage is None
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_usage_timestamps_are_datetime_objects(self):
        """Test that usage timestamps are proper datetime objects."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage
            manager.record_application_usage("Chrome", "user1")
            
            # Get usage
            usage = manager.get_application_usage("Chrome", "user1")
            
            # Verify timestamps are datetime objects
            assert isinstance(usage.first_launched, datetime)
            assert isinstance(usage.last_launched, datetime)
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_first_launched_remains_constant(self):
        """Test that first_launched timestamp doesn't change on subsequent launches."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record first launch
            manager.record_application_usage("Chrome", "user1")
            usage1 = manager.get_application_usage("Chrome", "user1")
            first_launched_time = usage1.first_launched
            
            # Small delay
            import time
            time.sleep(0.01)
            
            # Record second launch
            manager.record_application_usage("Chrome", "user1")
            usage2 = manager.get_application_usage("Chrome", "user1")
            
            # Verify first_launched stayed the same
            assert usage2.first_launched == first_launched_time
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_last_launched_updates_on_subsequent_launches(self):
        """Test that last_launched timestamp updates on each launch."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record first launch
            manager.record_application_usage("Chrome", "user1")
            usage1 = manager.get_application_usage("Chrome", "user1")
            
            # Small delay
            import time
            time.sleep(0.01)
            
            # Record second launch
            manager.record_application_usage("Chrome", "user1")
            usage2 = manager.get_application_usage("Chrome", "user1")
            
            # Verify last_launched was updated
            assert usage2.last_launched > usage1.last_launched
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_get_all_application_usage_empty_for_new_user(self):
        """Test that get_all_application_usage returns empty list for new user."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Get all usage for user who hasn't launched anything
            all_usage = manager.get_all_application_usage("user1")
            
            # Verify empty list is returned
            assert all_usage == []
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_get_all_application_usage_returns_all_applications(self):
        """Test that get_all_application_usage returns all tracked applications."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage for multiple applications
            manager.record_application_usage("Chrome", "user1")
            manager.record_application_usage("Firefox", "user1")
            manager.record_application_usage("VSCode", "user1")
            
            # Get all usage
            all_usage = manager.get_all_application_usage("user1")
            
            # Verify all applications are returned
            assert len(all_usage) == 3
            app_names = {usage.application_name for usage in all_usage}
            assert app_names == {"Chrome", "Firefox", "VSCode"}
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_get_all_application_usage_sorted_by_launch_count(self):
        """Test that get_all_application_usage returns sorted by launch count."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage with different counts
            for _ in range(5):
                manager.record_application_usage("Chrome", "user1")
            for _ in range(3):
                manager.record_application_usage("Firefox", "user1")
            for _ in range(7):
                manager.record_application_usage("VSCode", "user1")
            
            # Get all usage
            all_usage = manager.get_all_application_usage("user1")
            
            # Verify sorted by launch_count (descending)
            assert len(all_usage) == 3
            assert all_usage[0].application_name == "VSCode"
            assert all_usage[0].launch_count == 7
            assert all_usage[1].application_name == "Chrome"
            assert all_usage[1].launch_count == 5
            assert all_usage[2].application_name == "Firefox"
            assert all_usage[2].launch_count == 3
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_different_users_have_separate_usage_data(self):
        """Test that different users have completely separate usage data."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage for user1
            manager.record_application_usage("Chrome", "user1")
            manager.record_application_usage("Chrome", "user1")
            
            # Record usage for user2
            manager.record_application_usage("Chrome", "user2")
            
            # Verify separate tracking
            usage1 = manager.get_application_usage("Chrome", "user1")
            usage2 = manager.get_application_usage("Chrome", "user2")
            
            assert usage1.launch_count == 2
            assert usage2.launch_count == 1
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_usage_data_persists_across_manager_instances(self):
        """Test that usage data persists when creating new manager instances."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            # First manager instance
            manager1 = MemoryManager(storage_dir=temp_storage_dir)
            encryption_key = manager1.encryption_key
            manager1.record_application_usage("Chrome", "user1")
            
            # Second manager instance (simulating new session)
            manager2 = MemoryManager(
                encryption_key=encryption_key,
                storage_dir=temp_storage_dir
            )
            usage = manager2.get_application_usage("Chrome", "user1")
            
            # Verify data persisted
            assert usage is not None
            assert usage.application_name == "Chrome"
            assert usage.launch_count == 1
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_usage_data_encrypted_in_storage(self):
        """Test that usage data is encrypted when stored."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage
            manager.record_application_usage("Chrome", "user1")
            
            # Find the usage file
            import os
            from pathlib import Path
            usage_dir = Path(temp_storage_dir) / 'usage_patterns'
            
            # Verify directory exists
            assert usage_dir.exists()
            
            # Find user directory
            user_dirs = list(usage_dir.iterdir())
            assert len(user_dirs) > 0
            
            # Find usage file
            usage_files = list(user_dirs[0].glob("*.json"))
            assert len(usage_files) > 0
            
            # Read raw file content
            raw_content = usage_files[0].read_bytes()
            
            # Verify content is encrypted (not plain JSON)
            # Encrypted data should not contain readable JSON
            assert b'"application_name"' not in raw_content
            assert b'"Chrome"' not in raw_content
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_special_characters_in_application_name(self):
        """Test that application names with special characters are handled correctly."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage with special characters
            special_names = [
                "App:Name",
                "App/Name",
                "App\\Name",
                "App Name",
                "App-Name_v2.0"
            ]
            
            for app_name in special_names:
                manager.record_application_usage(app_name, "user1")
            
            # Verify all can be retrieved
            for app_name in special_names:
                usage = manager.get_application_usage(app_name, "user1")
                assert usage is not None
                assert usage.application_name == app_name
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)

    def test_special_characters_in_user_id(self):
        """Test that user IDs with special characters are handled correctly."""
        temp_storage_dir = tempfile.mkdtemp()
        
        try:
            manager = MemoryManager(storage_dir=temp_storage_dir)
            
            # Record usage with special characters in user_id
            special_users = [
                "user:123",
                "user/123",
                "user\\123",
                "user 123",
                "user@example.com"
            ]
            
            for user_id in special_users:
                manager.record_application_usage("Chrome", user_id)
            
            # Verify all can be retrieved
            for user_id in special_users:
                usage = manager.get_application_usage("Chrome", user_id)
                assert usage is not None
                assert usage.launch_count == 1
        finally:
            shutil.rmtree(temp_storage_dir, ignore_errors=True)
