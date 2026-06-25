from pathlib import Path

import joblib
import numpy as np

from customer_voice_ai.db.models import Complaint
from customer_voice_ai.db.session import SessionLocal

EMBEDDINGS_PATH = Path("artifacts/vector_index/complaint_embeddings.npy")
METADATA_PATH = Path("artifacts/vector_index/complaint_metadata.joblib")
BATCH_SIZE = 200


def main() -> None:
    embeddings = np.load(EMBEDDINGS_PATH)
    metadata = joblib.load(METADATA_PATH)

    if len(embeddings) != len(metadata):
        raise ValueError("Embeddings and metadata length mismatch")

    pairs = [
        (int(item["complaint_id"]), embeddings[index].astype(float).tolist())
        for index, item in enumerate(metadata)
    ]

    with SessionLocal() as session:
        updated = 0

        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start : start + BATCH_SIZE]

            for complaint_id, embedding in batch:
                complaint = (
                    session.query(Complaint)
                    .filter(Complaint.complaint_id == complaint_id)
                    .one_or_none()
                )

                if complaint is None:
                    continue

                complaint.embedding = embedding
                updated += 1

            session.commit()
            print(f"Processed {start + len(batch):,}/{len(pairs):,}, updated={updated:,}")

    print(f"Done. Updated embeddings: {updated:,}")


if __name__ == "__main__":
    main()