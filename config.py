from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5433/brawl_predictor"
    brawl_stars_api_key: str = ""
    model_path: str = "model/artifacts/model.joblib"

    brawl_stars_base_url: str = "https://api.brawlstars.com/v1"
    api_request_delay: float = 0.2  # seconds between BS API calls

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
