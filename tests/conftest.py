from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

from app.config import settings
from app.main import app
from app.models import Base, Post
from app.search import index_documents, recreate_index

POSTS = [
    {
        "id": 1,
        "rubrics": ["VK-1", "VK-2"],
        "text": "Новый конкурс для подписчиков группы",
        "created_date": datetime(2020, 3, 10, 12, 0, 0),
    },
    {
        "id": 2,
        "rubrics": ["VK-1"],
        "text": "Итоги конкурса подведём завтра",
        "created_date": datetime(2020, 3, 15, 18, 30, 0),
    },
    {
        "id": 3,
        "rubrics": ["VK-3"],
        "text": "Обзор новых возможностей приложения",
        "created_date": datetime(2020, 4, 1, 9, 15, 0),
    },
    {
        "id": 4,
        "rubrics": [],
        "text": "Конкурсы проводятся каждую неделю",
        "created_date": datetime(2019, 12, 1, 9, 0, 0),
    },
]


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        async with app.state.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(insert(Post), POSTS)

        es = app.state.es
        await recreate_index(es, settings.elasticsearch_index)
        await index_documents(es, settings.elasticsearch_index, POSTS)
        await es.indices.refresh(index=settings.elasticsearch_index)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
