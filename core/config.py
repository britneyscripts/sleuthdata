from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Query-Driven Job Crawler"
    ENV: str = Field(default="development", validation_alias="ENV")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///dev_jobs.db",
        validation_alias="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL"
    )
    
    # Optional LLM Key for Skill Extraction
    GEMINI_API_KEY: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")

    # API authentication key required on write endpoints (x-api-key header).
    # Falls back to a fixed dev key only when ENV=development (see core/security.py).
    API_KEY: str | None = Field(default=None, validation_alias="API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url_resolved(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("sqlite"):
            # Switch file depending on ENV
            if "local_jobs.db" in url or "dev_jobs.db" in url or "production_jobs.db" in url:
                db_name = "dev_jobs.db" if self.ENV == "development" else "production_jobs.db"
                if "///" in url:
                    return url.split("///")[0] + "///" + db_name
                return "sqlite:///" + db_name
        return url

settings = Settings()
