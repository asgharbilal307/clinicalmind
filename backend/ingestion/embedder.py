from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)
from backend.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    ABSTRACTS_COLLECTION,
    CLAIMS_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
)
from backend.models.schemas import Abstract, Claim
import uuid

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def ensure_collections():
    """Create Qdrant collections if they don't exist, or recreate if dimension changed."""
    client = get_client()

    existing = {c.name for c in client.get_collections().collections}

    # Check if collections exist and have correct dimension
    def needs_recreation(collection_name: str) -> bool:
        if collection_name not in existing:
            return True
        collection_info = client.get_collection(collection_name)
        return collection_info.config.params.vectors.size != EMBEDDING_DIM

    # Delete and recreate collections if needed
    for collection_name in [ABSTRACTS_COLLECTION, CLAIMS_COLLECTION]:
        if needs_recreation(collection_name):
            if collection_name in existing:
                client.delete_collection(collection_name=collection_name)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            client.create_payload_index(
                collection_name=collection_name,
                field_name="pmid",
                field_schema=PayloadSchemaType.KEYWORD,
            )


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


def upsert_abstracts(abstracts: list[Abstract]) -> int:
    """Embed and store abstracts. Returns number stored."""
    if not abstracts:
        return 0

    client = get_client()
    ensure_collections()

    # Check which PMIDs already exist to avoid duplicates
    existing_pmids = _get_existing_pmids(client, ABSTRACTS_COLLECTION)
    new_abstracts = [a for a in abstracts if a.pmid not in existing_pmids]

    if not new_abstracts:
        return 0

    texts = [f"{a.title}. {a.abstract}" for a in new_abstracts]
    vectors = embed_texts(texts)

    points = []
    for abstract, vector in zip(new_abstracts, vectors):
        points.append(
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, abstract.pmid)),
                vector=vector,
                payload={
                    "pmid": abstract.pmid,
                    "title": abstract.title,
                    "abstract": abstract.abstract,
                    "year": abstract.year,
                    "journal": abstract.journal,
                    "authors": abstract.authors,
                    "study_type": abstract.study_type.value,
                    "sample_size": abstract.sample_size,
                },
            )
        )

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=ABSTRACTS_COLLECTION,
            points=points[i : i + batch_size],
        )

    return len(new_abstracts)


def upsert_claims(claims: list[Claim], abstracts_map: dict[str, Abstract]) -> int:
    """Embed and store extracted claims. Returns number stored."""
    if not claims:
        return 0

    client = get_client()
    existing_pmids = _get_existing_pmids(client, CLAIMS_COLLECTION)
    new_claims = [c for c in claims if c.pmid not in existing_pmids]

    if not new_claims:
        return 0

    texts = [c.claim for c in new_claims]
    vectors = embed_texts(texts)

    points = []
    for claim, vector in zip(new_claims, vectors):
        abstract = abstracts_map.get(claim.pmid)
        points.append(
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"claim_{claim.pmid}")),
                vector=vector,
                payload={
                    "pmid": claim.pmid,
                    "claim": claim.claim,
                    "direction": claim.direction,
                    "outcome": claim.outcome,
                    "title": abstract.title if abstract else "",
                    "year": abstract.year if abstract else None,
                    "journal": abstract.journal if abstract else None,
                    "study_type": abstract.study_type.value if abstract else "unknown",
                    "sample_size": abstract.sample_size if abstract else None,
                },
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=CLAIMS_COLLECTION,
            points=points[i : i + batch_size],
        )

    return len(new_claims)


def _get_existing_pmids(client: QdrantClient, collection: str) -> set[str]:
    """Scroll through collection and return all stored PMIDs."""
    pmids = set()
    offset = None
    while True:
        result, offset = client.scroll(
            collection_name=collection,
            scroll_filter=None,
            limit=500,
            offset=offset,
            with_payload=["pmid"],
        )
        for point in result:
            if point.payload and "pmid" in point.payload:
                pmids.add(point.payload["pmid"])
        if offset is None:
            break
    return pmids