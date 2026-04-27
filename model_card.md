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

The system uses a 5-step agentic pipeline:

1. **Elicit:** A conversational LLM (Claude Haiku) asks the user about their mood and extracts structured preferences — 8 numeric features (energy, valence, danceability, acousticness, instrumentalness, liveness, speechiness, tempo) plus a mood label — via tool use.
2. **Retrieve:** The extracted preferences become an 8-dimensional vector. ChromaDB finds the 20 nearest songs by cosine similarity.
3. **Score:** A weighted distance scorer ranks the 20 candidates. Weights: energy (2.0), valence (1.5), danceability (1.5), acousticness (1.0), tempo (0.75), instrumentalness/liveness/speechiness (0.5 each). Mood adds a 1.0 bonus on exact match. Top 5 are selected.
4. **Explain:** An LLM (Claude Sonnet) writes natural-language explanations for each song, referencing the user's own words rather than raw feature values.
5. **Reflect:** An LLM (Claude Haiku) self-critiques the recommendations for genre diversity and feature dominance. If it fails, the pipeline retries once with a wider candidate pool.

---

## 4. Data

- **Original catalog:** 18 handcrafted songs (preserved in `data/songs_original.csv` as baseline for evaluation).
- **Expanded catalog:** 1,710 songs curated from the Kaggle "Spotify Tracks Genre" dataset. 15 songs sampled per genre with a fixed random seed for reproducibility.
- **Source:** Kaggle Spotify Tracks Genre dataset, containing real Spotify audio features.
- **Features (8 numeric):** energy, valence, danceability, acousticness, instrumentalness, liveness, speechiness, tempo_bpm — all in 0.0–1.0 range (except tempo_bpm which is raw BPM).
- **Genres:** 114 genres from the Spotify dataset, balanced at 15 songs each.
- **Moods (12):** excited, happy, energetic, aggressive, intense, fiery, peaceful, chill, tender, melancholy, moody, sad — derived using Russell's Circumplex Model of Affect (valence × energy quadrants) with acousticness and danceability as tiebreakers within each quadrant.
- **Curation script:** `utils/curate_dataset.py` — reads the raw Kaggle CSV, samples by genre, derives mood labels, renames columns, and outputs the final `data/songs.csv`.
- **Known gaps:** mood distribution is uneven (aggressive/happy/melancholy are overrepresented; tender/chill/sad are underrepresented) due to the natural distribution of Spotify audio features.

---

## 5. Strengths

- Natural input: users describe their mood in plain language instead of tuning numeric sliders, lowering the barrier to use.
- Large catalog: 1,710 songs across 114 genres provides real diversity compared to the original 18-song set.
- Human-readable explanations: LLM-generated explanations reference the user's own words, making recommendations feel personalized.
- Self-critique: the reflect step catches low-diversity results (e.g., all same genre) and retries automatically.
- Observable reasoning: every pipeline step is logged with timestamps, making the system's decisions transparent.

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

---

## 7. Evaluation

Test 1: Out-of-range Extremist

- Tested with user_prefs = {"valence score": -2.0}
- Breaks the scoring formula due to having out of range values (beyond [0,1])

  ![Test_1](docs/Test1.png)

Test 2: Contradictory Acoustic Lover

- Tested with user_prefs = {"energy_score": 1.0, "valence_score": 1.0, "likes_acoustic": True}
- High energy songs are rarely acoutic, thus resulting in top recommendations that are not that good of matches, but rather least-bad compromises.

![Test_2](docs/Test2.png)

Test 3: Unknown Mood String

- Tested with mood string that is a typo/not in catalog user_prefs = {"mood": "melancholic-vibes-2026"}
- Mood contribution becomes 0 for each song, so feature is silently dropped with no warning.

![Test_3](docs/Test3.png)

Test 4: Perfectly Neutral User

- Tested with user_prefs = {"energy_score": 0.5, "valence_score": 0.5, "dance_score": 0.5,
  "likes_acoustic": False, "mood": "sad"}
- Exposes bias, due to ranking being dominated entirely by mood match and acousticness.

![Test_4](docs/Test4.png)

---

## 8. Future Work

- Soft mood matching: replace exact-string mood with a similarity map or embeddings so near-synonyms contribute partially.
- Learned weights: replace hard-coded weights with values fit from user feedback or listening history.
- Real-time Spotify integration: query the Spotify API for live catalog data instead of a static CSV.
- User history: track past recommendations to avoid repeats and learn preferences over sessions.
- Genre filtering: allow users to exclude genres they dislike (e.g., filtering out "kids" genre results).

---

## 9. Personal Reflection

The biggest learning moment for me was how easy it is to confuse a recommender system, and how much more sophisticated these systems need to be in order to work like they should. Beyond matching user's preferences, these systems need to extract and normalize featueres, validate input, and balance bias, which are things I haven't thought about prior to working on this project.

When it comes to AI Tool's contributions, it was helpful to see more personalized explanations contributing to factors like "why should we use feature A vs feature B", "why should this feature A's vector should score more than others". It would be very tedious trying to look this up online, thus saving me a lot of time and giving me valuable insights into how these systems are built from architectural perspective.

What surprised me the most is how little code it takes to make output feel "opinionated", Vibe Buddy only uses weighted sum over five numbers, but when it says "Samba do Sol because it's a top match on danceability and valence," it reads like the system understood me, even though it only measured distance on a couple of axes and sorted.

If I were to extend this project, I would replace hard-coded weights, and binary mood match with softer, learned signals, fitting weights from user feedback and treating mood as a similarity map instead of exact string.

---
