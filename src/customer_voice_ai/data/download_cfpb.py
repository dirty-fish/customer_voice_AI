from pathlib import Path

import pandas as pd
import requests

CFPB_SOCRATA_URL = "https://data.consumerfinance.gov/resource/s6ew-h6mp.json"

SELECTED_COLUMNS = [
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
    "consumer_disputed",
    "submitted_via",
]


def fetch_batch(limit: int, offset: int) -> list[dict]:
    select_clause = ", ".join(SELECTED_COLUMNS)

    params = {
        "$select": select_clause,
        "$limit": limit,
        "$offset": offset,
        "$where": "consumer_complaint_narrative IS NOT NULL",
        "$order": "date_received DESC",
    }

    print(f"Requesting batch offset={offset}, limit={limit}...")
    response = requests.get(CFPB_SOCRATA_URL, params=params, timeout=60)
    response.raise_for_status()

    rows = response.json()
    print(f"Received {len(rows)} rows")
    return rows


def download_complaints(total_size: int = 5000, batch_size: int = 1000) -> pd.DataFrame:
    records: list[dict] = []

    for offset in range(0, total_size, batch_size):
        rows = fetch_batch(limit=batch_size, offset=offset)
        if not rows:
            break
        records.extend(rows)

    df = pd.DataFrame(records)

    for column in SELECTED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[SELECTED_COLUMNS]


def main() -> None:
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = download_complaints(total_size=5000, batch_size=1000)
    output_path = output_dir / "cfpb_complaints_sample.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {len(df):,} rows to {output_path}")
    print(df[["complaint_id", "product", "issue", "consumer_complaint_narrative"]].head())


if __name__ == "__main__":
    main()