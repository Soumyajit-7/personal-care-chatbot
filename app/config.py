
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "chatbot_user"
    postgres_password: str = "chatbot_pass"
    postgres_db: str = "chatbot_db"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # GROQ
    groq_api_key: str
    
    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    data_dir: str = "./data/csvs"
    
    # Contact
    support_contact_number: str = "+91-1800-XXX-XXXX"
    
    class Config:
        env_file = ".env"
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
