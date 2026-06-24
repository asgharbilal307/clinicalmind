from dotenv import load_dotenv
import os
from decimal import Decimal

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-8-versatile")
GROQ_INGEST_MODEL = os.getenv("GROQ_INGEST_MODEL", "llama-3.1-8b-instant")

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

# ==========================================
# SECURITY CONFIGURATION
# ==========================================

# Rate Limiting
AI_RATE_LIMIT_PER_MINUTE = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", 50))
AI_MAX_REQUESTS_PER_USER = int(os.getenv("AI_MAX_REQUESTS_PER_USER", 100))
AI_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AI_RATE_LIMIT_WINDOW_SECONDS", 60))

# Budget Controls
AI_MONTHLY_BUDGET_USD = Decimal(os.getenv("AI_MONTHLY_BUDGET_USD", "100"))
AI_MAX_COST_PER_REQUEST = Decimal(os.getenv("AI_MAX_COST_PER_REQUEST", "0.50"))
AI_COST_WARN_AT_PERCENT = int(os.getenv("AI_COST_WARN_AT_PERCENT", 75))
AI_COST_CRITICAL_AT_PERCENT = int(os.getenv("AI_COST_CRITICAL_AT_PERCENT", 90))

# Input Validation
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", 500))
MAX_TOPIC_LENGTH = int(os.getenv("MAX_TOPIC_LENGTH", 200))

# Prompt Guard (strict mode blocks injection attempts)
AI_ENABLE_PROMPT_GUARD = os.getenv("AI_ENABLE_PROMPT_GUARD", "true").lower() == "true"

# Debug mode (disable in production)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"