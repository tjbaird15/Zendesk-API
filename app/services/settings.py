from pydantic import BaseModel
from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed runtime settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    zendesk_subdomain: str = Field(..., description="Zendesk subdomain only")
    zendesk_email: str = Field(..., description="Zendesk account email")
    zendesk_api_token: SecretStr = Field(..., description="Zendesk API token")
    openai_api_key: SecretStr = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini")
    zendesk_chat_list_path: str = Field(default="/api/v2/chats.json")


class HealthInfo(BaseModel):
    status: str


def get_settings() -> Settings:
    """Return validated settings from environment variables."""

    return Settings()
