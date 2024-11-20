from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/documents"
    UPLOAD_DIR: Path = Path("./data")
    ANTHROPIC_API_KEY: str
    TEI_BASE_URL: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    class Config:
        case_sensitive = True


load_dotenv()
settings = Settings()
