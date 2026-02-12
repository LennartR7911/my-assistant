from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import DirectoryPath
import os

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GITHUB_TOKEN: str
    GITHUB_REPO: str
    KNOWLEDGE_BASE_PATH: DirectoryPath = "."

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
