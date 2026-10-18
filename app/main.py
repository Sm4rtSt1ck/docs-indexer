from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI

from app.api import router
from app.config import settings
from app.db import create_engine, create_sessionmaker, create_tables
from app.search import create_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(settings.database_url)
    es = AsyncElasticsearch(settings.elasticsearch_url)
    await create_tables(engine)
    await create_index(es, settings.elasticsearch_index)
    app.state.engine = engine
    app.state.sessionmaker = create_sessionmaker(engine)
    app.state.es = es
    try:
        yield
    finally:
        await es.close()
        await engine.dispose()


app = FastAPI(title="Posts search", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["service"], summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "ok"}
