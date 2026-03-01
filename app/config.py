from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    tg_bot_token: str
    webhook_url: str
    llm_api_key: str
    llm_provider: str
    google_sheets_credentials_path: str
    google_sheet_id: str
    admin_chat_id: list[str]
    notification_chat_id: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
