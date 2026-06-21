from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.models.schemas import IngestRequest, IngestResponse, DebateRequest, DebateOutput
from backend.ingestion.pubmed import fetch_topic
from backend.ingestion.embedder import upsert_abstracts, upsert_claims, ensure_collections
from backend.pipeline.claim_extractor import extract_claims_batch
from backend.pipeline.retriever import hybrid_retrieve
from backend.pipeline.stance_classifier import classify_batch
from backend.pipeline.debate_synthesiser import synthesise_debate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Qdrant collections exist on startup
    ensure_collections()
    yield


app = FastAPI(
    title="ClinicalMind API",
    description="Evidence intelligence platform — surfaces contradictions in medical literature",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ClinicalMind"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """
    Fetch PubMed abstracts for a topic, embed them, extract claims,
    and store everything in Qdrant.
    """
    # 1. Fetch from PubMed
    abstracts = await fetch_topic(req.topic, req.max_results)
    if not abstracts:
        raise HTTPException(
            status_code=404,
            detail=f"No abstracts found for topic: {req.topic}",
        )

    # 2. Store abstracts
    stored = upsert_abstracts(abstracts)

    # 3. Extract claims with LLM
    claims = await extract_claims_batch(abstracts, concurrency=5)

    # 4. Store claims (with abstract metadata for enrichment)
    abstracts_map = {a.pmid: a for a in abstracts}
    claims_stored = upsert_claims(claims, abstracts_map)

    return IngestResponse(
        topic=req.topic,
        abstracts_fetched=len(abstracts),
        abstracts_stored=stored,
        claims_extracted=claims_stored,
        message=f"Successfully ingested {stored} new abstracts and {claims_stored} claims for '{req.topic}'.",
    )


@app.post("/debate", response_model=DebateOutput)
async def debate(req: DebateRequest):
    """
    Given a clinical question, retrieve relevant studies,
    classify each study's stance, and return a structured debate.
    """
    # 1. Hybrid retrieval
    hits = hybrid_retrieve(req.query, top_k=req.top_k)
    if not hits:
        raise HTTPException(
            status_code=404,
            detail="No studies found. Ingest a relevant topic first.",
        )

    # 2. Classify stance for each retrieved study
    payloads = [h["payload"] for h in hits]
    classified = await classify_batch(req.query, payloads, concurrency=5)

    # 3. Split into camps
    supporting = [s for s in classified if s.stance == "SUPPORTS"]
    contradicting = [s for s in classified if s.stance == "CONTRADICTS"]
    neutral = [s for s in classified if s.stance == "NEUTRAL"]

    # 4. Synthesise debate
    result = await synthesise_debate(req.query, supporting, contradicting, neutral)
    return result


@app.post("/debate/debug")
async def debate_debug(req: DebateRequest):
    """
    TEMPORARY DEBUG ROUTE — shows raw retrieval + stance results
    before the min-studies-per-side filter is applied.
    Remove this route once Phase 1 is verified working.
    """
    hits = hybrid_retrieve(req.query, top_k=req.top_k)

    if not hits:
        return {
            "query": req.query,
            "retrieved_count": 0,
            "message": "Retrieval returned ZERO hits. The problem is in retrieval/ingestion, not stance classification. Check /collections/stats and confirm you ingested a topic related to this query.",
        }

    payloads = [h["payload"] for h in hits]
    classified = await classify_batch(req.query, payloads, concurrency=5)

    supporting = [s for s in classified if s.stance == "SUPPORTS"]
    contradicting = [s for s in classified if s.stance == "CONTRADICTS"]
    neutral = [s for s in classified if s.stance == "NEUTRAL"]

    return {
        "query": req.query,
        "retrieved_count": len(hits),
        "classified_count": len(classified),
        "failed_classifications": len(hits) - len(classified),
        "supporting_count": len(supporting),
        "contradicting_count": len(contradicting),
        "neutral_count": len(neutral),
        "retrieved_pmids_and_titles": [
            {"pmid": h["payload"].get("pmid"), "title": h["payload"].get("title", "")[:100], "score": round(h["score"], 4)}
            for h in hits
        ],
        "stance_breakdown": [
            {
                "pmid": s.pmid,
                "title": s.title[:100],
                "stance": s.stance,
                "confidence": s.confidence,
                "reason": s.reason,
                "claim": s.claim[:150],
            }
            for s in classified
        ],
    }


@app.get("/cost-status")
async def cost_status():
    """Return current cost/request-rate tracker status."""
    from backend.cost_tracker import default_cost_tracker
    return default_cost_tracker.get_status()


@app.get("/collections/stats")
async def collection_stats():
    """Return counts of stored abstracts and claims."""
    from backend.ingestion.embedder import get_client
    from backend.config import ABSTRACTS_COLLECTION, CLAIMS_COLLECTION

    client = get_client()
    try:
        abstracts_info = client.get_collection(ABSTRACTS_COLLECTION)
        claims_info = client.get_collection(CLAIMS_COLLECTION)
        return {
            "abstracts": abstracts_info.points_count,
            "claims": claims_info.points_count,
        }
    except Exception as e:
        return {"error": str(e)}