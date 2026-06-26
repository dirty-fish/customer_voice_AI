import argparse
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

CFPB_SOCRATA_URL = "https://data.consumerfinance.gov/resource/s6ew-h6mp.json"

CANONICAL_COLUMNS = [
    "complaint_id",
    "date_received",
    "product",
    "sub_product",
    "issue",
    "sub_issue",
    "company",
    "state",
    "zip_code",
    "consumer_complaint_narrative",
    "company_public_response",
    "company_response",
    "timely",
    "submitted_via",
]

CSV_COLUMN_RENAME_MAP = {
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

CSV_REQUIRED_COLUMNS = list(CSV_COLUMN_RENAME_MAP.keys())


def canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    for column in CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[CANONICAL_COLUMNS]
    df = df.dropna(subset=["complaint_id", "consumer_complaint_narrative", "product", "issue"])

    df["consumer_complaint_narrative"] = (
        df["consumer_complaint_narrative"].astype(str).str.strip()
    )
    df = df[df["consumer_complaint_narrative"].str.len() >= 80]

    df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
    df = df.sort_values("date_received", ascending=False)

    return df


def fetch_api_batch(
    limit: int,
    offset: int,
    retries: int,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    select_clause = ", ".join(CANONICAL_COLUMNS)

    params = {
        "$select": select_clause,
        "$limit": limit,
        "$offset": offset,
        "$where": "consumer_complaint_narrative IS NOT NULL",
        "$order": "date_received DESC",
    }

    for attempt in range(1, retries + 1):
        try:
            print(f"Requesting CFPB API batch offset={offset}, limit={limit}, attempt={attempt}")
            response = requests.get(CFPB_SOCRATA_URL, params=params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            if attempt == retries:
                raise RuntimeError(f"CFPB API request failed after {retries} attempts") from error
            time.sleep(sleep_seconds * attempt)

    return []


def ingest_from_api(
    rows: int,
    batch_size: int,
    retries: int,
    sleep_seconds: float,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []

    for offset in range(0, rows, batch_size):
        batch = fetch_api_batch(
            limit=min(batch_size, rows - offset),
            offset=offset,
            retries=retries,
            sleep_seconds=sleep_seconds,
        )

        if not batch:
            break

        records.extend(batch)
        print(f"Collected {len(records):,}/{rows:,} rows")

        if len(records) >= rows:
            break

    return canonicalize(pd.DataFrame(records))


def ingest_from_csv(path: Path, rows: int, chunk_size: int) -> pd.DataFrame:
    parts = []
    collected_rows = 0

    reader = pd.read_csv(
        path,
        usecols=CSV_REQUIRED_COLUMNS,
        chunksize=chunk_size,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(reader, start=1):
        chunk = chunk.rename(columns=CSV_COLUMN_RENAME_MAP)
        cleaned = canonicalize(chunk)

        if not cleaned.empty:
            parts.append(cleaned)
            collected_rows += len(cleaned)

        print(f"Processed chunk {chunk_number}, collected {collected_rows:,}/{rows:,} rows")

        if collected_rows >= rows:
            break

    if not parts:
        raise RuntimeError("No valid complaint narratives were found in CSV.")

    df = pd.concat(parts, ignore_index=True)
    sample_size = min(rows, len(df))

    return df.sample(n=sample_size, random_state=42).sort_values(
        "date_received",
        ascending=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest CFPB complaints into canonical CSV.")
    parser.add_argument("--source", choices=["api", "csv"], required=True)
    parser.add_argument("--csv-path", type=Path, default=Path("data/raw/complaints.csv"))
    parser.add_argument("--output-path", type=Path,
                         default=Path("data/interim/cfpb_complaints_sample.csv"))
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--chunk-size", type=int, default=50_000)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument(
        "--fallback-csv-path",
        type=Path,
        default=None,
        help="Optional CSV fallback path when API ingestion fails.",
    )    
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.source == "api":
        try:
            df = ingest_from_api(
                rows=args.rows,
                batch_size=args.batch_size,
                retries=args.retries,
                sleep_seconds=args.sleep_seconds,
            )
        except RuntimeError as error:
            if args.fallback_csv_path is None:
                raise SystemExit(f"API ingestion failed: {error}") from error

            print(f"API ingestion failed: {error}")
            print(f"Falling back to CSV: {args.fallback_csv_path}")
            df = ingest_from_csv(
                path=args.fallback_csv_path,
                rows=args.rows,
                chunk_size=args.chunk_size,
            )
    else:
        df = ingest_from_csv(
            path=args.csv_path,
            rows=args.rows,
            chunk_size=args.chunk_size,
        )

    df.to_csv(args.output_path, index=False)

    print(f"Saved rows: {len(df):,}")
    print(f"Saved canonical dataset to: {args.output_path}")
    print("\nTop products:")
    print(df["product"].value_counts().head(10))


if __name__ == "__main__":
    main()