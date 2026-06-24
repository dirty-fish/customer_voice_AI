from pathlib import Path

import pandas as pd

INPUT_PATH = Path("data/interim/cfpb_complaints_sample.csv")
OUTPUT_PATH = Path("data/processed/product_classification_dataset.csv")

TEXT_COLUMN = "consumer_complaint_narrative"
LABEL_COLUMN = "product"

MIN_CLASS_COUNT = 100
MAX_ROWS_PER_CLASS = 1200
RANDOM_STATE = 42


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    df = df.dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])
    df[TEXT_COLUMN] = df[TEXT_COLUMN].astype(str).str.strip()
    df = df[df[TEXT_COLUMN].str.len() >= 80]

    class_counts = df[LABEL_COLUMN].value_counts()
    keep_classes = class_counts[class_counts >= MIN_CLASS_COUNT].index

    df = df[df[LABEL_COLUMN].isin(keep_classes)]

    balanced_parts = []
    for label, group in df.groupby(LABEL_COLUMN):
        n = min(len(group), MAX_ROWS_PER_CLASS)
        balanced_parts.append(group.sample(n=n, random_state=RANDOM_STATE))

    dataset = pd.concat(balanced_parts, ignore_index=True)
    dataset = dataset.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)

    output_columns = [
        "complaint_id",
        "date_received",
        "product",
        "issue",
        "company",
        "state",
        "submitted_via",
        TEXT_COLUMN,
    ]
    dataset = dataset[output_columns]
    dataset.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved rows: {len(dataset):,}")
    print(f"Saved to: {OUTPUT_PATH}")
    print("\nClass distribution:")
    print(dataset[LABEL_COLUMN].value_counts())


if __name__ == "__main__":
    main()
    