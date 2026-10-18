from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/posts"
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "posts"
    search_limit: int = 20


settings = Settings()
