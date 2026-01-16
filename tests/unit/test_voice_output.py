"""
Unit tests for Voice Output Module.

This module contains unit tests for the VoiceOutputModule class,
testing specific functionality and edge cases.
"""

import pytest
import numpy as np
from prime.voice.voice_output import VoiceOutputModule
from prime.voice.audio_stream import AudioStream
from prime.models.data_models import VoiceProfile
import time


class TestVoiceOutputModuleInitialization:
    """Test Voice Output Module initialization."""
    
    def test_init_with_default_profile(self):
        """Test initialization with default profile."""
        module = VoiceOutputModule()
        
        assert module is not None
        assert module.get_current_profile() is not None
        assert module.get_current_profile().profile_id == "default"
        assert not module.is_playing()
    
    def test_init_with_custom_profile(self):
        """Test initialization with custom profile."""
        profile = VoiceProfile(
            profile_id="custom",
            voice_name="test_voice",
            speech_rate=200.0,
            pitch=1.2,
            volume=0.7
        )
        
        module = VoiceOutputModule(voice_profile=profile)
        
        assert module.get_current_profile().profile_id == "custom"
        assert module.get_current_profile().voice_name == "test_voice"
        assert module.get_current_profile().speech_rate == 200.0


class TestTextToSpeech:
    """Test text-to-speech conversion."""
    
    def test_simple_text_conversion(self):
        """Test converting simple text to speech."""
        module = VoiceOutputModule()
        text = "Hello world"
        
        audio = module.text_to_speech(text)
        
        assert isinstance(audio, AudioStream)
        assert audio.data is not None
        assert len(audio.data) > 0
        assert audio.sample_rate > 0
        assert audio.duration_ms > 0
    
    def test_long_text_conversion(self):
        """Test converting longer text to speech."""
        module = VoiceOutputModule()
        text = "This is a longer sentence with multiple words to test the text-to-speech conversion."
        
        audio = module.text_to_speech(text)
        
        assert isinstance(audio, AudioStream)
        assert len(audio.data) > 0
        # Longer text should produce longer audio
        assert audio.duration_ms > 1000  # At least 1 second
    
    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        module = VoiceOutputModule()
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            module.text_to_speech("")
    
    def test_whitespace_only_text_raises_error(self):
        """Test that whitespace-only text raises ValueError."""
        module = VoiceOutputModule()
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            module.text_to_speech("   \t\n  ")
    
    def test_text_to_speech_with_explicit_profile(self):
        """Test text-to-speech with explicitly provided profile."""
        module = VoiceOutputModule()
        
        custom_profile = VoiceProfile(
            profile_id="temp",
            voice_name="temp_voice",
            speech_rate=250.0,
            pitch=1.0,
            volume=0.9
        )
        
        audio = module.text_to_speech("Test", voice_profile=custom_profile)
        
        assert isinstance(audio, AudioStream)
        # Current profile should not change
        assert module.get_current_profile().profile_id == "default"


class TestVoiceProfileManagement:
    """Test voice profile management."""
    
    def test_set_voice_profile(self):
        """Test setting a new voice profile."""
        module = VoiceOutputModule()
        
        new_profile = VoiceProfile(
            profile_id="new",
            voice_name="new_voice",
            speech_rate=180.0,
            pitch=1.1,
            volume=0.8
        )
        
        module.set_voice_profile(new_profile)
        
        current = module.get_current_profile()
        assert current.profile_id == "new"
        assert current.voice_name == "new_voice"
        assert current.speech_rate == 180.0
    
    def test_set_none_profile_raises_error(self):
        """Test that setting None profile raises ValueError."""
        module = VoiceOutputModule()
        
        with pytest.raises(ValueError, match="Voice profile cannot be None"):
            module.set_voice_profile(None)
    
    def test_set_invalid_speech_rate_raises_error(self):
        """Test that invalid speech rate raises ValueError."""
        module = VoiceOutputModule()
        
        invalid_profile = VoiceProfile(
            profile_id="invalid",
            voice_name="test",
            speech_rate=-10.0,  # Invalid
            pitch=1.0,
            volume=0.5
        )
        
        with pytest.raises(ValueError, match="Speech rate must be positive"):
            module.set_voice_profile(invalid_profile)
    
    def test_set_invalid_volume_raises_error(self):
        """Test that invalid volume raises ValueError."""
        module = VoiceOutputModule()
        
        invalid_profile = VoiceProfile(
            profile_id="invalid",
            voice_name="test",
            speech_rate=150.0,
            pitch=1.0,
            volume=1.5  # Invalid: > 1.0
        )
        
        with pytest.raises(ValueError, match="Volume must be between 0 and 1"):
            module.set_voice_profile(invalid_profile)


class TestSpeechRateAdjustment:
    """Test speech rate adjustment."""
    
    def test_adjust_speech_rate(self):
        """Test adjusting speech rate."""
        module = VoiceOutputModule()
        original_rate = module.get_current_profile().speech_rate
        
        new_rate = 200.0
        module.adjust_speech_rate(new_rate)
        
        assert module.get_current_profile().speech_rate == new_rate
        assert module.get_current_profile().speech_rate != original_rate
    
    def test_adjust_speech_rate_negative_raises_error(self):
        """Test that negative speech rate raises ValueError."""
        module = VoiceOutputModule()
        
        with pytest.raises(ValueError, match="Speech rate must be positive"):
            module.adjust_speech_rate(-50.0)
    
    def test_adjust_speech_rate_zero_raises_error(self):
        """Test that zero speech rate raises ValueError."""
        module = VoiceOutputModule()
        
        with pytest.raises(ValueError, match="Speech rate must be positive"):
            module.adjust_speech_rate(0.0)


class TestAudioPlayback:
    """Test audio playback functionality."""
    
    def test_play_audio(self):
        """Test playing audio."""
        module = VoiceOutputModule()
        
        # Create test audio
        audio = AudioStream(
            data=np.random.randint(-1000, 1000, size=8000, dtype=np.int16),
            sample_rate=16000,
            channels=1,
            duration_ms=500
        )
        
        module.play_audio(audio)
        
        # Should be playing
        assert module.is_playing()
        
        # Stop playback
        module.stop_playback()
        time.sleep(0.1)
        
        # Should not be playing
        assert not module.is_playing()
    
    def test_play_none_audio_raises_error(self):
        """Test that playing None audio raises ValueError."""
        module = VoiceOutputModule()
        
        with pytest.raises(ValueError, match="Invalid audio stream"):
            module.play_audio(None)
    
    def test_play_empty_audio_raises_error(self):
        """Test that playing empty audio raises ValueError."""
        module = VoiceOutputModule()
        
        empty_audio = AudioStream(
            data=np.array([], dtype=np.int16),
            sample_rate=16000,
            channels=1,
            duration_ms=0
        )
        
        with pytest.raises(ValueError, match="Invalid audio stream"):
            module.play_audio(empty_audio)
    
    def test_stop_playback_when_not_playing(self):
        """Test that stopping playback when not playing has no effect."""
        module = VoiceOutputModule()
        
        # Should not raise error
        module.stop_playback()
        
        assert not module.is_playing()
    
    def test_stop_playback_interrupts_audio(self):
        """Test that stop_playback interrupts ongoing playback."""
        module = VoiceOutputModule()
        
        # Create longer audio
        audio = AudioStream(
            data=np.random.randint(-1000, 1000, size=32000, dtype=np.int16),
            sample_rate=16000,
            channels=1,
            duration_ms=2000  # 2 seconds
        )
        
        module.play_audio(audio)
        assert module.is_playing()
        
        # Stop immediately
        module.stop_playback()
        time.sleep(0.2)
        
        # Should have stopped
        assert not module.is_playing()


class TestIntegration:
    """Integration tests for Voice Output Module."""
    
    def test_complete_workflow(self):
        """Test complete workflow: init, set profile, generate speech, play."""
        # Initialize with custom profile
        profile = VoiceProfile(
            profile_id="workflow_test",
            voice_name="test_voice",
            speech_rate=175.0,
            pitch=1.0,
            volume=0.75
        )
        
        module = VoiceOutputModule(voice_profile=profile)
        
        # Generate speech
        text = "This is a test of the complete workflow"
        audio = module.text_to_speech(text)
        
        assert isinstance(audio, AudioStream)
        assert len(audio.data) > 0
        
        # Play audio
        module.play_audio(audio)
        assert module.is_playing()
        
        # Stop playback
        module.stop_playback()
        time.sleep(0.1)
        assert not module.is_playing()
        
        # Profile should still be the same
        assert module.get_current_profile().profile_id == "workflow_test"
    
    def test_multiple_speech_generations(self):
        """Test generating multiple speech outputs in sequence."""
        module = VoiceOutputModule()
        
        texts = [
            "First sentence",
            "Second sentence",
            "Third sentence"
        ]
        
        audios = []
        for text in texts:
            audio = module.text_to_speech(text)
            audios.append(audio)
            assert isinstance(audio, AudioStream)
            assert len(audio.data) > 0
        
        # All audios should be valid
        assert len(audios) == 3
        
        # Profile should remain consistent
        profile = module.get_current_profile()
        assert profile is not None
