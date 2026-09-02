import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.collector import start_collector, stop_collector
from app.config import get_settings
from app.routers import health, measures

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("airquality.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting sensor collector background job")
    start_collector()
    yield
    logger.info("Shutting down sensor collector background job")
    stop_collector()


app = FastAPI(
    title="Home Air Quality API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(measures.router)


@app.get("/api")
def root() -> dict:
    return {"name": "Home Air Quality API", "docs": "/docs"}
