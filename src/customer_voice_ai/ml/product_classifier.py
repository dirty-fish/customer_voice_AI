from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

MODEL_PATH = Path("artifacts/models/product_tfidf_logreg.joblib")


class ProductClassifier:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {model_path}")

        self.pipeline: Any = joblib.load(model_path)

    def predict(self, text: str, top_k: int = 3, confidence_threshold: float = 0.55) -> dict:
        if not text.strip():
            raise ValueError("Text must not be empty")

        probabilities = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_

        ranked = sorted(
            zip(classes, probabilities, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )

        top_predictions = [
            {"label": label, "score": float(score)}
            for label, score in ranked[:top_k]
        ]

        top_score = top_predictions[0]["score"]
        status = "known" if top_score >= confidence_threshold else "uncertain"

        return {
            "label": top_predictions[0]["label"],
            "score": top_score,
            "classification_status": status,
            "confidence_threshold": confidence_threshold,
            "top_predictions": top_predictions,
        }

@lru_cache
def get_product_classifier() -> ProductClassifier:
    return ProductClassifier()