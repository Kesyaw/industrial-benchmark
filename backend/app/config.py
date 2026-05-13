from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://benchmark:benchmark123@127.0.0.1:5434/financial_data_warehouse"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://benchmark:benchmark123@127.0.0.1:5434/financial_data_warehouse"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
