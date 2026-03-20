import logging
from typing import List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
VECTOR_SIZE = 768


class EmbeddingService:
    """Wraps nomic-embed-text-v1.5 for batch text embedding (768-d vectors)."""

    def __init__(self) -> None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        self._model: SentenceTransformer = SentenceTransformer(
            MODEL_NAME, trust_remote_code=True
        )
        logger.info("Embedding model loaded.")

    def embed_texts(
        self, texts: List[str], task: str = "search_document"
    ) -> List[List[float]]:
        """
        Embed a list of texts and return 768-d float vectors.

        Args:
            texts: input strings to embed.
            task:  nomic task prefix — "search_document" for ingestion,
                   "search_query" for query-time embedding.
        """
        if not texts:
            return []
        prefixed = [f"{task}: {t}" for t in texts]
        try:
            embeddings = self._model.encode(
                prefixed,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as exc:
            logger.error("Embedding failed: %s", exc)
            raise
