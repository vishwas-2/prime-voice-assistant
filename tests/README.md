# PRIME Voice Assistant - Testing Framework

This directory contains the test suite for the PRIME Voice Assistant project. The testing framework uses **pytest** for test execution and **Hypothesis** for property-based testing.

## Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── README.md                      # This file
├── test_setup_verification.py    # Sample tests to verify framework setup
├── unit/                          # Unit tests
│   ├── __init__.py
│   └── test_*.py                  # Unit test files
├── property/                      # Property-based tests
│   ├── __init__.py
│   └── test_*.py                  # Property test files
└── integration/                   # Integration tests
    ├── __init__.py
    └── test_*.py                  # Integration test files
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Tests with Verbose Output
```bash
pytest -v
```

### Run Tests in a Specific Directory
```bash
pytest tests/unit/          # Run only unit tests
pytest tests/property/      # Run only property-based tests
pytest tests/integration/   # Run only integration tests
```

### Run a Specific Test File
```bash
pytest tests/test_setup_verification.py
```

### Run Tests by Marker
```bash
pytest -m unit          # Run tests marked as unit tests
pytest -m property      # Run tests marked as property tests
pytest -m integration   # Run tests marked as integration tests
pytest -m slow          # Run slow tests
pytest -m voice         # Run voice-related tests
pytest -m system        # Run system-access tests
```

### Run Tests with Coverage
```bash
pytest --cov=prime --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Test Markers

The following markers are configured in `pytest.ini`:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.property` - Property-based tests using Hypothesis
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.voice` - Tests requiring voice input/output
- `@pytest.mark.system` - Tests requiring system access

## Writing Unit Tests

Unit tests verify specific examples and edge cases. Place unit tests in `tests/unit/`.

Example:
```python
import pytest
from prime.models import Session

class TestSession:
    def test_session_creation(self):
        """Test that a session can be created with required fields."""
        session = Session(
            session_id="test_001",
            user_id="user_123",
            start_time=datetime.now(),
            end_time=None
        )
        assert session.session_id == "test_001"
        assert session.user_id == "user_123"
```

## Writing Property-Based Tests

Property-based tests verify universal properties that should hold across all inputs. Place property tests in `tests/property/`.

Example:
```python
import pytest
from hypothesis import given, strategies as st
from prime.models import Entity

class TestEntityProperties:
    @pytest.mark.property
    @given(
        entity_type=st.text(min_size=1),
        value=st.text(),
        confidence=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_entity_confidence_range(self, entity_type, value, confidence):
        """Property: Entity confidence should always be between 0 and 1."""
        entity = Entity(
            entity_type=entity_type,
            value=value,
            confidence=confidence
        )
        assert 0.0 <= entity.confidence <= 1.0
```

### Hypothesis Strategies

Common strategies for generating test data:

- `st.integers()` - Generate integers
- `st.floats()` - Generate floating-point numbers
- `st.text()` - Generate strings
- `st.lists(strategy)` - Generate lists
- `st.dictionaries(keys, values)` - Generate dictionaries
- `st.booleans()` - Generate booleans
- `st.datetimes()` - Generate datetime objects

### Hypothesis Configuration

Hypothesis settings are configured in `pytest.ini`:
- `max_examples = 100` - Run each property test with 100 random examples
- `deadline = None` - No time limit per test case

## Writing Integration Tests

Integration tests verify that multiple components work together correctly. Place integration tests in `tests/integration/`.

Example:
```python
import pytest

@pytest.mark.integration
class TestVoiceInputFlow:
    def test_voice_to_command_flow(self):
        """Test the complete flow from voice input to command execution."""
        # Test implementation
        pass
```

## Test Fixtures

Use pytest fixtures for common test setup:

```python
import pytest
from prime.models import Session

@pytest.fixture
def sample_session():
    """Provide a sample session for testing."""
    return Session(
        session_id="test_001",
        user_id="user_123",
        start_time=datetime.now(),
        end_time=None
    )

def test_with_fixture(sample_session):
    assert sample_session.session_id == "test_001"
```

## Verifying Test Setup

Run the setup verification tests to ensure the testing framework is configured correctly:

```bash
pytest tests/test_setup_verification.py -v
```

This will verify:
- ✓ pytest is working
- ✓ Hypothesis is configured
- ✓ Test markers are recognized
- ✓ Package imports work
- ✓ Property-based testing features work

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
   - Good: `test_session_persists_command_history`
   - Bad: `test_session_1`

2. **One Assertion Per Test**: Each test should verify one specific behavior

3. **Use Markers**: Tag tests appropriately so they can be run selectively

4. **Property Tests**: Write properties that should hold for ALL inputs, not just specific examples

5. **Test Organization**: 
   - Unit tests: Test individual functions/classes in isolation
   - Property tests: Test universal properties across many inputs
   - Integration tests: Test component interactions

6. **Documentation**: Add docstrings to test classes and methods explaining what is being tested

7. **Property Validation**: For property tests validating requirements, use the format:
   ```python
   """Property: Description of the property.
   
   **Validates: Requirements X.Y**
   """
   ```

## Continuous Integration

Tests should be run automatically in CI/CD pipelines. Ensure all tests pass before merging code.

## Troubleshooting

### Import Errors
If you get import errors, ensure the project is installed in development mode:
```bash
pip install -e .
```

### Hypothesis Errors
If Hypothesis tests fail, check:
- Are the strategies generating valid inputs?
- Is the property actually universal?
- Does the code handle edge cases?

### Slow Tests
Mark slow tests with `@pytest.mark.slow` and exclude them during development:
```bash
pytest -m "not slow"
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
