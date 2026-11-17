import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator

_DEV_SECRET_KEY = "dev_secret_key_change_in_production"
_DEV_AUDITOR_SECRET = "dev_auditor_secret"


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./cias_test.db"
    SECRET_KEY: str = _DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # String simple o separado por comas: "http://localhost:3000,http://localhost:3001"
    CORS_ORIGINS: str = "http://localhost:3000"
    # Código requerido para registrar auditores (A3)
    AUDITOR_REGISTRATION_SECRET: str = _DEV_AUDITOR_SECRET

    @model_validator(mode="after")
    def check_production_secrets(self) -> "Settings":
        if os.getenv("APP_ENV") == "production":
            if self.SECRET_KEY == _DEV_SECRET_KEY:
                raise ValueError("SECRET_KEY no puede ser el valor por defecto en producción")
            if self.AUDITOR_REGISTRATION_SECRET == _DEV_AUDITOR_SECRET:
                raise ValueError(
                    "AUDITOR_REGISTRATION_SECRET no puede ser el valor por defecto en producción"
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Devuelve CORS_ORIGINS como lista (acepta string, JSON array o coma-separado)."""
        v = self.CORS_ORIGINS.strip()
        if v.startswith("["):
            import json
            return json.loads(v)
        return [o.strip() for o in v.split(",") if o.strip()]


settings = Settings()
