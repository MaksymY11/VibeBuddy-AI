from .llm_client import chat

SYSTEM_PROMPT = """
                You're writing short explanations for why each song was recommended.
                Use the user's own words, not numbers or feature names. One to two sentences per song.
                """

def generate_explanations(ranked_songs, user_messages, profile):
    """Ask Claude to write natural-language explanations for each recommended song.

    Returns a list of explanation strings, one per song. Uses '---' as a
    delimiter in the prompt so the response can be split back into individual explanations.
    """
    
    user_words = " | ".join(m["content"] for m in user_messages if m["role"] == "user")

    song_lines = []
    for i, song in enumerate(ranked_songs,1):
        top_features = sorted(song["contributions"].items(), key=lambda x: x[1], reverse=True)[:2]
        feature_names = ", ".join(f[0] for f in top_features)

        song_lines.append(f'{i}. "{song["title"]}" by {song["artist"]} ({song["genre"]}) - top factors: {feature_names}')

    prompt = f"""
    The user said: {user_words}
    Their preferences: {profile}

    Here are the 5 recommended songs. For each, write a 1-2 sentence explanations fo why it fits.
    Separate each explanation with ---

    {chr(10).join(song_lines)}
    """

    response = chat(
        SYSTEM_PROMPT, 
        [{"role": "user", "content": prompt}],
        model ="claude-sonnet-4-6",
        temperature=0.7
    )

    explanations = [e.strip() for e in response.split("---") if e.strip()]
    while len(explanations) < len(ranked_songs):
        explanations.append("This track matches your vibe.")
    return explanations[:len(ranked_songs)]