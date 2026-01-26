"""
Test Suite: Tone Validation for Jarvis AI Co-Pilot

Tests that all co-pilot messages adhere to tone guidelines:
- No forbidden phrases (error, failed, warning, critical, etc.)
- No technical jargon (exception, stack trace, API endpoint, etc.)
- No anxiety-inducing words (urgent, emergency, impossible, etc.)
- Empathetic and supportive language only

RED PHASE (Failing Tests) - Define expected behavior before implementation.
"""

import pytest
from app.modules.ai_copilot.persona import (
    validate_message_tone,
    ToneGuidelines,
    JarvisPersona,
    get_default_persona,
)


class TestToneValidationBasics:
    """RED: Test basic tone validation functionality."""
    
    def test_validate_good_message_passes(self):
        """Good: Calm, supportive message should pass tone validation."""
        guidelines = ToneGuidelines()
        message = "You're making great progress! Let's keep going."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is True, f"Good message should pass validation, but got violations: {violations}"
        assert violations == [], f"Good message should have no violations, but got: {violations}"
    
    def test_forbidden_phrase_error_detected(self):
        """RED: Message with 'error' should be flagged as invalid."""
        guidelines = ToneGuidelines()
        message = "An error occurred. Please try again."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'error' should fail validation"
        assert any("error" in v.lower() for v in violations), \
            f"Expected 'error' violation, but got: {violations}"
    
    def test_forbidden_phrase_failed_detected(self):
        """RED: Message with 'failed' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Task creation failed due to a server issue."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'failed' should fail validation"
        assert any("failed" in v.lower() for v in violations), \
            f"Expected 'failed' violation, but got: {violations}"
    
    def test_forbidden_phrase_warning_detected(self):
        """RED: Message with 'warning' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Warning: You have 10 overdue tasks."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'warning' should fail validation"
        assert any("warning" in v.lower() for v in violations), \
            f"Expected 'warning' violation, but got: {violations}"
    
    def test_forbidden_phrase_critical_detected(self):
        """RED: Message with 'critical' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Critical: System performance is degrading."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'critical' should fail validation"
        assert any("critical" in v.lower() for v in violations), \
            f"Expected 'critical' violation, but got: {violations}"


class TestJargonDetection:
    """RED: Test detection of technical jargon."""
    
    def test_exception_jargon_detected(self):
        """RED: Message with 'exception' should be flagged."""
        guidelines = ToneGuidelines()
        message = "A database exception occurred during the transaction."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'exception' should fail validation"
        assert any("exception" in v.lower() for v in violations), \
            f"Expected 'exception' violation, but got: {violations}"
    
    def test_stack_trace_jargon_detected(self):
        """RED: Message with 'stack trace' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Stack trace available in debug logs."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'stack trace' should fail validation"
        assert any("stack trace" in v.lower() for v in violations), \
            f"Expected 'stack trace' violation, but got: {violations}"
    
    def test_api_endpoint_jargon_detected(self):
        """RED: Message with 'API endpoint' should be flagged."""
        guidelines = ToneGuidelines()
        message = "The API endpoint returned an invalid response."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'API endpoint' should fail validation"
        assert any("api endpoint" in v.lower() for v in violations), \
            f"Expected 'API endpoint' violation, but got: {violations}"
    
    def test_null_pointer_jargon_detected(self):
        """RED: Message with 'null pointer' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Null pointer exception in memory allocation."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'null pointer' should fail validation"
        assert any("null pointer" in v.lower() for v in violations), \
            f"Expected 'null pointer' violation, but got: {violations}"


class TestAnxietyTriggerDetection:
    """RED: Test detection of anxiety-inducing words."""
    
    def test_urgent_word_detected(self):
        """RED: Message with 'urgent' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Urgent: You need to complete this task immediately."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'urgent' should fail validation"
        assert any("urgent" in v.lower() for v in violations), \
            f"Expected 'urgent' violation, but got: {violations}"
    
    def test_emergency_word_detected(self):
        """RED: Message with 'emergency' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Emergency: System shutdown in progress."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'emergency' should fail validation"
        assert any("emergency" in v.lower() for v in violations), \
            f"Expected 'emergency' violation, but got: {violations}"
    
    def test_impossible_word_detected(self):
        """RED: Message with 'impossible' should be flagged."""
        guidelines = ToneGuidelines()
        message = "It's impossible to complete this task by tomorrow."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'impossible' should fail validation"
        assert any("impossible" in v.lower() for v in violations), \
            f"Expected 'impossible' violation, but got: {violations}"
    
    def test_hopeless_word_detected(self):
        """RED: Message with 'hopeless' should be flagged."""
        guidelines = ToneGuidelines()
        message = "Your situation seems hopeless. There's nothing we can do."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with 'hopeless' should fail validation"
        assert any("hopeless" in v.lower() for v in violations), \
            f"Expected 'hopeless' violation, but got: {violations}"


class TestCaseSensitivity:
    """RED: Test that tone validation is case-insensitive."""
    
    def test_uppercase_forbidden_phrase_detected(self):
        """RED: Uppercase forbidden phrase should be detected."""
        guidelines = ToneGuidelines()
        message = "ERROR: Something went wrong."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Uppercase 'ERROR' should be detected"
        assert any("error" in v.lower() for v in violations), \
            f"Expected error violation for 'ERROR', but got: {violations}"
    
    def test_mixed_case_jargon_detected(self):
        """RED: Mixed-case jargon should be detected."""
        guidelines = ToneGuidelines()
        message = "Please review the Stack Trace for details."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Mixed-case 'Stack Trace' should be detected"
        assert any("stack trace" in v.lower() for v in violations), \
            f"Expected 'stack trace' violation, but got: {violations}"


class TestMultipleViolations:
    """RED: Test detection of multiple tone violations in one message."""
    
    def test_multiple_forbidden_phrases_detected(self):
        """RED: Message with multiple violations should list all of them."""
        guidelines = ToneGuidelines()
        message = "Error: Task creation failed due to a critical exception."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with multiple violations should fail"
        assert len(violations) >= 3, \
            f"Expected at least 3 violations for 'error', 'failed', 'critical', but got: {violations}"
    
    def test_forbidden_phrase_and_jargon_detected(self):
        """RED: Message mixing phrases and jargon should detect both."""
        guidelines = ToneGuidelines()
        message = "Warning: Database exception detected in API endpoint."
        is_valid, violations = validate_message_tone(message, guidelines)
        
        assert is_valid is False, "Message with phrase and jargon violations should fail"
        assert len(violations) >= 3, \
            f"Expected violations for 'warning', 'exception', 'API endpoint', but got: {violations}"


class TestDefaultPersonaGuidelines:
    """RED: Test that default Jarvis persona has tone guidelines configured."""
    
    def test_persona_has_tone_guidelines(self):
        """RED: Default persona should have tone guidelines."""
        persona = get_default_persona()
        
        assert persona.tone_guidelines is not None, \
            "Default persona must have tone_guidelines configured"
        assert isinstance(persona.tone_guidelines, ToneGuidelines), \
            "tone_guidelines should be ToneGuidelines instance"
    
    def test_tone_guidelines_have_forbidden_phrases(self):
        """RED: Tone guidelines should include forbidden phrases list."""
        persona = get_default_persona()
        guidelines = persona.tone_guidelines
        
        assert guidelines.forbidden_phrases is not None, \
            "forbidden_phrases must be configured"
        assert len(guidelines.forbidden_phrases) > 0, \
            "forbidden_phrases list must not be empty"
        assert "error" in guidelines.forbidden_phrases, \
            "'error' should be in forbidden phrases"
        assert "failed" in guidelines.forbidden_phrases, \
            "'failed' should be in forbidden phrases"
        assert "warning" in guidelines.forbidden_phrases, \
            "'warning' should be in forbidden phrases"
    
    def test_tone_guidelines_have_jargon_blacklist(self):
        """RED: Tone guidelines should include jargon blacklist."""
        persona = get_default_persona()
        guidelines = persona.tone_guidelines
        
        assert guidelines.jargon_blacklist is not None, \
            "jargon_blacklist must be configured"
        assert len(guidelines.jargon_blacklist) > 0, \
            "jargon_blacklist must not be empty"
        assert "exception" in guidelines.jargon_blacklist, \
            "'exception' should be in jargon blacklist"
    
    def test_tone_guidelines_have_anxiety_triggers(self):
        """RED: Tone guidelines should include anxiety trigger words."""
        persona = get_default_persona()
        guidelines = persona.tone_guidelines
        
        assert guidelines.anxiety_trigger_words is not None, \
            "anxiety_trigger_words must be configured"
        assert len(guidelines.anxiety_trigger_words) > 0, \
            "anxiety_trigger_words must not be empty"
        assert "urgent" in guidelines.anxiety_trigger_words, \
            "'urgent' should be in anxiety trigger words"


class TestPersonaMessageTemplates:
    """RED: Test that Jarvis persona has appropriate message templates."""
    
    def test_persona_has_message_templates(self):
        """RED: Default persona should have message templates."""
        persona = get_default_persona()
        
        assert persona.message_templates is not None, \
            "Default persona must have message_templates"
        assert len(persona.message_templates) > 0, \
            "message_templates dict must not be empty"
    
    def test_templates_for_core_categories(self):
        """RED: Persona should have templates for all message categories."""
        from app.modules.ai_copilot.persona import MessageCategory
        
        persona = get_default_persona()
        templates = persona.message_templates
        
        # At minimum, greeting and encouragement should be present
        assert MessageCategory.GREETING in templates or \
               "greeting" in str(templates).lower(), \
            "Templates should include greeting messages"
        assert MessageCategory.ENCOURAGEMENT in templates or \
               "encouragement" in str(templates).lower(), \
            "Templates should include encouragement messages"
    
    def test_greeting_templates_are_calm(self):
        """RED: Greeting templates should be calm and welcoming."""
        persona = get_default_persona()
        templates = persona.message_templates
        
        # Find greeting templates (by key or in dict)
        greeting_msgs = templates.get("greeting") or \
                       templates.get(list(templates.keys())[0]) or []
        
        if greeting_msgs:
            for msg in greeting_msgs:
                # Greeting should not contain forbidden words
                guidelines = persona.tone_guidelines
                is_valid, violations = validate_message_tone(str(msg), guidelines)
                assert is_valid, f"Greeting template violates tone: {msg} -> {violations}"
