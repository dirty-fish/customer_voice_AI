from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = Path("artifacts/vector_index")
EMBEDDINGS_PATH = INDEX_DIR / "complaint_embeddings.npy"
METADATA_PATH = INDEX_DIR / "complaint_metadata.joblib"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class LocalComplaintSearch:
    def __init__(self) -> None:
        if not EMBEDDINGS_PATH.exists():
            raise FileNotFoundError(f"Embeddings not found: {EMBEDDINGS_PATH}")
        if not METADATA_PATH.exists():
            raise FileNotFoundError(f"Metadata not found: {METADATA_PATH}")

        self.model = SentenceTransformer(MODEL_NAME)
        self.embeddings = np.load(EMBEDDINGS_PATH)
        self.metadata = joblib.load(METADATA_PATH)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip():
            raise ValueError("Query must not be empty")

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]

        scores = self.embeddings @ query_embedding
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for index in top_indices:
            item = self.metadata[int(index)].copy()
            item["score"] = float(scores[index])
            results.append(item)

        return results


@lru_cache
def get_complaint_search() -> LocalComplaintSearch:
    return LocalComplaintSearch()