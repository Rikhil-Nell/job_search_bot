from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key : str = Field(..., validate_alias="OPENAI_API_KEY")
    db_url : str = Field(..., validation_alias="DB_URL")
    logfire_write_token : str = Field(...,validate_alias="LOGFIRE_WRITE_TOKEN")

    class Config:
        env_file = "./.env"

settings = Settings()
