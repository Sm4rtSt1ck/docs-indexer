from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk
from fastapi import Request

INDEX_MAPPINGS = {
    "properties": {
        "id": {"type": "integer"},
        "text": {"type": "text", "analyzer": "russian"},
    }
}


def get_es(request: Request) -> AsyncElasticsearch:
    return request.app.state.es


async def create_index(es: AsyncElasticsearch, index: str) -> None:
    if not await es.indices.exists(index=index):
        await es.indices.create(index=index, mappings=INDEX_MAPPINGS)


async def recreate_index(es: AsyncElasticsearch, index: str) -> None:
    await es.indices.delete(index=index, ignore_unavailable=True)
    await create_index(es, index)


async def index_documents(es: AsyncElasticsearch, index: str, docs: list[dict]) -> None:
    actions = (
        {"_index": index, "_id": str(doc["id"]), "id": doc["id"], "text": doc["text"]}
        for doc in docs
    )
    await async_bulk(es, actions, chunk_size=1000)


async def search_ids(es: AsyncElasticsearch, index: str, query: str, limit: int) -> list[int]:
    response = await es.search(
        index=index,
        query={"match": {"text": query}},
        size=limit,
        source=["id"],
    )
    return [hit["_source"]["id"] for hit in response["hits"]["hits"]]


async def delete_document(es: AsyncElasticsearch, index: str, doc_id: int) -> None:
    try:
        await es.delete(index=index, id=str(doc_id), refresh=True)
    except NotFoundError:
        pass
