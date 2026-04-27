from dataclasses import dataclass
from datetime import datetime
from utils.retriever import retrieve_candidates
from scorer import rank_candidates
from explainer import generate_explanations
from llm_client import chat

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
        # STEP 2 (RETRIEVE)
        candidates = retrieve_candidates(profile, n=20)
        self.log_step(
            "RETRIEVE", 
            f"Profile: mood={profile['mood']}", 
            f"Found {len(candidates)} candidates",
        )
        # STEP 3 (SCORE)
        top_5 = rank_candidates(candidates, profile, k=5)
        self.log_step(
            "SCORE",
            f"{len(candidates)} candidates",
            f"Top: {top_5[0]['title']} ({top_5[0]['score']:.2f})",
        )
        # STEP 4 (EXPLAIN)
        explanations = generate_explanations(top_5, conversation_messages, profile)
        for i, song in enumerate(top_5):
            song['explanation'] = explanations[i]
        self.log_step(
            "EXPLAIN",
            f"{len(top_5)} songs",
            f"Generated {len(explanations)} explanations"
        )
        # STEP 5 (REFLECT)
        song_list = "\n".join(
            f'- "{s["title"]}" by {s["artist"]} ({s["genre"]}) - score: {s["score"]:.2f}'
            for s in top_5
        )
        prompt =f"""
                Review these music recommendations for someone who wanted: {profile['mood']}

                {song_list}

                Check:
                1. Are at least 2 different genres represented?
                2. Does one feature dominate all scores?

                Respond with exactly PASS or FAIL on the first line, then a short reason.
                """
        response = chat(
            "You are a music recommendation reviewer.",
            [{"role": "user", "content": prompt}],
            model ="claude-haiku-4-5-20251001",
            temperature=0
        )
        verdict = response.strip().split("\n")[0]

        if "FAIL" in verdict and self.max_retries > 0:
            self.max_retries -= 1
            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations",
                f"Result: {verdict} - retrying",
            )
            candidates = retrieve_candidates(profile, n=30)
            top_5 = rank_candidates(candidates, profile, k=5)
            explanations = generate_explanations(top_5, conversation_messages, profile)
            for i, song in enumerate(top_5):
                song["explanation"] = explanations[i]
        else:
            self.log_step(
                "REFLECT",
                f"{len(top_5)} recommendations",
                f"Result: {verdict}"
            )
        return top_5, self.steps


     