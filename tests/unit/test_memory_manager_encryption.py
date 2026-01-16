"""Unit tests for Memory Manager encryption utilities.

Tests the encrypt_data and decrypt_data methods to ensure:
- Encryption/decryption round-trip works correctly
- Different data types and sizes are handled properly
- Invalid inputs are rejected appropriately
- Encrypted data cannot be decrypted with wrong key
"""

import pytest
from cryptography.fernet import Fernet, InvalidToken
from prime.persistence import MemoryManager, derive_key_from_password


class TestEncryptionDecryption:
    """Test encryption and decryption functionality."""

    def test_encrypt_decrypt_round_trip_simple(self):
        """Test that encrypting and then decrypting returns the original data."""
        manager = MemoryManager()
        original_data = b"Hello, PRIME!"
        
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_encrypt_decrypt_round_trip_empty_bytes(self):
        """Test encryption/decryption with empty bytes."""
        manager = MemoryManager()
        original_data = b""
        
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_encrypt_decrypt_round_trip_large_data(self):
        """Test encryption/decryption with large data."""
        manager = MemoryManager()
        # Create 1MB of data
        original_data = b"A" * (1024 * 1024)
        
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_encrypt_decrypt_round_trip_binary_data(self):
        """Test encryption/decryption with binary data containing all byte values."""
        manager = MemoryManager()
        # Create data with all possible byte values
        original_data = bytes(range(256))
        
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_encrypt_decrypt_round_trip_unicode_data(self):
        """Test encryption/decryption with UTF-8 encoded unicode data."""
        manager = MemoryManager()
        original_text = "Hello 世界! 🌍 Привет"
        original_data = original_text.encode('utf-8')
        
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data
        assert decrypted.decode('utf-8') == original_text

    def test_encrypted_data_is_different_from_original(self):
        """Test that encrypted data is different from the original."""
        manager = MemoryManager()
        original_data = b"Secret data"
        
        encrypted = manager.encrypt_data(original_data)
        
        assert encrypted != original_data

    def test_encrypted_data_is_non_deterministic(self):
        """Test that encrypting the same data twice produces different ciphertext.
        
        This is important for security - Fernet includes a timestamp and random IV.
        """
        manager = MemoryManager()
        original_data = b"Same data"
        
        encrypted1 = manager.encrypt_data(original_data)
        encrypted2 = manager.encrypt_data(original_data)
        
        # Ciphertext should be different due to random IV
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same plaintext
        assert manager.decrypt_data(encrypted1) == original_data
        assert manager.decrypt_data(encrypted2) == original_data

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption fails when using a different key."""
        manager1 = MemoryManager()
        manager2 = MemoryManager()  # Different key
        
        original_data = b"Secret message"
        encrypted = manager1.encrypt_data(original_data)
        
        # Attempting to decrypt with wrong key should raise InvalidToken
        with pytest.raises(InvalidToken):
            manager2.decrypt_data(encrypted)

    def test_decrypt_corrupted_data_fails(self):
        """Test that decryption fails with corrupted data."""
        manager = MemoryManager()
        original_data = b"Valid data"
        
        encrypted = manager.encrypt_data(original_data)
        
        # Corrupt the encrypted data
        corrupted = encrypted[:-1] + b'X'
        
        with pytest.raises(InvalidToken):
            manager.decrypt_data(corrupted)

    def test_decrypt_invalid_format_fails(self):
        """Test that decryption fails with invalid format."""
        manager = MemoryManager()
        
        # Random bytes that are not valid Fernet tokens
        invalid_data = b"This is not encrypted data"
        
        with pytest.raises(InvalidToken):
            manager.decrypt_data(invalid_data)

    def test_encrypt_non_bytes_raises_type_error(self):
        """Test that encrypting non-bytes data raises TypeError."""
        manager = MemoryManager()
        
        with pytest.raises(TypeError, match="Data must be bytes"):
            manager.encrypt_data("string data")  # type: ignore
        
        with pytest.raises(TypeError, match="Data must be bytes"):
            manager.encrypt_data(12345)  # type: ignore
        
        with pytest.raises(TypeError, match="Data must be bytes"):
            manager.encrypt_data([1, 2, 3])  # type: ignore

    def test_decrypt_non_bytes_raises_type_error(self):
        """Test that decrypting non-bytes data raises TypeError."""
        manager = MemoryManager()
        
        with pytest.raises(TypeError, match="Encrypted data must be bytes"):
            manager.decrypt_data("string data")  # type: ignore
        
        with pytest.raises(TypeError, match="Encrypted data must be bytes"):
            manager.decrypt_data(12345)  # type: ignore

    def test_manager_with_custom_key(self):
        """Test creating a MemoryManager with a custom encryption key."""
        custom_key = Fernet.generate_key()
        manager = MemoryManager(encryption_key=custom_key)
        
        original_data = b"Data with custom key"
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data
        assert manager.encryption_key == custom_key

    def test_manager_key_persistence(self):
        """Test that the same key can be used across multiple manager instances."""
        # Create first manager and encrypt data
        manager1 = MemoryManager()
        key = manager1.encryption_key
        original_data = b"Persistent data"
        encrypted = manager1.encrypt_data(original_data)
        
        # Create second manager with the same key
        manager2 = MemoryManager(encryption_key=key)
        decrypted = manager2.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_multiple_encrypt_decrypt_operations(self):
        """Test multiple sequential encryption/decryption operations."""
        manager = MemoryManager()
        
        test_data = [
            b"First message",
            b"Second message",
            b"Third message",
            b"Fourth message",
        ]
        
        # Encrypt all messages
        encrypted_messages = [manager.encrypt_data(data) for data in test_data]
        
        # Decrypt all messages
        decrypted_messages = [manager.decrypt_data(enc) for enc in encrypted_messages]
        
        # Verify all messages match
        assert decrypted_messages == test_data


class TestDeriveKeyFromPassword:
    """Test password-based key derivation."""

    def test_derive_key_from_password(self):
        """Test that a key can be derived from a password."""
        password = "my_secure_password"
        salt = b"random_salt_1234"
        
        key = derive_key_from_password(password, salt)
        
        # Key should be 44 bytes (32 bytes base64-encoded) for Fernet
        assert len(key) == 44
        assert isinstance(key, bytes)
        # Verify it's valid base64
        import base64
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32

    def test_same_password_and_salt_produce_same_key(self):
        """Test that the same password and salt always produce the same key."""
        password = "consistent_password"
        salt = b"consistent_salt_"
        
        key1 = derive_key_from_password(password, salt)
        key2 = derive_key_from_password(password, salt)
        
        assert key1 == key2

    def test_different_passwords_produce_different_keys(self):
        """Test that different passwords produce different keys."""
        salt = b"same_salt_value_"
        
        key1 = derive_key_from_password("password1", salt)
        key2 = derive_key_from_password("password2", salt)
        
        assert key1 != key2

    def test_different_salts_produce_different_keys(self):
        """Test that different salts produce different keys."""
        password = "same_password"
        
        key1 = derive_key_from_password(password, b"salt_value_one__")
        key2 = derive_key_from_password(password, b"salt_value_two__")
        
        assert key1 != key2

    def test_derived_key_works_with_memory_manager(self):
        """Test that a derived key can be used with MemoryManager."""
        password = "user_password"
        salt = b"application_salt"
        
        key = derive_key_from_password(password, salt)
        manager = MemoryManager(encryption_key=key)
        
        original_data = b"Protected user data"
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_password_based_encryption_scenario(self):
        """Test a realistic scenario of password-based encryption.
        
        Simulates:
        1. User creates account with password
        2. System derives encryption key from password
        3. Data is encrypted and stored
        4. User logs in again with same password
        5. System derives same key and decrypts data
        """
        # User registration
        user_password = "MySecurePassword123!"
        salt = b"stored_salt_val_"  # In real app, this would be stored per user
        
        # Derive key and create manager
        encryption_key = derive_key_from_password(user_password, salt)
        manager1 = MemoryManager(encryption_key=encryption_key)
        
        # Encrypt user data
        user_data = b"Sensitive user preferences and history"
        encrypted_data = manager1.encrypt_data(user_data)
        
        # Simulate user logging in again
        # Derive key from same password and salt
        login_key = derive_key_from_password(user_password, salt)
        manager2 = MemoryManager(encryption_key=login_key)
        
        # Decrypt data
        decrypted_data = manager2.decrypt_data(encrypted_data)
        
        assert decrypted_data == user_data
        assert encryption_key == login_key
