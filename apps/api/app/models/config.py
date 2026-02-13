from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY", default="")
    api_host: str = "localhost"
    api_port: int = 8000
    
    # Authentication
    demo_password: str = Field(validation_alias="DEMO_PASSWORD", default="demo2024")
    admin_password: str = Field(validation_alias="ADMIN_PASSWORD", default="mph_admin_2024")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
