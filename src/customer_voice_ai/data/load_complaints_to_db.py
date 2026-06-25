from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from customer_voice_ai.db.models import Complaint
from customer_voice_ai.db.session import SessionLocal

DATA_PATH = Path("data/processed/product_classification_dataset.csv")
BATCH_SIZE = 500

TEXT_COLUMN = "consumer_complaint_narrative"


def normalize_record(row: pd.Series) -> dict:
    date_received = pd.to_datetime(row.get("date_received"), errors="coerce")
    if pd.isna(date_received):
        date_value = None
    else:
        date_value = date_received.to_pydatetime()
    
    complaint_id = row.get("complaint_id")
    if pd.isna(complaint_id):
        raise ValueError("Missing complaint_id")
    
    return {
        "complaint_id": int(complaint_id),
        "date_received": date_value,
        "product": str(row["product"]),
        "issue": str(row["issue"]),
        "company": None if pd.isna(row.get("company")) else str(row.get("company")),
        "state": None if pd.isna(row.get("state")) else str(row.get("state")),
        "submitted_via": (
            None if pd.isna(row.get("submitted_via")) else str(row.get("submitted_via"))
            ),
        "narrative": str(row[TEXT_COLUMN]),
    }


def main() -> None:
    df = pd.read_csv(DATA_PATH).dropna(subset=["complaint_id", "product", "issue", TEXT_COLUMN])

    records = [normalize_record(row) for _, row in df.iterrows()]

    with SessionLocal() as session:

        for start in range(0, len(records), BATCH_SIZE):
            batch = records[start : start + BATCH_SIZE]

            statement = insert(Complaint).values(batch)
            statement = statement.on_conflict_do_nothing(index_elements=["complaint_id"])

            session.execute(statement)
            session.commit()

            current_count = session.query(Complaint).count()
            print(
                f"Processed {start + len(batch):,}/{len(records):,}, "
                f"db_rows={current_count:,}"
            )

        final_count = session.query(Complaint).count()

    print(f"Done. DB rows: {final_count:,}")


if __name__ == "__main__":
    main()