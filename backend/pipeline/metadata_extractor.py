"""
Phase 2 metadata extractor.
Extracts funding source, study quality signals, and population characteristics
from a medical abstract in a single LLM call per abstract.
Running at ingest time so it never slows down the debate endpoint.
"""
import json
import asyncio
import logging
from decimal import Decimal
from groq import AsyncGroq
from backend.config import GROQ_API_KEY, GROQ_INGEST_MODEL as GROQ_MODEL
from backend.security.cost_tracker import default_cost_tracker

logger = logging.getLogger(__name__)

_client: AsyncGroq | None = None


def get_groq() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=GROQ_API_KEY)
    return _client


METADATA_PROMPT = """You are a biomedical research analyst. Extract metadata from this abstract.

Title: {title}
Abstract: {abstract}

Return ONLY valid JSON. No text outside the JSON. No trailing commas. Use null for unknown values.

{{
  "funding_source": "industry" or "government" or "university" or "mixed" or "unknown",
  "funder_name": "name of funder or null",
  "quality_score": "high" or "medium" or "low",
  "quality_randomized": true or false or null,
  "quality_blinded": true or false or null,
  "quality_has_control": true or false or null,
  "quality_duration_weeks": integer or null,
  "quality_reason": "one sentence",
  "pop_age_group": "children" or "adults" or "elderly" or "mixed" or "unknown",
  "pop_gender": "male" or "female" or "mixed" or "unknown",
  "pop_condition": "primary condition studied or null",
  "pop_country": "country or null",
  "pop_severity": "healthy" or "mild" or "moderate" or "severe" or "mixed" or "unknown"
}}

Rules:
- funding_source is "industry" if pharma, biotech, or supplement companies funded it
- quality_score is "high" for RCT or systematic review, "medium" for cohort, "low" for case report
- Only extract what is explicitly stated. Use null when unsure."""


async def extract_metadata(pmid: str, title: str, abstract: str) -> dict:
    """
    Extract funding, quality, and population metadata from one abstract.
    Returns a flat dict ready to be merged into a Qdrant payload.
    Returns empty dict on failure — never crashes the ingestion pipeline.
    """
    if not default_cost_tracker.can_proceed():
        logger.warning(f"Cost guard blocked metadata extraction for PMID {pmid}")
        return {}

    try:
        response = await get_groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": METADATA_PROMPT.format(
                        title=title,
                        abstract=abstract[:2500],
                    ),
                }
            ],
            temperature=0.1,
            max_tokens=400,
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

        # Flat structure — map directly to payload fields
        return {
            "funding_source": data.get("funding_source", "unknown"),
            "funder_name": data.get("funder_name"),
            "quality_score": data.get("quality_score", "unknown"),
            "quality_randomized": data.get("quality_randomized"),
            "quality_blinded": data.get("quality_blinded"),
            "quality_has_control": data.get("quality_has_control"),
            "quality_duration_weeks": data.get("quality_duration_weeks"),
            "quality_reason": data.get("quality_reason", ""),
            "pop_age_group": data.get("pop_age_group", "unknown"),
            "pop_min_age": None,
            "pop_max_age": None,
            "pop_gender": data.get("pop_gender", "unknown"),
            "pop_condition": data.get("pop_condition"),
            "pop_country": data.get("pop_country"),
            "pop_severity": data.get("pop_severity", "unknown"),
        }

    except Exception as e:
        logger.warning(f"Metadata extraction failed for PMID {pmid}: {e}")
        return {}


async def extract_metadata_batch(
    abstracts: list[dict],
    concurrency: int = 2,
) -> dict[str, dict]:
    """
    Extract metadata for a batch of abstracts.
    Concurrency kept at 2 to respect llama-3.1-8b-instant's
    6,000 TPM free-tier limit (~800 tokens per call = ~7 calls/min max).
    abstracts: list of dicts with keys pmid, title, abstract
    Returns: dict mapping pmid → metadata dict
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(abstract: dict) -> tuple[str, dict]:
        async with semaphore:
            pmid = abstract["pmid"]
            result = await extract_metadata(
                pmid=pmid,
                title=abstract.get("title", ""),
                abstract=abstract.get("abstract", ""),
            )
            await asyncio.sleep(1.0)  # ~60 calls/min max; TPM limit is ~7/min so Groq client retries handle the rest
            return pmid, result

    tasks = [_guarded(a) for a in abstracts]
    results = await asyncio.gather(*tasks)
    return {pmid: meta for pmid, meta in results if meta}