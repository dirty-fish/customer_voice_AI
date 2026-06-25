from functools import lru_cache

from sentence_transformers import SentenceTransformer

from customer_voice_ai.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = SentenceTransformer(settings.embedding_model_name)

    def embed_text(self, text: str) -> list[float]:
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
        )[0]
        return embedding.astype(float).tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()