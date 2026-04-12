import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    energy_score: float
    valence_score: float
    dance_score: float
    likes_acoustic: bool
    mood: str


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")

    song_id = {"id"}
    float_fields = {"energy", "valence", "danceability", "acousticness"}
    songs: List[Dict] = []
    with open(csv_path, newline= "", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in song_id:
                row[key] = int(row[key])
            for key in float_fields:
                row[key] = float(row[key])
            songs.append(row)
    return songs

def score_song(song: Dict, user_prefs: Dict) -> Tuple[float, Dict[str, float]]:
    """
    Computes a weighted score for a single song given user preferences.
    Returns (total_score, per_feature_contributions).
    """
    contributions = {
        "mood": 1.0 if song["mood"] == user_prefs["mood"] else 0.0,
        "energy": 2.0 * (1 - abs(song["energy"] - user_prefs["energy_score"])),
        "valence": 1.5 * (1 - abs(song["valence"] - user_prefs["valence_score"])),
        "danceability": 1.5 * (1 - abs(song["danceability"] - user_prefs["dance_score"])),
        "acousticness": (
            1.0 * song["acousticness"]
            if user_prefs["likes_acoustic"]
            else 1.0 * (1 - song["acousticness"])
        ),
    }
    total = sum(contributions.values())
    return total, contributions


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        total, contributions = score_song(song, user_prefs)
        top_factors = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)[:2]
        explanation = (
            f"Top match on {top_factors[0][0]} ({top_factors[0][1]:.2f}) "
            f"and {top_factors[1][0]} ({top_factors[1][1]:.2f})"
        )
        scored.append((song, total, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
