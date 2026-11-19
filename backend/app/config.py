from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./volunteermatch.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ai_enabled: bool = False
    ai_provider: str = "none"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def cors_list(self) -> list[str]:
        configured = [x.strip().rstrip("/") for x in self.cors_origins.split(",") if x.strip()]
        local_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
        return list(dict.fromkeys(configured + local_origins))

settings = Settings()
