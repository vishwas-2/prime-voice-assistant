"""Memory Manager for PRIME Voice Assistant.

This module provides the MemoryManager class responsible for:
- Storing and retrieving user preferences
- Persisting session history
- Managing notes and reminders
- Encrypting sensitive data
- Handling data deletion requests
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Any, Optional, List, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class MemoryManager:
    """Manages persistent storage and encryption for PRIME."""

    def __init__(self, encryption_key: Optional[bytes] = None, storage_dir: Optional[str] = None):
        """Initialize the Memory Manager.

        Args:
            encryption_key: Optional encryption key. If not provided, a new key
                          will be generated. The key should be 32 bytes for Fernet.
            storage_dir: Optional directory for storing data. If not provided,
                        defaults to '.prime_data' in the user's home directory.
        """
        if encryption_key is None:
            # Generate a new encryption key
            self._encryption_key = Fernet.generate_key()
        else:
            self._encryption_key = encryption_key
        
        self._cipher = Fernet(self._encryption_key)
        
        # Set up storage directory
        if storage_dir is None:
            self._storage_dir = Path.home() / '.prime_data'
        else:
            self._storage_dir = Path(storage_dir)
        
        # Create storage directory if it doesn't exist
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different data types
        self._preferences_dir = self._storage_dir / 'preferences'
        self._preferences_dir.mkdir(exist_ok=True)
        
        self._sessions_dir = self._storage_dir / 'sessions'
        self._sessions_dir.mkdir(exist_ok=True)
        
        self._notes_dir = self._storage_dir / 'notes'
        self._notes_dir.mkdir(exist_ok=True)
        
        self._reminders_dir = self._storage_dir / 'reminders'
        self._reminders_dir.mkdir(exist_ok=True)

    @property
    def encryption_key(self) -> bytes:
        """Get the encryption key (for storage/retrieval purposes).
        
        Returns:
            The encryption key as bytes.
        """
        return self._encryption_key

    def _sanitize_user_id(self, user_id: str) -> str:
        """Sanitize user_id to create a valid filename.
        
        Uses SHA-256 hash to create a safe filename from any user_id string.
        This ensures that any characters (including special characters like :, /, \, etc.)
        are converted to a valid filename.
        
        Args:
            user_id: The user identifier (may contain any characters).
            
        Returns:
            A sanitized filename-safe string.
        """
        # Create a hash of the user_id to ensure it's filename-safe
        hash_obj = hashlib.sha256(user_id.encode('utf-8'))
        return hash_obj.hexdigest()

    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using Fernet symmetric encryption.

        This method encrypts sensitive data before storing it. It uses the
        Fernet encryption scheme which provides authenticated encryption.

        Args:
            data: The plaintext data to encrypt as bytes.

        Returns:
            The encrypted data as bytes.

        Raises:
            TypeError: If data is not bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError(f"Data must be bytes, got {type(data).__name__}")
        
        return self._cipher.encrypt(data)

    def decrypt_data(self, encrypted: bytes) -> bytes:
        """Decrypt data that was encrypted with encrypt_data.

        This method decrypts data that was previously encrypted using the
        encrypt_data method.

        Args:
            encrypted: The encrypted data as bytes.

        Returns:
            The decrypted plaintext data as bytes.

        Raises:
            TypeError: If encrypted is not bytes.
            cryptography.fernet.InvalidToken: If the encrypted data is invalid
                or was encrypted with a different key.
        """
        if not isinstance(encrypted, bytes):
            raise TypeError(f"Encrypted data must be bytes, got {type(encrypted).__name__}")
        
        return self._cipher.decrypt(encrypted)

    def store_preference(self, key: str, value: Any, user_id: str) -> None:
        """Store a user preference.

        Preferences are stored as encrypted JSON files in the user's preference
        directory. Each user has their own preference file.

        Args:
            key: The preference key.
            value: The preference value (must be JSON-serializable).
            user_id: The user identifier.

        Raises:
            TypeError: If the value is not JSON-serializable.
        """
        # Sanitize user_id to create a valid filename
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Get the user's preference file path
        user_pref_file = self._preferences_dir / f"{safe_user_id}.json"
        
        # Load existing preferences or create new dict
        if user_pref_file.exists():
            # Read and decrypt existing preferences
            encrypted_data = user_pref_file.read_bytes()
            decrypted_data = self.decrypt_data(encrypted_data)
            preferences = json.loads(decrypted_data.decode('utf-8'))
        else:
            preferences = {}
        
        # Update the preference
        preferences[key] = value
        
        # Serialize, encrypt, and save
        json_data = json.dumps(preferences).encode('utf-8')
        encrypted_data = self.encrypt_data(json_data)
        user_pref_file.write_bytes(encrypted_data)

    def get_preference(self, key: str, user_id: str) -> Optional[Any]:
        """Retrieve a user preference.

        Args:
            key: The preference key.
            user_id: The user identifier.

        Returns:
            The preference value, or None if not found.
        """
        # Sanitize user_id to create a valid filename
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Get the user's preference file path
        user_pref_file = self._preferences_dir / f"{safe_user_id}.json"
        
        # Return None if file doesn't exist
        if not user_pref_file.exists():
            return None
        
        # Read and decrypt preferences
        encrypted_data = user_pref_file.read_bytes()
        decrypted_data = self.decrypt_data(encrypted_data)
        preferences = json.loads(decrypted_data.decode('utf-8'))
        
        # Return the preference value or None if key doesn't exist
        return preferences.get(key)

    def save_session(self, session: Any) -> None:
        """Save a session to persistent storage.

        Sessions are stored as encrypted JSON files in the sessions directory.
        Each session is stored in a file named with its session_id.

        Args:
            session: The session to save (must be a Session dataclass).

        Raises:
            AttributeError: If session doesn't have required attributes.
            TypeError: If session data is not JSON-serializable.
        """
        from prime.models.data_models import Session
        from dataclasses import asdict
        
        # Verify it's a Session object
        if not isinstance(session, Session):
            raise TypeError(f"Expected Session object, got {type(session).__name__}")
        
        # Convert session to dictionary
        session_dict = asdict(session)
        
        # Convert datetime objects to ISO format strings for JSON serialization
        session_dict['start_time'] = session.start_time.isoformat()
        if session.end_time:
            session_dict['end_time'] = session.end_time.isoformat()
        
        # Convert command_history timestamps
        for i, record in enumerate(session_dict['command_history']):
            record['timestamp'] = session.command_history[i].timestamp.isoformat()
            record['command']['timestamp'] = session.command_history[i].command.timestamp.isoformat()
        
        # Serialize to JSON
        json_data = json.dumps(session_dict).encode('utf-8')
        
        # Encrypt the data
        encrypted_data = self.encrypt_data(json_data)
        
        # Save to file
        session_file = self._sessions_dir / f"{session.session_id}.json"
        session_file.write_bytes(encrypted_data)

    def load_session(self, session_id: str) -> Any:
        """Load a session from persistent storage.

        Args:
            session_id: The session identifier.

        Returns:
            The loaded Session object, or None if not found.

        Raises:
            FileNotFoundError: If the session file doesn't exist.
            ValueError: If the session data is corrupted or invalid.
        """
        from prime.models.data_models import Session, CommandRecord, Command, CommandResult, Intent, Entity
        from datetime import datetime
        
        # Get the session file path
        session_file = self._sessions_dir / f"{session_id}.json"
        
        # Check if file exists
        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        
        # Read and decrypt the file
        encrypted_data = session_file.read_bytes()
        decrypted_data = self.decrypt_data(encrypted_data)
        
        # Parse JSON
        session_dict = json.loads(decrypted_data.decode('utf-8'))
        
        # Convert ISO format strings back to datetime objects
        session_dict['start_time'] = datetime.fromisoformat(session_dict['start_time'])
        if session_dict['end_time']:
            session_dict['end_time'] = datetime.fromisoformat(session_dict['end_time'])
        
        # Reconstruct command_history with proper dataclass instances
        command_history = []
        for record_dict in session_dict['command_history']:
            # Reconstruct entities
            entities = [
                Entity(**entity_dict)
                for entity_dict in record_dict['command']['intent']['entities']
            ]
            
            # Reconstruct intent
            intent = Intent(
                intent_type=record_dict['command']['intent']['intent_type'],
                entities=entities,
                confidence=record_dict['command']['intent']['confidence'],
                requires_clarification=record_dict['command']['intent']['requires_clarification']
            )
            
            # Reconstruct command
            command = Command(
                command_id=record_dict['command']['command_id'],
                intent=intent,
                parameters=record_dict['command']['parameters'],
                timestamp=datetime.fromisoformat(record_dict['command']['timestamp']),
                requires_confirmation=record_dict['command']['requires_confirmation']
            )
            
            # Reconstruct command result
            result = CommandResult(**record_dict['result'])
            
            # Reconstruct command record
            command_record = CommandRecord(
                command=command,
                result=result,
                timestamp=datetime.fromisoformat(record_dict['timestamp'])
            )
            
            command_history.append(command_record)
        
        session_dict['command_history'] = command_history
        
        # Create and return Session object
        return Session(**session_dict)

    def store_note(self, note: Any, user_id: str) -> None:
        """Store a note.

        Notes are stored as encrypted JSON files in the user's notes directory.
        Each note is stored in a file named with its note_id.

        Args:
            note: The note to store (must be a Note dataclass).
            user_id: The user identifier.

        Raises:
            TypeError: If note is not a Note object or data is not JSON-serializable.
        """
        from prime.models.data_models import Note
        from dataclasses import asdict
        
        # Verify it's a Note object
        if not isinstance(note, Note):
            raise TypeError(f"Expected Note object, got {type(note).__name__}")
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Create user-specific notes directory
        user_notes_dir = self._notes_dir / safe_user_id
        user_notes_dir.mkdir(exist_ok=True)
        
        # Convert note to dictionary
        note_dict = asdict(note)
        
        # Convert datetime objects to ISO format strings for JSON serialization
        note_dict['created_at'] = note.created_at.isoformat()
        note_dict['updated_at'] = note.updated_at.isoformat()
        
        # Serialize to JSON
        json_data = json.dumps(note_dict).encode('utf-8')
        
        # Encrypt the data
        encrypted_data = self.encrypt_data(json_data)
        
        # Save to file
        note_file = user_notes_dir / f"{note.note_id}.json"
        note_file.write_bytes(encrypted_data)

    def search_notes(self, query: str, user_id: str) -> List[Any]:
        """Search for notes.

        Searches notes by keywords in content, tags, or date. The search is
        case-insensitive and matches partial strings.

        Args:
            query: The search query (searches in content and tags).
            user_id: The user identifier.

        Returns:
            List of matching Note objects, sorted by updated_at (most recent first).
        """
        from prime.models.data_models import Note
        from datetime import datetime
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Get user-specific notes directory
        user_notes_dir = self._notes_dir / safe_user_id
        
        # Return empty list if directory doesn't exist
        if not user_notes_dir.exists():
            return []
        
        # Load all notes
        matching_notes = []
        query_lower = query.lower()
        
        for note_file in user_notes_dir.glob("*.json"):
            try:
                # Read and decrypt the note
                encrypted_data = note_file.read_bytes()
                decrypted_data = self.decrypt_data(encrypted_data)
                note_dict = json.loads(decrypted_data.decode('utf-8'))
                
                # Convert ISO format strings back to datetime objects
                note_dict['created_at'] = datetime.fromisoformat(note_dict['created_at'])
                note_dict['updated_at'] = datetime.fromisoformat(note_dict['updated_at'])
                
                # Create Note object
                note = Note(**note_dict)
                
                # Check if query matches content or tags
                content_match = query_lower in note.content.lower()
                tags_match = any(query_lower in tag.lower() for tag in note.tags)
                
                if content_match or tags_match:
                    matching_notes.append(note)
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Skip corrupted notes
                continue
        
        # Sort by updated_at (most recent first)
        matching_notes.sort(key=lambda n: n.updated_at, reverse=True)
        
        return matching_notes

    def create_reminder(self, reminder: Any, user_id: str) -> None:
        """Create a reminder.

        Reminders are stored as encrypted JSON files in the user's reminders directory.
        Each reminder is stored in a file named with its reminder_id.

        Args:
            reminder: The reminder to create (must be a Reminder dataclass).
            user_id: The user identifier.

        Raises:
            TypeError: If reminder is not a Reminder object or data is not JSON-serializable.
        """
        from prime.models.data_models import Reminder
        from dataclasses import asdict
        
        # Verify it's a Reminder object
        if not isinstance(reminder, Reminder):
            raise TypeError(f"Expected Reminder object, got {type(reminder).__name__}")
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Create user-specific reminders directory
        user_reminders_dir = self._reminders_dir / safe_user_id
        user_reminders_dir.mkdir(exist_ok=True)
        
        # Convert reminder to dictionary
        reminder_dict = asdict(reminder)
        
        # Convert datetime objects to ISO format strings for JSON serialization
        reminder_dict['due_time'] = reminder.due_time.isoformat()
        
        # Serialize to JSON
        json_data = json.dumps(reminder_dict).encode('utf-8')
        
        # Encrypt the data
        encrypted_data = self.encrypt_data(json_data)
        
        # Save to file
        reminder_file = user_reminders_dir / f"{reminder.reminder_id}.json"
        reminder_file.write_bytes(encrypted_data)

    def get_due_reminders(self, user_id: str) -> List[Any]:
        """Get reminders that are due.

        Returns all reminders that are not completed and whose due_time has passed
        or is equal to the current time.

        Args:
            user_id: The user identifier.

        Returns:
            List of due Reminder objects, sorted by due_time (earliest first).
        """
        from prime.models.data_models import Reminder
        from datetime import datetime
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Get user-specific reminders directory
        user_reminders_dir = self._reminders_dir / safe_user_id
        
        # Return empty list if directory doesn't exist
        if not user_reminders_dir.exists():
            return []
        
        # Load all reminders
        due_reminders = []
        current_time = datetime.now()
        
        for reminder_file in user_reminders_dir.glob("*.json"):
            try:
                # Read and decrypt the reminder
                encrypted_data = reminder_file.read_bytes()
                decrypted_data = self.decrypt_data(encrypted_data)
                reminder_dict = json.loads(decrypted_data.decode('utf-8'))
                
                # Convert ISO format strings back to datetime objects
                reminder_dict['due_time'] = datetime.fromisoformat(reminder_dict['due_time'])
                
                # Create Reminder object
                reminder = Reminder(**reminder_dict)
                
                # Check if reminder is due and not completed
                if not reminder.is_completed and reminder.due_time <= current_time:
                    due_reminders.append(reminder)
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Skip corrupted reminders
                continue
        
        # Sort by due_time (earliest first)
        due_reminders.sort(key=lambda r: r.due_time)
        
        return due_reminders

    def delete_user_data(self, user_id: str) -> None:
        """Delete all data for a user.

        This method removes all stored data associated with a user, including:
        - User preferences
        - User sessions
        - User notes
        - User reminders
        - User usage patterns

        Args:
            user_id: The user identifier.

        Raises:
            OSError: If there are issues deleting files or directories.
        """
        import shutil
        
        # Sanitize user_id to get the safe filename/directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Delete user preferences file
        user_pref_file = self._preferences_dir / f"{safe_user_id}.json"
        if user_pref_file.exists():
            user_pref_file.unlink()
        
        # Delete user notes directory
        user_notes_dir = self._notes_dir / safe_user_id
        if user_notes_dir.exists():
            shutil.rmtree(user_notes_dir)
        
        # Delete user reminders directory
        user_reminders_dir = self._reminders_dir / safe_user_id
        if user_reminders_dir.exists():
            shutil.rmtree(user_reminders_dir)
        
        # Delete user usage patterns directory
        user_usage_dir = self._storage_dir / 'usage_patterns' / safe_user_id
        if user_usage_dir.exists():
            shutil.rmtree(user_usage_dir)
        
        # Delete user sessions
        # Sessions are stored with session_id as filename, but we need to find
        # all sessions belonging to this user by reading and checking user_id
        for session_file in self._sessions_dir.glob("*.json"):
            try:
                # Read and decrypt the session
                encrypted_data = session_file.read_bytes()
                decrypted_data = self.decrypt_data(encrypted_data)
                session_dict = json.loads(decrypted_data.decode('utf-8'))
                
                # Check if this session belongs to the user
                if session_dict.get('user_id') == user_id:
                    session_file.unlink()
                    
            except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
                # Skip corrupted or unreadable sessions
                continue

    def record_application_usage(self, application_name: str, user_id: str) -> None:
        """Record application usage for tracking patterns.

        This method tracks when applications are launched by users. It maintains
        a count of launches and timestamps for first and last launch.

        Args:
            application_name: The name of the application that was launched.
            user_id: The user identifier.

        Raises:
            TypeError: If data is not JSON-serializable.
        """
        from datetime import datetime
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Create user-specific usage patterns directory
        user_usage_dir = self._storage_dir / 'usage_patterns' / safe_user_id
        user_usage_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the usage file path for this application
        # Sanitize application name for filename
        safe_app_name = self._sanitize_user_id(application_name)
        usage_file = user_usage_dir / f"{safe_app_name}.json"
        
        current_time = datetime.now()
        
        # Load existing usage data or create new
        if usage_file.exists():
            # Read and decrypt existing usage data
            encrypted_data = usage_file.read_bytes()
            decrypted_data = self.decrypt_data(encrypted_data)
            usage_data = json.loads(decrypted_data.decode('utf-8'))
            
            # Update usage data
            usage_data['launch_count'] += 1
            usage_data['last_launched'] = current_time.isoformat()
            # Keep first_launched as is
        else:
            # Create new usage data
            usage_data = {
                'application_name': application_name,
                'launch_count': 1,
                'first_launched': current_time.isoformat(),
                'last_launched': current_time.isoformat()
            }
        
        # Serialize, encrypt, and save
        json_data = json.dumps(usage_data).encode('utf-8')
        encrypted_data = self.encrypt_data(json_data)
        usage_file.write_bytes(encrypted_data)

    def get_application_usage(self, application_name: str, user_id: str) -> Optional[Any]:
        """Retrieve usage pattern data for an application.

        Args:
            application_name: The name of the application.
            user_id: The user identifier.

        Returns:
            ApplicationUsage object if found, None otherwise.
        """
        from prime.models.data_models import ApplicationUsage
        from datetime import datetime
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Get user-specific usage patterns directory
        user_usage_dir = self._storage_dir / 'usage_patterns' / safe_user_id
        
        # Return None if directory doesn't exist
        if not user_usage_dir.exists():
            return None
        
        # Get the usage file path for this application
        safe_app_name = self._sanitize_user_id(application_name)
        usage_file = user_usage_dir / f"{safe_app_name}.json"
        
        # Return None if file doesn't exist
        if not usage_file.exists():
            return None
        
        # Read and decrypt usage data
        encrypted_data = usage_file.read_bytes()
        decrypted_data = self.decrypt_data(encrypted_data)
        usage_data = json.loads(decrypted_data.decode('utf-8'))
        
        # Convert ISO format strings back to datetime objects
        usage_data['first_launched'] = datetime.fromisoformat(usage_data['first_launched'])
        usage_data['last_launched'] = datetime.fromisoformat(usage_data['last_launched'])
        
        # Create and return ApplicationUsage object
        return ApplicationUsage(**usage_data)

    def get_all_application_usage(self, user_id: str) -> List[Any]:
        """Retrieve all application usage patterns for a user.

        Args:
            user_id: The user identifier.

        Returns:
            List of ApplicationUsage objects, sorted by launch_count (most used first).
        """
        from prime.models.data_models import ApplicationUsage
        from datetime import datetime
        
        # Sanitize user_id to create a valid directory name
        safe_user_id = self._sanitize_user_id(user_id)
        
        # Get user-specific usage patterns directory
        user_usage_dir = self._storage_dir / 'usage_patterns' / safe_user_id
        
        # Return empty list if directory doesn't exist
        if not user_usage_dir.exists():
            return []
        
        # Load all usage patterns
        usage_patterns = []
        
        for usage_file in user_usage_dir.glob("*.json"):
            try:
                # Read and decrypt the usage data
                encrypted_data = usage_file.read_bytes()
                decrypted_data = self.decrypt_data(encrypted_data)
                usage_data = json.loads(decrypted_data.decode('utf-8'))
                
                # Convert ISO format strings back to datetime objects
                usage_data['first_launched'] = datetime.fromisoformat(usage_data['first_launched'])
                usage_data['last_launched'] = datetime.fromisoformat(usage_data['last_launched'])
                
                # Create ApplicationUsage object
                usage = ApplicationUsage(**usage_data)
                usage_patterns.append(usage)
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Skip corrupted usage data
                continue
        
        # Sort by launch_count (most used first)
        usage_patterns.sort(key=lambda u: u.launch_count, reverse=True)
        
        return usage_patterns


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive an encryption key from a password using PBKDF2.

    This utility function can be used to generate an encryption key from a
    user password, allowing password-based encryption. The derived key is
    base64-encoded to be compatible with Fernet.

    Args:
        password: The password to derive the key from.
        salt: A random salt value (should be at least 16 bytes).

    Returns:
        A 32-byte base64-encoded encryption key suitable for use with Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommendation as of 2023
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    # Fernet requires base64-encoded keys
    return base64.urlsafe_b64encode(key)
