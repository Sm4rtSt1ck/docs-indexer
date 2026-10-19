from app.config import settings


async def test_search_returns_matching_posts_ordered_by_date(client):
    response = await client.get("/posts/search", params={"query": "конкурс"})

    assert response.status_code == 200
    assert [post["id"] for post in response.json()] == [2, 1, 4]


async def test_search_returns_all_db_fields(client):
    response = await client.get("/posts/search", params={"query": "обзор возможностей"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 3,
            "rubrics": ["VK-3"],
            "text": "Обзор новых возможностей приложения",
            "created_date": "2020-04-01T09:15:00",
        }
    ]


async def test_search_without_matches_returns_empty_list(client):
    response = await client.get("/posts/search", params={"query": "несуществующееслово"})

    assert response.status_code == 200
    assert response.json() == []


async def test_search_requires_query(client):
    response = await client.get("/posts/search")

    assert response.status_code == 422


async def test_search_rejects_empty_query(client):
    response = await client.get("/posts/search", params={"query": ""})

    assert response.status_code == 422


async def test_search_respects_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "search_limit", 2)
    response = await client.get("/posts/search", params={"query": "конкурс"})

    assert response.status_code == 200
    assert len(response.json()) == 2
