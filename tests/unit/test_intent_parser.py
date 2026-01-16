"""
Unit tests for Intent Parser.

Tests cover:
- Common command patterns
- Entity extraction
- Ambiguity detection
- Clarification question generation
"""

import pytest
from prime.nlp import IntentParser
from prime.models import Intent, Entity


class TestIntentParserBasicCommands:
    """Test parsing of common command patterns."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()
    
    def test_parse_launch_app_simple(self):
        """Test parsing simple application launch commands."""
        result = self.parser.parse("open Chrome")
        assert result.intent_type == "launch_app"
        assert result.confidence > 0.5
        assert len(result.entities) > 0
    
    def test_parse_launch_app_variations(self):
        """Test various ways to launch applications."""
        commands = [
            "launch Firefox",
            "start Notepad",
            "run Calculator",
            "open Visual Studio Code"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "launch_app", f"Failed for: {cmd}"
            assert result.confidence > 0.5
    
    def test_parse_adjust_volume_with_level(self):
        """Test volume adjustment with specific level."""
        result = self.parser.parse("set volume to 50")
        assert result.intent_type == "adjust_volume"
        assert result.confidence > 0.5
        # Check for number entity
        number_entities = [e for e in result.entities if e.entity_type == "number"]
        assert len(number_entities) > 0
        assert number_entities[0].value == 50
    
    def test_parse_adjust_volume_direction(self):
        """Test volume adjustment with direction."""
        commands = [
            ("volume up", "adjust_volume"),
            ("turn volume down", "adjust_volume"),
            ("increase volume", "adjust_volume"),
            ("decrease the volume", "adjust_volume")
        ]
        
        for cmd, expected_intent in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == expected_intent, f"Failed for: {cmd}"
    
    def test_parse_adjust_brightness(self):
        """Test brightness adjustment commands."""
        commands = [
            "set brightness to 75",
            "brightness up",
            "increase brightness",
            "make brightness down"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "adjust_brightness", f"Failed for: {cmd}"
            assert result.confidence > 0.5
    
    def test_parse_search_files(self):
        """Test file search commands."""
        commands = [
            "find file named report.pdf",
            "search for document.txt",
            "locate myfile.docx"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "search_files", f"Failed for: {cmd}"
    
    def test_parse_create_file(self):
        """Test file creation commands."""
        result = self.parser.parse("create a file named test.txt")
        assert result.intent_type == "create_file"
        assert result.confidence > 0.5
    
    def test_parse_delete_file(self):
        """Test file deletion commands."""
        commands = [
            "delete file oldfile.txt",
            "remove the file temp.log",
            "erase backup.bak"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "delete_file", f"Failed for: {cmd}"
    
    def test_parse_move_file(self):
        """Test file move commands."""
        result = self.parser.parse("move file.txt to /home/user/documents")
        assert result.intent_type == "move_file"
        assert len(result.entities) >= 2  # Should have source and destination
    
    def test_parse_copy_file(self):
        """Test file copy commands."""
        result = self.parser.parse("copy report.pdf to backup folder")
        assert result.intent_type == "copy_file"
    
    def test_parse_shutdown_system(self):
        """Test system shutdown commands."""
        commands = [
            "shutdown the computer",
            "power off the system",
            "turn off pc",
            "shutdown"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "shutdown_system", f"Failed for: {cmd}"
    
    def test_parse_restart_system(self):
        """Test system restart commands."""
        commands = [
            "restart the computer",
            "reboot the system",
            "restart"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "restart_system", f"Failed for: {cmd}"
    
    def test_parse_manage_wifi(self):
        """Test Wi-Fi management commands."""
        commands = [
            ("turn on wifi", "manage_wifi"),
            ("switch off wi-fi", "manage_wifi"),
            ("connect to wifi MyNetwork", "manage_wifi")
        ]
        
        for cmd, expected_intent in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == expected_intent, f"Failed for: {cmd}"
    
    def test_parse_manage_bluetooth(self):
        """Test Bluetooth management commands."""
        commands = [
            "turn on bluetooth",
            "bluetooth off",
            "connect to bluetooth device MyHeadphones"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "manage_bluetooth", f"Failed for: {cmd}"
    
    def test_parse_list_processes(self):
        """Test process listing commands."""
        commands = [
            "list all processes",
            "show running processes",
            "what's running"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "list_processes", f"Failed for: {cmd}"
    
    def test_parse_terminate_process(self):
        """Test process termination commands."""
        commands = [
            "kill process chrome",
            "terminate the process firefox",
            "stop notepad"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "terminate_process", f"Failed for: {cmd}"
    
    def test_parse_read_screen(self):
        """Test screen reading commands."""
        commands = [
            "read the screen",
            "describe screen",
            "what's on the screen"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "read_screen", f"Failed for: {cmd}"
    
    def test_parse_create_note(self):
        """Test note creation commands."""
        commands = [
            "create a note buy milk",
            "take note meeting at 3pm",
            "remember to call John"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "create_note", f"Failed for: {cmd}"
    
    def test_parse_create_reminder(self):
        """Test reminder creation commands."""
        commands = [
            "remind me to call John at 3pm",
            "set a reminder to submit report in 2 hours"
        ]
        
        for cmd in commands:
            result = self.parser.parse(cmd)
            assert result.intent_type == "create_reminder", f"Failed for: {cmd}"


class TestEntityExtraction:
    """Test entity extraction from commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()
    
    def test_extract_numbers(self):
        """Test extraction of numeric values."""
        entities = self.parser.extract_entities("set volume to 75")
        number_entities = [e for e in entities if e.entity_type == "number"]
        assert len(number_entities) > 0
        assert number_entities[0].value == 75
    
    def test_extract_multiple_numbers(self):
        """Test extraction of multiple numbers."""
        entities = self.parser.extract_entities("set volume to 50 and brightness to 80")
        number_entities = [e for e in entities if e.entity_type == "number"]
        assert len(number_entities) == 2
        assert 50 in [e.value for e in number_entities]
        assert 80 in [e.value for e in number_entities]
    
    def test_extract_file_paths_windows(self):
        """Test extraction of Windows file paths."""
        entities = self.parser.extract_entities("open C:\\Users\\test\\document.txt")
        path_entities = [e for e in entities if e.entity_type == "file_path"]
        assert len(path_entities) > 0
        assert "C:\\Users\\test\\document.txt" in [e.value for e in path_entities]
    
    def test_extract_file_paths_unix(self):
        """Test extraction of Unix file paths."""
        entities = self.parser.extract_entities("open /home/user/document.txt")
        path_entities = [e for e in entities if e.entity_type == "file_path"]
        assert len(path_entities) > 0
        assert "/home/user/document.txt" in [e.value for e in path_entities]
    
    def test_extract_file_paths_home_relative(self):
        """Test extraction of home-relative paths."""
        entities = self.parser.extract_entities("open ~/documents/file.txt")
        path_entities = [e for e in entities if e.entity_type == "file_path"]
        assert len(path_entities) > 0
        assert "~/documents/file.txt" in [e.value for e in path_entities]
    
    def test_extract_quoted_strings(self):
        """Test extraction of quoted strings."""
        entities = self.parser.extract_entities('create file "my document.txt"')
        quoted_entities = [e for e in entities if e.entity_type == "quoted_string"]
        assert len(quoted_entities) > 0
        assert "my document.txt" in [e.value for e in quoted_entities]
    
    def test_extract_quoted_strings_single_quotes(self):
        """Test extraction of single-quoted strings."""
        entities = self.parser.extract_entities("create file 'my document.txt'")
        quoted_entities = [e for e in entities if e.entity_type == "quoted_string"]
        assert len(quoted_entities) > 0
        assert "my document.txt" in [e.value for e in quoted_entities]
    
    def test_extract_application_names(self):
        """Test extraction of capitalized application names."""
        entities = self.parser.extract_entities("open Google Chrome")
        app_entities = [e for e in entities if e.entity_type == "application"]
        assert len(app_entities) > 0
        # Should extract "Google Chrome" or at least one of them
        app_values = [e.value for e in app_entities]
        assert any("Google" in val or "Chrome" in val for val in app_values)
    
    def test_extract_directions(self):
        """Test extraction of direction indicators."""
        test_cases = [
            ("volume up", "up"),
            ("brightness down", "down"),
            ("increase volume", "up"),
            ("decrease brightness", "down"),
            ("raise volume", "up"),
            ("lower brightness", "down")
        ]
        
        for text, expected_direction in test_cases:
            entities = self.parser.extract_entities(text)
            direction_entities = [e for e in entities if e.entity_type == "direction"]
            assert len(direction_entities) > 0, f"No direction found in: {text}"
            assert direction_entities[0].value == expected_direction, \
                f"Expected {expected_direction}, got {direction_entities[0].value} for: {text}"
    
    def test_extract_entities_empty_text(self):
        """Test entity extraction with empty text."""
        entities = self.parser.extract_entities("")
        assert entities == []
    
    def test_extract_entities_no_entities(self):
        """Test entity extraction when no entities are present."""
        entities = self.parser.extract_entities("hello there")
        # Should return empty list or only very generic entities
        assert isinstance(entities, list)


class TestAmbiguityDetection:
    """Test ambiguity detection in intents."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()
    
    def test_is_ambiguous_unknown_intent(self):
        """Test that unknown intents are marked as ambiguous."""
        intent = Intent(
            intent_type="unknown",
            entities=[],
            confidence=0.3,
            requires_clarification=False
        )
        assert self.parser.is_ambiguous(intent) is True
    
    def test_is_ambiguous_low_confidence(self):
        """Test that low confidence intents are marked as ambiguous."""
        intent = Intent(
            intent_type="launch_app",
            entities=[],
            confidence=0.3,
            requires_clarification=False
        )
        assert self.parser.is_ambiguous(intent) is True
    
    def test_is_ambiguous_missing_required_entities(self):
        """Test that intents with missing required entities are ambiguous."""
        intent = Intent(
            intent_type="launch_app",
            entities=[],  # Missing application entity
            confidence=0.8,
            requires_clarification=False
        )
        assert self.parser.is_ambiguous(intent) is True
    
    def test_is_ambiguous_has_required_entities(self):
        """Test that intents with required entities are not ambiguous."""
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity(entity_type="application", value="Chrome", confidence=0.9)],
            confidence=0.8,
            requires_clarification=False
        )
        assert self.parser.is_ambiguous(intent) is False
    
    def test_is_ambiguous_already_marked(self):
        """Test that intents already marked for clarification are ambiguous."""
        intent = Intent(
            intent_type="launch_app",
            entities=[Entity(entity_type="application", value="Chrome", confidence=0.9)],
            confidence=0.8,
            requires_clarification=True
        )
        assert self.parser.is_ambiguous(intent) is True
    
    def test_is_ambiguous_high_confidence_no_entities_needed(self):
        """Test that high confidence intents without entity requirements are not ambiguous."""
        intent = Intent(
            intent_type="list_processes",
            entities=[],
            confidence=0.8,
            requires_clarification=False
        )
        assert self.parser.is_ambiguous(intent) is False


class TestClarificationQuestions:
    """Test clarification question generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()
    
    def test_generate_clarification_unknown_intent(self):
        """Test clarification for unknown intents."""
        intent = Intent(
            intent_type="unknown",
            entities=[],
            confidence=0.2,
            requires_clarification=True
        )
        question = self.parser.generate_clarification_question(intent)
        assert isinstance(question, str)
        assert len(question) > 0
        assert "?" in question
    
    def test_generate_clarification_low_confidence(self):
        """Test clarification for low confidence intents."""
        intent = Intent(
            intent_type="launch_app",
            entities=[],
            confidence=0.4,
            requires_clarification=True
        )
        question = self.parser.generate_clarification_question(intent)
        assert isinstance(question, str)
        assert "launch" in question.lower() or "application" in question.lower()
    
    def test_generate_clarification_missing_entities(self):
        """Test clarification for missing entities."""
        intent = Intent(
            intent_type="launch_app",
            entities=[],
            confidence=0.8,
            requires_clarification=True
        )
        question = self.parser.generate_clarification_question(intent)
        assert isinstance(question, str)
        assert "?" in question
        # Should ask about the missing application
        assert "application" in question.lower() or "launch" in question.lower()
    
    def test_generate_clarification_search_files(self):
        """Test clarification for file search without file name."""
        intent = Intent(
            intent_type="search_files",
            entities=[],
            confidence=0.7,
            requires_clarification=True
        )
        question = self.parser.generate_clarification_question(intent)
        assert isinstance(question, str)
        assert "file" in question.lower()
    
    def test_generate_clarification_all_intents(self):
        """Test that all intent types can generate clarification questions."""
        intent_types = [
            "launch_app", "search_files", "create_file", "delete_file",
            "move_file", "copy_file", "terminate_process", "create_note",
            "create_reminder", "unknown"
        ]
        
        for intent_type in intent_types:
            intent = Intent(
                intent_type=intent_type,
                entities=[],
                confidence=0.6,
                requires_clarification=True
            )
            question = self.parser.generate_clarification_question(intent)
            assert isinstance(question, str), f"Failed for intent: {intent_type}"
            assert len(question) > 0, f"Empty question for intent: {intent_type}"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = self.parser.parse("")
        assert result.intent_type == "unknown"
        assert result.confidence == 0.0
        assert result.requires_clarification is True
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string."""
        result = self.parser.parse("   ")
        assert result.intent_type == "unknown"
        assert result.confidence == 0.0
    
    def test_parse_none_input(self):
        """Test parsing None input."""
        result = self.parser.parse(None)
        assert result.intent_type == "unknown"
        assert result.confidence == 0.0
    
    def test_parse_very_long_command(self):
        """Test parsing very long command."""
        long_command = "open " + "a" * 1000
        result = self.parser.parse(long_command)
        assert result.intent_type == "launch_app"
    
    def test_parse_special_characters(self):
        """Test parsing commands with special characters."""
        result = self.parser.parse("open file@#$%.txt")
        assert result.intent_type == "launch_app"
    
    def test_parse_mixed_case(self):
        """Test parsing commands with mixed case."""
        result = self.parser.parse("OpEn ChRoMe")
        assert result.intent_type == "launch_app"
    
    def test_parse_with_extra_spaces(self):
        """Test parsing commands with extra spaces."""
        result = self.parser.parse("open    Chrome")
        assert result.intent_type == "launch_app"
    
    def test_parse_unicode_characters(self):
        """Test parsing commands with unicode characters."""
        result = self.parser.parse("open файл.txt")
        # Should at least not crash
        assert isinstance(result, Intent)
