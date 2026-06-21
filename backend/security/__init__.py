"""
ClinicalMind Security Module

Provides security utilities:
- Rate limiting (token bucket, per-user)
- Prompt injection defense
- Cost tracking and budget controls
- Secure logging
"""
from backend.security.rate_limiter import (
    RateLimiter,
    UserRateLimiter,
    default_limiter,
    default_user_limiter,
)
from backend.security.prompt_guard import (
    PromptGuard,
    default_prompt_guard,
)
from backend.security.cost_tracker import (
    CostTracker,
    CostConfig,
    get_cost_tracker,
    default_cost_tracker,
)
from backend.security.secure_logging import (
    SecureLogger,
    log_request,
    log_error,
    logger,
    setup_secure_logging,
)

__all__ = [
    # Rate limiting
    "RateLimiter",
    "UserRateLimiter",
    "default_limiter",
    "default_user_limiter",
    # Prompt guard
    "PromptGuard",
    "default_prompt_guard",
    # Cost tracking
    "CostTracker",
    "CostConfig",
    "get_cost_tracker",
    "default_cost_tracker",
    # Logging
    "SecureLogger",
    "log_request",
    "log_error",
    "logger",
    "setup_secure_logging",
]