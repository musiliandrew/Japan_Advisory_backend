from pathlib import Path
from typing import Protocol

import joblib
from catboost import CatBoostRegressor

from app.config import settings
from app.services.feature_engineering import inverse_log_price


class PredictableModel(Protocol):
    def predict(self, X): ...


class BaselineFallbackModel:
    def predict(self, X):
        mileage_penalty = X['mileage_km'].iloc[0] / 100000
        base = 9.1 - (0.15 * mileage_penalty) + (X['engine_cc'].iloc[0] / 12000)
        return [base]


class ModelService:
    def __init__(self) -> None:
        self._model: PredictableModel = self._load_model()

    def _load_model(self) -> PredictableModel:
        p = Path(settings.model_path)
        if not p.exists():
            return BaselineFallbackModel()

        if p.suffix.lower() == '.cbm':
            model = CatBoostRegressor()
            model.load_model(str(p))
            return model

        return joblib.load(p)

    def predict_price_usd(self, model_frame) -> float:
        try:
            pred = float(self._model.predict(model_frame)[0])
            return round(max(inverse_log_price(pred), 0.0), 2)
        except Exception:
            # Fall back to deterministic baseline when model features mismatch incoming data.
            pred = float(BaselineFallbackModel().predict(model_frame)[0])
            return round(max(inverse_log_price(pred), 0.0), 2)


model_service = ModelService()
