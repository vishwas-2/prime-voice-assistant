"""
Voice Input Module for PRIME Voice Assistant.

This module handles audio capture, noise filtering, speech-to-text conversion,
and pause detection for voice command processing.
"""

import time
import numpy as np
import speech_recognition as sr
from typing import Optional
from .audio_stream import AudioStream


class VoiceInputModule:
    """
    Handles voice input processing including audio capture, noise filtering,
    speech-to-text conversion, and pause detection.
    
    This module is responsible for:
    - Capturing audio from the microphone
    - Filtering background noise above threshold
    - Converting speech to text
    - Detecting command boundaries via pause detection
    """
    
    def __init__(self, noise_threshold_db: float = 70.0, pause_threshold_ms: int = 1500):
        """
        Initialize the Voice Input Module.
        
        Args:
            noise_threshold_db: Noise level threshold in decibels (default: 70dB)
            pause_threshold_ms: Pause duration threshold in milliseconds (default: 1500ms)
        """
        self.noise_threshold_db = noise_threshold_db
        self.pause_threshold_ms = pause_threshold_ms
        self.recognizer = sr.Recognizer()
        self.microphone: Optional[sr.Microphone] = None
        self.is_listening = False
        self._audio_buffer: Optional[AudioStream] = None
        
    def start_listening(self) -> None:
        """
        Start listening for voice input.
        
        Initializes the microphone and sets the listening state to active.
        This method prepares the system to capture audio input.
        """
        if not self.is_listening:
            self.microphone = sr.Microphone()
            self.is_listening = True
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
    
    def stop_listening(self) -> None:
        """
        Stop listening for voice input.
        
        Releases the microphone resource and sets the listening state to inactive.
        """
        if self.is_listening:
            self.is_listening = False
            self.microphone = None
            self._audio_buffer = None
    
    def get_audio_stream(self, duration_seconds: Optional[float] = None) -> AudioStream:
        """
        Capture audio from the microphone and return as an AudioStream.
        
        Args:
            duration_seconds: Optional duration to record. If None, records until pause detected.
        
        Returns:
            AudioStream containing the captured audio data
        
        Raises:
            RuntimeError: If not currently listening
        """
        if not self.is_listening or self.microphone is None:
            raise RuntimeError("Must call start_listening() before capturing audio")
        
        with self.microphone as source:
            if duration_seconds:
                # Record for specified duration
                audio_data = self.recognizer.record(source, duration=duration_seconds)
            else:
                # Record until pause detected
                audio_data = self.recognizer.listen(
                    source,
                    timeout=10,  # Maximum wait time for speech to start
                    phrase_time_limit=30  # Maximum phrase duration
                )
            
            # Convert to numpy array
            raw_data = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
            
            # Calculate duration
            sample_rate = audio_data.sample_rate
            duration_ms = (len(raw_data) / sample_rate) * 1000
            
            # Calculate noise level (RMS in dB)
            rms = np.sqrt(np.mean(raw_data.astype(np.float64) ** 2))
            noise_level_db = 20 * np.log10(rms + 1e-10)  # Add small value to avoid log(0)
            
            audio_stream = AudioStream(
                data=raw_data,
                sample_rate=sample_rate,
                channels=1,  # Microphone is typically mono
                duration_ms=duration_ms,
                noise_level_db=noise_level_db
            )
            
            self._audio_buffer = audio_stream
            return audio_stream
    
    def speech_to_text(self, audio: AudioStream, timeout_seconds: float = 2.0) -> str:
        """
        Convert speech audio to text using speech recognition.
        
        Args:
            audio: AudioStream containing the speech to convert
            timeout_seconds: Maximum time allowed for conversion (default: 2.0s)
        
        Returns:
            Transcribed text from the audio
        
        Raises:
            RuntimeError: If speech recognition fails or times out
        """
        start_time = time.time()
        
        try:
            # Convert AudioStream back to AudioData format for speech_recognition
            audio_data = sr.AudioData(
                audio.data.tobytes(),
                audio.sample_rate,
                2  # 2 bytes per sample for int16
            )
            
            # Perform speech recognition with timeout check
            text = self.recognizer.recognize_google(audio_data)
            
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise RuntimeError(
                    f"Speech-to-text conversion exceeded timeout: {elapsed_time:.2f}s > {timeout_seconds}s"
                )
            
            return text
            
        except sr.UnknownValueError:
            raise RuntimeError("Could not understand audio")
        except sr.RequestError as e:
            raise RuntimeError(f"Speech recognition service error: {e}")
        except Exception as e:
            raise RuntimeError(f"Speech-to-text conversion failed: {e}")
    
    def filter_noise(self, audio: AudioStream, threshold_db: Optional[float] = None) -> AudioStream:
        """
        Filter background noise from audio stream if it exceeds the threshold.
        
        Args:
            audio: AudioStream to filter
            threshold_db: Noise threshold in decibels (uses instance default if None)
        
        Returns:
            Filtered AudioStream with reduced noise
        """
        threshold = threshold_db if threshold_db is not None else self.noise_threshold_db
        
        # Check if noise filtering is needed
        if audio.noise_level_db is None or audio.noise_level_db <= threshold:
            # No filtering needed
            return audio
        
        # Apply noise reduction using improved spectral gating
        data = audio.data.astype(np.float64)
        
        # Calculate energy threshold using median absolute deviation (more robust)
        energy = np.abs(data)
        median_energy = np.median(energy)
        mad = np.median(np.abs(energy - median_energy))
        
        # Use MAD-based threshold (more robust than percentile)
        energy_threshold = median_energy + (mad * 2.0)
        
        # Create mask for signal vs noise
        signal_mask = energy > energy_threshold
        
        # Apply aggressive noise reduction
        filtered_data = np.where(
            signal_mask,
            data,  # Keep signal as-is
            data * 0.05  # Reduce noise by 95%
        )
        
        # Convert back to int16
        filtered_data = np.clip(filtered_data, -32768, 32767).astype(np.int16)
        
        # Calculate new noise level (should be significantly lower)
        rms = np.sqrt(np.mean(filtered_data.astype(np.float64) ** 2))
        new_noise_level_db = 20 * np.log10(rms + 1e-10)
        
        # Ensure noise level is actually reduced
        if new_noise_level_db >= audio.noise_level_db:
            # Apply additional filtering if needed
            filtered_data = (filtered_data * 0.7).astype(np.int16)
            rms = np.sqrt(np.mean(filtered_data.astype(np.float64) ** 2))
            new_noise_level_db = 20 * np.log10(rms + 1e-10)
        
        return AudioStream(
            data=filtered_data,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            duration_ms=audio.duration_ms,
            noise_level_db=new_noise_level_db
        )
    
    def detect_pause(self, audio: AudioStream, pause_duration_ms: Optional[int] = None) -> bool:
        """
        Detect if the audio stream contains a pause exceeding the threshold.
        
        A pause is defined as a continuous period of low energy (silence) in the audio.
        
        Args:
            audio: AudioStream to analyze
            pause_duration_ms: Pause threshold in milliseconds (uses instance default if None)
        
        Returns:
            True if a pause exceeding the threshold is detected, False otherwise
        """
        threshold_ms = pause_duration_ms if pause_duration_ms is not None else self.pause_threshold_ms
        
        # Calculate energy of audio samples
        data = audio.data.astype(np.float64)
        
        # Use a sliding window to detect silence
        window_size = int(audio.sample_rate * 0.1)  # 100ms windows
        
        # Calculate RMS energy for each window
        num_windows = len(data) // window_size
        if num_windows == 0:
            return False
        
        # Determine silence threshold (10% of max energy)
        max_energy = np.max(np.abs(data))
        silence_threshold = max_energy * 0.1
        
        # Track consecutive silent windows
        max_consecutive_silence_ms = 0
        current_silence_ms = 0
        
        for i in range(num_windows):
            window_start = i * window_size
            window_end = window_start + window_size
            window_data = data[window_start:window_end]
            
            window_energy = np.sqrt(np.mean(window_data ** 2))
            
            if window_energy < silence_threshold:
                # Silent window
                current_silence_ms += 100  # Each window is 100ms
                max_consecutive_silence_ms = max(max_consecutive_silence_ms, current_silence_ms)
            else:
                # Non-silent window, reset counter
                current_silence_ms = 0
        
        return max_consecutive_silence_ms >= threshold_ms
