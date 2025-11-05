from sentence_transformers import SentenceTransformer
from functools import lru_cache
import os


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    # Use cache directory from environment variable to reduce memory usage during build
    cache_folder = os.getenv("SENTENCE_TRANSFORMERS_HOME", "/tmp/st_cache")
    return SentenceTransformer(model_name, cache_folder=cache_folder)


def embed_texts(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> list[list[float]]:
    model = get_embedding_model(model_name)
    return model.encode(texts, normalize_embeddings=True).tolist()
