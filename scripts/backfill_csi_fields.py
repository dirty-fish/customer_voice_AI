import hashlib

from customer_voice_ai.db.models import Complaint
from customer_voice_ai.db.session import SessionLocal

NEGATIVE_KEYWORDS = [
    "fraud",
    "unauthorized",
    "scam",
    "identity theft",
    "harassment",
    "lawsuit",
    "garnish",
    "foreclosure",
    "late fee",
    "denied",
    "refuse",
    "not mine",
    "do not owe",
    "incorrect",
    "error",
]

HIGH_SEVERITY_KEYWORDS = [
    "identity theft",
    "lawsuit",
    "garnish",
    "foreclosure",
    "eviction",
    "fraud",
    "scam",
    "unauthorized",
]

CHANNEL_MAP = {
    "Web": "survey",
    "Phone": "call_center",
    "Referral": "regulator_referral",
    "Postal mail": "mail",
    "Fax": "fax",
    "Email": "email",
}


def stable_bucket(value: str, buckets: list[str]) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(buckets)
    return buckets[index]


def infer_sentiment(text: str) -> str:
    lowered = text.lower()
    hits = sum(keyword in lowered for keyword in NEGATIVE_KEYWORDS)

    if hits >= 2:
        return "negative"
    if hits == 1:
        return "mixed"
    return "neutral"


def infer_severity(text: str, issue: str) -> str:
    lowered = f"{text} {issue}".lower()

    if any(keyword in lowered for keyword in HIGH_SEVERITY_KEYWORDS):
        return "high"
    if any(keyword in lowered for keyword in NEGATIVE_KEYWORDS):
        return "medium"
    return "low"


def infer_csi_score(sentiment: str, severity: str) -> float:
    score = 4.0

    if sentiment == "negative":
        score -= 1.4
    elif sentiment == "mixed":
        score -= 0.8

    if severity == "high":
        score -= 1.0
    elif severity == "medium":
        score -= 0.5

    return max(1.0, min(5.0, round(score, 1)))


def main() -> None:
    segments = ["retail", "premium", "small_business"]

    with SessionLocal() as session:
        complaints = session.query(Complaint).all()

        for complaint in complaints:
            text = complaint.narrative or ""
            issue = complaint.issue or ""

            sentiment = infer_sentiment(text)
            severity = infer_severity(text, issue)

            complaint.sentiment = sentiment
            complaint.severity = severity
            complaint.csi_score = infer_csi_score(sentiment, severity)
            complaint.feedback_channel = CHANNEL_MAP.get(
                complaint.submitted_via or "",
                "other",
            )
            complaint.customer_segment = stable_bucket(
                str(complaint.complaint_id),
                segments,
            )

        session.commit()

    print(f"Updated CSI fields for complaints: {len(complaints):,}")


if __name__ == "__main__":
    main()