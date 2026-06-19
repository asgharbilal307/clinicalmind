from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

ABSTRACTS_COLLECTION = os.getenv("ABSTRACTS_COLLECTION", "clinicalmind_abstracts")
CLAIMS_COLLECTION = os.getenv("CLAIMS_COLLECTION", "clinicalmind_claims")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension

PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# How many abstracts to retrieve per query topic during ingestion
PUBMED_MAX_RESULTS = 100

# How many studies to retrieve per user question
RETRIEVAL_TOP_K = 20

# Minimum studies on each side to trigger debate (else returns "insufficient evidence")
MIN_STUDIES_PER_SIDE = 2