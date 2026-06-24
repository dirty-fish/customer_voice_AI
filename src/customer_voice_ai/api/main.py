from fastapi import FastAPI

from customer_voice_ai.api.routes import router
from customer_voice_ai.core.config import get_settings
from customer_voice_ai.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.project_name)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}