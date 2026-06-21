"""
Prompt Guard - Defense against prompt injection attacks.
Sanitizes user input before sending to LLM.
"""
import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PromptGuard:
    """Filter potentially malicious prompts."""

    # Patterns that indicate prompt injection attempts
    DANGEROUS_PATTERNS = [
        r"ignore\s+(previous|all\s+)?(instructions|rules)",
        r"disregard\s+(all\s+)?(safety|instructions)",
        r"system\s+prompt",
        r"you\s+are\s+(now\s+)?(a|an)\s+(different|new)",
        r"act\s+as\s+(a\s+)?(different|new)",
        r"roleplay",
        r"new\s+instructions",
        r"override",
        r"bypass",
        r"\\x00",  # Null bytes
        r"<script",  # XSS attempts
        r"javascript:",  # XSS attempts
        r"onerror=",  # XSS attempts
        r"--",  # SQL comment injection
        r";\s*DROP",  # SQL injection
        r"union\s+select",  # SQL injection
        r"{{",  # Template injection
        r"}}",
        r"\$_",  # PHP variables
    ]

    # Compile patterns for performance
    _compiled_patterns = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

    def __init__(self, strict: bool = False):
        self.strict = strict

    def sanitize(self, prompt: str) -> str:
        """Remove dangerous patterns from prompt."""
        sanitized = prompt

        for pattern in self._compiled_patterns:
            sanitized = pattern.sub("[FILTERED]", sanitized)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Remove excessive whitespace that could hide content
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized

    def is_safe(self, prompt: str) -> bool:
        """Check if prompt is safe to send."""
        # Check for dangerous patterns
        for pattern in self._compiled_patterns:
            if pattern.search(prompt):
                if self.strict:
                    logger.warning(f"Potential prompt injection detected: {pattern.pattern}")
                return False

        # Check for null bytes
        if "\x00" in prompt:
            return False

        return True

    def validate_and_sanitize(self, user_input: str) -> Optional[str]:
        """
        Validate and sanitize user input.
        Returns sanitized string if safe, None if rejected.
        """
        if not user_input or not user_input.strip():
            return None

        # Check length
        if len(user_input) > 2000:
            logger.warning("Input exceeds maximum length")
            return None

        # Check if safe
        if not self.is_safe(user_input):
            if self.strict:
                logger.warning(f"Rejecting potentially malicious input: {user_input[:50]}...")
            # In non-strict mode, still sanitize and allow
            return self.sanitize(user_input)

        # Sanitize and return
        return self.sanitize(user_input)


# Default instance
default_prompt_guard = PromptGuard(strict=False)