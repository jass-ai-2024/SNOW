from pathlib import Path

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/documents"
    UPLOAD_DIR: Path = Path("./data")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    class Config:
        case_sensitive = True


settings = Settings()
