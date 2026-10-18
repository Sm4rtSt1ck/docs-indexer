import argparse
import ast
import asyncio
import csv
from datetime import datetime

from elasticsearch import AsyncElasticsearch
from sqlalchemy import func, insert, select, text

from app.config import settings
from app.db import create_engine, create_tables
from app.models import Post
from app.search import index_documents, recreate_index

BATCH_SIZE = 1000


def read_posts(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return [
            {
                "id": i,
                "text": row["text"],
                "created_date": datetime.fromisoformat(row["created_date"]),
                "rubrics": ast.literal_eval(row["rubrics"]),
            }
            for i, row in enumerate(csv.DictReader(f), start=1)
        ]


async def load(path: str, force: bool) -> None:
    engine = create_engine(settings.database_url)
    es = AsyncElasticsearch(settings.elasticsearch_url)
    try:
        await create_tables(engine)
        async with engine.begin() as conn:
            count = await conn.scalar(select(func.count()).select_from(Post))
            if count and not force:
                print(f"Database already contains {count} posts, skipping")
                return
            await conn.execute(text("TRUNCATE posts"))
            posts = read_posts(path)
            for start in range(0, len(posts), BATCH_SIZE):
                await conn.execute(insert(Post), posts[start:start + BATCH_SIZE])
        await recreate_index(es, settings.elasticsearch_index)
        await index_documents(es, settings.elasticsearch_index, posts)
        await es.indices.refresh(index=settings.elasticsearch_index)
        print(f"Loaded {len(posts)} posts")
    finally:
        await es.close()
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load posts from CSV into PostgreSQL and Elasticsearch")
    parser.add_argument("path", nargs="?", default="posts.csv")
    parser.add_argument("--force", action="store_true", help="reload data even if the database is not empty")
    args = parser.parse_args()
    asyncio.run(load(args.path, args.force))


if __name__ == "__main__":
    main()
