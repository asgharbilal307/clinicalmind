from groq import AsyncGroq
from backend.config import GROQ_API_KEY, GROQ_MODEL, MIN_STUDIES_PER_SIDE
from backend.models.schemas import (
    StanceResult,
    DebateOutput,
    ConsensusStrength,
    STUDY_TYPE_WEIGHTS,
)

_client: AsyncGroq | None = None


def get_groq() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=GROQ_API_KEY)
    return _client


def _format_study_list(studies: list[StanceResult]) -> str:
    lines = []
    for s in studies:
        year = s.year or "n/a"
        journal = s.journal or "unknown journal"
        n = f"n={s.sample_size}" if s.sample_size else "sample size unknown"
        lines.append(
            f"- PMID {s.pmid} ({year}, {journal}, {n}, {s.study_type.value}): {s.claim}"
        )
    return "\n".join(lines)


def _compute_consensus(
    supporting: list[StanceResult],
    contradicting: list[StanceResult],
) -> ConsensusStrength:
    """
    Weighted consensus using study type weights.
    Returns a ConsensusStrength enum value.
    """
    def weighted_score(studies: list[StanceResult]) -> float:
        return sum(
            STUDY_TYPE_WEIGHTS.get(s.study_type, 3) * s.confidence
            for s in studies
        )

    pro_score = weighted_score(supporting)
    con_score = weighted_score(contradicting)
    total = pro_score + con_score

    if total == 0:
        return ConsensusStrength.INSUFFICIENT

    pro_ratio = pro_score / total

    if pro_ratio >= 0.80:
        return ConsensusStrength.STRONG_SUPPORT
    elif pro_ratio >= 0.65:
        return ConsensusStrength.MODERATE_SUPPORT
    elif pro_ratio >= 0.55:
        return ConsensusStrength.WEAK_SUPPORT
    elif pro_ratio >= 0.40:
        return ConsensusStrength.CONTESTED
    else:
        return ConsensusStrength.INSUFFICIENT


DEBATE_PROMPT = """You are a scientific referee reviewing conflicting medical evidence.

Clinical question: {query}

SUPPORTING EVIDENCE ({n_pro} studies):
{pro_studies}

CONTRADICTING EVIDENCE ({n_con} studies):
{con_studies}

Your task:
1. Write a "conflict_explanation" (2-3 sentences): explain WHY these studies likely disagree. Look for differences in population, dosage, duration, study type, or methodology visible in the claims.
2. Write a "verdict" (1-2 sentences): summarise the current state of evidence for a clinician.

Both fields must cite at least one PMID inline like (PMID: 12345678).

Return ONLY valid JSON:
{{
  "conflict_explanation": "...",
  "verdict": "..."
}}"""


async def synthesise_debate(
    query: str,
    supporting: list[StanceResult],
    contradicting: list[StanceResult],
    neutral: list[StanceResult],
) -> DebateOutput:
    """Build the full DebateOutput from classified studies."""

    consensus = _compute_consensus(supporting, contradicting)

    # If not enough studies on either side, return early
    if (
        len(supporting) < MIN_STUDIES_PER_SIDE
        or len(contradicting) < MIN_STUDIES_PER_SIDE
    ):
        return DebateOutput(
            query=query,
            consensus_strength=ConsensusStrength.INSUFFICIENT,
            supporting=supporting,
            contradicting=contradicting,
            neutral=neutral,
            conflict_explanation="Insufficient studies on one or both sides to generate a meaningful debate.",
            verdict="Not enough evidence retrieved to draw a conclusion. Try broadening the query or ingesting more studies on this topic.",
            total_studies=len(supporting) + len(contradicting) + len(neutral),
        )

    # Sort each side by confidence descending
    supporting_sorted = sorted(supporting, key=lambda s: s.confidence, reverse=True)
    contradicting_sorted = sorted(
        contradicting, key=lambda s: s.confidence, reverse=True
    )

    # Call Groq for conflict explanation + verdict
    prompt = DEBATE_PROMPT.format(
        query=query,
        n_pro=len(supporting_sorted),
        n_con=len(contradicting_sorted),
        pro_studies=_format_study_list(supporting_sorted[:8]),
        con_studies=_format_study_list(contradicting_sorted[:8]),
    )

    try:
        response = await get_groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        import json
        data = json.loads(raw)
        conflict_explanation = data.get("conflict_explanation", "")
        verdict = data.get("verdict", "")
    except Exception:
        conflict_explanation = "Could not generate conflict explanation."
        verdict = "Could not generate verdict."

    return DebateOutput(
        query=query,
        consensus_strength=consensus,
        supporting=supporting_sorted,
        contradicting=contradicting_sorted,
        neutral=neutral,
        conflict_explanation=conflict_explanation,
        verdict=verdict,
        total_studies=len(supporting) + len(contradicting) + len(neutral),
    )