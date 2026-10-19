from sqlalchemy import select

from app.config import settings
from app.main import app
from app.models import Post


async def test_delete_removes_post_from_db_and_index(client):
    response = await client.delete("/posts/1")

    assert response.status_code == 204
    async with app.state.sessionmaker() as session:
        assert await session.scalar(select(Post).where(Post.id == 1)) is None
    assert not await app.state.es.exists(index=settings.elasticsearch_index, id="1")


async def test_deleted_post_is_not_found_by_search(client):
    await client.delete("/posts/2")

    response = await client.get("/posts/search", params={"query": "конкурс"})

    assert [post["id"] for post in response.json()] == [1, 4]


async def test_delete_missing_post_returns_404(client):
    response = await client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


async def test_delete_twice_returns_404(client):
    assert (await client.delete("/posts/3")).status_code == 204
    assert (await client.delete("/posts/3")).status_code == 404


async def test_delete_with_invalid_id_returns_422(client):
    response = await client.delete("/posts/abc")

    assert response.status_code == 422
