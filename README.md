# Posts search

A simple full-text search service over documents. Documents are stored in PostgreSQL, the search index lives in Elasticsearch.

Stack: FastAPI, SQLAlchemy (asyncpg), Elasticsearch async client, pytest.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/posts/search?query=<text>` | Finds the 20 most relevant documents in the index and returns them with all DB fields, ordered by `created_date` (newest first) |
| `DELETE` | `/posts/{id}` | Deletes a document from the database and the index. `204` on success, `404` if not found |
| `GET` | `/health` | Health check |

OpenAPI specification is in [docs.json](docs.json). Interactive docs are available at http://localhost:8000/docs when the service is running.

Example:

```bash
curl -G "http://localhost:8000/posts/search" --data-urlencode "query=конкурс"
curl -X DELETE "http://localhost:8000/posts/42"
```

## Dataset

The service loads documents from `posts.csv` (not included in the repository). It is a UTF-8 CSV file with a header row and the following columns:

| Column | Format | Example |
|--------|--------|---------|
| `text` | document text, may contain line breaks (quoted) | `"Текст документа"` |
| `created_date` | `YYYY-MM-DD HH:MM:SS` | `2020-01-15 10:30:00` |
| `rubrics` | Python-style list of strings | `"['VK-123', 'VK-456']"` |

The file has no id column, documents get sequential ids starting from 1 in file order.

## Running with Docker

Put the `posts.csv` dataset into the project root (it is not included in the repository), then start everything:

```bash
docker compose up -d --build
```

This starts PostgreSQL, Elasticsearch and the service on http://localhost:8000. On the first start the service loads `posts.csv` into the database and the index. Subsequent starts skip loading if the database already has data.

To reload data from scratch:

```bash
docker compose exec app python -m app.load_data posts.csv --force
```

Stop and remove everything including data volumes:

```bash
docker compose down -v
```

## Running locally

Requires Python 3.12+ and running PostgreSQL and Elasticsearch (you can start just them with `docker compose up -d postgres elasticsearch`).

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.load_data posts.csv
uvicorn app.main:app --reload
```

Configuration via environment variables (or `.env`):

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/posts` |
| `ELASTICSEARCH_URL` | `http://localhost:9200` |
| `ELASTICSEARCH_INDEX` | `posts` |

## Project structure

```
app/
  main.py        application and lifespan (DB engine, ES client)
  api.py         HTTP endpoints
  services.py    search and delete logic
  search.py      Elasticsearch index management and queries
  models.py      SQLAlchemy models
  schemas.py     response schemas
  db.py          database helpers
  config.py      settings
  load_data.py   CSV loader
docs.json        OpenAPI specification
```
