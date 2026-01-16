"""
Property-based tests for Voice Input Module.

This module contains property-based tests using Hypothesis to verify
the correctness properties of the Voice Input Module as specified in
the design document.
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from prime.voice import VoiceInputModule, AudioStream
import speech_recognition as sr


# ============================================================================
# Hypothesis Strategies
# ============================================================================

@st.composite
def audio_stream_strategy(draw, min_duration_ms=100, max_duration_ms=5000):
    """
    Generate random AudioStream instances for testing.
    
    Args:
        draw: Hypothesis draw function
        min_duration_ms: Minimum duration in milliseconds
        max_duration_ms: Maximum duration in milliseconds
    
    Returns:
        AudioStream with random but valid parameters
    """
    sample_rate = draw(st.sampled_from([8000, 16000, 22050, 44100, 48000]))
    duration_ms = draw(st.floats(min_value=min_duration_ms, max_value=max_duration_ms))
    channels = draw(st.sampled_from([1, 2]))
    
    # Calculate number of samples
    num_samples = int((duration_ms / 1000.0) * sample_rate * channels)
    
    # Generate random audio data
    data = np.random.randint(-32768, 32767, size=num_samples, dtype=np.int16)
    
    # Calculate noise level
    rms = np.sqrt(np.mean(data.astype(np.float64) ** 2))
    noise_level_db = 20 * np.log10(rms + 1e-10)
    
    return AudioStream(
        data=data,
        sample_rate=sample_rate,
        channels=channels,
        duration_ms=duration_ms,
        noise_level_db=noise_level_db
    )


@st.composite
def audio_with_pause_strategy(draw, pause_duration_ms=2000):
    """
    Generate AudioStream with a pause (silence) in the middle.
    
    Args:
        draw: Hypothesis draw function
        pause_duration_ms: Duration of the pause in milliseconds
    
    Returns:
        AudioStream containing audio, silence, and more audio
    """
    sample_rate = draw(st.sampled_from([16000, 44100]))
    
    # Generate audio before pause (200-1000ms)
    before_duration_ms = draw(st.floats(min_value=200, max_value=1000))
    before_samples = int((before_duration_ms / 1000.0) * sample_rate)
    before_audio = np.random.randint(-10000, 10000, size=before_samples, dtype=np.int16)
    
    # Generate silence (pause)
    pause_samples = int((pause_duration_ms / 1000.0) * sample_rate)
    silence = np.zeros(pause_samples, dtype=np.int16)
    
    # Generate audio after pause (200-1000ms)
    after_duration_ms = draw(st.floats(min_value=200, max_value=1000))
    after_samples = int((after_duration_ms / 1000.0) * sample_rate)
    after_audio = np.random.randint(-10000, 10000, size=after_samples, dtype=np.int16)
    
    # Concatenate all parts
    data = np.concatenate([before_audio, silence, after_audio])
    total_duration_ms = before_duration_ms + pause_duration_ms + after_duration_ms
    
    rms = np.sqrt(np.mean(data.astype(np.float64) ** 2))
    noise_level_db = 20 * np.log10(rms + 1e-10)
    
    return AudioStream(
        data=data,
        sample_rate=sample_rate,
        channels=1,
        duration_ms=total_duration_ms,
        noise_level_db=noise_level_db
    )


# ============================================================================
# Property 1: Audio Capture Completeness
# ============================================================================

@pytest.mark.property
class TestProperty1AudioCaptureCompleteness:
    """
    **Validates: Requirements 1.1**
    
    Property 1: Audio Capture Completeness
    For any voice command spoken by a user, the Voice_Input_Module should 
    successfully capture the audio input without data loss.
    """
    
    @given(duration=st.floats(min_value=0.1, max_value=5.0))
    @settings(max_examples=50, deadline=None)
    @patch('speech_recognition.Microphone')
    @patch('speech_recognition.Recognizer.record')
    @patch('speech_recognition.Recognizer.adjust_for_ambient_noise')
    def test_audio_capture_preserves_all_data(
        self, mock_adjust, mock_record, mock_microphone, duration
    ):
        """
        Property: Captured audio should contain all samples without data loss.
        
        For any duration of audio input, the captured AudioStream should have
        the expected number of samples based on the sample rate and duration.
        """
        # Setup
        sample_rate = 16000
        expected_samples = int(duration * sample_rate)
        
        # Create mock audio data
        mock_audio_data = Mock(spec=sr.AudioData)
        mock_audio_data.sample_rate = sample_rate
        mock_audio_data.get_raw_data.return_value = np.random.randint(
            -32768, 32767, size=expected_samples, dtype=np.int16
        ).tobytes()
        
        mock_record.return_value = mock_audio_data
        mock_mic_instance = MagicMock()
        mock_microphone.return_value = mock_mic_instance
        mock_mic_instance.__enter__ = Mock(return_value=mock_mic_instance)
        mock_mic_instance.__exit__ = Mock(return_value=False)
        
        # Execute
        module = VoiceInputModule()
        module.start_listening()
        audio_stream = module.get_audio_stream(duration_seconds=duration)
        
        # Verify: No data loss - all samples captured
        assert audio_stream.num_samples == expected_samples, \
            f"Expected {expected_samples} samples but got {audio_stream.num_samples}"
        
        # Verify: Duration is preserved
        assert abs(audio_stream.duration_seconds - duration) < 0.01, \
            f"Duration mismatch: expected {duration}s, got {audio_stream.duration_seconds}s"
        
        # Verify: Sample rate is correct
        assert audio_stream.sample_rate == sample_rate


# ============================================================================
# Property 2: Speech-to-Text Performance
# ============================================================================

@pytest.mark.property
class TestProperty2SpeechToTextPerformance:
    """
    **Validates: Requirements 1.2, 18.3**
    
    Property 2: Speech-to-Text Performance
    For any captured audio input, the Voice_Input_Module should convert 
    speech to text within 2 seconds.
    """
    
    @given(audio=audio_stream_strategy())
    @settings(max_examples=30, deadline=None)
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_speech_to_text_completes_within_timeout(self, mock_recognize, audio):
        """
        Property: Speech-to-text conversion must complete within 2 seconds.
        
        For any audio input, the conversion time should not exceed the 
        specified timeout of 2.0 seconds.
        """
        import time
        
        # Setup: Mock recognizer to return quickly
        mock_recognize.return_value = "test transcription"
        
        module = VoiceInputModule()
        
        # Execute and measure time
        start_time = time.time()
        result = module.speech_to_text(audio, timeout_seconds=2.0)
        elapsed_time = time.time() - start_time
        
        # Verify: Conversion completed within timeout
        assert elapsed_time < 2.0, \
            f"Speech-to-text took {elapsed_time:.3f}s, exceeding 2.0s timeout"
        
        # Verify: Result is a string
        assert isinstance(result, str)
        assert len(result) > 0
    
    @given(audio=audio_stream_strategy())
    @settings(max_examples=20, deadline=None)
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_speech_to_text_timeout_enforcement(self, mock_recognize, audio):
        """
        Property: System should enforce timeout and raise error if exceeded.
        
        If speech-to-text takes longer than the timeout, an error should be raised.
        """
        import time
        
        # Setup: Mock recognizer to simulate slow response
        def slow_recognize(*args, **kwargs):
            time.sleep(2.5)  # Exceed 2.0s timeout
            return "delayed transcription"
        
        mock_recognize.side_effect = slow_recognize
        
        module = VoiceInputModule()
        
        # Execute and verify timeout is enforced
        with pytest.raises(RuntimeError, match="exceeded timeout"):
            module.speech_to_text(audio, timeout_seconds=2.0)


# ============================================================================
# Property 4: Noise Filtering Threshold
# ============================================================================

@pytest.mark.property
class TestProperty4NoiseFilteringThreshold:
    """
    **Validates: Requirements 1.4**
    
    Property 4: Noise Filtering Threshold
    For any audio input with background noise exceeding 70 decibels, 
    the Voice_Input_Module should apply noise filtering before processing.
    """
    
    @given(
        base_noise_db=st.floats(min_value=71.0, max_value=100.0),
        duration_ms=st.floats(min_value=500, max_value=3000)
    )
    @settings(max_examples=50, deadline=None)
    def test_noise_above_threshold_is_filtered(self, base_noise_db, duration_ms):
        """
        Property: Audio with noise > 70dB should be filtered.
        
        For any audio with noise level exceeding 70dB, the filter_noise method
        should reduce the noise level in the output.
        """
        # Create audio with high noise level
        sample_rate = 16000
        num_samples = int((duration_ms / 1000.0) * sample_rate)
        
        # Generate data with high amplitude to ensure high dB level
        data = np.random.randint(-30000, 30000, size=num_samples, dtype=np.int16)
        
        audio = AudioStream(
            data=data,
            sample_rate=sample_rate,
            channels=1,
            duration_ms=duration_ms,
            noise_level_db=base_noise_db
        )
        
        module = VoiceInputModule(noise_threshold_db=70.0)
        
        # Execute
        filtered = module.filter_noise(audio)
        
        # Verify: Filtering was applied (noise level reduced)
        assert filtered.noise_level_db < audio.noise_level_db, \
            f"Noise level not reduced: {audio.noise_level_db}dB -> {filtered.noise_level_db}dB"
        
        # Verify: Data was modified
        assert not np.array_equal(filtered.data, audio.data), \
            "Audio data should be modified when filtering is applied"
    
    @given(
        base_noise_db=st.floats(min_value=30.0, max_value=69.0),
        duration_ms=st.floats(min_value=500, max_value=3000)
    )
    @settings(max_examples=50, deadline=None)
    def test_noise_below_threshold_not_filtered(self, base_noise_db, duration_ms):
        """
        Property: Audio with noise <= 70dB should not be filtered.
        
        For any audio with noise level at or below 70dB, the filter_noise method
        should return the audio unchanged.
        """
        # Create audio with low noise level
        sample_rate = 16000
        num_samples = int((duration_ms / 1000.0) * sample_rate)
        
        # Generate data with lower amplitude
        data = np.random.randint(-5000, 5000, size=num_samples, dtype=np.int16)
        
        audio = AudioStream(
            data=data,
            sample_rate=sample_rate,
            channels=1,
            duration_ms=duration_ms,
            noise_level_db=base_noise_db
        )
        
        module = VoiceInputModule(noise_threshold_db=70.0)
        
        # Execute
        filtered = module.filter_noise(audio)
        
        # Verify: No filtering applied (data unchanged)
        np.testing.assert_array_equal(filtered.data, audio.data,
            err_msg="Audio data should not be modified when below threshold")
        
        # Verify: Noise level unchanged
        assert filtered.noise_level_db == audio.noise_level_db


# ============================================================================
# Property 5: Pause Detection
# ============================================================================

@pytest.mark.property
class TestProperty5PauseDetection:
    """
    **Validates: Requirements 1.5**
    
    Property 5: Pause Detection
    For any audio stream with a pause exceeding 1.5 seconds, the 
    Voice_Input_Module should treat it as a command boundary.
    """
    
    @given(pause_duration_ms=st.floats(min_value=1600, max_value=5000))
    @settings(max_examples=50, deadline=None)
    def test_pause_above_threshold_detected(self, pause_duration_ms):
        """
        Property: Pauses > 1.5s should be detected as command boundaries.
        
        For any audio containing a pause exceeding 1500ms, the detect_pause
        method should return True.
        """
        # Create audio with pause exceeding threshold
        sample_rate = 16000
        
        # Audio before pause (500ms)
        before_samples = int(0.5 * sample_rate)
        before_audio = np.random.randint(-10000, 10000, size=before_samples, dtype=np.int16)
        
        # Silence (pause)
        pause_samples = int((pause_duration_ms / 1000.0) * sample_rate)
        silence = np.zeros(pause_samples, dtype=np.int16)
        
        # Audio after pause (500ms)
        after_samples = int(0.5 * sample_rate)
        after_audio = np.random.randint(-10000, 10000, size=after_samples, dtype=np.int16)
        
        # Concatenate
        data = np.concatenate([before_audio, silence, after_audio])
        total_duration_ms = 1000 + pause_duration_ms
        
        audio = AudioStream(
            data=data,
            sample_rate=sample_rate,
            channels=1,
            duration_ms=total_duration_ms
        )
        
        module = VoiceInputModule(pause_threshold_ms=1500)
        
        # Execute
        has_pause = module.detect_pause(audio)
        
        # Verify: Pause detected
        assert has_pause is True, \
            f"Pause of {pause_duration_ms}ms should be detected (threshold: 1500ms)"
    
    @given(pause_duration_ms=st.floats(min_value=100, max_value=1400))
    @settings(max_examples=50, deadline=None)
    def test_pause_below_threshold_not_detected(self, pause_duration_ms):
        """
        Property: Pauses <= 1.5s should not be detected as command boundaries.
        
        For any audio containing a pause below 1500ms, the detect_pause
        method should return False.
        """
        # Create audio with pause below threshold
        sample_rate = 16000
        
        # Audio before pause (500ms)
        before_samples = int(0.5 * sample_rate)
        before_audio = np.random.randint(-10000, 10000, size=before_samples, dtype=np.int16)
        
        # Silence (pause)
        pause_samples = int((pause_duration_ms / 1000.0) * sample_rate)
        silence = np.zeros(pause_samples, dtype=np.int16)
        
        # Audio after pause (500ms)
        after_samples = int(0.5 * sample_rate)
        after_audio = np.random.randint(-10000, 10000, size=after_samples, dtype=np.int16)
        
        # Concatenate
        data = np.concatenate([before_audio, silence, after_audio])
        total_duration_ms = 1000 + pause_duration_ms
        
        audio = AudioStream(
            data=data,
            sample_rate=sample_rate,
            channels=1,
            duration_ms=total_duration_ms
        )
        
        module = VoiceInputModule(pause_threshold_ms=1500)
        
        # Execute
        has_pause = module.detect_pause(audio)
        
        # Verify: Pause not detected
        assert has_pause is False, \
            f"Pause of {pause_duration_ms}ms should not be detected (threshold: 1500ms)"
    
    @given(audio=audio_stream_strategy(min_duration_ms=1000, max_duration_ms=3000))
    @settings(max_examples=30, deadline=None)
    def test_continuous_audio_no_pause_detected(self, audio):
        """
        Property: Continuous audio without pauses should not trigger detection.
        
        For any audio without significant silence periods, the detect_pause
        method should return False.
        """
        module = VoiceInputModule(pause_threshold_ms=1500)
        
        # Execute
        has_pause = module.detect_pause(audio)
        
        # Verify: No pause detected in continuous audio
        # (This may occasionally fail if random data happens to have low energy,
        # but should pass most of the time)
        assert has_pause is False, \
            "Continuous audio should not be detected as having a pause"
