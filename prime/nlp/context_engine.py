"""
Context Engine for PRIME Voice Assistant.

This module provides context awareness and reference resolution capabilities.
The Context Engine maintains conversation state, resolves pronoun references,
tracks command history, generates proactive suggestions, learns from corrections,
and detects repetitive patterns.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from prime.models import Intent, Entity, Session, CommandRecord, Command, CommandResult
from prime.nlp import IntentParser
from prime.persistence import MemoryManager


@dataclass
class Suggestion:
    """Represents a proactive suggestion from the Context Engine."""
    suggestion_type: str  # "automation", "alternative", "preference"
    description: str
    benefit: str
    confidence: float


@dataclass
class Pattern:
    """Represents a detected repetitive pattern."""
    pattern_type: str  # "command_sequence", "time_based", "context_based"
    commands: List[str]
    frequency: int
    last_occurrence: datetime
    description: str


class ContextEngine:
    """
    Maintains conversation context and provides intelligent assistance.
    
    The Context Engine is responsible for:
    - Processing commands with session context
    - Resolving pronoun references ("it", "that", "the previous one")
    - Maintaining command history
    - Generating proactive suggestions
    - Learning from user corrections
    - Detecting repetitive patterns for automation opportunities
    """
    
    def __init__(self, intent_parser: IntentParser, memory_manager: MemoryManager):
        """
        Initialize the Context Engine.
        
        Args:
            intent_parser: The IntentParser instance for parsing commands
            memory_manager: The MemoryManager instance for persistent storage
        """
        self.intent_parser = intent_parser
        self.memory_manager = memory_manager
        
        # Track corrections for learning
        self._corrections: Dict[str, List[Tuple[str, str]]] = {}
        
        # Track patterns for automation suggestions
        self._pattern_buffer: Dict[str, List[Tuple[datetime, str]]] = {}
    
    def process_command(self, text: str, session: Session) -> Intent:
        """
        Process a command with session context.
        
        This method considers previous commands in the session to provide
        context-aware intent parsing. It resolves references and applies
        learned corrections.
        
        Args:
            text: The command text to process
            session: The current session containing command history
            
        Returns:
            Intent object with context-aware parsing results
        """
        # Apply learned corrections if available
        corrected_text = self._apply_corrections(text, session.user_id)
        
        # Resolve references in the text
        resolved_text = self._resolve_text_references(corrected_text, session)
        
        # Parse the command
        intent = self.intent_parser.parse(resolved_text)
        
        # Enhance intent with context if needed
        intent = self._enhance_intent_with_context(intent, session)
        
        return intent
    
    def resolve_reference(self, reference: str, session: Session) -> Optional[Entity]:
        """
        Resolve pronoun references using conversation history.
        
        This method resolves references like "it", "that", "the previous one"
        to specific entities from the conversation history.
        
        Args:
            reference: The reference to resolve (e.g., "it", "that")
            session: The current session containing command history
            
        Returns:
            Entity object representing the resolved reference, or None if
            the reference cannot be resolved
        """
        # Normalize the reference
        ref_lower = reference.lower().strip()
        
        # Define pronoun patterns
        pronouns = {
            "it", "that", "this", "them", "those", "these"
        }
        
        previous_patterns = {
            "the previous one", "the last one", "previous", "last"
        }
        
        # Check if it's a pronoun or previous reference
        is_pronoun = ref_lower in pronouns
        is_previous = any(pattern in ref_lower for pattern in previous_patterns)
        
        if not (is_pronoun or is_previous):
            return None
        
        # Search command history in reverse order (most recent first)
        for record in reversed(session.command_history):
            # Look for entities in the command
            for entity in record.command.intent.entities:
                # Skip low-confidence entities
                if entity.confidence < 0.5:
                    continue
                
                # Return the first relevant entity found
                # Prioritize file paths, applications, and specific values
                if entity.entity_type in [
                    "file_path", "application", "file_name",
                    "quoted_string", "process_name", "network_name",
                    "device_name"
                ]:
                    return entity
            
            # Also check the command result for referenced entities
            if record.result.success and record.result.output:
                # If the output contains a path or name, create an entity
                output = record.result.output.strip()
                if output and len(output) < 200:  # Reasonable length for an entity
                    return Entity(
                        entity_type="referenced_output",
                        value=output,
                        confidence=0.7
                    )
        
        # No suitable reference found
        return None
    
    def add_to_history(
        self, command: Command, result: CommandResult, session: Session
    ) -> None:
        """
        Add a command and its result to the session history.
        
        This method updates the session's command history and persists
        the session to storage.
        
        Args:
            command: The executed command
            result: The result of the command execution
            session: The current session to update
        """
        # Create a command record
        record = CommandRecord(
            command=command,
            result=result,
            timestamp=datetime.now()
        )
        
        # Add to session history
        session.command_history.append(record)
        
        # Update pattern buffer for pattern detection
        user_id = session.user_id
        if user_id not in self._pattern_buffer:
            self._pattern_buffer[user_id] = []
        
        # Store command text and timestamp
        command_text = command.intent.intent_type
        self._pattern_buffer[user_id].append((datetime.now(), command_text))
        
        # Keep only recent commands (last 50)
        if len(self._pattern_buffer[user_id]) > 50:
            self._pattern_buffer[user_id] = self._pattern_buffer[user_id][-50:]
        
        # Persist the session
        self.memory_manager.save_session(session)
    
    def get_suggestions(self, session: Session) -> List[Suggestion]:
        """
        Generate proactive suggestions based on session context.
        
        This method analyzes the command history and user patterns to
        generate helpful suggestions for automation, alternatives, or
        preference-based improvements.
        
        Args:
            session: The current session
            
        Returns:
            List of Suggestion objects
        """
        suggestions = []
        
        # Detect repetitive patterns and suggest automation
        pattern = self.detect_repetitive_pattern(session)
        if pattern:
            suggestions.append(Suggestion(
                suggestion_type="automation",
                description=f"Automate repetitive task: {pattern.description}",
                benefit=f"Save time by automating {pattern.frequency} repeated commands",
                confidence=min(0.9, 0.5 + (pattern.frequency * 0.1))
            ))
        
        # Suggest alternatives based on recent errors
        recent_errors = [
            record for record in session.command_history[-5:]
            if not record.result.success
        ]
        
        if recent_errors:
            last_error = recent_errors[-1]
            intent_type = last_error.command.intent.intent_type
            
            # Suggest alternatives based on intent type
            alternatives = self._get_alternative_suggestions(intent_type)
            if alternatives:
                suggestions.append(Suggestion(
                    suggestion_type="alternative",
                    description=alternatives["description"],
                    benefit=alternatives["benefit"],
                    confidence=0.7
                ))
        
        # Suggest based on usage patterns
        usage_patterns = self.memory_manager.get_all_application_usage(session.user_id)
        if usage_patterns and len(session.command_history) > 0:
            # Check if user frequently uses certain apps at certain times
            current_hour = datetime.now().hour
            
            # Morning suggestions (6-12)
            if 6 <= current_hour < 12 and usage_patterns:
                top_app = usage_patterns[0]
                if top_app.launch_count > 5:
                    suggestions.append(Suggestion(
                        suggestion_type="preference",
                        description=f"Launch {top_app.application_name}",
                        benefit=f"You frequently use {top_app.application_name}",
                        confidence=0.6
                    ))
        
        return suggestions
    
    def learn_from_correction(
        self, original: str, corrected: str, session: Session
    ) -> None:
        """
        Learn from user corrections to improve future parsing.
        
        When a user corrects PRIME's interpretation, this method stores
        the correction to improve future command understanding.
        
        Args:
            original: The original command text that was misunderstood
            corrected: The corrected command text
            session: The current session
        """
        user_id = session.user_id
        
        # Initialize corrections list for this user if needed
        if user_id not in self._corrections:
            self._corrections[user_id] = []
        
        # Store the correction
        self._corrections[user_id].append((original.lower(), corrected.lower()))
        
        # Keep only recent corrections (last 100)
        if len(self._corrections[user_id]) > 100:
            self._corrections[user_id] = self._corrections[user_id][-100:]
        
        # Persist corrections as a preference
        self.memory_manager.store_preference(
            "command_corrections",
            self._corrections[user_id],
            user_id
        )
    
    def detect_repetitive_pattern(self, session: Session) -> Optional[Pattern]:
        """
        Detect repetitive patterns in command history.
        
        This method analyzes the command history to identify sequences
        of commands that are repeated, which could be automated.
        
        Args:
            session: The current session
            
        Returns:
            Pattern object if a repetitive pattern is detected, None otherwise
        """
        user_id = session.user_id
        
        # Need at least 6 commands to detect a pattern
        if user_id not in self._pattern_buffer:
            return None
        
        buffer = self._pattern_buffer[user_id]
        if len(buffer) < 6:
            return None
        
        # Look for sequences of 2-4 commands that repeat
        for sequence_length in range(2, 5):
            # Check recent commands
            recent_commands = buffer[-20:]  # Look at last 20 commands
            
            # Extract command sequences
            sequences: Dict[tuple, List[datetime]] = {}
            
            for i in range(len(recent_commands) - sequence_length + 1):
                sequence = tuple(
                    cmd_text for _, cmd_text in recent_commands[i:i+sequence_length]
                )
                timestamp = recent_commands[i][0]
                
                if sequence not in sequences:
                    sequences[sequence] = []
                sequences[sequence].append(timestamp)
            
            # Find sequences that repeat at least 3 times
            for sequence, timestamps in sequences.items():
                if len(timestamps) >= 3:
                    # Found a repetitive pattern
                    command_names = list(sequence)
                    description = " → ".join(command_names)
                    
                    return Pattern(
                        pattern_type="command_sequence",
                        commands=command_names,
                        frequency=len(timestamps),
                        last_occurrence=max(timestamps),
                        description=description
                    )
        
        return None
    
    def _apply_corrections(self, text: str, user_id: str) -> str:
        """
        Apply learned corrections to the command text.
        
        Args:
            text: The original command text
            user_id: The user identifier
            
        Returns:
            The corrected command text
        """
        # Load corrections from memory if not in cache
        if user_id not in self._corrections:
            stored_corrections = self.memory_manager.get_preference(
                "command_corrections", user_id
            )
            if stored_corrections:
                self._corrections[user_id] = stored_corrections
            else:
                self._corrections[user_id] = []
        
        # Apply corrections
        corrected_text = text.lower()
        for original, corrected in self._corrections.get(user_id, []):
            if original in corrected_text:
                corrected_text = corrected_text.replace(original, corrected)
        
        # Return with original casing if no corrections were applied
        if corrected_text == text.lower():
            return text
        
        return corrected_text
    
    def _resolve_text_references(self, text: str, session: Session) -> str:
        """
        Resolve references in the command text.
        
        Args:
            text: The command text
            session: The current session
            
        Returns:
            The text with references resolved
        """
        # Common reference patterns
        reference_patterns = [
            "it", "that", "this", "them", "those", "these",
            "the previous one", "the last one", "previous", "last"
        ]
        
        text_lower = text.lower()
        
        # Check if text contains any references
        has_reference = any(pattern in text_lower for pattern in reference_patterns)
        
        if not has_reference:
            return text
        
        # Try to resolve each reference pattern
        for pattern in reference_patterns:
            if pattern in text_lower:
                # Resolve the reference
                entity = self.resolve_reference(pattern, session)
                if entity:
                    # Replace the reference with the entity value
                    # Be careful to maintain case and context
                    replacement = str(entity.value)
                    text = text.replace(pattern, replacement)
                    text = text.replace(pattern.capitalize(), replacement)
                    text = text.replace(pattern.upper(), replacement)
        
        return text
    
    def _enhance_intent_with_context(
        self, intent: Intent, session: Session
    ) -> Intent:
        """
        Enhance the parsed intent with session context.
        
        Args:
            intent: The parsed intent
            session: The current session
            
        Returns:
            Enhanced intent with context information
        """
        # If intent has low confidence, try to improve it with context
        if intent.confidence < 0.6 and len(session.command_history) > 0:
            # Look at recent commands to infer context
            recent_intents = [
                record.command.intent.intent_type
                for record in session.command_history[-3:]
            ]
            
            # If user is doing similar operations, boost confidence
            if intent.intent_type in recent_intents:
                intent.confidence = min(0.8, intent.confidence + 0.2)
        
        return intent
    
    def _get_alternative_suggestions(
        self, intent_type: str
    ) -> Optional[Dict[str, str]]:
        """
        Get alternative suggestions for a failed intent.
        
        Args:
            intent_type: The intent type that failed
            
        Returns:
            Dictionary with description and benefit, or None
        """
        alternatives = {
            "search_files": {
                "description": "Try searching in a specific directory",
                "benefit": "Narrow down the search scope for faster results"
            },
            "launch_app": {
                "description": "Try using the full application name",
                "benefit": "Avoid ambiguity in application identification"
            },
            "delete_file": {
                "description": "Verify the file path is correct",
                "benefit": "Ensure you're targeting the right file"
            },
            "terminate_process": {
                "description": "Try using the process ID (PID) instead",
                "benefit": "More precise process identification"
            }
        }
        
        return alternatives.get(intent_type)
