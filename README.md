# ClinicalMind

An evidence intelligence platform that automates the first step of a systematic review — by turning medical literature retrieval into a structured scientific debate instead of a one-sided summary.

## The Problem

Medical studies often contradict each other — not because science is broken, but because different studies use different populations, dosages, methodologies, and study designs. A standard RAG chatbot averages out this disagreement into a vague summary like "results are mixed," which is technically true and practically useless.

ClinicalMind doesn't summarize. It argues.

## How It Works

```
User Query: "Does Omega-3 reduce heart disease?"
                │
                ▼
        ┌───────────────┐
        │   PubMed      │
        │   Retrieval   │
        └───────────────┘
                │
                ▼
    ┌───────────────────────┐
    │   Hybrid Retriever    │
    │  (dual-index search)  │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │   Stance Classifier   │
    │ SUPPORTS / CONTRADICTS│
    │       / NEUTRAL       │
    └───────────────────────┘
                │
          ┌─────┴─────┐
          ▼           ▼
    ┌─────────┐  ┌─────────┐
    │Supports │  │Contra-  │
    │  camp   │  │dicts    │
    └─────────┘  └─────────┘
          │           │
          └─────┬─────┘
                ▼
    ┌───────────────────────┐
    │  Debate Synthesiser   │
    │ (weighted consensus + │
    │  conflict explainer)  │
    └───────────────────────┘
                │
                ▼
         ┌─────────────┐
         │   Verdict   │
         └─────────────┘
```

### Key Components

1. **Dual-index retrieval** — two Qdrant collections: one holding full abstract embeddings, one holding LLM-extracted structured claims. Claim-level matching produces more precise stance classification than chunk-level matching alone.

2. **Stance classifier** — for every retrieved study, an LLM call classifies its stance toward the user's query as `SUPPORTS`, `CONTRADICTS`, or `NEUTRAL`, with a confidence score and a one-sentence justification.

3. **Weighted consensus scoring** — studies aren't counted equally. A meta-analysis is weighted more heavily than a case report when computing the overall consensus strength (`Strong support` / `Moderate support` / `Weak support` / `Contested` / `Insufficient evidence`).

4. **Debate synthesiser** — a final LLM call explains *why* the supporting and contradicting studies disagree (population differences, dosage, duration, methodology) and produces a verdict, citing PMIDs.

## Tech Stack

- **Backend**: FastAPI (Python)
- **LLM**: Groq (`llama-3.1-70b-versatile`) — used for claim extraction, stance classification, and debate synthesis
- **Embeddings**: `sentence-transformers` running `nomic-ai/nomic-embed-text-v1` locally (no embedding API key required)
- **Vector store**: Qdrant, run via Docker
- **Data source**: PubMed E-utilities API (live retrieval, no offline dataset)
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS

## Example Output

**Query:** "Does intermittent fasting lead to greater weight loss than continuous calorie restriction?"

| Supports (n studies) | Contradicts (n studies) |
|---|---|
| PMID 12345678 — n=120, 6 months | PMID 87654321 — n=450, 12 months |
| PMID 12345679 — n=85, 3 months | PMID 87654322 — n=520, 18 months |

**Verdict:** "This question is contested. Supporting studies tend to be shorter-term with self-selected, motivated participants. Contradicting studies follow participants longer and show regression toward baseline after 12 months. Consensus strength: Contested."

## Why This Stands Out

- **Solves a real problem** — builds scientific evidence-weighing infrastructure, not another "chat with your PDFs" wrapper
- **Demonstrates architectural intent** — the dual-index design and weighted consensus scoring are deliberate engineering decisions made to solve a specific accuracy problem, not default choices
- **Designed around a known LLM failure mode** — language models default to smoothing over disagreement; this system is built specifically to stop that from happening, and was validated by manually checking model-classified stances against the actual PubMed abstracts

## Quick Start

### Backend

```bash
# 1. Start Qdrant
docker compose up -d

# 2. Configure environment
cp .env.example .env
# Add your free Groq API key (console.groq.com) to GROQ_API_KEY

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API
uvicorn backend.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if your backend isn't on `http://localhost:8000`.

## API Endpoints

- `POST /ingest` — fetch PubMed abstracts for a topic, extract claims, store in Qdrant
- `POST /debate` — submit a clinical question, get back a structured supports/contradicts/neutral debate with a weighted verdict
- `GET /collections/stats` — current count of stored abstracts and claims
- `GET /health` — health check

## License

MIT
