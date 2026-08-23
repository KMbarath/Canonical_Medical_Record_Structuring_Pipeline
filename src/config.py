from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Canonical FHIR Pipeline"
    version: str = "1.1.0"
    db_path: str = "pipeline_store.db"
    
    class Config:
        env_file = ".env"

settings = Settings()