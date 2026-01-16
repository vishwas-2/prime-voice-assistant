# PRIME Voice Assistant - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Voice Processing](#voice-processing)
3. [Natural Language](#natural-language)
4. [Command Execution](#command-execution)
5. [System Interface](#system-interface)
6. [Persistence](#persistence)
7. [Utilities](#utilities)
8. [Data Models](#data-models)

## Overview

PRIME provides a modular API for voice-controlled system interaction. All components are designed to work together seamlessly while remaining independently testable.

### Basic Usage

```python
from prime.voice.voice_input import VoiceInputModule
from prime.voice.voice_output import VoiceOutputModule
from prime.nlp.intent_parser import IntentParser
from prime.nlp.context_engine import ContextEngine
from prime.execution.command_executor import CommandExecutor

# Initialize components
voice_input = VoiceInputModule()
voice_output = VoiceOutputModule()
intent_parser = IntentParser()
context_engine = ContextEngine()
command_executor = CommandExecutor()

# Process voice command
voice_input.start_listening()
audio = voice_input.get_audio_stream()
text = voice_input.speech_to_text(audio)
intent = intent_parser.parse(text)
command = context_engine.process_command(text, session)
result = command_executor.execute(command)
voice_output.text_to_speech(result.output)
```

## Voice Processing

### VoiceInputModule

Handles audio capture and speech-to-text conversion.

#### Constructor

```python
VoiceInputModule(
    noise_threshold_db: float = 70.0,
    pause_threshold_ms: int = 1500
)
```

**Parameters:**
- `noise_threshold_db`: Noise level threshold in decibels
- `pause_threshold_ms`: Pause duration threshold in milliseconds

#### Methods

##### start_listening()

Start listening for voice input.

```python
voice_input.start_listening()
```

##### stop_listening()

Stop listening for voice input.

```python
voice_input.stop_listening()
```

##### get_audio_stream(duration_seconds=None)

Capture audio from microphone.

```python
audio = voice_input.get_audio_stream(duration_seconds=5.0)
```

**Parameters:**
- `duration_seconds`: Optional recording duration

**Returns:** `AudioStream` object

##### speech_to_text(audio, timeout_seconds=2.0)

Convert speech to text.

```python
text = voice_input.speech_to_text(audio)
```

**Parameters:**
- `audio`: AudioStream to convert
- `timeout_seconds`: Maximum conversion time

**Returns:** Transcribed text string

**Raises:** `RuntimeError` if conversion fails

##### filter_noise(audio, threshold_db=None)

Filter background noise from audio.

```python
filtered = voice_input.filter_noise(audio, threshold_db=75.0)
```

**Parameters:**
- `audio`: AudioStream to filter
- `threshold_db`: Optional noise threshold

**Returns:** Filtered AudioStream

##### detect_pause(audio, pause_duration_ms=None)

Detect if audio contains a pause.

```python
has_pause = voice_input.detect_pause(audio)
```

**Parameters:**
- `audio`: AudioStream to analyze
- `pause_duration_ms`: Optional pause threshold

**Returns:** Boolean indicating pause detection

### VoiceOutputModule

Handles text-to-speech and audio playback.

#### Constructor

```python
VoiceOutputModule(voice_profile: Optional[VoiceProfile] = None)
```

**Parameters:**
- `voice_profile`: Optional initial voice profile

#### Methods

##### text_to_speech(text, voice_profile=None)

Convert text to speech audio.

```python
audio = voice_output.text_to_speech("Hello, world!")
```

**Parameters:**
- `text`: Text to convert
- `voice_profile`: Optional voice profile

**Returns:** AudioStream with speech audio

**Raises:** `ValueError` if text is empty

##### play_audio(audio)

Play audio stream.

```python
voice_output.play_audio(audio)
```

**Parameters:**
- `audio`: AudioStream to play

**Raises:** `RuntimeError` if playback already in progress

##### set_voice_profile(profile)

Set voice profile for speech generation.

```python
profile = VoiceProfile(
    profile_id="custom",
    voice_name="default",
    speech_rate=150.0,
    pitch=1.0,
    volume=0.8
)
voice_output.set_voice_profile(profile)
```

**Parameters:**
- `profile`: VoiceProfile to use

**Raises:** `ValueError` if profile is invalid

##### adjust_speech_rate(rate)

Adjust speech rate.

```python
voice_output.adjust_speech_rate(175.0)
```

**Parameters:**
- `rate`: Speech rate in words per minute

**Raises:** `ValueError` if rate is invalid

##### stop_playback()

Stop current audio playback.

```python
voice_output.stop_playback()
```

## Natural Language

### IntentParser

Parses natural language commands into structured intents.

#### Methods

##### parse(text)

Parse text into intent.

```python
intent = intent_parser.parse("open Firefox")
```

**Parameters:**
- `text`: Natural language text

**Returns:** Intent object

##### extract_entities(text)

Extract entities from text.

```python
entities = intent_parser.extract_entities("open Firefox")
```

**Parameters:**
- `text`: Text to analyze

**Returns:** List of Entity objects

##### is_ambiguous(intent)

Check if intent is ambiguous.

```python
if intent_parser.is_ambiguous(intent):
    question = intent_parser.generate_clarification_question(intent)
```

**Parameters:**
- `intent`: Intent to check

**Returns:** Boolean

##### generate_clarification_question(intent)

Generate clarification question for ambiguous intent.

```python
question = intent_parser.generate_clarification_question(intent)
```

**Parameters:**
- `intent`: Ambiguous intent

**Returns:** Clarification question string

### ContextEngine

Maintains conversation context and resolves references.

#### Methods

##### process_command(text, session)

Process command with context.

```python
intent = context_engine.process_command("open it", session)
```

**Parameters:**
- `text`: Command text
- `session`: Current session

**Returns:** Intent object

##### resolve_reference(reference, session)

Resolve pronoun reference.

```python
entity = context_engine.resolve_reference("it", session)
```

**Parameters:**
- `reference`: Reference to resolve
- `session`: Current session

**Returns:** Entity object or None

##### add_to_history(command, result, session)

Add command to history.

```python
context_engine.add_to_history(command, result, session)
```

**Parameters:**
- `command`: Command string
- `result`: CommandResult object
- `session`: Current session

##### get_suggestions(session)

Get proactive suggestions.

```python
suggestions = context_engine.get_suggestions(session)
```

**Parameters:**
- `session`: Current session

**Returns:** List of suggestion strings

## Command Execution

### CommandExecutor

Executes system commands and operations.

#### Methods

##### execute(command)

Execute a command.

```python
result = command_executor.execute(command)
```

**Parameters:**
- `command`: Command object

**Returns:** CommandResult object

##### launch_application(app_name)

Launch an application.

```python
process = command_executor.launch_application("Firefox")
```

**Parameters:**
- `app_name`: Application name

**Returns:** Process handle

**Raises:** `RuntimeError` if launch fails

##### adjust_volume(level)

Adjust system volume.

```python
command_executor.adjust_volume(50)
```

**Parameters:**
- `level`: Volume level (0-100)

##### adjust_brightness(level)

Adjust screen brightness.

```python
command_executor.adjust_brightness(75)
```

**Parameters:**
- `level`: Brightness level (0-100)

##### get_execution_status(command_id)

Get command execution status.

```python
status = command_executor.get_execution_status(command_id)
```

**Parameters:**
- `command_id`: Command identifier

**Returns:** ExecutionStatus object

### AutomationEngine

Records and executes automation sequences.

#### Methods

##### start_recording()

Start recording automation.

```python
session = automation_engine.start_recording()
```

**Returns:** RecordingSession object

##### stop_recording(session)

Stop recording and get sequence.

```python
sequence = automation_engine.stop_recording(session)
```

**Parameters:**
- `session`: RecordingSession to stop

**Returns:** AutomationSequence object

##### execute_sequence(sequence)

Execute automation sequence.

```python
result = automation_engine.execute_sequence(sequence)
```

**Parameters:**
- `sequence`: AutomationSequence to execute

**Returns:** Execution result dictionary

##### save_sequence(name, sequence)

Save automation sequence.

```python
automation_engine.save_sequence("my_workflow", sequence)
```

**Parameters:**
- `name`: Sequence name
- `sequence`: AutomationSequence to save

##### load_sequence(name)

Load saved sequence.

```python
sequence = automation_engine.load_sequence("my_workflow")
```

**Parameters:**
- `name`: Sequence name

**Returns:** AutomationSequence object

##### simulate_keyboard(keys)

Simulate keyboard input.

```python
automation_engine.simulate_keyboard("hello world")
automation_engine.simulate_keyboard("ctrl+c")
```

**Parameters:**
- `keys`: Keys to type or key combination

##### simulate_mouse(action, coordinates)

Simulate mouse action.

```python
coords = Coordinates(x=100, y=200)
automation_engine.simulate_mouse("click", coords)
```

**Parameters:**
- `action`: Mouse action ("click", "double_click", "right_click", "move")
- `coordinates`: Coordinates object

## System Interface

### FileSystemInterface

Provides file system operations.

#### Methods

##### create_file(path, content)

Create a new file.

```python
file_system.create_file("test.txt", "Hello, world!")
```

##### read_file(path)

Read file contents.

```python
content = file_system.read_file("test.txt")
```

##### update_file(path, content)

Update file contents.

```python
file_system.update_file("test.txt", "Updated content")
```

##### delete_file(path)

Delete a file.

```python
file_system.delete_file("test.txt")
```

##### search_files(query, search_path)

Search for files.

```python
files = file_system.search_files("*.py", "/home/user")
```

##### move_file(source, destination)

Move a file.

```python
file_system.move_file("old.txt", "new.txt")
```

##### copy_file(source, destination)

Copy a file.

```python
file_system.copy_file("source.txt", "dest.txt")
```

##### get_file_metadata(path)

Get file metadata.

```python
metadata = file_system.get_file_metadata("test.txt")
```

### ProcessManager

Manages system processes.

#### Methods

##### list_processes()

List all running processes.

```python
processes = process_manager.list_processes()
```

**Returns:** List of Process objects

##### get_process_info(pid)

Get process information.

```python
info = process_manager.get_process_info(1234)
```

**Parameters:**
- `pid`: Process ID

**Returns:** ProcessInfo object

##### monitor_resources(pid)

Monitor process resources.

```python
usage = process_manager.monitor_resources(1234)
```

**Parameters:**
- `pid`: Process ID

**Returns:** ResourceUsage object

##### terminate_process(pid)

Terminate a process.

```python
process_manager.terminate_process(1234)
```

**Parameters:**
- `pid`: Process ID

##### set_alert_threshold(resource, threshold)

Set resource alert threshold.

```python
process_manager.set_alert_threshold("cpu", 80.0)
```

**Parameters:**
- `resource`: Resource type
- `threshold`: Threshold value

### ScreenReader

Captures and interprets screen content.

#### Methods

##### capture_screen()

Capture current screen.

```python
image = screen_reader.capture_screen()
```

**Returns:** Image object

##### extract_text(image)

Extract text from image using OCR.

```python
text = screen_reader.extract_text(image)
```

**Parameters:**
- `image`: Image to process

**Returns:** Extracted text string

##### identify_ui_elements(image)

Identify UI elements in image.

```python
elements = screen_reader.identify_ui_elements(image)
```

**Parameters:**
- `image`: Image to analyze

**Returns:** List of UIElement objects

##### describe_screen(image)

Generate natural language description of screen.

```python
description = screen_reader.describe_screen(image)
```

**Parameters:**
- `image`: Image to describe

**Returns:** Description string

## Persistence

### MemoryManager

Manages persistent storage with encryption.

#### Methods

##### store_preference(key, value, user_id)

Store user preference.

```python
memory_manager.store_preference("theme", "dark", "user123")
```

##### get_preference(key, user_id)

Get user preference.

```python
theme = memory_manager.get_preference("theme", "user123")
```

##### save_session(session)

Save session to storage.

```python
memory_manager.save_session(session)
```

##### load_session(session_id)

Load session from storage.

```python
session = memory_manager.load_session("session123")
```

##### store_note(note, user_id)

Store a note.

```python
note = Note(
    note_id="note1",
    content="Meeting notes",
    tags=["work"],
    created_at=datetime.now(),
    updated_at=datetime.now()
)
memory_manager.store_note(note, "user123")
```

##### search_notes(query, user_id)

Search notes.

```python
notes = memory_manager.search_notes("meeting", "user123")
```

##### create_reminder(reminder, user_id)

Create a reminder.

```python
reminder = Reminder(
    reminder_id="rem1",
    content="Call John",
    due_time=datetime.now() + timedelta(hours=2),
    is_completed=False
)
memory_manager.create_reminder(reminder, "user123")
```

##### get_due_reminders(user_id)

Get due reminders.

```python
reminders = memory_manager.get_due_reminders("user123")
```

##### delete_user_data(user_id)

Delete all user data.

```python
memory_manager.delete_user_data("user123")
```

## Utilities

### ResourceMonitor

Monitors system resource usage.

#### Methods

##### get_current_usage()

Get current resource usage.

```python
usage = monitor.get_current_usage()
print(f"CPU: {usage.cpu_percent}%")
print(f"Memory: {usage.memory_mb}MB")
```

##### is_within_limits(usage=None)

Check if within resource limits.

```python
limits = monitor.is_within_limits()
if not limits["overall_ok"]:
    print("Resource limits exceeded!")
```

##### start_monitoring()

Start continuous monitoring.

```python
monitor.start_monitoring()
```

##### stop_monitoring()

Stop monitoring.

```python
monitor.stop_monitoring()
```

##### cleanup_resources()

Perform resource cleanup.

```python
monitor.cleanup_resources()
```

### ErrorHandler

Handles errors with user-friendly messages.

#### Methods

##### format_error(error, context=None)

Format error into user-friendly message.

```python
error_info = ErrorHandler.format_error(
    FileNotFoundError("test.txt"),
    context={"file_path": "test.txt"}
)
```

**Returns:** Dictionary with message, category, suggestions, technical_details

##### create_error(message, category, suggestions, technical_details)

Create PRIMEError.

```python
error = ErrorHandler.create_error(
    message="Custom error",
    category=ErrorCategory.COMMAND_EXECUTION,
    suggestions=["Try this", "Or that"]
)
```

##### print_error(error_info)

Print formatted error to console.

```python
ErrorHandler.print_error(error_info)
```

### Performance Utilities

#### Caching

```python
from prime.utils.performance import cached

@cached(max_size=256)
def expensive_function(x, y):
    return x + y
```

#### Profiling

```python
from prime.utils.performance import profile

@profile("operation_name")
def my_function():
    # ... code ...
    pass

# Get stats
stats = get_performance_stats()
```

## Data Models

### Session

```python
@dataclass
class Session:
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    command_history: List[CommandRecord]
    context_state: Dict[str, Any]
```

### Intent

```python
@dataclass
class Intent:
    intent_type: str
    entities: List[Entity]
    confidence: float
    requires_clarification: bool
```

### Command

```python
@dataclass
class Command:
    command_id: str
    intent: Intent
    parameters: Dict[str, Any]
    timestamp: datetime
    requires_confirmation: bool
```

### CommandResult

```python
@dataclass
class CommandResult:
    command_id: str
    success: bool
    output: str
    error: Optional[str]
    execution_time_ms: int
```

### VoiceProfile

```python
@dataclass
class VoiceProfile:
    profile_id: str
    voice_name: str
    speech_rate: float
    pitch: float
    volume: float
```

### AutomationSequence

```python
@dataclass
class AutomationSequence:
    sequence_id: str
    name: str
    actions: List[Action]
    created_at: datetime
```

## Error Handling

All PRIME methods raise appropriate exceptions:

- `RuntimeError`: For operational errors
- `ValueError`: For invalid parameters
- `FileNotFoundError`: For missing files
- `PermissionError`: For permission issues
- `PRIMEError`: For PRIME-specific errors

Always wrap PRIME calls in try-except blocks:

```python
try:
    result = command_executor.execute(command)
except PRIMEError as e:
    print(f"Error: {e.message}")
    for suggestion in e.suggestions:
        print(f"  - {suggestion}")
```

## Best Practices

1. **Always initialize components before use**
2. **Handle exceptions appropriately**
3. **Clean up resources when done**
4. **Use context managers where available**
5. **Monitor resource usage**
6. **Enable logging for debugging**
7. **Validate user input**
8. **Use type hints**

## Examples

See `docs/USER_GUIDE.md` for complete usage examples.

---

**Version:** 0.1.0  
**Last Updated:** January 16, 2026
