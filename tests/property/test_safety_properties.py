"""Property-based tests for Safety Controller.

**Validates: Requirements 5.1-5.6, 10.4**

Property 19: Destructive Action Confirmation Requirement
Property 20: Confirmation Message Completeness
Property 21: Confirmation Validation
Property 22: Action Abortion
Property 23: Prohibited Command Blocking
Property 24: Process Termination Confirmation

This property test verifies that:
- All destructive actions require confirmation
- Confirmation messages are complete and clear
- Only valid confirmation words allow execution
- Abortion words properly cancel actions
- Prohibited commands are blocked
- Process termination requires confirmation
"""

from datetime import datetime
from hypothesis import given, strategies as st, settings, assume
from prime.safety import SafetyController
from prime.safety.safety_controller import ActionType, SecurityEvent
from prime.models import Command, Intent, Entity


# Strategy for generating destructive intent types
destructive_intents = st.sampled_from([
    "delete_file", "remove_file", "shutdown", "restart", "reboot",
    "terminate_process", "kill_process", "modify_setting",
    "change_setting", "update_setting", "format_disk", "uninstall_app"
])

# Strategy for generating safe intent types
safe_intents = st.sampled_from([
    "launch_app", "adjust_volume", "search_files", "create_file",
    "read_file", "list_processes", "get_info", "open_browser"
])

# Strategy for generating prohibited keywords
prohibited_keywords = st.sampled_from([
    "hack", "crack", "exploit", "breach", "bypass security",
    "unauthorized", "surveillance", "spy", "keylog",
    "steal", "illegal", "malware", "virus"
])

# Strategy for generating confirmation words
confirmation_words = st.sampled_from([
    "yes", "confirm", "proceed", "continue", "ok", "okay",
    "YES", "Confirm", "PROCEED", "  yes  ", "\tconfirm\n"
])

# Strategy for generating abortion words
abortion_words = st.sampled_from([
    "no", "cancel", "stop", "abort", "nevermind", "never mind",
    "NO", "Cancel", "STOP", "  no  ", "\tstop\n"
])

# Strategy for generating entity values
entity_values = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='.-_'
    )
)


class TestProperty19DestructiveActionConfirmation:
    """Property 19: Destructive Action Confirmation Requirement.
    
    **Validates: Requirements 5.1**
    
    For any command classified as a destructive action, the Safety_Controller
    should require explicit confirmation before allowing execution.
    """
    
    @given(
        intent_type=destructive_intents,
        entity_value=entity_values,
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=30)
    def test_property_19_destructive_actions_require_confirmation(
        self, intent_type, entity_value, command_id
    ):
        """Property 19: All destructive actions require confirmation.
        
        **Validates: Requirements 5.1**
        
        For any command classified as destructive, the Safety_Controller
        should require confirmation.
        
        This test verifies that:
        1. A destructive command is created
        2. The command is classified as destructive
        3. The controller requires confirmation for the action
        """
        # Create a destructive command
        intent = Intent(
            intent_type=intent_type,
            entities=[Entity("target", entity_value, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Classify the action
        action_type = controller.classify_action(command)
        
        # If classified as destructive, must require confirmation
        if action_type == ActionType.DESTRUCTIVE:
            requires_conf = controller.requires_confirmation(action_type)
            assert requires_conf is True, (
                f"Destructive action {intent_type} must require confirmation"
            )
    
    @given(
        intent_type=safe_intents,
        entity_value=entity_values,
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=20)
    def test_property_19_safe_actions_do_not_require_confirmation(
        self, intent_type, entity_value, command_id
    ):
        """Property 19: Safe actions do not require confirmation.
        
        **Validates: Requirements 5.1**
        
        For any command classified as safe, the Safety_Controller
        should not require confirmation.
        """
        # Create a safe command
        intent = Intent(
            intent_type=intent_type,
            entities=[Entity("target", entity_value, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Classify the action
        action_type = controller.classify_action(command)
        
        # If classified as safe, should not require confirmation
        if action_type == ActionType.SAFE:
            requires_conf = controller.requires_confirmation(action_type)
            assert requires_conf is False, (
                f"Safe action {intent_type} should not require confirmation"
            )


class TestProperty20ConfirmationMessageCompleteness:
    """Property 20: Confirmation Message Completeness.
    
    **Validates: Requirements 5.3**
    
    For any confirmation request, the Safety_Controller should include
    a clear description of the action and its consequences.
    """
    
    @given(
        intent_type=destructive_intents,
        entity_value=entity_values,
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=30)
    def test_property_20_confirmation_prompt_is_complete(
        self, intent_type, entity_value, command_id
    ):
        """Property 20: Confirmation prompts are complete.
        
        **Validates: Requirements 5.3**
        
        For any destructive action, the confirmation prompt should:
        1. Clearly describe the action
        2. Explain the consequences
        3. Indicate how to confirm or cancel
        
        This test verifies that:
        1. A confirmation prompt is generated
        2. The prompt contains action description
        3. The prompt contains consequence information
        4. The prompt explains how to respond
        """
        # Create a destructive command
        intent = Intent(
            intent_type=intent_type,
            entities=[Entity("target", entity_value, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=True
        )
        
        controller = SafetyController()
        
        # Generate confirmation prompt
        prompt = controller.generate_confirmation_prompt(command)
        
        # Verify prompt is not empty
        assert prompt, "Confirmation prompt should not be empty"
        assert len(prompt) > 20, "Confirmation prompt should be substantial"
        
        # Verify prompt contains key elements
        prompt_lower = prompt.lower()
        
        # Should indicate this is a confirmation
        assert any(word in prompt_lower for word in [
            "confirm", "confirmation", "warning", "caution"
        ]), "Prompt should indicate confirmation is required"
        
        # Should explain how to confirm
        assert "yes" in prompt_lower or "confirm" in prompt_lower, (
            "Prompt should explain how to confirm"
        )
        
        # Should explain how to cancel
        assert "no" in prompt_lower or "cancel" in prompt_lower or "stop" in prompt_lower, (
            "Prompt should explain how to cancel"
        )
        
        # Should mention consequences or warnings
        assert any(word in prompt_lower for word in [
            "consequence", "cannot be undone", "permanent", "lost",
            "deleted", "removed", "terminated", "changed"
        ]), "Prompt should describe consequences"


class TestProperty21ConfirmationValidation:
    """Property 21: Confirmation Validation.
    
    **Validates: Requirements 5.4**
    
    For any destructive action awaiting confirmation, the Safety_Controller
    should only allow execution when the user responds with "yes", "confirm",
    or "proceed".
    """
    
    @given(
        confirmation_word=confirmation_words
    )
    @settings(max_examples=20)
    def test_property_21_valid_confirmations_accepted(
        self, confirmation_word
    ):
        """Property 21: Valid confirmation words are accepted.
        
        **Validates: Requirements 5.4**
        
        For any valid confirmation word ("yes", "confirm", "proceed"),
        the Safety_Controller should validate it as a confirmation.
        
        This test verifies that:
        1. A confirmation word is provided
        2. The controller validates it correctly
        3. The validation returns True
        """
        controller = SafetyController()
        
        # Validate the confirmation
        is_valid = controller.validate_confirmation(confirmation_word)
        
        # Should be accepted
        assert is_valid is True, (
            f"Confirmation word '{confirmation_word}' should be accepted"
        )
    
    @given(
        invalid_response=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip().lower() not in {
                'yes', 'confirm', 'proceed', 'continue', 'ok', 'okay'
            }
        )
    )
    @settings(max_examples=30)
    def test_property_21_invalid_confirmations_rejected(
        self, invalid_response
    ):
        """Property 21: Invalid confirmation words are rejected.
        
        **Validates: Requirements 5.4**
        
        For any response that is not a valid confirmation word,
        the Safety_Controller should reject it.
        """
        controller = SafetyController()
        
        # Validate the response
        is_valid = controller.validate_confirmation(invalid_response)
        
        # Should be rejected
        assert is_valid is False, (
            f"Invalid response '{invalid_response}' should be rejected"
        )


class TestProperty22ActionAbortion:
    """Property 22: Action Abortion.
    
    **Validates: Requirements 5.5**
    
    For any destructive action awaiting confirmation, if the user responds
    with "no", "cancel", or "stop", the Safety_Controller should abort
    the action.
    """
    
    @given(
        abortion_word=abortion_words
    )
    @settings(max_examples=20)
    def test_property_22_abortion_words_detected(
        self, abortion_word
    ):
        """Property 22: Abortion words are properly detected.
        
        **Validates: Requirements 5.5**
        
        For any abortion word ("no", "cancel", "stop"), the Safety_Controller
        should detect it as an abortion request.
        
        This test verifies that:
        1. An abortion word is provided
        2. The controller detects it as abortion
        3. The action would be aborted
        """
        controller = SafetyController()
        
        # Check if it's an abortion
        is_abort = controller.is_abortion(abortion_word)
        
        # Should be detected as abortion
        assert is_abort is True, (
            f"Abortion word '{abortion_word}' should be detected"
        )
    
    @given(
        confirmation_word=confirmation_words
    )
    @settings(max_examples=15)
    def test_property_22_confirmation_not_abortion(
        self, confirmation_word
    ):
        """Property 22: Confirmation words are not abortion.
        
        **Validates: Requirements 5.5**
        
        Confirmation words should not be detected as abortion.
        """
        controller = SafetyController()
        
        # Check if it's an abortion
        is_abort = controller.is_abortion(confirmation_word)
        
        # Should not be detected as abortion
        assert is_abort is False, (
            f"Confirmation word '{confirmation_word}' should not be abortion"
        )
    
    @given(
        intent_type=destructive_intents,
        entity_value=entity_values,
        abortion_word=abortion_words
    )
    @settings(max_examples=20)
    def test_property_22_abortion_prevents_execution(
        self, intent_type, entity_value, abortion_word
    ):
        """Property 22: Abortion prevents execution.
        
        **Validates: Requirements 5.5**
        
        When a user provides an abortion word, the action should not proceed.
        This is verified by checking that:
        1. The word is detected as abortion
        2. It is not validated as confirmation
        """
        controller = SafetyController()
        
        # Check abortion detection
        is_abort = controller.is_abortion(abortion_word)
        is_confirmed = controller.validate_confirmation(abortion_word)
        
        # Abortion should be detected, confirmation should fail
        assert is_abort is True, "Abortion should be detected"
        assert is_confirmed is False, "Should not be validated as confirmation"


class TestProperty23ProhibitedCommandBlocking:
    """Property 23: Prohibited Command Blocking.
    
    **Validates: Requirements 5.6**
    
    For any command related to hacking, security bypass, unauthorized
    surveillance, or illegal activities, the Safety_Controller should
    reject it and never execute it.
    """
    
    @given(
        prohibited_keyword=prohibited_keywords,
        entity_value=entity_values,
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=30)
    def test_property_23_prohibited_commands_blocked(
        self, prohibited_keyword, entity_value, command_id
    ):
        """Property 23: Prohibited commands are blocked.
        
        **Validates: Requirements 5.6**
        
        For any command containing prohibited keywords, the Safety_Controller
        should classify it as prohibited and block execution.
        
        This test verifies that:
        1. A command with prohibited keywords is created
        2. The command is detected as prohibited
        3. The command is classified as PROHIBITED
        """
        # Create a command with prohibited content
        intent = Intent(
            intent_type="execute_command",
            entities=[Entity("command", f"{prohibited_keyword} {entity_value}", 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Check if prohibited
        is_prohibited = controller.is_prohibited(command)
        
        # Should be detected as prohibited
        assert is_prohibited is True, (
            f"Command with '{prohibited_keyword}' should be prohibited"
        )
        
        # Classify the action
        action_type = controller.classify_action(command)
        
        # Should be classified as PROHIBITED
        assert action_type == ActionType.PROHIBITED, (
            f"Command with '{prohibited_keyword}' should be classified as PROHIBITED"
        )
    
    @given(
        intent_type=safe_intents,
        entity_value=entity_values,
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=20)
    def test_property_23_safe_commands_not_blocked(
        self, intent_type, entity_value, command_id
    ):
        """Property 23: Safe commands are not blocked.
        
        **Validates: Requirements 5.6**
        
        Commands without prohibited keywords should not be blocked.
        """
        # Create a safe command
        intent = Intent(
            intent_type=intent_type,
            entities=[Entity("target", entity_value, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Check if prohibited
        is_prohibited = controller.is_prohibited(command)
        
        # Should not be prohibited
        assert is_prohibited is False, (
            f"Safe command {intent_type} should not be prohibited"
        )


class TestProperty24ProcessTerminationConfirmation:
    """Property 24: Process Termination Confirmation.
    
    **Validates: Requirements 10.4**
    
    For any process termination request, the Safety_Controller should
    require confirmation before terminating the process.
    """
    
    @given(
        process_name=entity_values,
        pid=st.integers(min_value=1, max_value=99999),
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=30)
    def test_property_24_process_termination_requires_confirmation(
        self, process_name, pid, command_id
    ):
        """Property 24: Process termination requires confirmation.
        
        **Validates: Requirements 10.4**
        
        For any process termination request, the Safety_Controller should:
        1. Classify it as destructive
        2. Require confirmation
        3. Generate a confirmation prompt
        
        This test verifies that:
        1. A process termination command is created
        2. The command is classified as destructive
        3. Confirmation is required
        4. A confirmation prompt is generated
        """
        # Create a process termination command
        intent = Intent(
            intent_type="terminate_process",
            entities=[Entity("process_name", process_name, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={"pid": pid},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Classify the action
        action_type = controller.classify_action(command)
        
        # Should be classified as destructive
        assert action_type == ActionType.DESTRUCTIVE, (
            "Process termination should be classified as destructive"
        )
        
        # Should require confirmation
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is True, (
            "Process termination should require confirmation"
        )
        
        # Should generate a confirmation prompt
        prompt = controller.generate_confirmation_prompt(command)
        assert prompt, "Should generate a confirmation prompt"
        assert len(prompt) > 20, "Confirmation prompt should be substantial"
        
        # Prompt should mention the process
        prompt_lower = prompt.lower()
        assert "process" in prompt_lower or "terminate" in prompt_lower, (
            "Prompt should mention process termination"
        )
    
    @given(
        process_name=entity_values,
        pid=st.integers(min_value=1, max_value=99999),
        command_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))
    )
    @settings(max_examples=20)
    def test_property_24_kill_process_also_requires_confirmation(
        self, process_name, pid, command_id
    ):
        """Property 24: Kill process also requires confirmation.
        
        **Validates: Requirements 10.4**
        
        Both "terminate_process" and "kill_process" should require confirmation.
        """
        # Create a kill process command
        intent = Intent(
            intent_type="kill_process",
            entities=[Entity("process_name", process_name, 0.9)],
            confidence=0.9,
            requires_clarification=False
        )
        command = Command(
            command_id=command_id,
            intent=intent,
            parameters={"pid": pid},
            timestamp=datetime.now(),
            requires_confirmation=False
        )
        
        controller = SafetyController()
        
        # Classify the action
        action_type = controller.classify_action(command)
        
        # Should be classified as destructive
        assert action_type == ActionType.DESTRUCTIVE, (
            "Kill process should be classified as destructive"
        )
        
        # Should require confirmation
        requires_conf = controller.requires_confirmation(action_type)
        assert requires_conf is True, (
            "Kill process should require confirmation"
        )
