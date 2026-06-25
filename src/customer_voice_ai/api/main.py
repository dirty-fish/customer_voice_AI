from fastapi import FastAPI
from sqlalchemy import text

from customer_voice_ai.api.routes import router
from customer_voice_ai.core.config import get_settings
from customer_voice_ai.core.logging import configure_logging
from customer_voice_ai.db.session import engine

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.project_name)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    database_status = "ok"

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception:
        database_status = "error"

    overall_status = "ok" if database_status == "ok" else "degraded"

    return {
        "status": overall_status,
        "environment": settings.environment,
        "database": database_status,
    }