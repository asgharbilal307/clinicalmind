# ClinicalMind

An AI-powered system that automates the first step of systematic reviews by transforming medical literature retrieval into structured scientific debates.

## The Problem

Medical studies often contradict each other — not because science is broken, but because different studies use different populations, dosages, methodologies, and funding sources. A standard RAG system averages out this disagreement, producing vague summaries like "results are mixed" — which is technically true but useless for decision-making.

ClinicalMind doesn't summarize. It argues.

## How It Works

```
User Query: "Does Omega-3 reduce heart disease?"
                │
                ▼
        ┌───────────────┐
        │   Retriever   │
        │ (Dual Index)  │
        └───────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Stance Classifier    │
    │  PRO / CON / NEUTRAL  │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Group by Position    │
    └───────────────────────┘
                │
          ┌─────┴─────┐
          ▼           ▼
    ┌─────────┐  ┌─────────┐
    │   PRO   │  │   CON   │
    │  Camp   │  │  Camp   │
    └─────────┘  └─────────┘
          │           │
          └─────┬─────┘
                ▼
    ┌───────────────────────┐
    │ Debate Synthesiser    │
    │ (Conflict Explainer)  │
    └───────────────────────┘
                │
                ▼
         ┌─────────────┐
         │   Verdict   │
         └─────────────┘
```

### Key Components

1. **Dual-Index Retrieval**: Two vector indexes — one for claims, one for full abstracts — because claim-level matching produces better stance classification.

2. **Stance Classifier**: Classifies each retrieved study as SUPPORTING, CONTRADICTING, or NEUTRAL toward the user's query.

3. **Group by Position**: Splits studies into opposing camps (teal = PRO, coral = CON) for side-by-side comparison.

4. **Debate Synthesiser**: Explains *why* studies disagree — population differences, dosage variations, funding sources, study duration — and provides a consensus verdict.

## Example Output

**Query:** "Does low-carb dieting improve blood sugar control in type 2 diabetics?"

| PRO Camp (7 studies) | CON Camp (5 studies) |
|---------------------|----------------------|
| PMID: 12345, n=120, 6 months | PMID: 12367, n=450, 12 months |
| PMID: 12348, n=85, 3 months | PMID: 12369, n=520, 18 months |
| ... | ... |

**Verdict:** "This question is scientifically contested. Supporting studies tend to be shorter-term (under 6 months) with self-selected motivated participants. Contradicting studies are longer-term and show regression toward baseline after 12 months. Current consensus: low-carb diets show strong short-term glycemic benefit with uncertain long-term adherence outcomes. Consensus strength: CONTESTED."

## Why This Stands Out

- **Solves a real problem**: Build scientific fact-checking infrastructure, not another PDF chatbot
- **Demonstrates architectural thinking**: Dual-index design shows deliberate engineering decisions
- **Understands AI failure modes**: Built around compensating for LLM weaknesses in representing disagreement

## Tech Stack

- **Backend**: FastAPI
- **AI/LLM**: Hugging Face Transformers, sentence-transformers
- **Vector Store**: ChromaDB
- **Data Source**: PubMed API

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run with Docker
docker-compose up --build

# Or run locally
uvicorn main:app --reload --port 8080
```

## API Endpoints

- `POST /query` - Submit a medical query and receive structured debate results
- `GET /health` - Health check

## License

MIT