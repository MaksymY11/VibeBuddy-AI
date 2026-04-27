import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrieve_candidates(user_profile, n=20, genre_hint="") -> list:
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(
        "songs",
    )

    query_vector = [
        user_profile["energy"],
        user_profile["valence"],
        user_profile["danceability"],
        user_profile["acousticness"],
        user_profile["instrumentalness"],
        user_profile["liveness"],
        user_profile["speechiness"],
        user_profile["tempo_bpm"],
    ]

    candidates = []

    if genre_hint:
        # Trying filtered query first, matching genre exactly or as substring
        filtered = collection.query(
            query_embeddings=[query_vector],
            n_results=n,
            where={"genre": {"$eq": genre_hint}}
        )
        candidates = filtered["metadatas"][0]
    
    # If not enough filtered results fill with unfiltered
    if len(candidates) < n:
        remaining = n -len(candidates)
        unfiltered = collection.query(
            query_embeddings=[query_vector],
            n_results=remaining+len(candidates)
        )
        # Adding unfiltered results that aren't already in candidates
        existing_titles = {c["title"] for c in candidates}
        for song in unfiltered["metadatas"][0]:
            if song["title"] not in existing_titles and len(candidates) < n:
                candidates.append(song)

    return candidates

def get_all_genres():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("songs")
    all_metadata = collection.get()["metadatas"]
    return sorted({m["genre"] for m in all_metadata})