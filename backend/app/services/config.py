from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str 
    DEBUG: bool

    class Config:
        env_file = ".env"

settings = Settings()