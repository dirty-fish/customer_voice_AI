from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

DATA_PATH = Path("data/processed/product_classification_dataset.csv")
INDEX_DIR = Path("artifacts/vector_index")
EMBEDDINGS_PATH = INDEX_DIR / "complaint_embeddings.npy"
METADATA_PATH = INDEX_DIR / "complaint_metadata.joblib"

TEXT_COLUMN = "consumer_complaint_narrative"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MAX_ROWS = 3000
BATCH_SIZE = 64
RANDOM_STATE = 42


def main() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH).dropna(subset=[TEXT_COLUMN])
    sample_size = min(MAX_ROWS, len(df))
    df = df.sample(n=sample_size, random_state=RANDOM_STATE).reset_index(drop=True)

    texts = df[TEXT_COLUMN].astype(str).tolist()

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    np.save(EMBEDDINGS_PATH, embeddings.astype("float32"))

    metadata = df[
        [
            "complaint_id",
            "date_received",
            "product",
            "issue",
            "company",
            "state",
            "consumer_complaint_narrative",
        ]
    ].to_dict(orient="records")
    joblib.dump(metadata, METADATA_PATH)

    print(f"Saved embeddings: {EMBEDDINGS_PATH} shape={embeddings.shape}")
    print(f"Saved metadata: {METADATA_PATH} rows={len(metadata):,}")


if __name__ == "__main__":
    main()