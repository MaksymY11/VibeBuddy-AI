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


def test_score_song_returns_positive():
    total, contributions = score_song(fake_song, fake_profile)
    assert total > 0


def test_score_song_mood_match_bonus():
    total, contributions = score_song(fake_song, fake_profile)
    assert contributions["mood"] == 1.0


def test_score_song_no_mood_match():
    sad_song = {**fake_song, "mood": "sad"}
    total, contributions = score_song(sad_song, fake_profile)
    assert contributions["mood"] == 0.0


def test_rank_candidates_respects_k():
    ranked = rank_candidates([fake_song, fake_song], fake_profile, k=1)
    assert len(ranked) == 1


def test_rank_candidates_includes_score():
    ranked = rank_candidates([fake_song], fake_profile, k=1)
    assert "score" in ranked[0]
    assert ranked[0]["score"] > 0
