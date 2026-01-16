# PRIME Voice Assistant - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Voice Commands Reference](#voice-commands-reference)
3. [Configuration](#configuration)
4. [Features](#features)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Getting Started

### First Launch

After installation, launch PRIME from your terminal:

```bash
prime
```

PRIME will:
1. Initialize your user profile
2. Create necessary directories in `~/.prime/`
3. Start listening for voice commands
4. Display a welcome message

### Basic Interaction

PRIME responds to natural language. You don't need to memorize exact commands. For example:

- "Open Firefox" or "Launch Firefox" or "Start Firefox browser"
- "What's the time?" or "Tell me the current time"
- "Show me my files" or "List files in this directory"

### Text Mode

If you prefer text input or voice is unavailable:

```bash
prime --text-only
```

Type your commands instead of speaking them.

## Voice Commands Reference

### Application Management

**Launch Applications:**
```
"Open [application name]"
"Launch [application name]"
"Start [application name]"
```

Examples:
- "Open Chrome"
- "Launch Visual Studio Code"
- "Start Spotify"

**Close Applications:**
```
"Close [application name]"
"Quit [application name]"
"Exit [application name]"
```

### File Operations

**Create Files:**
```
"Create a file called [filename]"
"Make a new file named [filename]"
```

**Open Files:**
```
"Open [filename]"
"Show me [filename]"
```

**Search Files:**
```
"Find files containing [text]"
"Search for [filename]"
"Show me all [file type] files"
```

**Move/Copy Files:**
```
"Move [filename] to [destination]"
"Copy [filename] to [destination]"
```

**Delete Files (Requires Confirmation):**
```
"Delete [filename]"
"Remove [filename]"
```

### System Control

**Volume Control:**
```
"Set volume to [0-100]"
"Increase volume"
"Decrease volume"
"Mute"
```

**Brightness Control:**
```
"Set brightness to [0-100]"
"Increase brightness"
"Decrease brightness"
```

**Network Management:**
```
"Connect to WiFi [network name]"
"Disconnect from WiFi"
"Show WiFi networks"
```

**System Power:**
```
"Shut down the computer" (Requires confirmation)
"Restart the computer" (Requires confirmation)
"Sleep"
```

### Process Management

**View Processes:**
```
"Show running processes"
"List all processes"
"What processes are using the most CPU?"
"What processes are using the most memory?"
```

**Terminate Processes (Requires Confirmation):**
```
"Kill process [name or PID]"
"Terminate [process name]"
"Stop [process name]"
```

### Screen Reading

**Capture Screen:**
```
"What's on my screen?"
"Read the screen"
"Describe what you see"
```

**Find UI Elements:**
```
"Where is the [button/field] named [name]?"
"Find the [element type] on screen"
```

### Notes and Reminders

**Create Notes:**
```
"Create a note: [content]"
"Take a note: [content]"
"Remember this: [content]"
```

**Search Notes:**
```
"Show my notes"
"Find notes about [topic]"
"Search notes for [keyword]"
```

**Create Reminders:**
```
"Remind me to [task] at [time]"
"Set a reminder for [task] in [duration]"
```

Examples:
- "Remind me to call John at 3pm"
- "Set a reminder for the meeting in 2 hours"

**View Reminders:**
```
"Show my reminders"
"What reminders do I have?"
```

### Task Automation

**Record Automation:**
```
"Start recording"
"Begin automation recording"
```

Then perform your actions. When done:
```
"Stop recording"
"End recording"
```

**Save Automation:**
```
"Save this automation as [name]"
```

**Run Automation:**
```
"Run automation [name]"
"Execute [automation name]"
```

**List Automations:**
```
"Show my automations"
"List saved automations"
```

### Context and References

PRIME understands context and pronouns:

```
"Open Chrome"
"Close it"  # Refers to Chrome

"Find the report.pdf file"
"Open that"  # Refers to report.pdf

"Show me the last file I opened"
"Delete the previous one"
```

### Getting Help

```
"Help"
"What can you do?"
"Show me available commands"
```

## Configuration

### Configuration File

PRIME uses a configuration file at `~/.prime/config/settings.json`:

```json
{
  "voice": {
    "enabled": true,
    "profile": "default",
    "speech_rate": 150,
    "volume": 0.8
  },
  "safety": {
    "require_confirmation": true,
    "prohibited_commands": ["hack", "bypass", "surveillance"]
  },
  "logging": {
    "level": "INFO",
    "log_to_file": true,
    "log_to_console": true
  },
  "memory": {
    "session_retention_days": 30,
    "max_storage_mb": 1024
  }
}
```

### Environment Variables

Create a `.env` file in your project directory:

```env
# Logging
PRIME_LOG_LEVEL=INFO

# Voice settings
PRIME_VOICE_ENABLED=true
PRIME_VOICE_PROFILE=default

# Safety settings
PRIME_REQUIRE_CONFIRMATION=true

# Storage
PRIME_DATA_DIR=~/.prime/data
```

### Voice Profiles

Customize voice output by creating profiles:

```python
# In Python console or script
from prime.voice.voice_output import VoiceOutputModule
from prime.models.data_models import VoiceProfile

profile = VoiceProfile(
    profile_id="custom",
    voice_name="default",
    speech_rate=175,  # Words per minute
    pitch=1.0,
    volume=0.9
)

# Save profile to config
```

## Features

### Context Awareness

PRIME remembers:
- Previous commands in the current session
- Frequently used applications
- Your preferences and habits
- Recent files and operations

This allows natural conversation:
```
"Open the file I was working on yesterday"
"Launch my usual browser"
"Show me that document again"
```

### Proactive Suggestions

PRIME learns from your patterns and suggests:
- Automation opportunities for repetitive tasks
- More efficient ways to accomplish goals
- Relevant commands based on context

### Safety Controls

PRIME protects you from accidents:

**Destructive Actions Require Confirmation:**
- File deletion
- System shutdown/restart
- Process termination
- System setting modifications

**Prohibited Operations:**
- Hacking attempts
- Security bypass
- Unauthorized surveillance
- Illegal activities

### Privacy and Security

- **Local Processing:** All voice processing happens on your machine
- **Encrypted Storage:** User data is encrypted at rest
- **No External Servers:** Your data never leaves your computer
- **Audit Logs:** All actions are logged for review

## Troubleshooting

### Voice Recognition Issues

**Problem:** PRIME doesn't understand my voice

**Solutions:**
1. Check microphone is working: `prime --test-microphone`
2. Reduce background noise
3. Speak clearly and at normal pace
4. Adjust microphone sensitivity in system settings

**Problem:** Speech-to-text is slow

**Solutions:**
1. Check internet connection (if using online service)
2. Switch to offline recognition
3. Close resource-intensive applications

### Application Launch Issues

**Problem:** "Application not found" error

**Solutions:**
1. Use full application name: "Google Chrome" not "Chrome"
2. Check application is installed
3. Add application to PATH
4. Use absolute path: "Open /Applications/Firefox.app"

### Permission Issues

**Problem:** "Permission denied" errors

**Solutions:**
1. Run PRIME with appropriate permissions
2. Check file/directory permissions
3. Use sudo for system operations (with caution)

### Performance Issues

**Problem:** PRIME is slow or unresponsive

**Solutions:**
1. Check resource usage: `prime --status`
2. Clear old session data: `prime --cleanup`
3. Reduce session retention period in config
4. Close unnecessary applications

### Common Error Messages

**"No microphone detected"**
- Check microphone is connected
- Grant microphone permissions to terminal
- Test with: `prime --test-microphone`

**"Speech recognition service unavailable"**
- Check internet connection
- Try offline mode: `prime --offline`
- Restart PRIME

**"Confirmation required"**
- This is normal for destructive actions
- Respond with "yes", "confirm", or "proceed"
- Or cancel with "no", "cancel", or "stop"

## Best Practices

### Voice Commands

1. **Speak Naturally:** Don't use robotic speech
2. **Be Specific:** "Open Firefox" is better than "Open browser"
3. **Use Context:** Reference previous commands when possible
4. **Pause Between Commands:** Wait for PRIME to respond

### Safety

1. **Review Confirmations:** Always read confirmation prompts carefully
2. **Use Descriptive Names:** For files, automations, and notes
3. **Regular Backups:** PRIME doesn't replace backups
4. **Test Automations:** Test in safe environment first

### Performance

1. **Close Unused Sessions:** Exit PRIME when not needed
2. **Clean Up Regularly:** Delete old notes and automations
3. **Monitor Resources:** Check `~/.prime/logs/` for issues
4. **Update Regularly:** Keep PRIME and dependencies updated

### Privacy

1. **Review Logs:** Check what's being recorded
2. **Clear Sensitive Data:** Use `prime --delete-user-data` if needed
3. **Secure Your Machine:** PRIME is only as secure as your system
4. **Use Strong Passwords:** For system accounts

## Advanced Usage

### Scripting with PRIME

You can script PRIME commands:

```bash
#!/bin/bash
# Automated workflow

prime --text-only << EOF
Open Visual Studio Code
Create a file called script.py
Open script.py
EOF
```

### Integration with Other Tools

PRIME can be integrated with:
- Shell scripts
- Cron jobs
- System automation tools
- CI/CD pipelines

### Custom Automations

Create complex workflows:

1. Start recording
2. Perform your workflow
3. Stop recording
4. Save with descriptive name
5. Run anytime with voice command

Example workflow:
```
"Start recording"
# Open IDE
# Create new project
# Set up git repository
# Install dependencies
"Stop recording"
"Save this automation as new-project-setup"
```

Later:
```
"Run automation new-project-setup"
```

## Getting Help

### Documentation
- User Guide: `docs/USER_GUIDE.md` (this file)
- API Documentation: `docs/API.md`
- Contributing: `CONTRIBUTING.md`

### Support
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share tips
- Wiki: Community-contributed guides

### Logs
Check logs for detailed information:
```bash
tail -f ~/.prime/logs/prime.log
```

---

**Version:** 0.1.0  
**Last Updated:** January 16, 2026  
**Status:** Alpha - Some features may be experimental
