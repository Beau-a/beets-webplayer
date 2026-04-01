from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Resolve .env relative to this file so the server can be started from any directory.
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8")

    beets_db_path: str = "/mnt/nfs/musiclibrary.db"
    beets_config_path: str = str(Path.home() / ".config/beets/config.yaml")
    music_base_path: str = "/mnt/nfs/ml"
    import_base_path: str = "/mnt/nfs"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    host: str = "0.0.0.0"
    port: int = 5000


settings = Settings()
