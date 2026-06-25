from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from customer_voice_ai.core.config import get_settings
from customer_voice_ai.db.models import Complaint
from customer_voice_ai.db.session import SessionLocal


class PgVectorComplaintSearch:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = SentenceTransformer(settings.embedding_model_name)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip():
            raise ValueError("Query must not be empty")

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0].tolist()

        distance = Complaint.embedding.cosine_distance(query_embedding)

        statement = (
            select(
                Complaint.complaint_id,
                Complaint.date_received,
                Complaint.product,
                Complaint.issue,
                Complaint.company,
                Complaint.state,
                Complaint.narrative,
                distance.label("distance"),
            )
            .where(Complaint.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        )

        with SessionLocal() as session:
            rows = session.execute(statement).all()

        results = []
        for row in rows:
            score = 1.0 - float(row.distance)
            results.append(
                {
                    "complaint_id": row.complaint_id,
                    "date_received": (
                        row.date_received.date().isoformat()
                        if row.date_received
                        else None
                    ),
                    "product": row.product,
                    "issue": row.issue,
                    "company": row.company,
                    "state": row.state,
                    "consumer_complaint_narrative": row.narrative,
                    "score": score,
                }
            )

        return results


@lru_cache
def get_pgvector_complaint_search() -> PgVectorComplaintSearch:
    return PgVectorComplaintSearch()