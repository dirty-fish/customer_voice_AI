from functools import lru_cache

from sqlalchemy import desc, func, select

from customer_voice_ai.db.models import Complaint
from customer_voice_ai.db.session import SessionLocal


class ComplaintAnalytics:
    def product_summary(self, top_n: int = 10) -> dict:
        with SessionLocal() as session:
            total_rows = session.scalar(select(func.count()).select_from(Complaint)) or 0

            top_products_rows = session.execute(
                select(Complaint.product, func.count().label("count"))
                .group_by(Complaint.product)
                .order_by(desc("count"))
                .limit(top_n)
            ).all()

            top_products = [
                {"product": product, "count": int(count)}
                for product, count in top_products_rows
            ]

            issue_rows = session.execute(
                select(
                    Complaint.product,
                    Complaint.issue,
                    func.count().label("count"),
                )
                .group_by(Complaint.product, Complaint.issue)
                .order_by(Complaint.product, desc("count"))
            ).all()

            top_issues_by_product: dict[str, list[dict]] = {}
            for product, issue, count in issue_rows:
                product_issues = top_issues_by_product.setdefault(product, [])
                if len(product_issues) < 5:
                    product_issues.append(
                        {"issue": issue, "count": int(count)}
                    )

            monthly_rows = session.execute(
                select(
                    func.to_char(
                        func.date_trunc("month", Complaint.date_received),
                        "YYYY-MM",
                    ).label("month"),
                    Complaint.product,
                    func.count().label("count"),
                )
                .where(Complaint.date_received.is_not(None))
                .group_by("month", Complaint.product)
                .order_by("month", desc("count"))
            ).all()

            monthly_counts = [
                {"month": month, "product": product, "count": int(count)}
                for month, product, count in monthly_rows[-50:]
            ]

        return {
            "total_rows": int(total_rows),
            "top_products": top_products,
            "top_issues_by_product": top_issues_by_product,
            "monthly_counts": monthly_counts,
        }
    
    def csi_summary(self) -> dict:
        with SessionLocal() as session:
            total_rows = session.scalar(select(func.count()).select_from(Complaint)) or 0

            avg_csi = session.scalar(
                select(func.avg(Complaint.csi_score)).where(Complaint.csi_score.is_not(None))
            )

            sentiment_rows = session.execute(
                select(Complaint.sentiment, func.count().label("count"))
                .where(Complaint.sentiment.is_not(None))
                .group_by(Complaint.sentiment)
                .order_by(desc("count"))
            ).all()

            severity_rows = session.execute(
                select(Complaint.severity, func.count().label("count"))
                .where(Complaint.severity.is_not(None))
                .group_by(Complaint.severity)
                .order_by(desc("count"))
            ).all()

            product_rows = session.execute(
                select(
                    Complaint.product,
                    func.avg(Complaint.csi_score).label("avg_csi"),
                    func.count().label("count"),
                )
                .where(Complaint.csi_score.is_not(None))
                .group_by(Complaint.product)
                .order_by("avg_csi")
                .limit(10)
            ).all()

            monthly_rows = session.execute(
                select(
                    func.to_char(
                        func.date_trunc("month", Complaint.date_received),
                        "YYYY-MM",
                    ).label("month"),
                    func.avg(Complaint.csi_score).label("avg_csi"),
                    func.count().label("count"),
                )
                .where(Complaint.date_received.is_not(None))
                .where(Complaint.csi_score.is_not(None))
                .group_by("month")
                .order_by("month")
            ).all()

        return {
            "total_rows": int(total_rows),
            "avg_csi_score": round(float(avg_csi), 3) if avg_csi is not None else None,
            "sentiment_counts": {
                sentiment: int(count) for sentiment, count in sentiment_rows
            },
            "severity_counts": {
                severity: int(count) for severity, count in severity_rows
            },
            "lowest_csi_products": [
                {
                    "product": product,
                    "avg_csi_score": round(float(avg_csi), 3),
                    "count": int(count),
                }
                for product, avg_csi, count in product_rows
            ],
            "monthly_csi": [
                {
                    "month": month,
                    "avg_csi_score": round(float(avg_csi), 3),
                    "count": int(count),
                }
                for month, avg_csi, count in monthly_rows
            ],
        }
    def csi_drivers(self, min_count: int = 20, limit: int = 10) -> dict:
        with SessionLocal() as session:
            rows = session.execute(
                select(
                    Complaint.issue,
                    Complaint.product,
                    func.avg(Complaint.csi_score).label("avg_csi"),
                    func.count().label("count"),
                )
                .where(Complaint.csi_score.is_not(None))
                .group_by(Complaint.issue, Complaint.product)
                .having(func.count() >= min_count)
                .order_by("avg_csi")
                .limit(limit)
            ).all()

        return {
            "min_count": min_count,
            "drivers": [
                {
                    "issue": issue,
                    "product": product,
                    "avg_csi_score": round(float(avg_csi), 3),
                    "count": int(count),
                }
                for issue, product, avg_csi, count in rows
            ],
        }


@lru_cache
def get_complaint_analytics() -> ComplaintAnalytics:
    return ComplaintAnalytics()