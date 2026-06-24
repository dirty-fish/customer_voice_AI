import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

DATA_PATH = Path("data/processed/product_classification_dataset.csv")
MODEL_PATH = Path("artifacts/models/product_tfidf_logreg.joblib")
OUTPUT_PATH = Path("artifacts/reports/product_threshold_evaluation.json")

TEXT_COLUMN = "consumer_complaint_narrative"
LABEL_COLUMN = "product"
RANDOM_STATE = 42
THRESHOLDS = [0.3, 0.4, 0.5, 0.55, 0.6, 0.7, 0.8]


def evaluate_threshold(
        y_true: pd.Series,y_pred: list[str],confidence: list[float],threshold: float,
        ) -> dict:
    known_mask = [score >= threshold for score in confidence]
    uncertain_count = known_mask.count(False)
    coverage = sum(known_mask) / len(known_mask)

    known_y_true = [label for label, keep in zip(y_true, known_mask, strict=True) if keep]
    known_y_pred = [label for label, keep in zip(y_pred, known_mask, strict=True) if keep]

    if known_y_true:
        known_accuracy = accuracy_score(known_y_true, known_y_pred)
        known_macro_f1 = f1_score(known_y_true, known_y_pred, average="macro")
    else:
        known_accuracy = 0.0
        known_macro_f1 = 0.0

    return {
        "threshold": threshold,
        "coverage": coverage,
        "uncertain_rate": uncertain_count / len(confidence),
        "uncertain_count": uncertain_count,
        "known_accuracy": known_accuracy,
        "known_macro_f1": known_macro_f1,
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH).dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])

    _, x_test, _, y_test = train_test_split(
        df[TEXT_COLUMN],
        df[LABEL_COLUMN],
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=df[LABEL_COLUMN],
    )

    model = joblib.load(MODEL_PATH)
    probabilities = model.predict_proba(x_test)
    classes = model.classes_

    top_indices = probabilities.argmax(axis=1)
    y_pred = [classes[index] for index in top_indices]
    confidence = [
        float(probabilities[row_index, class_index])
        for row_index, class_index in enumerate(top_indices)
        ]

    results = {
        "model": "tfidf_logistic_regression",
        "target": LABEL_COLUMN,
        "test_rows": len(y_test),
        "thresholds": [
            evaluate_threshold(y_test, y_pred, confidence, threshold)
            for threshold in THRESHOLDS
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Saved threshold evaluation to: {OUTPUT_PATH}")
    print("\nThreshold evaluation:")
    for item in results["thresholds"]:
        print(
            f"threshold={item['threshold']:.2f} "
            f"coverage={item['coverage']:.3f} "
            f"uncertain_rate={item['uncertain_rate']:.3f} "
            f"known_accuracy={item['known_accuracy']:.3f} "
            f"known_macro_f1={item['known_macro_f1']:.3f}"
        )


if __name__ == "__main__":
    main()