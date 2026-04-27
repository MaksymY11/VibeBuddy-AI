# Vibe Buddy AI — Music Recommender

## Project Summary

Vibe Buddy AI is an AI-powered music recommendation system. Users describe their mood in natural language (e.g., "I'm feeling groovy" or "chill rainy day vibes"), and the system uses conversational AI to extract preferences, retrieves matching songs from a 1,710-song catalog via RAG, and returns personalized recommendations with natural-language explanations.

**Key capabilities:**
- Conversational preference elicitation via Claude API
- RAG retrieval over a real Spotify audio features catalog (ChromaDB + cosine similarity)
- Agentic orchestration with observable intermediate reasoning steps
- Input/output guardrails and self-critique
- Automated eval harness covering known edge cases

---

## How The System Works

### Data Pipeline
- **Catalog:** 1,710 songs curated from real Spotify audio features data, balanced across 114 genres (15 songs per genre)
- **Features (8 numeric):** energy, valence, danceability, acousticness, instrumentalness, liveness, speechiness, tempo — all normalized to 0.0-1.0
- **Mood (12 labels):** derived using Russell's Circumplex Model of Affect (valence x energy quadrants) with acousticness and danceability as tiebreakers
- **Vector store:** ChromaDB with cosine similarity over 8-dimensional feature vectors

### Recommendation Pipeline
1. User describes their mood in natural language
2. LLM extracts structured preferences (8 features + mood) from the conversation
3. **Input guardrails** validate and clean the extracted profile (value clamping, fuzzy mood matching)
4. Preferences are converted to an 8-dimensional query vector
5. ChromaDB retrieves the 20 most similar songs (candidates)
6. Candidate count is verified before scoring
7. Scorer ranks candidates using weighted distance and selects the top 5
8. **Output guardrails** check genre diversity, duplicate artists, and relevance scores
9. LLM generates natural-language explanations for each recommendation
10. LLM self-critiques recommendations (informed by guardrail results), retries once if needed

---

## Model Card

See the full [Model Card](model_card.md) for details on intended use, scoring logic, data, limitations, and evaluation.

---

## Setup

```bash
pip install -r requirements.txt
python utils/curate_dataset.py    # generate curated songs.csv (only needed once)
python utils/data_loader.py       # ingest into ChromaDB (only needed once)
```

Set your API key in a `.env` file at the project root:

```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

Run the app:

```bash
streamlit run app.py
```

Test the conversational elicitation standalone:

```bash
python -m pipeline.conversation
```

---

## Project Structure

```
VibeBuddy-AI/
├── app.py                      # Streamlit UI
├── pipeline/
│   ├── __init__.py
│   ├── agent.py                # Agentic orchestrator (multi-step pipeline)
│   ├── conversation.py         # Multi-turn conversation manager + preference extraction
│   ├── explainer.py            # LLM explanation generation
│   ├── guardrails.py           # Input validation, output checks, prompt injection detection
│   ├── llm_client.py           # Claude API wrapper (prompt caching, model selection)
│   ├── rate_limiter.py         # Session-level cost controls (flow + turn caps)
│   └── scorer.py               # Weighted distance scoring (8 features)
├── src/
│   └── recommender.py          # Original scoring logic (baseline, preserved for eval)
├── utils/
│   ├── curate_dataset.py       # Spotify CSV → curated songs.csv
│   ├── data_loader.py          # CSV → ChromaDB ingestion
│   └── retriever.py            # ChromaDB query wrapper
├── data/
│   ├── songs.csv               # Curated 1,710-song catalog
│   └── train.csv               # Raw Spotify dataset
├── tests/
│   ├── test_scorer.py
│   ├── test_agent.py
│   └── test_recommender.py
├── .env                        # API key (not committed)
├── model_card.md
├── requirements.txt
└── README.md
```
