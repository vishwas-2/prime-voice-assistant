"""
Audio stream data structures for PRIME Voice Assistant.

This module defines the AudioStream class and related utilities for
handling audio data in the voice processing pipeline.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class AudioStream:
    """
    Represents an audio stream with raw audio data and metadata.
    
    Attributes:
        data: Raw audio data as numpy array
        sample_rate: Sample rate in Hz (e.g., 16000, 44100)
        channels: Number of audio channels (1 for mono, 2 for stereo)
        duration_ms: Duration of the audio in milliseconds
        noise_level_db: Measured noise level in decibels (optional)
    """
    data: np.ndarray
    sample_rate: int
    channels: int
    duration_ms: float
    noise_level_db: Optional[float] = None
    
    def __post_init__(self):
        """Validate audio stream parameters."""
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if self.channels not in [1, 2]:
            raise ValueError("Channels must be 1 (mono) or 2 (stereo)")
        if self.duration_ms < 0:
            raise ValueError("Duration must be non-negative")
    
    @property
    def num_samples(self) -> int:
        """Get the number of samples in the audio stream."""
        return len(self.data)
    
    @property
    def duration_seconds(self) -> float:
        """Get the duration in seconds."""
        return self.duration_ms / 1000.0
