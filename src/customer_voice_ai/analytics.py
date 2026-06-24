from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/processed/product_classification_dataset.csv")


class ComplaintAnalytics:
    def __init__(self, data_path: Path = DATA_PATH) -> None:
        if not data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {data_path}")

        self.df = pd.read_csv(data_path)
        self.df["date_received"] = pd.to_datetime(self.df["date_received"], errors="coerce")

    def product_summary(self, top_n: int = 10) -> dict:
        product_counts = self.df["product"].value_counts().head(top_n)

        issue_counts = (
            self.df.groupby(["product", "issue"])
            .size()
            .reset_index(name="count")
            .sort_values(["product", "count"], ascending=[True, False])
        )

        top_issues_by_product = {}
        for product, group in issue_counts.groupby("product"):
            top_issues_by_product[product] = (
                group.head(5)[["issue", "count"]].to_dict(orient="records")
                )

        monthly_counts = (
            self.df.dropna(subset=["date_received"])
            .assign(month=lambda data: data["date_received"].dt.to_period("M").astype(str))
            .groupby(["month", "product"])
            .size()
            .reset_index(name="count")
            .sort_values(["month", "count"], ascending=[True, False])
        )

        return {
            "total_rows": int(len(self.df)),
            "top_products": [
                {"product": product, "count": int(count)}
                for product, count in product_counts.items()
            ],
            "top_issues_by_product": top_issues_by_product,
            "monthly_counts": monthly_counts.tail(50).to_dict(orient="records"),
        }


@lru_cache
def get_complaint_analytics() -> ComplaintAnalytics:
    return ComplaintAnalytics()