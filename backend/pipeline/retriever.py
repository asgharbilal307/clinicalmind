from qdrant_client import QdrantClient
from qdrant_client.models import Filter
from rank_bm25 import BM25Okapi
from backend.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    ABSTRACTS_COLLECTION,
    CLAIMS_COLLECTION,
    RETRIEVAL_TOP_K,
)
from backend.ingestion.embedder import embed_texts, get_client
from backend.models.schemas import Abstract, Claim, StudyType


def _payload_to_abstract(payload: dict) -> Abstract:
    return Abstract(
        pmid=payload["pmid"],
        title=payload.get("title", ""),
        abstract=payload.get("abstract", ""),
        year=payload.get("year"),
        journal=payload.get("journal"),
        authors=payload.get("authors", []),
        study_type=StudyType(payload.get("study_type", "unknown")),
        sample_size=payload.get("sample_size"),
    )


def _payload_to_claim_abstract(payload: dict) -> tuple[str, Abstract]:
    """Returns (claim_text, Abstract) from a claims collection payload."""
    abstract = Abstract(
        pmid=payload["pmid"],
        title=payload.get("title", ""),
        abstract=payload.get("claim", ""),  # claim text as the abstract body
        year=payload.get("year"),
        journal=payload.get("journal"),
        study_type=StudyType(payload.get("study_type", "unknown")),
        sample_size=payload.get("sample_size"),
    )
    return payload.get("claim", ""), abstract


def dense_search(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """Search abstracts collection by dense vector similarity."""
    client = get_client()
    vector = embed_texts([query])[0]

    results = client.search(
        collection_name=ABSTRACTS_COLLECTION,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "pmid": r.payload["pmid"],
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]


def claims_dense_search(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """Search claims collection by dense vector similarity."""
    client = get_client()
    vector = embed_texts([query])[0]

    results = client.search(
        collection_name=CLAIMS_COLLECTION,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "pmid": r.payload["pmid"],
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]


def hybrid_retrieve(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """
    Hybrid retrieval: combine dense search on abstracts + dense search on claims.
    Merge by PMID, keeping highest score. Return top_k unique results.
    """
    abstract_hits = dense_search(query, top_k=top_k)
    claim_hits = claims_dense_search(query, top_k=top_k)

    # Merge by PMID — prefer abstract payload, take max score
    merged: dict[str, dict] = {}

    for hit in abstract_hits:
        pmid = hit["pmid"]
        if pmid not in merged or hit["score"] > merged[pmid]["score"]:
            merged[pmid] = hit

    for hit in claim_hits:
        pmid = hit["pmid"]
        # Merge claim text into payload if we already have abstract data
        if pmid in merged:
            if hit["score"] > merged[pmid]["score"]:
                merged[pmid]["score"] = hit["score"]
            merged[pmid]["payload"]["claim"] = hit["payload"].get("claim", "")
        else:
            merged[pmid] = hit

    # Sort by score descending and return top_k
    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]