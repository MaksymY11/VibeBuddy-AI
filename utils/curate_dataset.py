import pandas as pd
import numpy as np

df = pd.read_csv("data/train.csv")
df = df.drop("Unnamed: 0", axis=1)

# Removing duplicates and missing values
before_missing = len(df)
df = df.dropna(subset=[
    "artists", "track_name", "danceability", "energy", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo", "track_genre",
    ])
after_missing = len(df)
print(f"Removed {before_missing-after_missing} rows due to missing values.")

before_dupes = len(df)
df = df.drop_duplicates()
after_dupes = len(df)
print(f"Removed {before_dupes-after_dupes} duplicate rows.")

# Grouping by genre and creating mood column
sampled = []
for genre in df["track_genre"].unique():
    group = df[df["track_genre"] == genre]
    sampled.append(group.sample(n = min(15, len(group)), random_state=42))
df = pd.concat(sampled).reset_index(drop=True)
print(df.columns.tolist())

def derive_mood(row):
    v = row["valence"]
    e = row["energy"]
    d = row["danceability"]
    a = row["acousticness"]
    s = row["speechiness"]

    # High valence, high energy → Exuberance
    if v >= 0.5 and e >= 0.5:
        if d > 0.75:
            return "excited"
        if v > 0.65:
            return "happy"
        return "energetic"
    
    # Low valence, high energy → Anxious/Frantic
    if v < 0.5 and e >= 0.5:
        if e > 0.75:
            return "aggressive"
        if v < 0.3:
            return "intense"
        return "fiery"
    
    # High valence, low energy → Contentment
    if v >= 0.5 and e < 0.5:
        if a > 0.5:
            return "peaceful"
        if e >= 0.35:
            return "chill"
        return "tender"
    
    # Low valence, low energy → Depression
    if a > 0.5:
        return "melancholy"
    if e >= 0.35:
        return "moody"
    return "sad"

df["mood"] = df.apply(derive_mood,axis=1)

# Renaming columns
df = df.rename(columns= {
    "track_name": "title",
    "artists": "artist",
    "track_genre": "genre",
    "tempo": "tempo_bpm"
})

# Assigning sequential IDs
df = df.reset_index(drop=True)
df["id"] = df.index + 1

# Select only schema columns
df = df[["id", "title", "artist", "genre", "mood", "energy",
         "tempo_bpm", "valence", "danceability", "acousticness",
         "instrumentalness", "liveness", "speechiness"
]]

# Write to new .csv
df.to_csv("data/songs.csv", index=False)
print(f"Saved {len(df)} songs to data/songs.csv")
print(df["mood"].value_counts())
