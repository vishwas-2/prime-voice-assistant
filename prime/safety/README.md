# Safety Controller

The Safety Controller is a critical component of the PRIME Voice Assistant that validates and confirms potentially destructive operations, blocks prohibited commands, and logs security-relevant events.

## Overview

The Safety Controller implements the safety and security requirements (5.1-5.6, 10.4) by:

- **Classifying actions** as safe, destructive, or prohibited
- **Requiring confirmation** for destructive actions before execution
- **Validating user confirmations** with explicit keywords
- **Blocking prohibited operations** related to hacking, security bypass, or illegal activities
- **Logging security events** for audit and monitoring

## Usage

### Basic Usage

```python
from prime.safety import SafetyController
from prime.models import Command, Intent, Entity
from datetime import datetime

# Create a safety controller
controller = SafetyController()

# Create a command
intent = Intent(
    intent_type="delete_file",
    entities=[Entity("file_name", "important.txt", 0.9)],
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

# Classify the action
action_type = controller.classify_action(command)

# Check if confirmation is required
if controller.requires_confirmation(action_type):
    # Generate confirmation prompt
    prompt = controller.generate_confirmation_prompt(command)
    print(prompt)
    
    # Get user response
    user_response = input("Your response: ")
    
    # Validate confirmation
    if controller.validate_confirmation(user_response):
        print("Action confirmed - proceeding...")
        # Execute the command
    elif controller.is_abortion(user_response):
        print("Action aborted by user")
    else:
        print("Invalid response - action cancelled")
```

### Action Classification

The Safety Controller classifies commands into three categories:

1. **SAFE**: Normal operations that don't require confirmation
   - Launching applications
   - Adjusting volume
   - Searching files
   - Reading information

2. **DESTRUCTIVE**: Operations that modify or delete data
   - File deletion (`delete_file`, `remove_file`)
   - System shutdown/restart (`shutdown`, `restart`, `reboot`)
   - Process termination (`terminate_process`, `kill_process`)
   - Setting modifications (`modify_setting`, `change_setting`)

3. **PROHIBITED**: Operations that should never be executed
   - Hacking-related commands
   - Security bypass attempts
   - Unauthorized surveillance
   - Illegal activities

### Confirmation Workflow

For destructive actions, the Safety Controller implements a confirmation workflow:

1. **Classify** the command
2. **Check** if confirmation is required
3. **Generate** a clear confirmation prompt
4. **Wait** for user response
5. **Validate** the response
6. **Execute** or **abort** based on validation

### Confirmation Keywords

**Accepted confirmation words** (case-insensitive):
- `yes`
- `confirm`
- `proceed`
- `continue`
- `ok`
- `okay`

**Abortion words** (case-insensitive):
- `no`
- `cancel`
- `stop`
- `abort`
- `nevermind`
- `never mind`

### Security Event Logging

The Safety Controller logs security-relevant events with appropriate severity levels:

```python
from prime.safety.safety_controller import SecurityEvent
from datetime import datetime

# Create a security event
event = SecurityEvent(
    event_type="destructive_action_confirmed",
    command_id="cmd-001",
    description="User confirmed file deletion",
    timestamp=datetime.now(),
    severity="warning"  # "info", "warning", or "critical"
)

# Log the event
controller.log_security_event(event)
```

**Severity levels:**
- `info`: Normal security checks and confirmations
- `warning`: Suspicious or potentially dangerous actions
- `critical`: Prohibited actions or security violations

## Requirements Validation

The Safety Controller validates the following requirements:

- **Requirement 5.1**: Requires explicit confirmation before destructive actions
- **Requirement 5.2**: Classifies file deletion, shutdown, restart, and setting modifications as destructive
- **Requirement 5.3**: Clearly describes actions and consequences in confirmation prompts
- **Requirement 5.4**: Waits for explicit "yes", "confirm", or "proceed" before allowing execution
- **Requirement 5.5**: Aborts on "no", "cancel", or "stop"
- **Requirement 5.6**: Never executes prohibited commands
- **Requirement 10.4**: Requires confirmation before process termination

## Properties Verified

The Safety Controller has been verified against the following correctness properties:

- **Property 19**: Destructive actions require confirmation
- **Property 20**: Confirmation messages are complete and clear
- **Property 21**: Only valid confirmation words allow execution
- **Property 22**: Abortion words properly cancel actions
- **Property 23**: Prohibited commands are blocked
- **Property 24**: Process termination requires confirmation

## Testing

The Safety Controller has comprehensive test coverage:

- **33 unit tests** covering individual methods and edge cases
- **12 property-based tests** verifying correctness properties across many inputs
- **10 integration tests** validating complete workflows

Run all tests:
```bash
pytest tests/unit/test_safety_controller.py \
       tests/property/test_safety_properties.py \
       tests/integration/test_safety_integration.py -v
```

## Architecture

The Safety Controller is part of the Safety and Security Layer in the PRIME architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Layer                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ Safety       │ │ Command      │ │ Automation       │   │
│  │ Controller   │ │ Executor     │ │ Engine           │   │
│  └──────────────┘ └──────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

The Safety Controller sits between the Command Executor and the actual system operations, providing a security gate that validates all potentially dangerous operations.

## API Reference

### SafetyController

#### Methods

- `classify_action(command: Command) -> ActionType`
  - Classifies a command as SAFE, DESTRUCTIVE, or PROHIBITED

- `requires_confirmation(action: ActionType) -> bool`
  - Determines if an action requires user confirmation

- `generate_confirmation_prompt(command: Command) -> str`
  - Generates a clear confirmation prompt describing the action and consequences

- `validate_confirmation(response: str) -> bool`
  - Validates if a user response confirms the action

- `is_abortion(response: str) -> bool`
  - Checks if a user response indicates abortion

- `is_prohibited(command: Command) -> bool`
  - Checks if a command is prohibited

- `log_security_event(event: SecurityEvent) -> None`
  - Logs a security-relevant event

### ActionType (Enum)

- `SAFE`: Normal operations
- `DESTRUCTIVE`: Operations requiring confirmation
- `PROHIBITED`: Blocked operations

### SecurityEvent (Dataclass)

- `event_type: str` - Type of security event
- `command_id: str` - ID of the related command
- `description: str` - Human-readable description
- `timestamp: datetime` - When the event occurred
- `severity: str` - "info", "warning", or "critical"

## Future Enhancements

Potential improvements for future versions:

1. **Configurable keyword lists**: Allow users to customize destructive/prohibited keywords
2. **Machine learning classification**: Use ML to improve action classification
3. **User-specific policies**: Different confirmation requirements per user
4. **Audit trail**: Persistent storage of all security events
5. **Rate limiting**: Prevent rapid-fire destructive commands
6. **Multi-factor confirmation**: Require additional verification for critical actions
