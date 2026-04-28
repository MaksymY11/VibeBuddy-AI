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
    timestamp: str

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
            f'{i+1}. "{s["title"]}" by {s["artist"]} ({s["genre"]}) - score: {s["score"]:.2f}'
            for i, s in enumerate(top_5)
        )
        guardrail_note = ""
        if not report["passed"]:
            guardrail_note = f"\nAutomated checks found issues: {', '.join(report['issues'])}"
        if genre_hint:
            user_wanted = f"{profile['mood']} mood, specifically {genre_hint} genre"
        else:
            user_wanted = f"{profile['mood']} mood (no genre preference)"
        prompt = f"""Review these music recommendations for someone who wanted: {user_wanted}

        {song_list}
        {guardrail_note}

        For each song, decide if it fits the user's requested mood and vibe.
        Respond with exactly one line per song: the song number followed by PASS or FAIL.
        After all 5 lines, write a short explanation of your reasoning.

        Example format:
        1. PASS
        2. FAIL
        3. PASS
        4. PASS
        5. FAIL
        Reason: [your reasoning ...]
        """
        response = chat(
            "You are a music recommendation reviewer.",
            [{"role": "user", "content": prompt}],
            model="claude-haiku-4-5-20251001",
            temperature=0,
        )
        verdicts, reason = self._parse_per_song_reflect(response, len(top_5))
        keepers = [top_5[i] for i, v in enumerate(verdicts) if v]
        fail_count = sum(1 for v in verdicts if not v)

        if fail_count > 0 and self.max_retries > 0:
            self.max_retries -= 1
            slots = 5 - len(keepers)
            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations",
                f"FAIL ({fail_count}/{len(top_5)} songs): {reason} — replacing {slots}",
            )
            genre_hint = profile.get("genre_hint", "")
            candidates = retrieve_candidates(profile, n=30, genre_hint=genre_hint)
            exclude_titles = {s["title"] for s in top_5}
            fresh = [c for c in candidates if c["title"] not in exclude_titles]
            replacements = rank_candidates(fresh or candidates, profile, k=slots)
            top_5 = sorted(keepers + replacements, key=lambda x: x["score"], reverse=True)

            report = run_output_guardrails(top_5, skip_diversity=bool(genre_hint))
            self.log_step(
                "GUARDRAILS",
                f"{len(top_5)} recommendations (retry)",
                f"{'PASS' if report['passed'] else 'FAIL'}: {report['issues']}",
            )

            explanations = generate_explanations(top_5, conversation_messages, profile)
            for i, song in enumerate(top_5):
                song["explanation"] = explanations[i]
            self.log_step(
                "EXPLAIN",
                f"{len(top_5)} songs (retry)",
                f"Generated {len(explanations)} explanations",
            )

            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations (retry)",
                f"{reason}",
            )
        else:
            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations",
                f"PASS ({len(keepers)}/{len(verdicts)} songs) — {reason}",
            )
        return top_5, self.steps

    @staticmethod
    def _parse_per_song_reflect(response, count):
        lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
        verdicts = []
        reason_lines = []
        for line in lines:
            upper = line.upper()
            if "FAIL" in upper:
                verdicts.append(False)
            elif "PASS" in upper:
                verdicts.append(True)
            else:
                reason_lines.append(line)
        reason = " ".join(reason_lines) if reason_lines else "No reason given"
        return verdicts, reason
