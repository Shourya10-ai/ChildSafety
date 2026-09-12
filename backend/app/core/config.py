from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Child Safety Platform"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://childsafety:childsafety_dev_2024@localhost:5432/childsafety"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "childsafety_neo4j_2024"
    
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "childsafety_minio"
    MINIO_SECRET_KEY: str = "childsafety_minio_secret_2024"
    MINIO_BUCKET: str = "childsafety-evidence"
    
    JWT_SECRET_KEY: str = "childsafety_dev_secret_key_at_least_32_chars_2024"
    SECRET_KEY: str = "childsafety_dev_secret_key_at_least_32_chars_2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    AI_SERVER_URL: str = ""
    IDENTITY_VAULT_KEY: str = "CHANGE_ME_IDENTITY_VAULT_KEY_32CH"

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
