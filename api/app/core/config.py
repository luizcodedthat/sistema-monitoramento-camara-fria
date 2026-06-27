from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "API Câmara Fria"
    VERSION: str = "1.0.0"
    API_FREE_LLM_URL: str = "https://apifreellm.com/api/v1/chat"
    API_FREE_LLM_KEY: str = "apf_w2dxhb02p14fnfv7k7wqr8jb"

    class Config:
        env_file = ".env"

settings = Settings()