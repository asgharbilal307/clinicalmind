import json
import asyncio
import logging
from decimal import Decimal
from groq import AsyncGroq
from backend.config import GROQ_API_KEY, GROQ_MODEL
from backend.models.schemas import Abstract, Claim
from backend.cost_tracker import default_cost_tracker

logger = logging.getLogger(__name__)

_client: AsyncGroq | None = None


def get_groq() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=GROQ_API_KEY)
    return _client


CLAIM_EXTRACTION_PROMPT = """You are a biomedical research analyst. Extract the single primary finding from this study abstract.

Return ONLY valid JSON with this exact structure:
{{
  "claim": "one sentence describing the main finding",
  "direction": "positive" | "negative" | "null" | "unknown",
  "outcome": "the specific outcome measured (e.g. cardiovascular events, blood pressure, mortality)"
}}

Rules:
- "claim" must be a complete, specific sentence including the effect size if mentioned
- "direction" is "positive" if the intervention showed benefit, "negative" if it showed harm or no benefit, "null" if no significant effect was found, "unknown" if unclear
- Do NOT include any text outside the JSON object

Abstract title: {title}
Abstract: {abstract}"""


async def extract_claim(abstract: Abstract) -> Claim | None:
    """Extract a structured claim from a single abstract."""
    if not default_cost_tracker.can_proceed():
        logger.warning("Cost/rate guard blocked claim extraction call — skipping.")
        return None

    try:
        response = await get_groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": CLAIM_EXTRACTION_PROMPT.format(
                        title=abstract.title, abstract=abstract.abstract[:2000]
                    ),
                }
            ],
            temperature=0.1,
            max_tokens=300,
        )

        usage = getattr(response, "usage", None)
        if usage:
            cost = default_cost_tracker.estimate_cost(
                GROQ_MODEL,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
            )
            default_cost_tracker.record_cost(cost)
        else:
            default_cost_tracker.record_cost(Decimal("0.00"))

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)

        return Claim(
            pmid=abstract.pmid,
            claim=data.get("claim", ""),
            direction=data.get("direction", "unknown"),
            outcome=data.get("outcome"),
        )

    except Exception:
        return None


async def extract_claims_batch(
    abstracts: list[Abstract], concurrency: int = 5
) -> list[Claim]:
    """Extract claims from multiple abstracts with rate-limited concurrency."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(abstract: Abstract) -> Claim | None:
        async with semaphore:
            result = await extract_claim(abstract)
            await asyncio.sleep(0.2)  # gentle rate limiting
            return result

    tasks = [_guarded(a) for a in abstracts]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]