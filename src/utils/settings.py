from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_CONNECTION: str
    SECRET_KEY: str

    # Supabase Storage (for resume and trade license files)
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    RESUME_BUCKET: str
    TRADE_LICENSE_BUCKET: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()