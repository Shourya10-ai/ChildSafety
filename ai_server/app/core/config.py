from __future__ import annotations
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_STORE_PATH: str = './model_store'
    DEVICE: str = 'cpu'
    NLP_MODEL_NAME: str = 'xlm-roberta-base'
    CV_MODEL_NAME: str = 'yolov8n'
    EMBEDDING_MODEL_NAME: str = 'openai/clip-vit-base-patch32'
    WHISPER_MODEL_NAME: str = 'openai/whisper-small'
    MAX_BATCH_SIZE: int = 32
    BACKEND_URL: str = 'http://localhost:8000'
    LOG_LEVEL: str = 'INFO'
    ENVIRONMENT: str = 'development'

    class Config:
        env_file = ".env"

settings = Settings()
