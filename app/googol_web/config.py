from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_token :str

    class Config:
        env_file = ".env"

settings = Settings()