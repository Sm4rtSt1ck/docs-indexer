from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.db import get_session
from app.schemas import ErrorOut, PostOut
from app.search import get_es

router = APIRouter(prefix="/posts", tags=["posts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
EsDep = Annotated[AsyncElasticsearch, Depends(get_es)]


@router.get(
    "/search",
    response_model=list[PostOut],
    summary="Full-text search over posts",
    description="Returns up to 20 most relevant posts ordered by creation date (newest first).",
)
async def search_posts(
    session: SessionDep,
    es: EsDep,
    query: Annotated[str, Query(min_length=1, max_length=1000, description="Search text")],
) -> list[PostOut]:
    posts = await services.search_posts(session, es, query)
    return [PostOut.model_validate(post) for post in posts]


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete post from database and search index",
    responses={404: {"model": ErrorOut, "description": "Post not found"}},
)
async def delete_post(post_id: int, session: SessionDep, es: EsDep) -> Response:
    if not await services.delete_post(session, es, post_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
