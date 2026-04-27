import sys
sys.path.insert(0, ".")

from pipeline.scorer import rank_candidates, score_song

fake_profile = {
    "energy": 0.8, "valence": 0.7, "danceability": 0.6,
    "acousticness": 0.2, "instrumentalness": 0.1, "liveness": 0.3,
    "speechiness": 0.1, "tempo_bpm": 0.5, "mood": "energetic"
}

fake_song = {
    "title": "Test Song", "artist": "Test Artist", "genre": "pop",
    "mood": "energetic", "energy": 0.85, "valence": 0.75,
    "danceability": 0.65, "acousticness": 0.15, "instrumentalness": 0.05,
    "liveness": 0.25, "speechiness": 0.08, "tempo_bpm": 0.55
}

total, contributions = score_song(fake_song, fake_profile)
print(f"Score: {total:.2f}")
print(f"Contributions: {contributions}")

ranked = rank_candidates([fake_song, fake_song], fake_profile, k=1)
print(f"Top pick: {ranked[0]['title']} — Score: {ranked[0]['score']:.2f}")