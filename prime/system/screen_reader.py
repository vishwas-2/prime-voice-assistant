"""
Screen Reader module for PRIME Voice Assistant.

This module provides functionality to capture screen content, extract text using OCR,
identify UI elements, and describe screen content in natural language.
"""

from typing import List, Optional
from PIL import Image, ImageGrab
import pytesseract
from prime.models.data_models import UIElement, Coordinates, Size


class ScreenReader:
    """
    Screen Reader component that captures and interprets screen content.
    
    Responsibilities:
    - Capture screen content
    - Extract text using OCR
    - Identify UI elements
    - Describe screen layout
    - Provide element coordinates
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the Screen Reader.
        
        Args:
            tesseract_cmd: Optional path to tesseract executable.
                          If not provided, assumes tesseract is in PATH.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def capture_screen(self) -> Image.Image:
        """
        Capture the current screen content.
        
        Returns:
            PIL Image object containing the screen capture.
            
        Validates: Requirements 6.1
        """
        # Capture the entire screen
        screenshot = ImageGrab.grab()
        return screenshot
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image: PIL Image object to extract text from.
            
        Returns:
            Extracted text as a string.
            
        Validates: Requirements 6.2
        """
        # Use pytesseract to extract text from the image
        text = pytesseract.image_to_string(image)
        return text.strip()
    
    def identify_ui_elements(self, image: Image.Image) -> List[UIElement]:
        """
        Identify UI elements (buttons, text fields, menus) in the image.
        
        This is a simplified implementation that uses OCR data to identify
        text-based UI elements. A more sophisticated implementation would use
        computer vision models for UI element detection.
        
        Args:
            image: PIL Image object to analyze.
            
        Returns:
            List of identified UIElement objects.
            
        Validates: Requirements 6.3
        """
        ui_elements = []
        
        # Get detailed OCR data including bounding boxes
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Process each detected text element
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            # Filter out empty text and low confidence detections
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i])
            
            if text and conf > 30:  # Confidence threshold
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                # Heuristic to classify element type based on text and size
                element_type = self._classify_element_type(text, w, h)
                
                ui_element = UIElement(
                    element_type=element_type,
                    text=text,
                    coordinates=Coordinates(x=x, y=y),
                    size=Size(width=w, height=h)
                )
                ui_elements.append(ui_element)
        
        return ui_elements
    
    def _classify_element_type(self, text: str, width: int, height: int) -> str:
        """
        Classify UI element type based on text content and dimensions.
        
        This is a heuristic-based classification. A production system would
        use machine learning models for more accurate classification.
        
        Args:
            text: The text content of the element.
            width: Width of the element in pixels.
            height: Height of the element in pixels.
            
        Returns:
            Element type as a string.
        """
        text_lower = text.lower()
        
        # Button heuristics
        button_keywords = ['ok', 'cancel', 'submit', 'save', 'delete', 'close', 
                          'yes', 'no', 'apply', 'confirm', 'next', 'back']
        if any(keyword in text_lower for keyword in button_keywords):
            return "button"
        
        # Menu heuristics
        menu_keywords = ['file', 'edit', 'view', 'help', 'tools', 'window']
        if any(keyword in text_lower for keyword in menu_keywords):
            return "menu"
        
        # Text field heuristics (typically wider than tall)
        if width > height * 3 and len(text) < 50:
            return "text_field"
        
        # Default to text label
        return "text_label"
    
    def describe_screen(self, image: Image.Image) -> str:
        """
        Describe screen content in natural language.
        
        Args:
            image: PIL Image object to describe.
            
        Returns:
            Natural language description of the screen content.
            
        Validates: Requirements 6.4
        """
        # Extract text and UI elements
        text = self.extract_text(image)
        ui_elements = self.identify_ui_elements(image)
        
        # Build description
        description_parts = []
        
        # Add overall text content summary
        if text:
            word_count = len(text.split())
            description_parts.append(f"The screen contains approximately {word_count} words of text.")
        else:
            description_parts.append("The screen appears to have minimal or no text content.")
        
        # Summarize UI elements by type
        if ui_elements:
            element_counts = {}
            for element in ui_elements:
                element_type = element.element_type
                element_counts[element_type] = element_counts.get(element_type, 0) + 1
            
            element_summary = []
            for element_type, count in element_counts.items():
                element_summary.append(f"{count} {element_type}{'s' if count > 1 else ''}")
            
            description_parts.append(f"Identified UI elements: {', '.join(element_summary)}.")
            
            # Mention some specific elements
            buttons = [e for e in ui_elements if e.element_type == "button"]
            if buttons:
                button_texts = [b.text for b in buttons[:3]]  # First 3 buttons
                description_parts.append(f"Notable buttons: {', '.join(button_texts)}.")
        else:
            description_parts.append("No distinct UI elements were identified.")
        
        return " ".join(description_parts)
    
    def get_element_location(self, element: UIElement) -> Coordinates:
        """
        Get the location of a UI element.
        
        Args:
            element: UIElement to get location for.
            
        Returns:
            Coordinates of the element.
            
        Validates: Requirements 6.5
        """
        return element.coordinates
