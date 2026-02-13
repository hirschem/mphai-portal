from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache



class Settings(BaseSettings):
    # Request size limiting
    ENFORCE_REQUEST_SIZE_LIMIT: bool = Field(default=True, validation_alias="ENFORCE_REQUEST_SIZE_LIMIT")
    MAX_REQUEST_BYTES: int = Field(default=25_000_000, validation_alias="MAX_REQUEST_BYTES")
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY", default="")
    api_host: str = "localhost"
    api_port: int = 8000

    # Authentication
    demo_password: str = Field(validation_alias="DEMO_PASSWORD", default="demo2024")
    admin_password: str = Field(validation_alias="ADMIN_PASSWORD", default="mph_admin_2024")

    # Rate limiting
    login_rate_limit: int = Field(default=5, validation_alias="LOGIN_RATE_LIMIT")
    generate_rate_limit: int = Field(default=3, validation_alias="GENERATE_RATE_LIMIT")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
