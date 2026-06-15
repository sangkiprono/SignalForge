from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    app_name: str = "SignalForge API"
    debug: bool = True
    webhook_secret: str = "change-this-secret"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    metaapi_token: str = ""
    metaapi_account_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
