"""
Voice processing module for PRIME Voice Assistant.

This module provides voice input and output capabilities including
audio capture, speech recognition, text-to-speech, and audio processing.
"""

from .audio_stream import AudioStream

# Import voice modules with graceful error handling
__all__ = ['AudioStream']

try:
    from .voice_input import VoiceInputModule
    __all__.append('VoiceInputModule')
except ImportError:
    pass

try:
    from .voice_output import VoiceOutputModule
    __all__.append('VoiceOutputModule')
except ImportError:
    pass
