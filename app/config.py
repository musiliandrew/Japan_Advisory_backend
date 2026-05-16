from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore', protected_namespaces=('settings_',))

    app_name: str = 'Japan Advisory Backend'
    app_version: str = '1.0.0'
    cors_origins: str = '*'

    # Security / external config
    secret_key: str = 'change-me'
    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/japan_advisory'
    frontend_url: str = 'http://localhost:5173'

    # Model/runtime settings
    model_path: str = 'app/models/model.cbm'
    model_version: str = 'notebook-v1'
    current_year: int = 2026

    # Cost engine defaults
    usd_to_kes_rate: float = 130.0
    fx_cache_ttl_seconds: int = 1800
    inventory_cache_ttl_seconds: int = 300
    market_price_markup: float = 1.45
    inventory_max_rows: int = 600
    shipping_usd: float = 1200.0
    insurance_rate: float = 0.002
    clearing_fee_kes: float = 200000.0


settings = Settings()
