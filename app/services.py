from elasticsearch import AsyncElasticsearch
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import search
from app.config import settings
from app.models import Post


async def search_posts(session: AsyncSession, es: AsyncElasticsearch, query: str) -> list[Post]:
    ids = await search.search_ids(es, settings.elasticsearch_index, query, settings.search_limit)
    if not ids:
        return []
    result = await session.scalars(
        select(Post).where(Post.id.in_(ids)).order_by(Post.created_date.desc(), Post.id)
    )
    return list(result)


async def delete_post(session: AsyncSession, es: AsyncElasticsearch, post_id: int) -> bool:
    result = await session.execute(delete(Post).where(Post.id == post_id).returning(Post.id))
    if result.scalar_one_or_none() is None:
        await session.rollback()
        return False
    await search.delete_document(es, settings.elasticsearch_index, post_id)
    await session.commit()
    return True
