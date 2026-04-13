"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Out-of-range extremist
    user_prefs = {"energy_score": 0.5, "valence_score": 0.5, "dance_score": 0.5,
 "likes_acoustic": False, "mood": "sad"}


    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}/7.00")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
