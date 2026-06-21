"""
Secure Logging - Log without sensitive data.
Redacts PII and sensitive information before logging.
"""
import logging
import hashlib
import re
from typing import Any, Dict, Optional
from functools import wraps

# Fields that should be redacted
SENSITIVE_FIELDS = {
    "password", "secret", "token", "api_key", "apikey", "access_token",
    "refresh_token", "authorization", "credit_card", "card_number",
    "ssn", "social_security", "address", "phone", "email", "pin",
}

# Pattern for redacting email addresses
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Pattern for redacting phone numbers
PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")


class SecureLogger:
    """Log without sensitive data."""

    @staticmethod
    def redact_sensitive(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or redact sensitive fields from data."""
        if not isinstance(data, dict):
            return data

        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()

            # Check if field is sensitive
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = SecureLogger.redact_sensitive(value)
            elif isinstance(value, list):
                redacted[key] = [
                    SecureLogger.redact_sensitive(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value

        return redacted

    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """Hash user ID for logging."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:8]

    @staticmethod
    def redact_email(text: str) -> str:
        """Redact email addresses from text."""
        return EMAIL_PATTERN.sub("[EMAIL]", text)

    @staticmethod
    def redact_phone(text: str) -> str:
        """Redact phone numbers from text."""
        return PHONE_PATTERN.sub("[PHONE]", text)

    @staticmethod
    def sanitize_for_logging(text: str) -> str:
        """Sanitize text for safe logging."""
        if not text:
            return text

        # Redact emails and phones
        text = SecureLogger.redact_email(text)
        text = SecureLogger.redact_phone(text)

        # Truncate if too long
        if len(text) > 1000:
            text = text[:1000] + "... [TRUNCATED]"

        return text


def log_request(action: str, user_id: Optional[str] = None, **kwargs):
    """Log a request with sensitive data redacted."""
    safe_kwargs = SecureLogger.redact_sensitive(kwargs)

    if user_id:
        user_hash = SecureLogger.hash_user_id(user_id)
        logging.info(f"[{action}] User: {user_hash} | {safe_kwargs}")
    else:
        logging.info(f"[{action}] {safe_kwargs}")


def log_error(error: Exception, context: Optional[Dict] = None):
    """Log an error without exposing sensitive details."""
    safe_context = SecureLogger.redact_sensitive(context or {})

    logging.error(
        f"Error: {type(error).__name__}: {str(error)[:100]} | Context: {safe_context}"
    )


def setup_secure_logging(level: int = logging.INFO):
    """Set up secure logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# Default logger instance
logger = logging.getLogger("clinicalmind")

# Configure default logging
setup_secure_logging()