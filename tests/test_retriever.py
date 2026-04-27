import sys
sys.path.insert(0, ".")

from utils.retriever import retrieve_candidates

sample_profile = {
      "energy": 0.7, "valence": 0.6, "danceability": 0.5,
      "acousticness": 0.3, "instrumentalness": 0.2, "liveness": 0.3,
      "speechiness": 0.1, "tempo_bpm": 0.5, "mood": "energetic"
}

def test_returns_results():
    res = retrieve_candidates(sample_profile)
    assert len(res) == 20 # 20 is default val

def test_result_structure():
    expected_keys = {
        "title", "artist", "genre", "mood",
        "energy", "valence", "danceability", "acousticness",
        "instrumentalness", "liveness", "speechiness", "tempo_bpm"
    }

    res = retrieve_candidates(sample_profile)
    first_song = res[0]
    assert expected_keys.issubset(first_song.keys())

def test_respects_n_parameter():
    res = retrieve_candidates(sample_profile, n=10)
    assert len(res) == 10

def test_similarity_relevance():
    energetic_profile = {
        "energy": 0.95, "valence": 0.8, "danceability": 0.9,
        "acousticness": 0.05, "instrumentalness": 0.1, "liveness": 0.3,
        "speechiness": 0.2, "tempo_bpm": 0.7, "mood": "energetic"
    }

    res = retrieve_candidates(energetic_profile)
    avg_nrg = sum(song["energy"] for song in res)/len(res)
    assert avg_nrg > 0.5
    