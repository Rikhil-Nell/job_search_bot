from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    groq_api_key: str = Field(..., validation_alias="GROQ_API_KEY")
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    db_url: str = Field(..., validation_alias="DB_URL")
    logfire_write_token : str = Field(...,validation_alias="LOGFIRE_WRITE_TOKEN")

    class Config:
        env_file = "./.env"

settings = Settings()
