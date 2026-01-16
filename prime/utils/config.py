"""
Configuration management for PRIME Voice Assistant.

This module handles loading configuration from environment variables,
configuration files, and provides default values.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings for PRIME Voice Assistant."""
    
    # Directories
    HOME_DIR = Path.home() / ".prime"
    LOG_DIR = Path(os.getenv("PRIME_LOG_DIR", HOME_DIR / "logs"))
    DATA_DIR = Path(os.getenv("PRIME_DATA_DIR", HOME_DIR / "data"))
    CONFIG_DIR = Path(os.getenv("PRIME_CONFIG_DIR", HOME_DIR / "config"))
    
    # Logging
    LOG_LEVEL = os.getenv("PRIME_LOG_LEVEL", "INFO").upper()
    
    # Voice Settings
    VOICE_ENABLED = os.getenv("PRIME_VOICE_ENABLED", "true").lower() == "true"
    VOICE_PROFILE = os.getenv("PRIME_VOICE_PROFILE", "default")
    SPEECH_RATE = float(os.getenv("PRIME_SPEECH_RATE", "1.0"))
    
    # Safety Settings
    REQUIRE_CONFIRMATION = os.getenv("PRIME_REQUIRE_CONFIRMATION", "true").lower() == "true"
    ALLOW_SYSTEM_SHUTDOWN = os.getenv("PRIME_ALLOW_SYSTEM_SHUTDOWN", "false").lower() == "true"
    
    # Performance Settings
    MAX_MEMORY_MB = int(os.getenv("PRIME_MAX_MEMORY_MB", "500"))
    SPEECH_TIMEOUT_SECONDS = int(os.getenv("PRIME_SPEECH_TIMEOUT_SECONDS", "2"))
    MAX_CPU_PERCENT_IDLE = float(os.getenv("PRIME_MAX_CPU_PERCENT_IDLE", "5.0"))
    
    # Storage Settings
    MAX_STORAGE_GB = int(os.getenv("PRIME_MAX_STORAGE_GB", "1"))
    SESSION_RETENTION_DAYS = int(os.getenv("PRIME_SESSION_RETENTION_DAYS", "30"))
    
    # Feature Flags
    ENABLE_SCREEN_READER = os.getenv("PRIME_ENABLE_SCREEN_READER", "true").lower() == "true"
    ENABLE_AUTOMATION = os.getenv("PRIME_ENABLE_AUTOMATION", "true").lower() == "true"
    ENABLE_PROACTIVE_SUGGESTIONS = os.getenv("PRIME_ENABLE_PROACTIVE_SUGGESTIONS", "true").lower() == "true"
    
    # Voice Processing
    NOISE_THRESHOLD_DB = float(os.getenv("PRIME_NOISE_THRESHOLD_DB", "70.0"))
    PAUSE_DETECTION_MS = int(os.getenv("PRIME_PAUSE_DETECTION_MS", "1500"))
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.HOME_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_data_file(cls, filename: str) -> Path:
        """
        Get path to a data file in the data directory.
        
        Args:
            filename: Name of the data file
            
        Returns:
            Full path to the data file
        """
        cls.ensure_directories()
        return cls.DATA_DIR / filename
    
    @classmethod
    def get_config_file(cls, filename: str) -> Path:
        """
        Get path to a config file in the config directory.
        
        Args:
            filename: Name of the config file
            
        Returns:
            Full path to the config file
        """
        cls.ensure_directories()
        return cls.CONFIG_DIR / filename


# Create directories on import
Config.ensure_directories()
