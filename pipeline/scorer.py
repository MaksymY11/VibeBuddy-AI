WEIGHTS = {
    "energy": 2.0,
    "valence": 1.5,
    "danceability": 1.5,
    "acousticness": 1.0,
    "instrumentalness": 0.5,
    "liveness": 0.5,
    "speechiness": 0.5,
    "tempo_bpm": 0.75
}

MOOD_BONUS = 1.0
GENRE_BONUS = 1.5

def score_song(song, profile, genre_hint=""):
    contributions = {}
    for feature, weight in WEIGHTS.items():
        contributions[feature] = weight * (1 - abs(song[feature] - profile[feature]))
    if song["mood"] == profile["mood"]:
        contributions["mood"] = MOOD_BONUS
    else:
        contributions["mood"] = 0.0
    if genre_hint and song["genre"] == genre_hint:
        contributions["genre_match"] = GENRE_BONUS
    else:
        contributions["genre_match"] = 0.0
    total_score = sum(contributions.values())
    return (total_score, contributions)

def rank_candidates(candidates, profile, k=5):
    genre_hint = profile.get("genre_hint", "")
    scored = []
    for song in candidates:
        total_score, contributions = score_song(song, profile, genre_hint)
        scored.append({**song, "score": total_score, "contributions": contributions})
    scored.sort(key = lambda x: x["score"], reverse=True)
    return scored[:k]


    