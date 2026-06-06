from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    DATABASE_URL: str = "sqlite+aiosqlite:///./cias_test.db"
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Acepta tanto lista JSON como string con coma: http://localhost:3000,http://localhost:3001
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Si ya viene como JSON array
            if v.strip().startswith("["):
                import json
                return json.loads(v)
            # Si viene como string separado por comas
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
