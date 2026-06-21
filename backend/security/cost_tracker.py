"""
Cost Tracker - Track and enforce API cost and request-rate limits.
Prevents unexpected billing and free-tier rate-limit violations from LLM API calls.

Note on Groq pricing: Groq's free developer tier currently has $0 per-token
cost but enforces requests-per-minute and requests-per-day limits instead.
PRICING below reflects Groq's PAID tier rates so this tracker is accurate
the moment a paid model or paid tier is used — but on the free tier, the
real constraint enforced here is request count, not dollars. Check current
rates at https://groq.com/pricing before relying on these numbers in production.
"""
import os
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CostConfig:
    monthly_budget: Decimal = Decimal("100.00")
    max_cost_per_request: Decimal = Decimal("0.50")
    warn_at_percent: int = 75
    critical_at_percent: int = 90
    # Free-tier request guard — independent of dollar cost.
    # Groq's free tier enforces RPM/RPD limits; this is a soft local guard
    # to avoid silently hammering the API past what the free tier allows.
    max_requests_per_run: int = 500


class CostTracker:
    """Track and enforce API cost and request-count limits."""

    # Groq PAID-tier pricing per 1K tokens, in USD.
    # Source: https://groq.com/pricing — verify before trusting in production,
    # provider pricing changes without notice.
    PRICING = {
        "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
        "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079},
        "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
        "mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
    }

    def __init__(self, config: Optional[CostConfig] = None):
        self.config = config or CostConfig()
        self.spent = Decimal("0.00")
        self.request_count = 0
        self.daily_spent = Decimal("0.00")
        self.last_reset = datetime.now()
        self._lock = False  # Circuit breaker

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Estimate cost before making a request. Returns $0 for free-tier usage
        of these models today, but reflects real cost if pricing changes."""
        prices = self.PRICING.get(model, {"input": 0.00, "output": 0.00})
        input_cost = Decimal(str(prices["input"])) * (Decimal(input_tokens) / 1000)
        output_cost = Decimal(str(prices["output"])) * (Decimal(output_tokens) / 1000)
        return input_cost + output_cost

    def can_proceed(self, estimated_cost: Decimal = Decimal("0.00")) -> bool:
        """Check if a request is within budget AND within the request-count guard."""
        if self._lock:
            logger.critical("Circuit breaker activated — further requests blocked")
            return False

        # Request-count guard — meaningful today even at $0 cost, since this
        # protects against accidentally looping past Groq's free-tier RPD limit.
        if self.request_count >= self.config.max_requests_per_run:
            logger.critical(
                f"Request count limit reached ({self.request_count}/"
                f"{self.config.max_requests_per_run}) — stopping to avoid "
                f"exceeding Groq's free-tier rate limit."
            )
            self._activate_circuit_breaker()
            return False

        # Dollar budget guard — inert at $0.00 cost today, active if pricing changes.
        if self.spent >= self.config.monthly_budget:
            logger.critical(f"MONTHLY BUDGET EXCEEDED: ${self.spent}")
            self._activate_circuit_breaker()
            return False

        if estimated_cost > self.config.max_cost_per_request:
            logger.warning(
                f"Request cost ${estimated_cost} exceeds max ${self.config.max_cost_per_request}"
            )
            return False

        if self.config.monthly_budget > 0:
            percent_used = (self.spent / self.config.monthly_budget) * 100
            if percent_used >= self.config.critical_at_percent:
                logger.critical(f"CRITICAL: {percent_used:.0f}% of budget used (${self.spent})")
            elif percent_used >= self.config.warn_at_percent:
                logger.warning(f"WARNING: {percent_used:.0f}% of budget used (${self.spent})")

        return True

    def record_cost(self, actual_cost: Decimal) -> None:
        """Record actual cost and increment request count after a call completes."""
        self.spent += actual_cost
        self.daily_spent += actual_cost
        self.request_count += 1

        if self.config.monthly_budget > 0:
            percent_used = (self.spent / self.config.monthly_budget) * 100
            if percent_used >= self.config.critical_at_percent:
                logger.critical(f"CRITICAL: {percent_used:.0f}% of budget used (${self.spent})")
            elif percent_used >= self.config.warn_at_percent:
                logger.warning(f"WARNING: {percent_used:.0f}% of budget used (${self.spent})")

    def _activate_circuit_breaker(self) -> None:
        self._lock = True
        logger.critical("Circuit breaker activated")

    def get_status(self) -> dict:
        percent_used = (
            float((self.spent / self.config.monthly_budget) * 100)
            if self.config.monthly_budget > 0
            else 0
        )
        return {
            "spent": float(self.spent),
            "monthly_budget": float(self.config.monthly_budget),
            "percent_used": round(percent_used, 1),
            "request_count": self.request_count,
            "max_requests_per_run": self.config.max_requests_per_run,
            "circuit_breaker_active": self._lock,
        }

    def reset_daily(self) -> None:
        now = datetime.now()
        if now - self.last_reset > timedelta(days=1):
            self.daily_spent = Decimal("0.00")
            self.last_reset = now
            logger.info("Daily cost tracker reset")

    def reset_run(self) -> None:
        """Reset request_count and circuit breaker — call at the start of a
        fresh ingestion or debate run if you want per-run rather than
        process-lifetime limits."""
        self.request_count = 0
        self._lock = False


def get_cost_tracker() -> CostTracker:
    """Create a cost tracker from environment variables."""
    monthly_budget = Decimal(os.getenv("AI_MONTHLY_BUDGET_USD", "100"))
    max_cost = Decimal(os.getenv("AI_MAX_COST_PER_REQUEST", "0.50"))
    max_requests = int(os.getenv("AI_MAX_REQUESTS_PER_RUN", "500"))
    return CostTracker(
        CostConfig(
            monthly_budget=monthly_budget,
            max_cost_per_request=max_cost,
            max_requests_per_run=max_requests,
        )
    )


# Shared singleton — imported by pipeline modules that make Groq calls.
default_cost_tracker = get_cost_tracker()