import sys
sys.path.insert(0, ".")

from agent import Agent

fake_profile = {
      "energy": 0.8, "valence": 0.7, "danceability": 0.6,
      "acousticness": 0.2, "instrumentalness": 0.1, "liveness": 0.3,
      "speechiness": 0.1, "tempo_bpm": 0.5, "mood": "energetic"
}

fake_messages = [
    {"role": "user", "content": "I just finished a workout and want something high energy"},
    {"role": "assistant", "content": "Got it! Let me find some tracks for you."}
]

agent = Agent()
recommendations, steps = agent.run(fake_profile, fake_messages)

print("\n--- Agent Steps ---")
for step in steps:
    print(f"[{step.timestamp}] {step.step_name}: {step.input_summary} → {step.output_summary}")

print("\n--- Recommendations ---")
for song in recommendations:
    print(f'{song["title"]} by {song["artist"]} ({song["genre"]}) — {song["score"]:.2f}')
    print(f'  → {song["explanation"]}')
    print()