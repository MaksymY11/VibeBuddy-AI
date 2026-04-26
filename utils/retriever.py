import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrieve_candidates(user_profile, n=20) -> list:
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

    result = collection.query(query_embeddings=[query_vector], n_results=n)
    return result["metadatas"][0]