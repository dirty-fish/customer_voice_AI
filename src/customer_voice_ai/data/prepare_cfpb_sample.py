from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/complaints.csv")
OUTPUT_PATH = Path("data/interim/cfpb_complaints_sample.csv")

TARGET_ROWS = 20_000
CHUNK_SIZE = 50_000

REQUIRED_COLUMNS = [
    "Complaint ID",
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company",
    "State",
    "ZIP code",
    "Consumer complaint narrative",
    "Company public response",
    "Company response to consumer",
    "Timely response?",
    "Submitted via",
]

COLUMN_RENAME_MAP = {
    "Complaint ID": "complaint_id",
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Consumer complaint narrative": "consumer_complaint_narrative",
    "Company public response": "company_public_response",
    "Company response to consumer": "company_response",
    "Timely response?": "timely",
    "Submitted via": "submitted_via",
}


def clean_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.rename(columns=COLUMN_RENAME_MAP)

    chunk = chunk.dropna(subset=["consumer_complaint_narrative", "product", "issue"])
    chunk["consumer_complaint_narrative"] = (
        chunk["consumer_complaint_narrative"].astype(str).str.strip()
    )
    chunk = chunk[chunk["consumer_complaint_narrative"].str.len() >= 80]

    return chunk


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    parts = []
    collected_rows = 0

    reader = pd.read_csv(
        RAW_PATH,
        usecols=REQUIRED_COLUMNS,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(reader, start=1):
        cleaned = clean_chunk(chunk)
        if not cleaned.empty:
            parts.append(cleaned)
            collected_rows += len(cleaned)

        print(
            f"Processed chunk {chunk_number}, "
            f"collected {collected_rows:,}/{TARGET_ROWS:,} narrative rows"
        )

        if collected_rows >= TARGET_ROWS:
            break

    if not parts:
        raise RuntimeError("No rows with consumer complaint narratives were found.")

    df = pd.concat(parts, ignore_index=True)
    sample_size = min(TARGET_ROWS, len(df))
    df = df.sample(n=sample_size, random_state=42)

    df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
    df = df.sort_values("date_received", ascending=False)

    df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved sample rows: {len(df):,}")
    print(f"Saved sample to: {OUTPUT_PATH}")
    print("\nTop products:")
    print(df["product"].value_counts().head(10))
    print("\nTop issues:")
    print(df["issue"].value_counts().head(10))


if __name__ == "__main__":
    main()