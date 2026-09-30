"""
JOCKY Platform — Application Configuration
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    jocky_env: str = "development"
    jocky_secret_key: str = "dev_secret_key_change_in_production_at_least_32"
    jocky_jwt_algorithm: str = "HS256"
    jocky_jwt_expire_minutes: int = 1440

    # Database
    database_url: str = "sqlite+aiosqlite:///./jocky_dev.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Frontend
    vite_api_base_url: str = "http://localhost:8000"

    # Agent
    agent_api_url: str = "http://localhost:8000"
    agent_heartbeat_interval: int = 30
    agent_poll_interval: int = 10

    # Seed
    seed_demo_data: bool = True
    seed_admin_password: str = "admin123"

    # Reports
    report_output_dir: str = "./reports_output"

    # Security
    allow_unauthenticated_agents: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",")]

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url

    @property
    def is_development(self) -> bool:
        return self.jocky_env == "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
