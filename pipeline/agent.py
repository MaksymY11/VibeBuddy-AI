from dataclasses import dataclass
from datetime import datetime
from utils.retriever import retrieve_candidates
from .scorer import rank_candidates
from .explainer import generate_explanations
from .llm_client import chat
from .guardrails import validate_profile, check_candidates, run_output_guardrails

@dataclass
class StepResult:
    step_name: str
    input_summary: str
    output_summary: str
    timestamp: datetime

class Agent():
    def __init__(self):
        self.steps = []
        self.max_retries = 1
    
    def log_step(self, step_name, input_summary, output_summary):
        self.steps.append(StepResult(
            step_name=step_name,
            input_summary=input_summary,
            output_summary=output_summary,
            timestamp=datetime.now().isoformat(),
            ))

    def run(self, profile, conversation_messages):
        # STEP 1 (ELICIT)
        self.log_step(
            "ELICIT", 
            "User conversation", 
            f"Extracted profile: mood={profile['mood']}",
        )
        # STEP 2 (VALIDATE)
        raw_mood = profile['mood']
        raw_genre = profile.get('genre_hint', '')
        validate_profile(profile)
        if profile['mood'] != raw_mood or profile.get('genre_hint', '') != raw_genre:
            self.log_step(
                "VALIDATE",
                f"Raw profile: mood={raw_mood}, genre={raw_genre}",
                f"Validated profile: mood={profile['mood']}, genre={profile['genre_hint']}",
            )
        else:
            self.log_step(
                "VALIDATE",
                f"Profile : mood={profile['mood']}",
                "No changes needed",
            )
        # STEP 3 (RETRIEVE)
        genre_hint = profile.get("genre_hint", "")
        candidates = retrieve_candidates(profile, n=20, genre_hint=genre_hint)
        self.log_step(
            "RETRIEVE", 
            f"Profile: mood={profile['mood']}", 
            f"Found {len(candidates)} candidates",
        )
        # STEP 4 (CHECK CANDIDATES)
        passed = check_candidates(candidates)
        self.log_step(
            "CHECK_CANDIDATES",
            f"{len(candidates)} candidates retrieved",
            f"{'PASS' if passed else 'FAIL'} (minimum: 5)",
        )
        if not passed:
            return [], self.steps
        # STEP 5 (SCORE)
        top_5 = rank_candidates(candidates, profile, k=5)
        self.log_step(
            "SCORE",
            f"{len(candidates)} candidates",
            f"Top: {top_5[0]['title']} ({top_5[0]['score']:.2f})",
        )
        # STEP 6 (GUARDRAILS)
        report = run_output_guardrails(top_5, skip_diversity=bool(genre_hint))
        self.log_step(
            "GUARDRAILS",
            f"{len(top_5)} recommendations",
            f"{'PASS' if report['passed'] else 'FAIL'}: {report['issues']}",
        )
        # STEP 7 (EXPLAIN)
        explanations = generate_explanations(top_5, conversation_messages, profile)
        for i, song in enumerate(top_5):
            song['explanation'] = explanations[i]
        self.log_step(
            "EXPLAIN",
            f"{len(top_5)} songs",
            f"Generated {len(explanations)} explanations"
        )
        # STEP 8 (REFLECT)
        song_list = "\n".join(
            f'- "{s["title"]}" by {s["artist"]} ({s["genre"]}) - score: {s["score"]:.2f}'
            for s in top_5
        )
        guardrail_note = ""
        if not report["passed"]:
            guardrail_note = f"\nAutomated checks found issues: {', '.join(report['issues'])}"
        genre_note = f"(The user specifically requrest {genre_hint}, so same-genre results are expected.)" if genre_hint else ""
        prompt =f"""
                Review these music recommendations for someone who wanted: {profile['mood']}

                {song_list}
                {guardrail_note}

                Check:
                1. Are at least 2 different genres represented? {genre_note}
                2. Does one feature dominate all scores?
                3. Are there any issues noted above?

                Respond with exactly PASS or FAIL on the first line, then a short reason.
                """
        response = chat(
            "You are a music recommendation reviewer.",
            [{"role": "user", "content": prompt}],
            model ="claude-haiku-4-5-20251001",
            temperature=0
        )
        lines = response.strip().split("\n")
        verdict = lines[0]
        reason = lines[1] if len(lines)>1 else ""

        if "FAIL" in verdict and self.max_retries > 0:
            self.max_retries -= 1
            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations",
                f"Result: {verdict} - {reason} - retrying",
            )
            genre_hint = profile.get("genre_hint", "")
            candidates = retrieve_candidates(profile, n=30, genre_hint=genre_hint)
            top_5 = rank_candidates(candidates, profile, k=5)
            explanations = generate_explanations(top_5, conversation_messages, profile)
            for i, song in enumerate(top_5):
                song["explanation"] = explanations[i]
        else:
            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations",
                f"Result: {verdict} - {reason}"
            )
        return top_5, self.steps


     