# Command Executor

The Command Executor is a core component of the PRIME Voice Assistant's Execution Layer. It is responsible for executing system commands, launching applications, and managing command execution status.

## Overview

The Command Executor implements the following key functionality:

- **Command Execution**: Executes commands with safety checks and error handling
- **Application Launching**: Launches applications within 3 seconds (Requirement 4.1)
- **Status Tracking**: Provides real-time status updates during execution (Requirement 4.4)
- **Error Reporting**: Reports errors with clear, user-friendly explanations (Requirement 4.5)
- **Safety Integration**: Integrates with Safety Controller to block prohibited commands

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Executor                          │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ execute()      │  │ launch_app()   │  │ get_status() │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Execution State Tracking                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Safety Controller│
                    └──────────────────┘
```

## Usage

### Basic Usage

```python
from prime.execution import CommandExecutor
from prime.models import Command, Intent, Entity
from datetime import datetime

# Create a command executor
executor = CommandExecutor()

# Create a command to launch an application
intent = Intent(
    intent_type="launch_app",
    entities=[Entity("application", "notepad", 0.9)],
    confidence=0.9,
    requires_clarification=False
)

command = Command(
    command_id="cmd-001",
    intent=intent,
    parameters={},
    timestamp=datetime.now(),
    requires_confirmation=False
)

# Execute the command
result = executor.execute(command)

if result.success:
    print(f"Success: {result.output}")
else:
    print(f"Error: {result.error}")
```

### With Status Callback

```python
def status_callback(command_id: str, message: str):
    print(f"[{command_id}] {message}")

executor = CommandExecutor(status_callback=status_callback)
result = executor.execute(command)
```

### Direct Application Launch

```python
executor = CommandExecutor()

try:
    process = executor.launch_application("notepad")
    print(f"Launched application with PID: {process.pid}")
except FileNotFoundError as e:
    print(f"Application not found: {e}")
```

### Checking Execution Status

```python
executor = CommandExecutor()
result = executor.execute(command)

# Get execution status
status = executor.get_execution_status(command.command_id)

print(f"Status: {status.status}")
print(f"Progress: {status.progress_message}")
print(f"Execution time: {status.end_time - status.start_time}")
```

## API Reference

### CommandExecutor

#### `__init__(safety_controller=None, logger=None, status_callback=None)`

Initialize the Command Executor.

**Parameters:**
- `safety_controller` (SafetyController, optional): Safety controller for command validation
- `logger` (Logger, optional): Logger instance for logging
- `status_callback` (Callable, optional): Callback function for status updates

#### `execute(command: Command) -> CommandResult`

Execute a command and return the result.

**Parameters:**
- `command` (Command): The command to execute

**Returns:**
- `CommandResult`: Result of the command execution

**Validates:**
- Requirements 4.4: Provides real-time status updates
- Requirements 4.5: Reports errors with clear explanations

#### `launch_application(app_name: str) -> subprocess.Popen`

Launch an application by name.

**Parameters:**
- `app_name` (str): Name or path of the application to launch

**Returns:**
- `subprocess.Popen`: Process handle for the launched application

**Raises:**
- `FileNotFoundError`: If the application cannot be found
- `subprocess.SubprocessError`: If the application fails to launch

**Validates:**
- Requirements 4.1: Launches application within 3 seconds

#### `get_execution_status(command_id: str) -> Optional[ExecutionState]`

Get the current execution status of a command.

**Parameters:**
- `command_id` (str): The ID of the command to check

**Returns:**
- `ExecutionState` or `None`: Current execution state if tracked, None otherwise

**Validates:**
- Requirements 4.4: Provides real-time status updates

### ExecutionStatus (Enum)

Represents the status of command execution:

- `PENDING`: Command is waiting to be executed
- `IN_PROGRESS`: Command is currently executing
- `COMPLETED`: Command completed successfully
- `FAILED`: Command failed during execution
- `CANCELLED`: Command was cancelled

### ExecutionState

Represents the current state of a command execution:

**Attributes:**
- `command_id` (str): The command ID
- `status` (ExecutionStatus): Current execution status
- `start_time` (datetime): When execution started
- `end_time` (Optional[datetime]): When execution ended
- `progress_message` (Optional[str]): Current progress message
- `result` (Optional[CommandResult]): Final result if completed

## Safety Integration

The Command Executor integrates with the Safety Controller to ensure safe command execution:

1. **Prohibited Command Blocking**: Commands related to hacking, security bypass, or illegal activities are blocked
2. **Destructive Action Confirmation**: Destructive actions require explicit user confirmation (handled by Safety Controller)
3. **Security Event Logging**: Security-relevant events are logged for audit purposes

Example of prohibited command handling:

```python
# This command will be blocked
intent = Intent(
    intent_type="execute_command",
    entities=[Entity("command", "hack the system", 0.9)],
    confidence=0.9,
    requires_clarification=False
)

command = Command(
    command_id="cmd-002",
    intent=intent,
    parameters={},
    timestamp=datetime.now(),
    requires_confirmation=False
)

result = executor.execute(command)
# result.success will be False
# result.error will explain that the command is prohibited
```

## Error Handling

The Command Executor provides clear, user-friendly error messages:

### FileNotFoundError
```
Could not find application 'myapp'. Please check the application name and try again.
```

### PermissionError
```
Permission denied. PRIME does not have the necessary permissions to perform this action.
You may need to run PRIME with elevated privileges or check file permissions.
```

### Unimplemented Commands
```
Command type 'future_feature' is not yet implemented.
```

### Missing Parameters
```
No application name specified. Please specify which application to launch.
```

## Performance

The Command Executor is designed to meet the following performance requirements:

- **Application Launch**: Applications launch within 3 seconds (Requirement 4.1)
- **Status Updates**: Real-time status updates are provided during execution (Requirement 4.4)
- **Error Reporting**: Errors are reported immediately with clear explanations (Requirement 4.5)

## Testing

The Command Executor is thoroughly tested with:

- **Property-Based Tests**: 7 tests validating Properties 15, 17, and 18
- **Unit Tests**: 16 tests covering all methods and edge cases
- **Integration Tests**: Full execution flow testing

Run tests with:

```bash
# Property-based tests
pytest tests/property/test_command_executor_properties.py -v

# Unit tests
pytest tests/unit/test_command_executor.py -v

# All tests
pytest tests/property/test_command_executor_properties.py tests/unit/test_command_executor.py -v
```

## Future Enhancements

The following features are planned for future releases:

- System settings adjustment (volume, brightness, Wi-Fi, Bluetooth)
- File operations (create, read, update, delete)
- Process management (list, monitor, terminate)
- Multi-step command execution
- Command history and replay
- Asynchronous command execution

## Related Components

- **Safety Controller** (`prime/safety/safety_controller.py`): Validates commands for safety
- **Data Models** (`prime/models/data_models.py`): Defines Command and CommandResult structures
- **Context Engine** (`prime/nlp/context_engine.py`): Processes commands and maintains context
- **Intent Parser** (`prime/nlp/intent_parser.py`): Parses natural language into intents

## References

- **Requirements**: 4.1, 4.2, 4.4, 4.5
- **Properties**: 15 (Application Launch Performance), 17 (Status Update Delivery), 18 (Error Reporting)
- **Design Document**: `.kiro/specs/prime-voice-assistant/design.md`
