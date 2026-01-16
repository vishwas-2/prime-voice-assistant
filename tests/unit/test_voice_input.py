"""
Unit tests for Voice Input Module.

Tests the basic functionality of the VoiceInputModule including
audio capture, noise filtering, speech-to-text, and pause detection.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from prime.voice import VoiceInputModule, AudioStream
import speech_recognition as sr


class TestVoiceInputModule:
    """Test suite for VoiceInputModule."""
    
    def test_initialization(self):
        """Test that VoiceInputModule initializes with correct defaults."""
        module = VoiceInputModule()
        assert module.noise_threshold_db == 70.0
        assert module.pause_threshold_ms == 1500
        assert module.is_listening is False
        assert module.microphone is None
    
    def test_initialization_custom_thresholds(self):
        """Test initialization with custom threshold values."""
        module = VoiceInputModule(noise_threshold_db=80.0, pause_threshold_ms=2000)
        assert module.noise_threshold_db == 80.0
        assert module.pause_threshold_ms == 2000
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_start_listening(self, mock_microphone, mock_recognizer):
        """Test that start_listening initializes the microphone."""
        # Mock the recognizer instance
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        
        module = VoiceInputModule()
        
        # Mock the microphone context manager properly
        mock_mic_instance = MagicMock()
        mock_microphone.return_value = mock_mic_instance
        
        # Mock the context manager protocol
        mock_source = MagicMock()
        mock_mic_instance.__enter__ = Mock(return_value=mock_source)
        mock_mic_instance.__exit__ = Mock(return_value=False)
        
        module.start_listening()
        
        assert module.is_listening is True
        assert module.microphone is not None
        # Verify adjust_for_ambient_noise was called
        module.recognizer.adjust_for_ambient_noise.assert_called_once()
    
    def test_stop_listening(self):
        """Test that stop_listening releases resources."""
        module = VoiceInputModule()
        module.is_listening = True
        module.microphone = Mock()
        
        module.stop_listening()
        
        assert module.is_listening is False
        assert module.microphone is None
    
    def test_get_audio_stream_not_listening(self):
        """Test that get_audio_stream raises error when not listening."""
        module = VoiceInputModule()
        
        with pytest.raises(RuntimeError, match="Must call start_listening"):
            module.get_audio_stream()
    
    def test_filter_noise_below_threshold(self):
        """Test that audio below noise threshold is not filtered."""
        # Create audio with low noise level
        data = np.random.randint(-1000, 1000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000,
            noise_level_db=50.0  # Below 70dB threshold
        )
        
        module = VoiceInputModule()
        filtered = module.filter_noise(audio)
        
        # Should return same audio when below threshold
        assert filtered.noise_level_db == audio.noise_level_db
        np.testing.assert_array_equal(filtered.data, audio.data)
    
    def test_filter_noise_above_threshold(self):
        """Test that audio above noise threshold is filtered."""
        # Create audio with high noise level
        data = np.random.randint(-20000, 20000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000,
            noise_level_db=80.0  # Above 70dB threshold
        )
        
        module = VoiceInputModule()
        filtered = module.filter_noise(audio)
        
        # Filtered audio should have lower noise level
        assert filtered.noise_level_db < audio.noise_level_db
        # Data should be modified
        assert not np.array_equal(filtered.data, audio.data)
    
    def test_filter_noise_custom_threshold(self):
        """Test noise filtering with custom threshold."""
        data = np.random.randint(-10000, 10000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000,
            noise_level_db=65.0
        )
        
        module = VoiceInputModule(noise_threshold_db=70.0)
        
        # Should not filter with default threshold (65 < 70)
        filtered1 = module.filter_noise(audio)
        np.testing.assert_array_equal(filtered1.data, audio.data)
        
        # Should filter with custom threshold (65 > 60)
        filtered2 = module.filter_noise(audio, threshold_db=60.0)
        assert filtered2.noise_level_db < audio.noise_level_db
    
    def test_detect_pause_no_pause(self):
        """Test pause detection with continuous audio (no pause)."""
        # Create continuous audio with consistent energy
        data = np.random.randint(-10000, 10000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000
        )
        
        module = VoiceInputModule()
        has_pause = module.detect_pause(audio)
        
        # Should not detect pause in continuous audio
        assert has_pause is False
    
    def test_detect_pause_with_pause(self):
        """Test pause detection with silence in audio."""
        # Create audio with silence in the middle
        sample_rate = 16000
        
        # 500ms of audio
        audio_part = np.random.randint(-10000, 10000, size=sample_rate // 2, dtype=np.int16)
        # 2000ms of silence (exceeds 1500ms threshold)
        silence_part = np.zeros(sample_rate * 2, dtype=np.int16)
        # 500ms of audio
        audio_part2 = np.random.randint(-10000, 10000, size=sample_rate // 2, dtype=np.int16)
        
        data = np.concatenate([audio_part, silence_part, audio_part2])
        audio = AudioStream(
            data=data,
            sample_rate=sample_rate,
            channels=1,
            duration_ms=3000
        )
        
        module = VoiceInputModule()
        has_pause = module.detect_pause(audio)
        
        # Should detect pause
        assert has_pause is True
    
    def test_detect_pause_custom_threshold(self):
        """Test pause detection with custom threshold."""
        sample_rate = 16000
        
        # Create audio with 1000ms silence
        audio_part = np.random.randint(-10000, 10000, size=sample_rate // 2, dtype=np.int16)
        silence_part = np.zeros(sample_rate, dtype=np.int16)  # 1000ms silence
        
        data = np.concatenate([audio_part, silence_part, audio_part])
        audio = AudioStream(
            data=data,
            sample_rate=sample_rate,
            channels=1,
            duration_ms=2000
        )
        
        module = VoiceInputModule()
        
        # Should not detect with default threshold (1000ms < 1500ms)
        has_pause_default = module.detect_pause(audio)
        assert has_pause_default is False
        
        # Should detect with custom threshold (1000ms >= 800ms)
        has_pause_custom = module.detect_pause(audio, pause_duration_ms=800)
        assert has_pause_custom is True
    
    def test_detect_pause_short_audio(self):
        """Test pause detection with very short audio."""
        # Create very short audio (less than window size)
        data = np.random.randint(-10000, 10000, size=100, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=6.25  # Very short
        )
        
        module = VoiceInputModule()
        has_pause = module.detect_pause(audio)
        
        # Should return False for audio too short to analyze
        assert has_pause is False
    
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_speech_to_text_success(self, mock_recognize):
        """Test successful speech-to-text conversion."""
        mock_recognize.return_value = "hello world"
        
        # Create sample audio
        data = np.random.randint(-10000, 10000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000
        )
        
        module = VoiceInputModule()
        text = module.speech_to_text(audio)
        
        assert text == "hello world"
        assert mock_recognize.called
    
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_speech_to_text_unknown_value(self, mock_recognize):
        """Test speech-to-text with unintelligible audio."""
        mock_recognize.side_effect = sr.UnknownValueError()
        
        data = np.random.randint(-10000, 10000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000
        )
        
        module = VoiceInputModule()
        
        with pytest.raises(RuntimeError, match="Could not understand audio"):
            module.speech_to_text(audio)
    
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_speech_to_text_request_error(self, mock_recognize):
        """Test speech-to-text with service error."""
        mock_recognize.side_effect = sr.RequestError("Network error")
        
        data = np.random.randint(-10000, 10000, size=16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000
        )
        
        module = VoiceInputModule()
        
        with pytest.raises(RuntimeError, match="Speech recognition service error"):
            module.speech_to_text(audio)


class TestAudioStream:
    """Test suite for AudioStream data class."""
    
    def test_audio_stream_creation(self):
        """Test creating a valid AudioStream."""
        data = np.zeros(16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000
        )
        
        assert audio.sample_rate == 16000
        assert audio.channels == 1
        assert audio.duration_ms == 1000
        assert audio.num_samples == 16000
        assert audio.duration_seconds == 1.0
    
    def test_audio_stream_with_noise_level(self):
        """Test AudioStream with noise level."""
        data = np.zeros(16000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=1,
            duration_ms=1000,
            noise_level_db=65.5
        )
        
        assert audio.noise_level_db == 65.5
    
    def test_audio_stream_invalid_sample_rate(self):
        """Test that invalid sample rate raises error."""
        data = np.zeros(16000, dtype=np.int16)
        
        with pytest.raises(ValueError, match="Sample rate must be positive"):
            AudioStream(
                data=data,
                sample_rate=0,
                channels=1,
                duration_ms=1000
            )
    
    def test_audio_stream_invalid_channels(self):
        """Test that invalid channel count raises error."""
        data = np.zeros(16000, dtype=np.int16)
        
        with pytest.raises(ValueError, match="Channels must be 1"):
            AudioStream(
                data=data,
                sample_rate=16000,
                channels=3,
                duration_ms=1000
            )
    
    def test_audio_stream_invalid_duration(self):
        """Test that negative duration raises error."""
        data = np.zeros(16000, dtype=np.int16)
        
        with pytest.raises(ValueError, match="Duration must be non-negative"):
            AudioStream(
                data=data,
                sample_rate=16000,
                channels=1,
                duration_ms=-100
            )
    
    def test_audio_stream_stereo(self):
        """Test creating stereo AudioStream."""
        data = np.zeros(32000, dtype=np.int16)
        audio = AudioStream(
            data=data,
            sample_rate=16000,
            channels=2,
            duration_ms=1000
        )
        
        assert audio.channels == 2
        assert audio.num_samples == 32000
