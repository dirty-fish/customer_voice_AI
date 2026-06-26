import json
from pathlib import Path

import joblib
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from customer_voice_ai.core.config import get_settings

DATA_PATH = Path("data/processed/product_classification_dataset.csv")
MODEL_PATH = Path("artifacts/models/product_embedding_logreg.joblib")
REPORT_PATH = Path("artifacts/reports/product_embedding_logreg_metrics.json")

TEXT_COLUMN = "consumer_complaint_narrative"
LABEL_COLUMN = "product"
RANDOM_STATE = 42
MAX_ROWS = 5000


class EmbeddingTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def fit(self, texts, y=None):
        return self

    def transform(self, texts):
        return self.model.encode(
            list(texts),
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,
        )


def main() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    settings = get_settings()

    df = pd.read_csv(DATA_PATH).dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])
    if len(df) > MAX_ROWS:
        df = df.sample(n=MAX_ROWS, random_state=RANDOM_STATE)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df[LABEL_COLUMN])

    x_train, x_test, y_train, y_test = train_test_split(
        df[TEXT_COLUMN],
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    pipeline = Pipeline(
        steps=[
            ("embeddings", EmbeddingTransformer(settings.embedding_model_name)),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    target_names = label_encoder.classes_

    report = classification_report(
        y_test,
        y_pred,
        target_names=target_names,
        output_dict=True,
    )
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    artifact = {
        "pipeline": pipeline,
        "label_encoder": label_encoder,
    }
    joblib.dump(artifact, MODEL_PATH)

    metrics = {
        "model": "sentence_transformer_embeddings_logistic_regression",
        "embedding_model_name": settings.embedding_model_name,
        "target": LABEL_COLUMN,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "classification_report": report,
    }

    REPORT_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metrics to: {REPORT_PATH}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")


if __name__ == "__main__":
    main()