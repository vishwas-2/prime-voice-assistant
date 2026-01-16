# Process Manager Implementation

## Overview

The Process Manager provides comprehensive process monitoring and management capabilities for the PRIME Voice Assistant. It enables listing running processes, monitoring resource usage, terminating processes, and setting up resource threshold alerts.

## Features

### 1. List Processes
- Lists all running processes on the system
- Returns process information including PID, name, CPU usage, memory usage, and status
- Gracefully handles inaccessible processes (access denied, zombie processes)

### 2. Get Process Info
- Retrieves detailed information about a specific process by PID
- Provides real-time CPU and memory usage statistics
- Raises appropriate exceptions for non-existent or inaccessible processes

### 3. Monitor Resources
- Monitors CPU usage, memory usage, and disk I/O for a specific process
- Returns comprehensive resource metrics:
  - CPU percentage
  - Memory in MB and percentage
  - Disk read/write in MB
  - Disk I/O rate in MB/s
- Automatically checks against configured thresholds and triggers alerts

### 4. Terminate Process
- Terminates a process by PID
- Attempts graceful termination first (SIGTERM)
- Falls back to force kill (SIGKILL) if graceful termination times out
- Should be used with Safety Controller confirmation for destructive actions

### 5. Alert Thresholds
- Configurable thresholds for CPU, memory, and disk I/O
- Default thresholds: CPU 80%, Memory 80%, Disk I/O 100 MB/s
- Supports custom alert callbacks for threshold violations
- Independent threshold management for each resource type

## Usage Examples

### Basic Usage

```python
from prime.system import ProcessManager

# Initialize the manager
pm = ProcessManager()

# List all processes
processes = pm.list_processes()
for proc in processes:
    print(f"PID: {proc.pid}, Name: {proc.name}, CPU: {proc.cpu_percent}%")

# Get info for a specific process
process_info = pm.get_process_info(1234)
print(f"Process {process_info.name} using {process_info.memory_mb:.2f} MB")

# Monitor resources
resources = pm.monitor_resources(1234)
print(f"CPU: {resources['cpu_percent']}%")
print(f"Memory: {resources['memory_mb']:.2f} MB")
print(f"Disk I/O: {resources['disk_io_mb_per_sec']:.2f} MB/s")
```

### Setting Up Alerts

```python
from prime.system import ProcessManager

pm = ProcessManager()

# Define alert callback
def handle_alert(resource, process):
    print(f"ALERT: Process {process.name} (PID {process.pid}) "
          f"exceeded {resource} threshold!")

# Set callback and thresholds
pm.set_alert_callback(handle_alert)
pm.set_alert_threshold('cpu', 90.0)
pm.set_alert_threshold('memory', 85.0)

# Monitor a process (alerts will trigger if thresholds exceeded)
pm.monitor_resources(1234)
```

### Terminating a Process

```python
from prime.system import ProcessManager

pm = ProcessManager()

# Terminate a process (should be confirmed by Safety Controller first)
try:
    pm.terminate_process(1234)
    print("Process terminated successfully")
except psutil.NoSuchProcess:
    print("Process not found")
except psutil.AccessDenied:
    print("Permission denied to terminate process")
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 10.1**: List running processes with resource usage ✓
- **Requirement 10.2**: Monitor CPU usage, memory usage, and disk I/O ✓
- **Requirement 10.3**: Alert when process consumes excessive resources ✓
- **Requirement 10.4**: Confirm before terminating process (handled by Safety Controller) ✓
- **Requirement 10.5**: Provide process details including PID, name, and resource consumption ✓

## Testing

The implementation includes comprehensive test coverage:

### Unit Tests (29 tests)
- Initialization and configuration
- Process listing and filtering
- Process information retrieval
- Resource monitoring
- Alert threshold management
- Process termination
- Error handling and edge cases

### Integration Tests (10 tests)
- Real process lifecycle management
- Multi-process monitoring
- Alert callback integration
- Resource threshold validation

All tests pass successfully, ensuring robust and reliable process management functionality.

## Dependencies

- **psutil**: Cross-platform library for process and system monitoring
  - Version: 5.9.6 or higher
  - Provides access to system processes, CPU, memory, and I/O statistics

## Error Handling

The Process Manager handles various error conditions gracefully:

- `psutil.NoSuchProcess`: Raised when a process doesn't exist
- `psutil.AccessDenied`: Raised when lacking permission to access a process
- `psutil.ZombieProcess`: Raised when a process is a zombie
- `psutil.TimeoutExpired`: Raised when process termination times out
- `ValueError`: Raised for invalid threshold configurations

## Thread Safety

The current implementation is not thread-safe. If used in a multi-threaded environment, external synchronization is required.

## Performance Considerations

- Process listing iterates through all system processes (can be slow on systems with many processes)
- CPU percentage calculation includes a 0.1-second interval for accuracy
- Resource monitoring includes disk I/O which may not be available on all platforms
- Alert callbacks are executed synchronously during monitoring

## Future Enhancements

Potential improvements for future versions:

1. Process filtering by name, user, or resource usage
2. Historical resource usage tracking
3. Process tree visualization
4. Batch operations on multiple processes
5. Asynchronous monitoring with background threads
6. Process priority management
7. Network I/O monitoring
