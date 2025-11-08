from openai import OpenAI
from app.config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Get cached OpenAI client instance."""
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str], model_name: str = "text-embedding-3-small") -> list[list[float]]:
    """
    Generate embeddings using OpenAI API.
    
    Args:
        texts: List of text strings to embed
        model_name: OpenAI embedding model name (default: text-embedding-3-small)
    
    Returns:
        List of normalized embedding vectors (list of lists of floats)
    """
    client = get_openai_client()
    
    try:
        response = client.embeddings.create(
            model=model_name,
            input=texts
        )
        
        # Extract embeddings from response
        # OpenAI embeddings are already normalized
        embeddings = [data.embedding for data in response.data]
        return embeddings
    except Exception as e:
        raise Exception(f"OpenAI embedding API error: {e}")


# Keep get_embedding_model for backward compatibility (if needed)
# But it's not used anymore since we use OpenAI API directly
def get_embedding_model(model_name: str = "text-embedding-3-small") -> None:
    """
    Deprecated: This function is kept for backward compatibility.
    Embeddings are now generated via OpenAI API directly.
    """
    return None
