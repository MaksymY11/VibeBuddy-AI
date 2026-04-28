# 🎧 Model Card: Vibe Buddy AI

## 1. Model Name

**Vibe Buddy AI**

---

## 2. Intended Use

Vibe Buddy takes natural-language mood descriptions (e.g., "I just finished a workout and want something high energy") and returns the top 5 songs from a 1,710-song catalog, each with a match score and a natural-language explanation.

- Recommendations: a ranked list of 5 songs with match scores and LLM-generated explanations that reference the user's own words.
- User assumptions: the user describes their mood conversationally. The system extracts structured preferences (8 audio features + mood) via LLM, with no manual numeric input.

---

## 3. How the Model Works

The system uses an 8-step agentic pipeline (see [architecture diagram](assets/architecture.png)). The core reasoning steps:

1. **Elicit:** A conversational LLM (Claude Haiku) asks the user about their mood and extracts structured preferences — 8 numeric features (energy, valence, danceability, acousticness, instrumentalness, liveness, speechiness, tempo) plus a mood label and an optional genre hint — via tool use. If the LLM fails to extract after 3 user turns, extraction is forced via a synthetic follow-up.
2. **Retrieve:** The extracted preferences become an 8-dimensional vector. If a genre hint is present, ChromaDB first retrieves songs filtered by that genre, then backfills with unfiltered results if needed. Without a genre hint, retrieval is purely similarity-based across all 114 genres.
3. **Score:** A weighted distance scorer ranks the 20 candidates. Weights: energy (2.0), valence (1.5), danceability (1.5), acousticness (1.0), tempo (0.75), instrumentalness/liveness/speechiness (0.5 each). Mood adds a 1.0 bonus on exact match. Genre adds a 1.5 bonus when the song's genre matches the user's genre hint. Top 5 are selected.
4. **Explain:** An LLM (Claude Sonnet) writes natural-language explanations for each song, referencing the user's own words rather than raw feature values.
5. **Reflect:** An LLM (Claude Haiku) self-critiques the recommendations for genre diversity and feature dominance, informed by automated guardrail results. When the user requested a specific genre, same-genre results are expected and not penalized. If it fails, the pipeline retries once with a wider candidate pool.

### Guardrails & Reliability

**Input guardrails:**
- Profile values clamped to 0.0–1.0 (handles out-of-range extraction)
- Fuzzy mood matching via `difflib` (e.g., "chil" → "chill", unknown moods default to "chill")
- Genre hint validation with alias mapping (e.g., "rap" → "hip-hop", "r&b" → "r-n-b") and fuzzy matching against the full catalog of 114 genres
- Input validation rejects empty/too-short messages before they reach the LLM
- Prompt injection detection using `difflib.SequenceMatcher` with sliding-window fuzzy matching against known injection patterns
- HTML escaping on LLM-generated explanations before rendering in the UI

**Output guardrails:**
- Genre diversity check: top 5 must include at least 2 genres (skipped when user requested a specific genre)
- Duplicate artist check: no artist appears more than once in top 5
- Relevance threshold: average match score must exceed a minimum
- Candidate count verification: ensures enough songs were retrieved before scoring

**Cost controls:**
- Session rate limiter: 3 recommendation flows per session, 4 conversation turns per flow
- Model tiering: Haiku for extraction/critique, Sonnet for explanations
- Anthropic console spending cap as a hard monthly limit

---

## 4. Data

- **Original catalog:** 18 handcrafted songs (preserved in `data/songs_original.csv` as baseline for evaluation).
- **Expanded catalog:** 1,710 songs curated from the Kaggle "Spotify Tracks Genre" dataset. 15 songs sampled per genre with a fixed random seed for reproducibility.
- **Source:** Kaggle Spotify Tracks Genre dataset, containing real Spotify audio features.
- **Features (8 numeric):** energy, valence, danceability, acousticness, instrumentalness, liveness, speechiness, tempo_bpm — all normalized to 0.0–1.0 range (tempo normalized by dividing by dataset max during curation).
- **Genres:** 114 genres from the Spotify dataset, balanced at 15 songs each.
- **Moods (12):** excited, happy, energetic, aggressive, intense, fiery, peaceful, chill, tender, melancholy, moody, sad — derived using Russell's Circumplex Model of Affect (valence × energy quadrants) with acousticness and danceability as tiebreakers within each quadrant.
- **Curation script:** `utils/curate_dataset.py` — reads the raw Kaggle CSV, samples by genre, derives mood labels, renames columns, and outputs the final `data/songs.csv`.
- **Known gaps:** mood distribution is uneven (aggressive/happy/melancholy are overrepresented; tender/chill/sad are underrepresented) due to the natural distribution of Spotify audio features.

---

## 5. Strengths

- Natural input: users describe their mood in plain language instead of tuning numeric sliders, lowering the barrier to use.
- Genre awareness: when users mention a genre or artist, the system prioritizes songs from that genre via filtered retrieval and a scoring bonus, with alias mapping for common name variants (e.g., "rap" → "hip-hop").
- Large catalog: 1,710 songs across 114 genres provides real diversity compared to the original 18-song set.
- Human-readable explanations: LLM-generated explanations reference the user's own words, making recommendations feel personalized.
- Self-critique: the reflect step catches low-diversity results (e.g., all same genre) and retries automatically, with genre-aware logic that avoids penalizing same-genre results when the user requested a specific genre.
- Observable reasoning: every pipeline step is logged with timestamps and displayed in the sidebar, making the system's decisions transparent.

---

## 6. Limitations and Bias

1. Energy Dominance Bias
   - Energy's weight (2.0) is double most other features. A user emphasizing energy will get results skewed toward that axis. The reflect step mitigates this partially but does not adjust weights dynamically.

2. Mood Distribution Skew
   - The 1,710-song catalog has uneven mood distribution: aggressive (322), happy (286), and melancholy (292) are overrepresented, while tender (9), chill (17), and sad (30) are underrepresented. Users seeking underrepresented moods get fewer quality matches.

3. Mood is a Binary Feature
   - Mood contributes exactly 1.0 or 0.0 — there's no notion of "happy" being closer to "excited" than to "sad." The LLM maps vague descriptions to the nearest label, but the scoring itself has no soft matching.

4. LLM Extraction Variance
   - Different phrasings of the same intent can produce different numeric profiles, since the LLM infers feature values from conversation. This introduces non-determinism even at temperature=0.

5. Single-Genre Matching
   - Genre hints match exactly one genre at a time. A user requesting "rock" will only get songs tagged as "rock" — not "alt-rock", "hard-rock", or "psych-rock". Related sub-genres require a genre similarity map (see Future Work).

6. Extraction Reliability
   - The LLM occasionally fails to call the extraction tool even after sufficient conversation turns. A forced retry mechanism mitigates this, but adds latency when triggered.

---

## 7. Evaluation

### Automated Eval Harness (`python eval_harness.py`)

7 test cases targeting documented failure modes from the baseline system and new edge cases. Each test calls the full agent pipeline (retrieve → score → explain → reflect) and checks a specific pass condition.

| Test | Input | Pass Condition | Result |
|------|-------|----------------|--------|
| Energy dominance | energy=0.9, all others=0.5 | Not all 5 songs have energy > 0.8 | PASS (4/5 high-energy) |
| Contradictory preferences | energy=0.9, acousticness=0.9 | Returns results without crashing | PASS (5 results) |
| Unknown mood | mood="cosmic void energy" | Guardrail corrects mood, results returned | PASS (corrected to "chill") |
| Neutral user | All features=0.5 | Results span at least 2 genres | PASS (5 genres) |
| Out-of-range values | energy=5.0, valence=-2.0 | Values clamped, results returned | PASS (energy=1.0, valence=0.0) |
| Vague conversation | "idk play something" | LLM asks follow-up, no extraction | PASS |
| Refinement | Low energy → high energy | Second run has higher avg energy | PASS (0.47 → 0.79) |

### Unit and Integration Tests

- **`tests/test_guardrails.py`** — 18 pytest tests covering `validate_mood`, `validate_profile`, `validate_input`, `check_diversity`, `check_duplicates`, `check_relevance`, `check_candidates`, and `run_output_guardrails`. No API calls.
- **`tests/test_retriever.py`** — 4 pytest tests verifying ChromaDB returns results, result structure matches expected keys, `n` parameter is respected, and similarity search returns directionally relevant songs.

### Baseline Comparison

These failure modes were originally documented against the baseline system (5 features, 18 songs, no guardrails):

1. **Out-of-range values:** Baseline broke the scoring formula. Now `validate_profile` clamps all values to 0.0–1.0 before scoring.
2. **Contradictory preferences:** Baseline returned least-bad compromises with no feedback. Now `check_relevance` flags low scores, and the reflect step acknowledges tension.
3. **Unknown mood:** Baseline silently dropped mood contribution (scored 0). Now `validate_mood` fuzzy-matches via `difflib` or defaults to "chill".
4. **Neutral user:** Baseline ranking was dominated by mood match and acousticness. Now the 8-feature scorer with genre diversity checks produces varied results.

---

## 8. Future Work

- Soft mood matching: replace exact-string mood with a similarity map or embeddings so near-synonyms contribute partially.
- Learned weights: replace hard-coded weights with values fit from user feedback or listening history.
- Real-time Spotify integration: query the Spotify API for live catalog data instead of a static CSV.
- User history: track past recommendations to avoid repeats and learn preferences over sessions.
- Multi-genre matching: expand genre hints to include related genres (e.g., "rock" → rock, alt-rock, hard-rock, indie) using a genre similarity map instead of single exact match.

---

## 9. Personal Reflection

The biggest learning moment for me was how easy it is to confuse a recommender system, and how much more sophisticated these systems need to be in order to work like they should. Beyond matching user's preferences, these systems need to extract and normalize featueres, validate input, and balance bias, which are things I haven't thought about prior to working on this project.

When it comes to AI Tool's contributions, it was helpful to see more personalized explanations contributing to factors like "why should we use feature A vs feature B", "why should this feature A's vector should score more than others". It would be very tedious trying to look this up online, thus saving me a lot of time and giving me valuable insights into how these systems are built from architectural perspective.

What surprised me the most is how little code it takes to make output feel "opinionated", Vibe Buddy only uses weighted sum over five numbers, but when it says "Samba do Sol because it's a top match on danceability and valence," it reads like the system understood me, even though it only measured distance on a couple of axes and sorted.

If I were to extend this project, I would replace hard-coded weights, and binary mood match with softer, learned signals, fitting weights from user feedback and treating mood as a similarity map instead of exact string.

---
