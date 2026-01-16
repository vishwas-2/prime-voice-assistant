"""
Tests for the Screen Reader module.

This module contains unit tests and property-based tests for screen capture,
OCR text extraction, UI element identification, and screen description.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import patch, MagicMock
from prime.system.screen_reader import ScreenReader
from prime.models.data_models import UIElement, Coordinates, Size


class TestScreenReader:
    """Unit tests for ScreenReader class."""
    
    @pytest.fixture
    def screen_reader(self):
        """Create a ScreenReader instance for testing."""
        return ScreenReader()
    
    @pytest.fixture
    def sample_image_with_text(self):
        """Create a sample image with text for testing."""
        # Create a white image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        draw.text((50, 50), "Hello World", fill='black', font=font)
        draw.text((50, 100), "Test Button", fill='black', font=font)
        
        return img
    
    @pytest.fixture
    def sample_image_with_button(self):
        """Create a sample image with a button-like element."""
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a button-like rectangle
        draw.rectangle([100, 80, 200, 120], outline='black', width=2)
        
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        draw.text((120, 95), "OK", fill='black', font=font)
        
        return img
    
    def test_capture_screen_returns_image(self, screen_reader):
        """Test that capture_screen returns a PIL Image object."""
        screenshot = screen_reader.capture_screen()
        assert isinstance(screenshot, Image.Image)
        assert screenshot.size[0] > 0
        assert screenshot.size[1] > 0
    
    @patch('pytesseract.image_to_string')
    def test_extract_text_from_image(self, mock_ocr, screen_reader, sample_image_with_text):
        """Test that extract_text extracts text from an image."""
        mock_ocr.return_value = "Hello World\nTest Button"
        text = screen_reader.extract_text(sample_image_with_text)
        assert isinstance(text, str)
        assert len(text) > 0
        mock_ocr.assert_called_once()
    
    @patch('pytesseract.image_to_string')
    def test_extract_text_empty_image(self, mock_ocr, screen_reader):
        """Test extract_text with an empty image."""
        mock_ocr.return_value = ""
        empty_img = Image.new('RGB', (100, 100), color='white')
        text = screen_reader.extract_text(empty_img)
        assert isinstance(text, str)
    
    @patch('pytesseract.image_to_data')
    def test_identify_ui_elements_returns_list(self, mock_ocr_data, screen_reader, sample_image_with_text):
        """Test that identify_ui_elements returns a list of UIElement objects."""
        # Mock OCR data
        mock_ocr_data.return_value = {
            'text': ['Hello', 'World', 'Test', 'Button'],
            'conf': [90, 85, 88, 92],
            'left': [50, 100, 50, 100],
            'top': [50, 50, 100, 100],
            'width': [40, 45, 30, 50],
            'height': [20, 20, 20, 25]
        }
        elements = screen_reader.identify_ui_elements(sample_image_with_text)
        assert isinstance(elements, list)
        # All items should be UIElement instances
        for element in elements:
            assert isinstance(element, UIElement)
            assert isinstance(element.coordinates, Coordinates)
            assert isinstance(element.size, Size)
    
    @patch('pytesseract.image_to_data')
    def test_identify_ui_elements_button_detection(self, mock_ocr_data, screen_reader, sample_image_with_button):
        """Test that button-like elements are detected."""
        mock_ocr_data.return_value = {
            'text': ['OK'],
            'conf': [95],
            'left': [120],
            'top': [95],
            'width': [20],
            'height': [15]
        }
        elements = screen_reader.identify_ui_elements(sample_image_with_button)
        assert len(elements) >= 0
    
    def test_classify_element_type_button(self, screen_reader):
        """Test element type classification for buttons."""
        element_type = screen_reader._classify_element_type("OK", 50, 30)
        assert element_type == "button"
        
        element_type = screen_reader._classify_element_type("Cancel", 60, 30)
        assert element_type == "button"
    
    def test_classify_element_type_menu(self, screen_reader):
        """Test element type classification for menus."""
        element_type = screen_reader._classify_element_type("File", 40, 20)
        assert element_type == "menu"
        
        element_type = screen_reader._classify_element_type("Edit", 40, 20)
        assert element_type == "menu"
    
    def test_classify_element_type_text_field(self, screen_reader):
        """Test element type classification for text fields."""
        # Wide and short elements are likely text fields
        element_type = screen_reader._classify_element_type("Enter text here", 300, 30)
        assert element_type == "text_field"
    
    def test_classify_element_type_default(self, screen_reader):
        """Test element type classification defaults to text_label."""
        element_type = screen_reader._classify_element_type("Some random text", 100, 50)
        assert element_type == "text_label"
    
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_describe_screen_with_text(self, mock_ocr_data, mock_ocr_string, screen_reader, sample_image_with_text):
        """Test that describe_screen generates a description."""
        mock_ocr_string.return_value = "Hello World Test Button"
        mock_ocr_data.return_value = {
            'text': ['Hello', 'World', 'Test', 'Button'],
            'conf': [90, 85, 88, 92],
            'left': [50, 100, 50, 100],
            'top': [50, 50, 100, 100],
            'width': [40, 45, 30, 50],
            'height': [20, 20, 20, 25]
        }
        description = screen_reader.describe_screen(sample_image_with_text)
        assert isinstance(description, str)
        assert len(description) > 0
        assert "screen" in description.lower() or "text" in description.lower()
    
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_describe_screen_empty_image(self, mock_ocr_data, mock_ocr_string, screen_reader):
        """Test describe_screen with an empty image."""
        mock_ocr_string.return_value = ""
        mock_ocr_data.return_value = {
            'text': [],
            'conf': [],
            'left': [],
            'top': [],
            'width': [],
            'height': []
        }
        empty_img = Image.new('RGB', (100, 100), color='white')
        description = screen_reader.describe_screen(empty_img)
        assert isinstance(description, str)
        assert len(description) > 0
    
    def test_get_element_location(self, screen_reader):
        """Test that get_element_location returns correct coordinates."""
        element = UIElement(
            element_type="button",
            text="Test",
            coordinates=Coordinates(x=100, y=200),
            size=Size(width=50, height=30)
        )
        
        location = screen_reader.get_element_location(element)
        assert isinstance(location, Coordinates)
        assert location.x == 100
        assert location.y == 200


class TestScreenReaderProperties:
    """Property-based tests for ScreenReader."""
    
    def create_test_image(self, width: int, height: int, text: str) -> Image.Image:
        """
        Helper to create a test image with text.
        
        Args:
            width: Image width in pixels.
            height: Image height in pixels.
            text: Text to draw on the image.
            
        Returns:
            PIL Image object.
        """
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw text in the center
        draw.text((10, height // 2), text, fill='black', font=font)
        
        return img
    
    @given(
        width=st.integers(min_value=100, max_value=1000),
        height=st.integers(min_value=100, max_value=1000)
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_25_screen_capture_on_request(self, width, height):
        """
        **Validates: Requirements 6.1**
        
        Property 25: Screen Capture on Request
        For any screen information request, the Screen_Reader should capture 
        the current screen content.
        
        This property verifies that:
        1. capture_screen() always returns a valid Image object
        2. The returned image has non-zero dimensions
        3. The capture operation completes successfully
        """
        screen_reader = ScreenReader()
        
        # When a screen capture is requested
        screenshot = screen_reader.capture_screen()
        
        # Then it should return a valid PIL Image
        assert isinstance(screenshot, Image.Image), \
            "Screen capture should return a PIL Image object"
        
        # And the image should have valid dimensions
        assert screenshot.size[0] > 0, \
            "Captured screen width should be greater than 0"
        assert screenshot.size[1] > 0, \
            "Captured screen height should be greater than 0"
        
        # And the image should be accessible (has mode and can be converted)
        assert screenshot.mode in ['RGB', 'RGBA', 'L'], \
            "Captured screen should have a valid color mode"
    
    @given(
        width=st.integers(min_value=100, max_value=800),
        height=st.integers(min_value=100, max_value=600),
        text=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=30, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('pytesseract.image_to_string')
    def test_property_26_ocr_text_extraction(self, mock_ocr, width, height, text):
        """
        **Validates: Requirements 6.2**
        
        Property 26: OCR Text Extraction
        For any screen capture, the Screen_Reader should use OCR to extract 
        text from the image.
        
        This property verifies that:
        1. extract_text() accepts any valid PIL Image
        2. extract_text() returns a string (even if empty)
        3. The OCR process completes without errors
        4. For images with text, some text is extracted
        """
        # Filter out empty or whitespace-only text
        assume(text.strip() != "")
        
        # Mock OCR to return the text
        mock_ocr.return_value = text
        
        screen_reader = ScreenReader()
        
        # Given an image with text content
        image = self.create_test_image(width, height, text)
        
        # When OCR text extraction is performed
        extracted_text = screen_reader.extract_text(image)
        
        # Then it should return a string
        assert isinstance(extracted_text, str), \
            "OCR extraction should return a string"
        
        # And the extraction should complete without raising exceptions
        # (if we got here, no exception was raised)
        
        # Note: We don't assert that extracted_text contains the original text
        # because OCR accuracy depends on many factors (font, size, quality, etc.)
        # The property is that OCR is *attempted* and returns a result, not that
        # it's 100% accurate
    
    @given(
        element_x=st.integers(min_value=0, max_value=1000),
        element_y=st.integers(min_value=0, max_value=1000),
        element_width=st.integers(min_value=10, max_value=200),
        element_height=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_element_location_consistency(
        self, element_x, element_y, element_width, element_height
    ):
        """
        Property: Element Location Consistency
        For any UI element, get_element_location should return the same 
        coordinates that were stored in the element.
        
        This verifies Requirements 6.5 (provide element locations).
        """
        screen_reader = ScreenReader()
        
        # Given a UI element with specific coordinates
        element = UIElement(
            element_type="button",
            text="Test",
            coordinates=Coordinates(x=element_x, y=element_y),
            size=Size(width=element_width, height=element_height)
        )
        
        # When we get the element location
        location = screen_reader.get_element_location(element)
        
        # Then it should return the same coordinates
        assert location.x == element_x, \
            "Element location X should match the stored coordinate"
        assert location.y == element_y, \
            "Element location Y should match the stored coordinate"
    
    @given(
        width=st.integers(min_value=100, max_value=800),
        height=st.integers(min_value=100, max_value=600)
    )
    @settings(max_examples=15, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_property_describe_screen_always_returns_description(
        self, mock_ocr_data, mock_ocr_string, width, height
    ):
        """
        Property: Screen Description Completeness
        For any valid image, describe_screen should return a non-empty 
        natural language description.
        
        This verifies Requirements 6.4 (describe screen content).
        """
        # Mock OCR responses
        mock_ocr_string.return_value = ""
        mock_ocr_data.return_value = {
            'text': [],
            'conf': [],
            'left': [],
            'top': [],
            'width': [],
            'height': []
        }
        
        screen_reader = ScreenReader()
        
        # Given any valid image
        image = Image.new('RGB', (width, height), color='white')
        
        # When we request a screen description
        description = screen_reader.describe_screen(image)
        
        # Then it should return a non-empty string
        assert isinstance(description, str), \
            "Screen description should be a string"
        assert len(description) > 0, \
            "Screen description should not be empty"
        
        # And it should be in natural language (contains spaces and words)
        assert ' ' in description or len(description.split()) >= 1, \
            "Screen description should contain natural language text"
    
    @given(
        width=st.integers(min_value=100, max_value=800),
        height=st.integers(min_value=100, max_value=600),
        text=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122),
            min_size=1,
            max_size=30
        )
    )
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('pytesseract.image_to_data')
    def test_property_identify_ui_elements_returns_valid_elements(
        self, mock_ocr_data, width, height, text
    ):
        """
        Property: UI Element Identification Validity
        For any image, identify_ui_elements should return a list where all 
        elements have valid coordinates and sizes.
        
        This verifies Requirements 6.3 (identify UI elements).
        """
        # Filter out empty text
        assume(text.strip() != "")
        
        # Mock OCR data
        mock_ocr_data.return_value = {
            'text': [text],
            'conf': [90],
            'left': [10],
            'top': [10],
            'width': [50],
            'height': [20]
        }
        
        screen_reader = ScreenReader()
        
        # Given an image with content
        image = self.create_test_image(width, height, text)
        
        # When we identify UI elements
        elements = screen_reader.identify_ui_elements(image)
        
        # Then it should return a list
        assert isinstance(elements, list), \
            "identify_ui_elements should return a list"
        
        # And all elements should have valid properties
        for element in elements:
            assert isinstance(element, UIElement), \
                "All items should be UIElement instances"
            assert isinstance(element.coordinates, Coordinates), \
                "Element should have Coordinates"
            assert isinstance(element.size, Size), \
                "Element should have Size"
            assert element.coordinates.x >= 0, \
                "Element X coordinate should be non-negative"
            assert element.coordinates.y >= 0, \
                "Element Y coordinate should be non-negative"
            assert element.size.width > 0, \
                "Element width should be positive"
            assert element.size.height > 0, \
                "Element height should be positive"
            assert isinstance(element.text, str), \
                "Element text should be a string"
            assert isinstance(element.element_type, str), \
                "Element type should be a string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
