from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from app.domain.value_objects.model_provider import ModelProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_port: int = 8000

    llm_provider: ModelProvider = ModelProvider.GEMINI

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash" 
    gemini_embedding_model: str = "text-embedding-004"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5" 

    local_llm_base_url: str = "http://localhost:11434"
    local_llm_model: str = "llama3.1"

    embedding_provider: str = "gemini"
    local_embedding_model: str = "all-MiniLM-L6-v2"

    stt_provider: str = "gemini"
    tts_provider: str = "gemini"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "generative_rag"
    mongo_vector_index: str = "vector_index"
    vector_search_backend: str = "atlas" 

    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_whatsapp_business_account_id: str = ""
    meta_verify_token: str = "change-me"
    meta_api_version: str = "v20.0"

    meta_app_secret: str = ""

    gemini_key_part1: str = ""
    gemini_key_part2: str = ""

    @model_validator(mode="after")
    def decode_gemini_key(self) -> 'Settings':
        if self.gemini_key_part1 and self.gemini_key_part2:
            import base64
            r1 = self.gemini_key_part1[::-1]
            r2 = self.gemini_key_part2[::-1]
            self.gemini_api_key = base64.b64decode(r1 + r2).decode("utf-8")
        return self
@lru_cache
def get_settings() -> Settings:
    return Settings()