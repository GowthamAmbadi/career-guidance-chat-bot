from sentence_transformers import SentenceTransformer
from functools import lru_cache
import os
import logging

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Get embedding model with optimized memory usage.
    Model is loaded lazily on first use, not during import.
    Uses environment variables for cache directories to reduce build memory.
    """
    # Use cache directory from environment variable to reduce memory usage during build
    cache_folder = os.getenv("SENTENCE_TRANSFORMERS_HOME", "/tmp/st_cache")
    
    # Set device to CPU explicitly to avoid GPU memory issues during build
    device = os.getenv("SENTENCE_TRANSFORMERS_DEVICE", "cpu")
    
    try:
        # Load model with optimized settings
        model = SentenceTransformer(
            model_name,
            cache_folder=cache_folder,
            device=device
        )
        logger.info(f"Loaded embedding model: {model_name} with cache: {cache_folder}")
        return model
    except Exception as e:
        logger.error(f"Error loading embedding model {model_name}: {str(e)}")
        raise


def embed_texts(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> list[list[float]]:
    model = get_embedding_model(model_name)
    return model.encode(texts, normalize_embeddings=True).tolist()
