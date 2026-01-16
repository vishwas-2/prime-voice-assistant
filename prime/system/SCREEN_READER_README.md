# Screen Reader Module

## Overview

The Screen Reader module provides functionality to capture screen content, extract text using OCR (Optical Character Recognition), identify UI elements, and describe screen content in natural language.

## Features

- **Screen Capture**: Capture the current screen content as a PIL Image
- **OCR Text Extraction**: Extract text from images using Tesseract OCR
- **UI Element Identification**: Identify UI elements like buttons, menus, and text fields
- **Screen Description**: Generate natural language descriptions of screen content
- **Element Location**: Retrieve coordinates of identified UI elements

## Dependencies

### Python Packages
- `Pillow` (PIL): For image manipulation and screen capture
- `pytesseract`: Python wrapper for Tesseract OCR

### System Requirements
- **Tesseract OCR**: The Tesseract OCR engine must be installed on your system
  - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
  - **Linux**: `sudo apt-get install tesseract-ocr`
  - **macOS**: `brew install tesseract`

## Installation

1. Install Python dependencies:
```bash
pip install Pillow pytesseract
```

2. Install Tesseract OCR (system-level):
   - Follow the instructions for your operating system above
   - Make sure `tesseract` is in your system PATH, or configure the path in ScreenReader:

```python
from prime.system import ScreenReader

# If tesseract is not in PATH, specify the path
screen_reader = ScreenReader(tesseract_cmd='/path/to/tesseract')
```

## Usage

### Basic Usage

```python
from prime.system import ScreenReader

# Create a Screen Reader instance
screen_reader = ScreenReader()

# Capture the current screen
screenshot = screen_reader.capture_screen()

# Extract text from the screenshot
text = screen_reader.extract_text(screenshot)
print(f"Extracted text: {text}")

# Identify UI elements
elements = screen_reader.identify_ui_elements(screenshot)
for element in elements:
    print(f"{element.element_type}: {element.text} at ({element.coordinates.x}, {element.coordinates.y})")

# Get a natural language description
description = screen_reader.describe_screen(screenshot)
print(f"Screen description: {description}")

# Get element location
if elements:
    location = screen_reader.get_element_location(elements[0])
    print(f"First element location: ({location.x}, {location.y})")
```

### Working with Images

```python
from PIL import Image
from prime.system import ScreenReader

screen_reader = ScreenReader()

# Load an image from file
image = Image.open('screenshot.png')

# Extract text
text = screen_reader.extract_text(image)

# Identify UI elements
elements = screen_reader.identify_ui_elements(image)
```

## Implementation Details

### Screen Capture
Uses `PIL.ImageGrab.grab()` to capture the entire screen. Returns a PIL Image object.

### OCR Text Extraction
Uses Tesseract OCR via the `pytesseract` library to extract text from images. The accuracy depends on:
- Image quality
- Text size and font
- Contrast between text and background
- Language settings

### UI Element Identification
Uses OCR data with bounding boxes to identify text-based UI elements. The classification is heuristic-based:
- **Buttons**: Keywords like "OK", "Cancel", "Submit", etc.
- **Menus**: Keywords like "File", "Edit", "View", etc.
- **Text Fields**: Wide, short elements
- **Text Labels**: Default classification

For production use, consider integrating computer vision models for more accurate UI element detection.

### Screen Description
Generates natural language descriptions by:
1. Extracting text and counting words
2. Identifying and counting UI elements by type
3. Highlighting notable elements (e.g., button names)

## Testing

The module includes comprehensive unit tests and property-based tests:

```bash
# Run all tests
python -m pytest prime/system/test_screen_reader.py -v

# Run only property-based tests
python -m pytest prime/system/test_screen_reader.py::TestScreenReaderProperties -v
```

### Property-Based Tests

- **Property 25**: Screen Capture on Request (validates Requirements 6.1)
- **Property 26**: OCR Text Extraction (validates Requirements 6.2)

## Limitations

1. **OCR Accuracy**: OCR is not 100% accurate and depends on image quality
2. **UI Element Detection**: Current implementation uses heuristics; may not detect all element types
3. **Language Support**: Default Tesseract configuration; may need language packs for non-English text
4. **Performance**: Screen capture and OCR can be slow for large images

## Future Improvements

1. Integrate computer vision models (e.g., YOLO, Faster R-CNN) for better UI element detection
2. Add support for accessibility APIs (e.g., UI Automation on Windows, Accessibility API on macOS)
3. Implement caching for repeated screen captures
4. Add support for region-specific captures
5. Improve element classification with machine learning

## Requirements Validation

This module validates the following requirements from the PRIME Voice Assistant specification:

- **6.1**: Capture screen content on request ✓
- **6.2**: Use OCR to extract text from screen captures ✓
- **6.3**: Identify UI elements (buttons, text fields, menus) ✓
- **6.4**: Describe screen content in natural language ✓
- **6.5**: Provide element locations and suggest interactions ✓

## License

Part of the PRIME Voice Assistant project.
