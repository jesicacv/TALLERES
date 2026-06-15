from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valores placeholder que NO deben usarse como clave de firma JWT.
_PLACEHOLDER_SECRETS = {
    "cambia_esta_clave",
    "cambiar_esta_clave_en_desarrollo_local_2026",
    "changeme",
    "secret",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    app_name: str = "Gestion Taller Mecanico"
    app_version: str = "1.0.0"
    debug: bool = False

    # Origenes CORS permitidos (coma-separados). Default: dev local same-origin.
    cors_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    # Marca la cookie de sesion como Secure (solo HTTPS). Activar en produccion.
    cookie_secure: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("secret_key")
    @classmethod
    def _reject_placeholder_secret(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned.lower() in _PLACEHOLDER_SECRETS or len(cleaned) < 32:
            raise ValueError(
                "SECRET_KEY invalido: define una clave fuerte (>=32 chars) en .env, "
                'p.ej. `python -c "import secrets; print(secrets.token_urlsafe(64))"`.'
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
