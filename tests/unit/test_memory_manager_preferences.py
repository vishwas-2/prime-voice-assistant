"""Unit tests for Memory Manager preference storage.

Tests the store_preference and get_preference methods to ensure:
- Preferences can be stored and retrieved correctly
- Different data types are handled properly
- Multiple preferences can be stored for the same user
- Different users have separate preference storage
- Preferences persist across manager instances
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from prime.persistence import MemoryManager


class TestPreferenceStorage:
    """Test preference storage and retrieval functionality."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_storage_dir):
        """Create a MemoryManager instance with temporary storage."""
        return MemoryManager(storage_dir=temp_storage_dir)

    def test_store_and_retrieve_string_preference(self, manager):
        """Test storing and retrieving a string preference."""
        user_id = "user1"
        key = "theme"
        value = "dark"
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_and_retrieve_integer_preference(self, manager):
        """Test storing and retrieving an integer preference."""
        user_id = "user1"
        key = "volume"
        value = 75
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_and_retrieve_float_preference(self, manager):
        """Test storing and retrieving a float preference."""
        user_id = "user1"
        key = "speech_rate"
        value = 1.5
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_and_retrieve_boolean_preference(self, manager):
        """Test storing and retrieving a boolean preference."""
        user_id = "user1"
        key = "voice_enabled"
        value = True
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_and_retrieve_list_preference(self, manager):
        """Test storing and retrieving a list preference."""
        user_id = "user1"
        key = "favorite_apps"
        value = ["chrome", "vscode", "terminal"]
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_and_retrieve_dict_preference(self, manager):
        """Test storing and retrieving a dictionary preference."""
        user_id = "user1"
        key = "voice_profile"
        value = {"name": "default", "pitch": 1.0, "rate": 1.2}
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_and_retrieve_none_preference(self, manager):
        """Test storing and retrieving None as a preference value."""
        user_id = "user1"
        key = "optional_setting"
        value = None
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_get_nonexistent_preference_returns_none(self, manager):
        """Test that getting a non-existent preference returns None."""
        user_id = "user1"
        key = "nonexistent_key"
        
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved is None

    def test_get_preference_for_nonexistent_user_returns_none(self, manager):
        """Test that getting a preference for a non-existent user returns None."""
        user_id = "nonexistent_user"
        key = "some_key"
        
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved is None

    def test_store_multiple_preferences_for_same_user(self, manager):
        """Test storing multiple preferences for the same user."""
        user_id = "user1"
        preferences = {
            "theme": "dark",
            "volume": 80,
            "voice_enabled": True,
            "favorite_apps": ["chrome", "vscode"]
        }
        
        # Store all preferences
        for key, value in preferences.items():
            manager.store_preference(key, value, user_id)
        
        # Retrieve and verify all preferences
        for key, expected_value in preferences.items():
            retrieved = manager.get_preference(key, user_id)
            assert retrieved == expected_value

    def test_update_existing_preference(self, manager):
        """Test updating an existing preference."""
        user_id = "user1"
        key = "volume"
        
        # Store initial value
        manager.store_preference(key, 50, user_id)
        assert manager.get_preference(key, user_id) == 50
        
        # Update value
        manager.store_preference(key, 75, user_id)
        assert manager.get_preference(key, user_id) == 75

    def test_different_users_have_separate_preferences(self, manager):
        """Test that different users have separate preference storage."""
        user1_id = "user1"
        user2_id = "user2"
        key = "theme"
        
        # Store different values for different users
        manager.store_preference(key, "dark", user1_id)
        manager.store_preference(key, "light", user2_id)
        
        # Verify each user gets their own value
        assert manager.get_preference(key, user1_id) == "dark"
        assert manager.get_preference(key, user2_id) == "light"

    def test_preferences_persist_across_manager_instances(self, temp_storage_dir):
        """Test that preferences persist when creating a new manager instance."""
        user_id = "user1"
        key = "persistent_setting"
        value = "persisted_value"
        
        # Create first manager and store preference
        manager1 = MemoryManager(storage_dir=temp_storage_dir)
        encryption_key = manager1.encryption_key
        manager1.store_preference(key, value, user_id)
        
        # Create second manager with same key and storage dir
        manager2 = MemoryManager(encryption_key=encryption_key, storage_dir=temp_storage_dir)
        retrieved = manager2.get_preference(key, user_id)
        
        assert retrieved == value

    def test_preferences_are_encrypted_on_disk(self, manager, temp_storage_dir):
        """Test that preferences are encrypted when stored on disk."""
        user_id = "user1"
        key = "secret_preference"
        value = "secret_value"
        
        manager.store_preference(key, value, user_id)
        
        # Get the sanitized user_id (hash)
        import hashlib
        safe_user_id = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        
        # Read the raw file content
        pref_file = Path(temp_storage_dir) / 'preferences' / f'{safe_user_id}.json'
        raw_content = pref_file.read_bytes()
        
        # Verify the raw content doesn't contain the plaintext value
        assert b"secret_value" not in raw_content
        assert b"secret_preference" not in raw_content

    def test_store_complex_nested_structure(self, manager):
        """Test storing a complex nested data structure."""
        user_id = "user1"
        key = "complex_config"
        value = {
            "ui": {
                "theme": "dark",
                "font_size": 14,
                "colors": ["#000000", "#FFFFFF"]
            },
            "voice": {
                "enabled": True,
                "profiles": [
                    {"name": "default", "rate": 1.0},
                    {"name": "fast", "rate": 1.5}
                ]
            },
            "shortcuts": ["ctrl+c", "ctrl+v"]
        }
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_empty_string_preference(self, manager):
        """Test storing an empty string as a preference."""
        user_id = "user1"
        key = "empty_setting"
        value = ""
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_zero_value_preference(self, manager):
        """Test storing zero as a preference value."""
        user_id = "user1"
        key = "counter"
        value = 0
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_false_boolean_preference(self, manager):
        """Test storing False as a preference value."""
        user_id = "user1"
        key = "disabled_feature"
        value = False
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved is False

    def test_store_empty_list_preference(self, manager):
        """Test storing an empty list as a preference."""
        user_id = "user1"
        key = "empty_list"
        value = []
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_store_empty_dict_preference(self, manager):
        """Test storing an empty dictionary as a preference."""
        user_id = "user1"
        key = "empty_dict"
        value = {}
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_unicode_in_preference_key(self, manager):
        """Test storing preferences with unicode characters in the key."""
        user_id = "user1"
        key = "设置_key"
        value = "unicode_value"
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_unicode_in_preference_value(self, manager):
        """Test storing preferences with unicode characters in the value."""
        user_id = "user1"
        key = "greeting"
        value = "Hello 世界! 🌍 Привет"
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value

    def test_special_characters_in_user_id(self, manager):
        """Test storing preferences for users with special characters in ID."""
        user_id = "user@example.com"
        key = "email_preference"
        value = "test_value"
        
        manager.store_preference(key, value, user_id)
        retrieved = manager.get_preference(key, user_id)
        
        assert retrieved == value
