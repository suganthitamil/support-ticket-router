from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    ANTHROPIC_API_KEY: SecretStr

    # Jira
    JIRA_BASE_URL: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: SecretStr
    JIRA_PROJECT_KEY: str

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
