"""
Intent Parser for PRIME Voice Assistant.

This module provides natural language understanding capabilities to parse
user commands, extract entities, detect ambiguity, and generate clarification
questions when needed.
"""

import re
from typing import List, Dict, Optional, Tuple
from prime.models import Intent, Entity


class IntentParser:
    """
    Parses natural language commands into structured Intent objects.
    
    The Intent Parser uses pattern matching and keyword detection to identify
    user intents and extract relevant entities from voice commands.
    """
    
    def __init__(self):
        """Initialize the Intent Parser with command patterns and entity extractors."""
        # Define intent patterns with keywords and entity types
        self.intent_patterns = {
            "launch_app": {
                "keywords": ["open", "launch", "start", "run"],
                "entity_types": ["application"],
                "patterns": [
                    r"(?:open|launch|start|run)\s+(.+)",
                ]
            },
            "adjust_volume": {
                "keywords": ["volume", "sound"],
                "entity_types": ["volume_level", "direction"],
                "patterns": [
                    r"(?:set|adjust|change)\s+(?:the\s+)?volume\s+to\s+(\d+)",
                    r"(?:turn|make)\s+(?:the\s+)?volume\s+(up|down)",
                    r"volume\s+(up|down)",
                    r"(?:increase|decrease|raise|lower)\s+(?:the\s+)?volume",
                    r"set\s+volume\s+to\s+(\d+)",
                ]
            },
            "adjust_brightness": {
                "keywords": ["brightness", "screen"],
                "entity_types": ["brightness_level", "direction"],
                "patterns": [
                    r"(?:set|adjust|change)\s+(?:the\s+)?brightness\s+to\s+(\d+)",
                    r"(?:turn|make)\s+(?:the\s+)?brightness\s+(up|down)",
                    r"brightness\s+(up|down)",
                    r"(?:increase|decrease|raise|lower)\s+(?:the\s+)?brightness",
                ]
            },
            "search_files": {
                "keywords": ["find", "search", "locate"],
                "entity_types": ["file_name", "file_type", "search_path"],
                "patterns": [
                    r"(?:find|search|locate)\s+(?:file|files)\s+(?:named|called)\s+(.+)",
                    r"(?:find|search|locate)\s+(.+)\s+(?:file|files)",
                    r"(?:find|search|locate)\s+(.+)",
                ]
            },
            "create_note": {
                "keywords": ["note", "remember", "write down"],
                "entity_types": ["note_content"],
                "patterns": [
                    r"(?:create|make|take)\s+(?:a\s+)?note\s+(.+)",
                    r"(?:remember|write\s+down)\s+(.+)",
                ]
            },
            "create_file": {
                "keywords": ["create", "make", "new", "file"],
                "entity_types": ["file_name", "file_path"],
                "patterns": [
                    r"(?:create|make)\s+(?:a\s+)?(?:new\s+)?file\s+(?:named|called)\s+(.+)",
                    r"(?:create|make)\s+(?:a\s+)?(?:new\s+)?file\s+(.+)",
                ]
            },
            "delete_file": {
                "keywords": ["delete", "remove", "erase"],
                "entity_types": ["file_name", "file_path"],
                "patterns": [
                    r"(?:delete|remove|erase)\s+(?:the\s+)?file\s+(.+)",
                    r"(?:delete|remove|erase)\s+(.+)",
                ]
            },
            "move_file": {
                "keywords": ["move", "relocate"],
                "entity_types": ["source_path", "destination_path"],
                "patterns": [
                    r"move\s+(.+)\s+to\s+(.+)",
                    r"relocate\s+(.+)\s+to\s+(.+)",
                ]
            },
            "copy_file": {
                "keywords": ["copy", "duplicate"],
                "entity_types": ["source_path", "destination_path"],
                "patterns": [
                    r"copy\s+(.+)\s+to\s+(.+)",
                    r"duplicate\s+(.+)\s+to\s+(.+)",
                ]
            },
            "shutdown_system": {
                "keywords": ["shutdown", "power off", "turn off"],
                "entity_types": [],
                "patterns": [
                    r"(?:shutdown|power\s+off|turn\s+off)\s+(?:the\s+)?(?:computer|system|pc)",
                    r"shutdown",
                ]
            },
            "restart_system": {
                "keywords": ["restart", "reboot", "computer", "system"],
                "entity_types": [],
                "patterns": [
                    r"(?:restart|reboot)\s+(?:the\s+)?(?:computer|system|pc)",
                    r"^(?:restart|reboot)$",
                ]
            },
            "manage_wifi": {
                "keywords": ["wifi", "wi-fi", "wireless"],
                "entity_types": ["action", "network_name"],
                "patterns": [
                    r"(?:turn|switch)\s+(on|off)\s+(?:the\s+)?(?:wifi|wi-fi)",
                    r"(?:connect|disconnect)\s+(?:to\s+)?(?:wifi|wi-fi)\s+(.+)",
                    r"(?:wifi|wi-fi)\s+(on|off)",
                ]
            },
            "manage_bluetooth": {
                "keywords": ["bluetooth"],
                "entity_types": ["action", "device_name"],
                "patterns": [
                    r"(?:turn|switch)\s+(on|off)\s+(?:the\s+)?bluetooth",
                    r"(?:connect|disconnect)\s+(?:to\s+)?bluetooth\s+(?:device\s+)?(.+)",
                    r"bluetooth\s+(on|off)",
                ]
            },
            "list_processes": {
                "keywords": ["list", "show", "processes", "running"],
                "entity_types": [],
                "patterns": [
                    r"(?:list|show)\s+(?:all\s+)?(?:running\s+)?processes",
                    r"what(?:'s|\s+is)\s+running",
                ]
            },
            "terminate_process": {
                "keywords": ["kill", "terminate", "stop", "close"],
                "entity_types": ["process_name", "pid"],
                "patterns": [
                    r"(?:kill|terminate|stop|close)\s+(?:the\s+)?process\s+(.+)",
                    r"(?:kill|terminate|stop|close)\s+(.+)",
                ]
            },
            "read_screen": {
                "keywords": ["read", "screen", "what's on"],
                "entity_types": [],
                "patterns": [
                    r"(?:read|describe)\s+(?:the\s+)?screen",
                    r"what(?:'s|\s+is)\s+on\s+(?:the\s+)?screen",
                ]
            },
            "create_reminder": {
                "keywords": ["remind", "reminder"],
                "entity_types": ["reminder_content", "time"],
                "patterns": [
                    r"remind\s+me\s+to\s+(.+)\s+(?:at|in)\s+(.+)",
                    r"(?:create|set)\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)\s+(?:at|in)\s+(.+)",
                ]
            },
            "unknown": {
                "keywords": [],
                "entity_types": [],
                "patterns": []
            }
        }
        
        # Common words to filter out when extracting entities
        self.stop_words = {
            "the", "a", "an", "to", "from", "in", "on", "at", "for", "with",
            "by", "of", "and", "or", "but", "is", "are", "was", "were",
            "please", "can", "you", "could", "would"
        }
    
    def parse(self, text: str) -> Intent:
        """
        Parse a natural language command into an Intent object.
        
        Args:
            text: The natural language command text
            
        Returns:
            Intent object containing the parsed intent type, entities, confidence,
            and whether clarification is required
        """
        if not text or not text.strip():
            return Intent(
                intent_type="unknown",
                entities=[],
                confidence=0.0,
                requires_clarification=True
            )
        
        # Normalize the text
        normalized_text = text.lower().strip()
        
        # Try to match against known patterns
        best_match = None
        best_confidence = 0.0
        matched_entities = []
        
        for intent_type, pattern_info in self.intent_patterns.items():
            if intent_type == "unknown":
                continue
            
            # Check if any keywords are present
            keyword_matches = sum(
                1 for keyword in pattern_info["keywords"]
                if keyword in normalized_text
            )
            
            if keyword_matches > 0:
                # Try to match specific patterns
                for pattern in pattern_info["patterns"]:
                    match = re.search(pattern, normalized_text, re.IGNORECASE)
                    if match:
                        # Calculate confidence based on keyword matches and pattern match
                        confidence = min(0.9, 0.5 + (keyword_matches * 0.2))
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = intent_type
                            # Extract entities from regex groups
                            matched_entities = self._extract_entities_from_match(
                                match, pattern_info["entity_types"]
                            )
                        break
        
        # If no pattern matched but keywords were found, use keyword-based matching
        if best_match is None:
            for intent_type, pattern_info in self.intent_patterns.items():
                if intent_type == "unknown":
                    continue
                
                keyword_matches = sum(
                    1 for keyword in pattern_info["keywords"]
                    if keyword in normalized_text
                )
                
                if keyword_matches > 0:
                    confidence = min(0.7, 0.3 + (keyword_matches * 0.2))
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = intent_type
                        # Extract entities using generic extraction
                        matched_entities = self.extract_entities(normalized_text)
        
        # Determine if clarification is needed
        requires_clarification = (
            best_match is None or
            best_confidence < 0.5 or
            (len(matched_entities) == 0 and self.intent_patterns.get(best_match, {}).get("entity_types", []))
        )
        
        return Intent(
            intent_type=best_match or "unknown",
            entities=matched_entities,
            confidence=best_confidence,
            requires_clarification=requires_clarification
        )
    
    def _extract_entities_from_match(
        self, match: re.Match, entity_types: List[str]
    ) -> List[Entity]:
        """
        Extract entities from regex match groups.
        
        Args:
            match: The regex match object
            entity_types: List of expected entity types
            
        Returns:
            List of Entity objects
        """
        entities = []
        groups = match.groups()
        
        for i, group in enumerate(groups):
            if group:
                entity_type = entity_types[i] if i < len(entity_types) else "generic"
                # Clean up the entity value
                cleaned_value = group.strip()
                
                # Try to convert to number if it looks like one
                if cleaned_value.isdigit():
                    entities.append(Entity(
                        entity_type="number",
                        value=int(cleaned_value),
                        confidence=0.9
                    ))
                else:
                    entities.append(Entity(
                        entity_type=entity_type,
                        value=cleaned_value,
                        confidence=0.8
                    ))
        
        return entities
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text using generic extraction methods.
        
        This method identifies potential entities like numbers, file paths,
        application names, and other relevant information from the command text.
        
        Args:
            text: The command text to extract entities from
            
        Returns:
            List of Entity objects found in the text
        """
        entities = []
        normalized_text = text.lower().strip()
        
        # Extract numbers (potential volume levels, brightness, etc.)
        number_pattern = r'\b(\d+)\b'
        for match in re.finditer(number_pattern, normalized_text):
            entities.append(Entity(
                entity_type="number",
                value=int(match.group(1)),
                confidence=0.9
            ))
        
        # Extract file paths (basic detection)
        # Windows paths: C:\path\to\file or \\network\path
        # Unix paths: /path/to/file or ~/path
        path_patterns = [
            r'([A-Za-z]:\\(?:[^\s\\]+\\)*[^\s\\]+)',  # Windows absolute
            r'(\\\\[^\s\\]+(?:\\[^\s\\]+)+)',  # UNC paths
            r'(/(?:[^\s/]+/)*[^\s/]+)',  # Unix absolute
            r'(~/(?:[^\s/]+/)*[^\s/]+)',  # Unix home-relative
        ]
        
        for pattern in path_patterns:
            for match in re.finditer(pattern, text):  # Use original text for paths
                entities.append(Entity(
                    entity_type="file_path",
                    value=match.group(1),
                    confidence=0.85
                ))
        
        # Extract quoted strings (often file names or specific values)
        quoted_pattern = r'["\']([^"\']+)["\']'
        for match in re.finditer(quoted_pattern, text):
            entities.append(Entity(
                entity_type="quoted_string",
                value=match.group(1),
                confidence=0.9
            ))
        
        # Extract potential application names (capitalized words)
        app_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        for match in re.finditer(app_pattern, text):
            app_name = match.group(1)
            # Filter out common words
            if app_name.lower() not in self.stop_words:
                entities.append(Entity(
                    entity_type="application",
                    value=app_name,
                    confidence=0.7
                ))
        
        # Extract direction indicators
        direction_pattern = r'\b(up|down|increase|decrease|raise|lower|higher|lower)\b'
        for match in re.finditer(direction_pattern, normalized_text):
            direction = match.group(1)
            # Normalize to up/down
            if direction in ["increase", "raise", "higher"]:
                direction = "up"
            elif direction in ["decrease", "lower"]:
                direction = "down"
            entities.append(Entity(
                entity_type="direction",
                value=direction,
                confidence=0.85
            ))
        
        return entities
    
    def is_ambiguous(self, intent: Intent) -> bool:
        """
        Determine if an intent is ambiguous and requires clarification.
        
        An intent is considered ambiguous if:
        - The confidence is below threshold (< 0.5)
        - Required entities are missing
        - Multiple interpretations are possible
        
        Args:
            intent: The Intent object to check
            
        Returns:
            True if the intent is ambiguous, False otherwise
        """
        # Check if already marked as requiring clarification
        if intent.requires_clarification:
            return True
        
        # Check confidence threshold
        if intent.confidence < 0.5:
            return True
        
        # Check if intent is unknown
        if intent.intent_type == "unknown":
            return True
        
        # Check if required entities are missing for specific intents
        required_entities = {
            "launch_app": ["application"],
            "search_files": ["file_name", "quoted_string", "file_path"],
            "create_file": ["file_name", "quoted_string", "file_path"],
            "delete_file": ["file_name", "quoted_string", "file_path"],
            "move_file": ["source_path", "destination_path"],
            "copy_file": ["source_path", "destination_path"],
            "terminate_process": ["process_name", "pid"],
            "create_note": ["note_content"],
            "create_reminder": ["reminder_content", "time"],
        }
        
        if intent.intent_type in required_entities:
            required = required_entities[intent.intent_type]
            entity_types = [e.entity_type for e in intent.entities]
            
            # Check if at least one required entity type is present
            has_required = any(req in entity_types for req in required)
            if not has_required:
                return True
        
        return False
    
    def generate_clarification_question(self, intent: Intent) -> str:
        """
        Generate a clarification question for an ambiguous intent.
        
        Args:
            intent: The Intent object that needs clarification
            
        Returns:
            A natural language question to clarify the user's intent
        """
        # Handle unknown intents
        if intent.intent_type == "unknown" or intent.confidence < 0.3:
            return "I'm not sure what you want me to do. Could you please rephrase your request?"
        
        # Handle low confidence intents
        if intent.confidence < 0.5:
            intent_descriptions = {
                "launch_app": "launch an application",
                "adjust_volume": "adjust the volume",
                "adjust_brightness": "adjust the brightness",
                "search_files": "search for files",
                "create_file": "create a file",
                "delete_file": "delete a file",
                "move_file": "move a file",
                "copy_file": "copy a file",
                "shutdown_system": "shutdown the system",
                "restart_system": "restart the system",
                "manage_wifi": "manage Wi-Fi",
                "manage_bluetooth": "manage Bluetooth",
                "list_processes": "list running processes",
                "terminate_process": "terminate a process",
                "read_screen": "read the screen",
                "create_note": "create a note",
                "create_reminder": "create a reminder",
            }
            
            description = intent_descriptions.get(intent.intent_type, "perform an action")
            return f"Did you want me to {description}?"
        
        # Handle missing entities
        missing_entity_questions = {
            "launch_app": "Which application would you like me to launch?",
            "search_files": "What file are you looking for?",
            "create_file": "What should I name the new file?",
            "delete_file": "Which file would you like me to delete?",
            "move_file": "Where would you like me to move the file to?",
            "copy_file": "Where would you like me to copy the file to?",
            "terminate_process": "Which process would you like me to terminate?",
            "create_note": "What would you like me to note down?",
            "create_reminder": "What should I remind you about, and when?",
        }
        
        if intent.intent_type in missing_entity_questions:
            return missing_entity_questions[intent.intent_type]
        
        # Default clarification
        return "Could you provide more details about what you'd like me to do?"
