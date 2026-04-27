import sys
sys.path.insert(0, ".")

from pipeline.agent import Agent
from pipeline.guardrails import validate_mood
from pipeline.conversation import ConversationManager

def run_test(test):
    try:
        passed, reason = test["run"]()
        return {
            "name": test["name"],
            "passed": passed,
            "reason": reason,
        }
    except Exception as e:
        return {
            "name": test["name"],
            "passed": False,
            "reason": f"Exception {e}",
        }
    
def test_energy_dominance():
    """
    Profile with high energy and energetic mood.
    To prove that system's energy weight (2.0) wouldn't dominate the results.
    """
    profile = {
        "energy": 0.9, "valence": 0.5, "danceability": 0.5,
        "acousticness": 0.5, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.5, "mood": "energetic"
    }

    messages = [{"role": "user", "content": "I want high energy music"}]
    agent = Agent()
    recs, steps = agent.run(profile, messages)
    high_nrg_cnt = sum(1 for s in recs if s["energy"] > 0.8)
    passed = high_nrg_cnt < len(recs)
    return passed, f"{high_nrg_cnt}/{len(recs)} songs had energy > 0.8"

def test_contradictory():
    """
    Profile with contradictory tastes (energy = 0.9 and and acousticness = 0.9).
    To prove that system doesn't crash and returns at least 1 result.
    """
    profile = {
        "energy": 0.9, "valence": 0.5, "danceability": 0.5,
        "acousticness": 0.9, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.5, "mood": "energetic"
    }
    messages = [{"role": "user", "content": "I want intense acoustic music"}]
    agent = Agent()
    recs, steps = agent.run(profile, messages)
    passed = len(recs) > 0
    return passed, f"Returned {len(recs)} results"

def test_unknown_mood():
    """
    Profile with mood = cosmic void energy.
    To prove that guardrail is working and mood gets changed to "chill" by default.
    """
    profile = {
        "energy": 0.7, "valence": 0.3, "danceability": 0.5,
        "acousticness": 0.2, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.6, "mood": "cosmic void energy"
    }
    messages = [{"role": "user", "content": "I'm in a cosmic void energy mood"}]
    agent = Agent()
    recs, steps = agent.run(profile, messages)
    passed = len(recs) > 0 and profile["mood"] != "cosmic void energy"
    return passed, f"Mood corrected to '{profile['mood']}', got {len(recs)} results"

def test_neutral_user():
    """
    Profile with all features 0.5, and mood="chill".
    To prove that results span at least 2 genres.
    """
    profile = {
        "energy": 0.5, "valence": 0.5, "danceability": 0.5,
        "acousticness": 0.5, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.5, "mood": "chill"
    }
    messages = [{"role":"user", "content":"Play me something, no preference really"}]
    agent = Agent()
    recs, steps = agent.run(profile, messages)
    genres = {s["genre"] for s in recs}
    passed = len(genres) >= 2
    return passed, f"Got {len(genres)} genres: {genres}"

def test_out_of_range():
    """
    Profile with out-of-range energy (5.0), and valence (2.0).
    To prove that dict is mutated by validate_profile and clamped at 0-1 interval.
    """
    profile = {
        "energy": 5.0, "valence": -2.0, "danceability": 0.5,
        "acousticness": 0.5, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.5, "mood": "chill"
    }
    messages = [{"role": "user", "content": "Something chill"}]
    agent = Agent()
    recs, steps = agent.run(profile, messages)
    clamped = profile["energy"] == 1.0 and profile["valence"] == 0.0
    passed = clamped and len(recs) > 0
    return passed, f"energy={profile['energy']}, valence={profile['valence']}, {len(recs)} results"

def test_vague_input():
    """
    Tests ConversationManager, rather than Agent.
    We send "idk play something" and check that LLM asks a follow-up instead of extracting preferences.
    """
    convo = ConversationManager()
    convo.add_user_message("idk play something")
    response = convo.get_response()
    passed = not convo.is_complete()
    return passed, f"Extracted: {convo.is_complete()}, Response: '{response[:80]}...'"

def test_refinement():
    """
    Two separate agent runs:
        1. Run with low energy
        2. Run with high energy
    Check if average energy of results in run 2 is higher than run 1.
    """
    profile_1 = {
        "energy": 0.4, "valence": 0.5, "danceability": 0.5,
        "acousticness": 0.5, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.5, "mood": "chill"
    }
    profile_2 = {
        "energy": 0.8, "valence": 0.5, "danceability": 0.5,
        "acousticness": 0.5, "instrumentalness": 0.5, "liveness": 0.5,
        "speechiness": 0.5, "tempo_bpm": 0.5, "mood": "chill"
    }
    messages_1 = [{"role": "user", "content": "Something mellow and low-key"}]
    messages_2 = [{"role": "user", "content": "Actually, something more upbeat"}]

    agent_1 = Agent()
    recs_1, _ = agent_1.run(profile_1, messages_1)
    agent_2 = Agent()
    recs_2, _ = agent_2.run(profile_2, messages_2)

    avg_1 = sum(s["energy"] for s in recs_1) / len(recs_1)
    avg_2 = sum(s["energy"] for s in recs_2) / len(recs_2)
    passed = avg_2 > avg_1
    return passed, f"Avg energy: {avg_1:.2f} → {avg_2:.2f}"

tests = [
    {"name": "Energy dominance", "run": test_energy_dominance},
    {"name": "Contradictory preferences", "run": test_contradictory},
    {"name": "Unknown mood", "run": test_unknown_mood},
    {"name": "Neutral user", "run": test_neutral_user},
    {"name": "Out-of-range values", "run": test_out_of_range},
    {"name": "Vague conversation", "run": test_vague_input},
    {"name": "Refinement", "run": test_refinement},
]

results = [run_test(t) for t in tests]

for r in results:
    status = "PASS" if r["passed"] else "FAIL"
    print(f"[{status}] {r['name']} - {r['reason']}")

passed = sum(1 for r in results if r["passed"])
print(f"\n{passed}/{len(results)} passed")