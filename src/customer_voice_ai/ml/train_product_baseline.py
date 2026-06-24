import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

DATA_PATH = Path("data/processed/product_classification_dataset.csv")
MODEL_PATH = Path("artifacts/models/product_tfidf_logreg.joblib")
REPORT_PATH = Path("artifacts/reports/product_tfidf_logreg_metrics.json")

TEXT_COLUMN = "consumer_complaint_narrative"
LABEL_COLUMN = "product"
RANDOM_STATE = 42


def main() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])

    x_train, x_test, y_train, y_test = train_test_split(
        df[TEXT_COLUMN],
        df[LABEL_COLUMN],
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=df[LABEL_COLUMN],
    )

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.9,
                    max_features=80_000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    report = classification_report(y_test, y_pred, output_dict=True)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    metrics = {
        "model": "tfidf_logistic_regression",
        "target": LABEL_COLUMN,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "classification_report": report,
    }

    joblib.dump(pipeline, MODEL_PATH)
    REPORT_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metrics to: {REPORT_PATH}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))


if __name__ == "__main__":
    main()