from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.players import router as players_router
from app.api.routes.sync import router as sync_router
from app.core.config import get_settings
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title="AFM Search Filters", version="0.1.0")
app.include_router(health_router)
app.include_router(players_router)
app.include_router(sync_router)
