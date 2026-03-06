import os
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer


QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant-lingwo")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "themes")
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)


def get_themes_path() -> Path:
    local = Path("all_themes.txt")
    if local.exists():
        return local
    return Path("qdrant/all_themes.txt")


def load_themes(path: Path) -> list[str]:
    themes: set[str] = set()
    with path.open("r", encoding="utf8") as file:
        for line in file:
            raw = line.strip()
            if not raw:
                continue
            if "." in raw:
                raw = raw[raw.index(".") + 1 :].strip()
            if raw:
                themes.add(raw)
    return sorted(themes)


def main() -> None:
    themes_path = get_themes_path()
    themes = load_themes(themes_path)
    if not themes:
        raise RuntimeError(f"Список тем пуст: {themes_path}")

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(themes, normalize_embeddings=True).tolist()
    vector_size = len(embeddings[0])

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    if not client.collection_exists(collection_name=QDRANT_COLLECTION_NAME):
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    points = [
        PointStruct(id=index, vector=vector, payload={"theme": theme})
        for index, (theme, vector) in enumerate(zip(themes, embeddings))
    ]
    client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)


if __name__ == "__main__":
    main()
