import pandas as pd
import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_songs():
    df = pd.read_csv("data/songs.csv")
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(
        "songs", 
        metadata={"hnsw:space": "cosine"}
    )
    if collection.count() > 0:
        logger.info(f"Collection already has {collection.count()} songs, skipping ingestion.")
        return

    ids = []
    embeddings = [] # numeric vector ChromaDB actually searches on
    metadatas = [] # key-value paurs we can filer on or read back
    documents = [] # text string required by ChromaDB (not used for search)

    for _, row in df.iterrows():
        ids.append(str(row["id"]))

        embeddings.append([
            row["energy"],
            row["valence"],
            row["danceability"],
            row["acousticness"],
            row["instrumentalness"],
            row["liveness"],
            row["speechiness"],
            row["tempo_bpm"],
        ])

        metadatas.append({
            "title": row["title"],
            "artist": row["artist"],
            "genre": row["genre"],
            "mood": row["mood"],
            "energy": float(row["energy"]),
            "valence": float(row["valence"]),
            "danceability": float(row["danceability"]),
            "acousticness": float(row["acousticness"]),
            "instrumentalness": float(row["instrumentalness"]),
            "liveness": float(row["liveness"]),
            "speechiness": float(row["speechiness"]),
            "tempo_bpm": float(row["tempo_bpm"]),
        })

        documents.append(f"{row['title']} by {row['artist']} - {row['genre']}, {row['mood']}")
    
    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
    logger.info(f"Ingested {len(ids)} songs into ChromaDB.")

if __name__ == "__main__":
    ingest_songs()