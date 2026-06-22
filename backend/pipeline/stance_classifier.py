import json
import asyncio
import logging
from decimal import Decimal
from groq import AsyncGroq
from backend.config import GROQ_API_KEY, GROQ_MODEL
from backend.models.schemas import Abstract, StanceResult, StudyType
from backend.security.cost_tracker import default_cost_tracker

logger = logging.getLogger(__name__)

_client: AsyncGroq | None = None


def get_groq() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=GROQ_API_KEY)
    return _client


STANCE_PROMPT = """You are a biomedical evidence analyst. Given a clinical question and a study's key finding, classify the study's stance toward the question.

Clinical question: {query}

Study details:
- Title: {title}
- Finding: {claim}
- Abstract excerpt: {abstract_excerpt}

Classify the stance as exactly one of:
- SUPPORTS: The study finding supports, confirms, or provides evidence in favour of the claim in the question
- CONTRADICTS: The study finding contradicts, refutes, or provides evidence against the claim in the question
- NEUTRAL: The study finding is inconclusive, mixed, unrelated, or cannot be clearly classified

Return ONLY valid JSON with this exact structure:
{{
  "stance": "SUPPORTS" | "CONTRADICTS" | "NEUTRAL",
  "confidence": 0.0 to 1.0,
  "reason": "one sentence explaining why"
}}

Do NOT include any text outside the JSON object."""


async def classify_stance(
    query: str,
    payload: dict,
) -> StanceResult | None:
    """Classify one study's stance toward the query."""
    if not default_cost_tracker.can_proceed():
        logger.warning("Cost/rate guard blocked stance classification call — skipping.")
        return None

    try:
        claim = payload.get("claim", "") or payload.get("abstract", "")[:300]
        abstract_excerpt = payload.get("abstract", "")[:500]
        title = payload.get("title", "")

        response = await get_groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": STANCE_PROMPT.format(
                        query=query,
                        title=title,
                        claim=claim,
                        abstract_excerpt=abstract_excerpt,
                    ),
                }
            ],
            temperature=0.1,
            max_tokens=200,
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
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        stance = data.get("stance", "NEUTRAL")
        if stance not in ("SUPPORTS", "CONTRADICTS", "NEUTRAL"):
            stance = "NEUTRAL"

        return StanceResult(
            pmid=payload["pmid"],
            title=title,
            year=payload.get("year"),
            journal=payload.get("journal"),
            study_type=StudyType(payload.get("study_type", "unknown")),
            sample_size=payload.get("sample_size"),
            claim=claim,
            stance=stance,
            confidence=float(data.get("confidence", 0.5)),
            reason=data.get("reason", ""),
        )

    except Exception:
        return None


async def classify_batch(
    query: str,
    payloads: list[dict],
    concurrency: int = 5,
) -> list[StanceResult]:
    """Classify stances for multiple studies with rate-limited concurrency."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(payload: dict) -> StanceResult | None:
        async with semaphore:
            result = await classify_stance(query, payload)
            await asyncio.sleep(0.15)
            return result

    tasks = [_guarded(p) for p in payloads]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]