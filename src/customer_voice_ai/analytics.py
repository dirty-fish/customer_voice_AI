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


@lru_cache
def get_complaint_analytics() -> ComplaintAnalytics:
    return ComplaintAnalytics()