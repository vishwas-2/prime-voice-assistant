# PRIME Voice Assistant - Deployment Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Installation Methods](#installation-methods)
3. [Platform-Specific Instructions](#platform-specific-instructions)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Distribution](#distribution)
7. [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

Before deploying PRIME, ensure:

- [ ] All tests pass (run `pytest`)
- [ ] Code is formatted (run `black prime/ tests/`)
- [ ] No linting errors (run `flake8 prime/`)
- [ ] Documentation is up to date
- [ ] Version number is updated in `setup.py`
- [ ] CHANGELOG is updated
- [ ] Dependencies are pinned in `requirements.txt`
- [ ] Security audit completed

## Installation Methods

### Method 1: PyPI Installation (Recommended for Users)

Once published to PyPI:

```bash
pip install prime-voice-assistant
```

### Method 2: From Source (For Development)

```bash
git clone https://github.com/yourusername/prime-voice-assistant.git
cd prime-voice-assistant
pip install -e .
```

### Method 3: From Distribution Package

```bash
pip install prime-voice-assistant-0.1.0.tar.gz
```

## Platform-Specific Instructions

### Windows

#### Prerequisites
1. **Python 3.9+**
   ```powershell
   # Download from python.org or use Microsoft Store
   python --version
   ```

2. **Tesseract OCR**
   - Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to default location: `C:\Program Files\Tesseract-OCR`
   - Add to PATH: `C:\Program Files\Tesseract-OCR`

3. **PyAudio**
   ```powershell
   pip install pipwin
   pipwin install pyaudio
   ```

#### Installation
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install PRIME
pip install prime-voice-assistant

# Download spaCy model
python -m spacy download en_core_web_sm

# Test installation
prime --version
```

#### Common Issues
- **Microphone Access:** Grant microphone permissions in Windows Settings
- **PyAudio Installation:** Use `pipwin` as shown above
- **Tesseract Not Found:** Ensure PATH is set correctly

### macOS

#### Prerequisites
1. **Homebrew** (if not installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **System Dependencies**
   ```bash
   brew install python@3.11 portaudio tesseract
   ```

#### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PRIME
pip install prime-voice-assistant

# Download spaCy model
python -m spacy download en_core_web_sm

# Test installation
prime --version
```

#### Common Issues
- **Microphone Access:** Grant microphone permissions in System Preferences > Security & Privacy
- **PyAudio Build Errors:** Ensure portaudio is installed via Homebrew
- **Permission Errors:** Use `sudo` only if necessary

### Linux (Ubuntu/Debian)

#### Prerequisites
```bash
# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    tesseract-ocr \
    libtesseract-dev
```

#### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PRIME
pip install prime-voice-assistant

# Download spaCy model
python -m spacy download en_core_web_sm

# Test installation
prime --version
```

#### Common Issues
- **PyAudio Errors:** Install `portaudio19-dev` before pip install
- **Tesseract Not Found:** Install `tesseract-ocr` package
- **Permission Issues:** Add user to audio group: `sudo usermod -a -G audio $USER`

### Linux (Fedora/RHEL)

#### Prerequisites
```bash
# Install system dependencies
sudo dnf install -y \
    python3 \
    python3-pip \
    portaudio-devel \
    tesseract \
    tesseract-devel
```

#### Installation
Same as Ubuntu/Debian after prerequisites.

## Configuration

### Post-Installation Setup

1. **Create Configuration Directory**
   ```bash
   mkdir -p ~/.prime/{config,data,logs}
   ```

2. **Create Default Configuration**
   ```bash
   prime --init-config
   ```

3. **Set Environment Variables**
   
   Create `~/.prime/.env`:
   ```env
   PRIME_LOG_LEVEL=INFO
   PRIME_VOICE_ENABLED=true
   PRIME_DATA_DIR=~/.prime/data
   ```

4. **Download Language Models**
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Configuration Files

**Main Config:** `~/.prime/config/settings.json`
```json
{
  "voice": {
    "enabled": true,
    "profile": "default",
    "speech_rate": 150
  },
  "safety": {
    "require_confirmation": true
  },
  "logging": {
    "level": "INFO"
  }
}
```

## Testing

### Verify Installation

```bash
# Check version
prime --version

# Test microphone
prime --test-microphone

# Test speech recognition
prime --test-speech

# Run system check
prime --check-system
```

### Run Test Suite

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=prime --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/property/
```

### Manual Testing Checklist

- [ ] Voice input works
- [ ] Voice output works
- [ ] Application launching works
- [ ] File operations work
- [ ] Safety confirmations work
- [ ] Notes and reminders work
- [ ] Automation recording/playback works
- [ ] Screen reading works
- [ ] Process management works

## Distribution

### Building Distribution Packages

#### Source Distribution
```bash
python setup.py sdist
```

Output: `dist/prime-voice-assistant-0.1.0.tar.gz`

#### Wheel Distribution
```bash
pip install wheel
python setup.py bdist_wheel
```

Output: `dist/prime_voice_assistant-0.1.0-py3-none-any.whl`

#### Both
```bash
python setup.py sdist bdist_wheel
```

### Publishing to PyPI

#### Test PyPI (Recommended First)
```bash
# Install twine
pip install twine

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ prime-voice-assistant
```

#### Production PyPI
```bash
# Upload to PyPI
twine upload dist/*

# Verify
pip install prime-voice-assistant
```

### Creating Releases

#### GitHub Release
1. Tag the release:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. Create release on GitHub:
   - Go to Releases
   - Click "Create a new release"
   - Select tag v0.1.0
   - Add release notes
   - Attach distribution files

#### Release Checklist
- [ ] Version bumped in `setup.py`
- [ ] CHANGELOG updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Git tag created
- [ ] GitHub release created
- [ ] PyPI package published
- [ ] Release announcement posted

## Docker Deployment (Optional)

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install PRIME
RUN pip install -e .

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Create data directory
RUN mkdir -p /root/.prime

# Set entrypoint
ENTRYPOINT ["prime"]
```

### Build and Run

```bash
# Build image
docker build -t prime-voice-assistant .

# Run container
docker run -it \
  --device /dev/snd \
  -v ~/.prime:/root/.prime \
  prime-voice-assistant
```

## Continuous Integration/Deployment

### GitHub Actions Example

`.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

## Troubleshooting

### Installation Issues

**Problem:** `pip install` fails with compilation errors

**Solution:**
- Ensure system dependencies are installed
- Try using pre-built wheels: `pip install --only-binary :all: prime-voice-assistant`
- Check Python version compatibility

**Problem:** Import errors after installation

**Solution:**
- Verify installation: `pip show prime-voice-assistant`
- Check Python path: `python -c "import sys; print(sys.path)"`
- Reinstall: `pip uninstall prime-voice-assistant && pip install prime-voice-assistant`

### Runtime Issues

**Problem:** "No module named 'prime'"

**Solution:**
- Ensure virtual environment is activated
- Reinstall in development mode: `pip install -e .`

**Problem:** Microphone not working

**Solution:**
- Check system permissions
- Test with: `prime --test-microphone`
- Verify audio device: `python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_default_input_device_info())"`

### Performance Issues

**Problem:** Slow startup

**Solution:**
- Preload spaCy models
- Use SSD for data directory
- Reduce logging level

**Problem:** High memory usage

**Solution:**
- Clear old session data
- Reduce session retention period
- Limit automation sequence size

## Security Considerations

### Before Deployment

1. **Review Code:** Audit for security vulnerabilities
2. **Update Dependencies:** Ensure all dependencies are up to date
3. **Secure Storage:** Verify encryption is working
4. **Access Control:** Set appropriate file permissions
5. **Logging:** Ensure no sensitive data in logs

### Production Recommendations

1. **Use HTTPS:** For any web interfaces
2. **Limit Permissions:** Run with minimal required permissions
3. **Regular Updates:** Keep PRIME and dependencies updated
4. **Monitor Logs:** Watch for suspicious activity
5. **Backup Data:** Regular backups of user data

## Support

### Getting Help

- **Documentation:** Check `docs/` directory
- **Issues:** Report on GitHub
- **Community:** Join discussions

### Reporting Issues

When reporting deployment issues, include:
- Operating system and version
- Python version
- Installation method
- Error messages
- Steps to reproduce

---

**Version:** 0.1.0  
**Last Updated:** January 16, 2026  
**Maintainer:** PRIME Development Team
