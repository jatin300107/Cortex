import os
from google import genai
from backend.exceptions import EmbeddingError

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not EMBEDDING_MODEL or not GEMINI_API_KEY:
    raise ValueError("Invalid or missing EMBEDDING_MODEL or GEMINI_API_KEY")
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])



def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        result = _client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
        return [e.values for e in result.embeddings]
    except Exception as e:
        raise EmbeddingError(f"Error generating embeddings: {e}") from e