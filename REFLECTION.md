# Reflection

## Base Project Identification

**Original project:** Vibe Buddy — a Python music recommendation system built as a Module 3 project for the CodePath Applied AI Engineering course (AI110).

**Original repo:** [ai110-module3show-musicrecommendersimulation-starter](https://github.com/MaksymY11/ai110-module3show-musicrecommendersimulation-starter)

**Original scope:**
- 18 hardcoded songs with 5 manually assigned feature values (energy, valence, danceability, acousticness, mood)
- `Song` and `UserProfile` dataclasses with slider-based input
- Weighted distance scoring with fixed weights (energy=2.0, valence=1.5, danceability=1.5, mood=1.0, acousticness=1.0)
- Basic "because" explanations citing the two strongest contributing features
- Streamlit UI with manual slider controls
- 4 documented failure modes: energy dominance bias, contradictory preferences, unknown moods, neutral users

**What changed:**
The extended version replaces every major component. The 18 hardcoded songs became a 1,710-song catalog from real Spotify audio features data, indexed in ChromaDB for vector similarity search. Sliders became a conversational AI interface powered by Claude. The 5-feature scoring expanded to 8 features with mood and genre bonuses. A full agentic pipeline (ELICIT → VALIDATE → RETRIEVE → CHECK_CANDIDATES → SCORE → GUARDRAILS → EXPLAIN → REFLECT) replaced the single-pass scorer. Input/output guardrails, prompt injection detection, and LLM self-critique were added for reliability. An automated eval harness proves the system handles the original 4 failure modes plus 3 additional edge cases.

---

## How AI Was Used in Development

Claude (via Claude Code CLI) was used throughout development as a pair programming partner:

- **Architecture planning:** Claude helped design the phased implementation plan, including the decision to use ChromaDB for vector search, tool use for structured extraction, and the agentic pipeline pattern.
- **Code generation:** Most modules were drafted by Claude and then reviewed, tested, and revised. The conversation system prompt, few-shot examples, and guardrail logic went through multiple iterations.
- **Debugging:** Claude helped diagnose issues like ChromaDB query structure, Streamlit session state management, and edge cases in the scoring math.
- **Documentation:** README, model card, and this reflection were structured with Claude's help.

---

## One Helpful AI Suggestion

When struggling with AI top 5 songs output, Claude helped me successfully diagnose the issue - missing genre bias, and helped me improve relevance of picked songs by introducing GENRE_MATCH weight bonus.

---

## One Flawed AI Suggestion

When asking Claude to generate Streamlit UI with my design in mind, it first generated .html webpage, choosing wrong style, drifting from the vision I described in the prompt.

---

## Design Decisions

**Why ChromaDB over Pinecone/FAISS?** ChromaDB runs locally with no server or API key, supports persistent storage, and has a simple Python API. For a 1,710-song catalog, a hosted vector database would be overkill. FAISS would also work but lacks built-in metadata filtering — ChromaDB's `where` clause enabled genre-filtered retrieval without a second query.

**Why tool use instead of raw JSON for extraction?** Asking the LLM to return JSON in its response is fragile — it can wrap it in markdown, add commentary, or produce invalid syntax. Tool use (structured output) guarantees a valid schema and cleanly separates the user-facing conversational text from the extracted data.

**Why Haiku/Sonnet tiering instead of one model?** Extraction and self-critique are structured tasks where Haiku performs well and costs ~10x less than Sonnet. Explanations benefit from Sonnet's stronger natural language. This split keeps per-session cost under a few cents while maintaining quality where it matters most.

**Why weighted distance over embeddings-only?** Pure cosine similarity over 8-D vectors treats all features equally. Weighted distance lets the system emphasize features that matter more for music preference (energy, valence) while downweighting features that are less perceptually meaningful (liveness, speechiness). The mood and genre bonuses add categorical matching that pure vector similarity can't express.

**Why genre filter + backfill instead of just boosting?** A scoring-only genre bonus still surfaces irrelevant genres when the filtered pool is small. Filtering first guarantees genre-relevant candidates, then backfilling with unfiltered results prevents empty results when the genre pool is too small (e.g., tender mood + niche genre).

---

## Testing Summary

The eval harness runs 8 end-to-end tests covering all 4 original failure modes plus 4 new edge cases. All 8 pass. The unit test suite includes 27 deterministic tests (no API calls) covering all guardrail functions, scoring logic, and ChromaDB retrieval.

Key findings from testing:
- The energy dominance test showed 4/5 songs had high energy (not 5/5), confirming the reflect step provides some mitigation but doesn't fully eliminate the bias.
- The vague conversation test confirmed the LLM asks follow-up questions instead of extracting garbage values — a behavioral guardrail that can't be unit-tested.
- The genre hint test revealed that the initial retrieve-then-boost approach wasn't strong enough — switching to filter-first + backfill was necessary to make genre requests feel responsive.
- Confidence scores average 7-9 out of 12.25 max for on-target requests, dropping to 4-6 for contradictory or neutral profiles — which is expected behavior, not a bug.

---

## Limitations

1. **Latency:** Each recommendation flow makes 3-4 Claude API calls (extraction, explanation, self-critique, plus potential retry). End-to-end response time is 5-15 seconds depending on API load.

2. **Catalog size:** 1,710 songs across 114 genres is enough to demonstrate RAG but tiny compared to Spotify's 100M+ tracks. Users requesting niche subgenres or specific artists will often get no exact matches.

3. **Cold start:** ChromaDB must be ingested on first run (`python utils/data_loader.py`). This takes ~10 seconds locally but adds startup latency on cloud deployment.

4. **Mood distribution skew:** Mood labels are derived algorithmically (Russell's Circumplex), not human-labeled. Aggressive (322 songs), happy (286), and melancholy (292) are overrepresented. Tender (9), chill (17), and sad (30) are underrepresented, meaning recommendations for these moods draw from a very small pool.

5. **Energy dominance bias:** Energy has the highest weight (2.0) in scoring. Users who mention energy-related words will get results heavily skewed by that single feature, even if other preferences matter more to them.

6. **LLM extraction variance:** Even at temperature=0, Claude doesn't always extract the same numeric features from identical input. Two runs with the same conversation can produce slightly different recommendations.

7. **Single-genre matching:** Genre matching is binary (exact match or no match). "Indie rock" and "alternative rock" are treated as completely unrelated genres with no partial credit.

8. **Cost:** While model tiering (Haiku for extraction/critique, Sonnet for explanations) and session caps (5 flows, 4 turns each) keep costs low, the system still requires a paid Anthropic API key to function.

---

## Future Improvements

1. **Spotify API integration:** Replace the static CSV catalog with real-time search via the Spotify Web API. Users could get recommendations from the full Spotify library and play previews directly.

2. **User listening history:** Store past recommendations and feedback to build a persistent user profile that improves over time, rather than starting fresh each session.

3. **Collaborative filtering:** Combine content-based similarity (current approach) with collaborative signals — "users who liked these songs also liked..." — for better discovery.

4. **Soft mood matching:** Replace binary mood matching with a mood similarity matrix (e.g., "happy" and "excited" are close, "happy" and "melancholy" are far). This would improve recommendations for underrepresented moods.

5. **Learned feature weights:** Replace hardcoded scoring weights with weights learned from user feedback. If users consistently reject high-energy recommendations, the system should learn to reduce the energy weight.

6. **Multi-genre support:** Allow the extraction to return multiple genre preferences (e.g., "something between jazz and electronic") and score against all of them with partial matching.

7. **Streaming audio previews:** Embed Spotify preview clips directly in the Streamlit UI so users can listen before deciding.
