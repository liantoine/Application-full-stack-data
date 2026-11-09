from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str | None = None
    sql_echo: bool = False
    jwt_secret: str  # pas de valeur par défaut : le backend refuse de démarrer sans
    jwt_expire_minutes: int = 60


settings = Settings()
