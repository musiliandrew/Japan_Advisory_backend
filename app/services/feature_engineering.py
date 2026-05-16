import numpy as np
import pandas as pd

from app.config import settings
from app.schemas.car import CarFeatures


def engine_class(cc: int) -> str:
    if cc <= 1500:
        return '<=1500cc'
    if cc <= 2000:
        return '1501-2000cc'
    if cc <= 2500:
        return '2001-2500cc'
    return '>2500cc'


def normalize_segment(body_type: str) -> str:
    bt = body_type.lower()
    if 'suv' in bt:
        return 'SUV'
    if 'van' in bt:
        return 'Van'
    if 'hatch' in bt:
        return 'Hatchback'
    return body_type


def to_model_frame(car: CarFeatures) -> pd.DataFrame:
    car_age = max(settings.current_year - car.year, 0)
    mileage_per_year = car.mileage_km / car_age if car_age > 0 else car.mileage_km
    segment = normalize_segment(car.body_type)

    return pd.DataFrame([
        {
            'make': car.make.strip(),
            'model': car.model.strip(),
            'year': car.year,
            'mileage_km': float(car.mileage_km),
            'engine_cc': int(car.engine_cc),
            'fuel_type': car.fuel_type,
            'transmission': car.transmission,
            'body_type': car.body_type,
            'source_platform': car.source_platform,
            'drive_type': car.drive_type,
            'car_age': car_age,
            'mileage_per_year': float(mileage_per_year),
            'engine_class': engine_class(car.engine_cc),
            'segment': segment,
            'is_suv': int(segment == 'SUV'),
            'is_van': int(segment == 'Van'),
            'is_hatchback': int(segment == 'Hatchback'),
            'make_model': f"{car.make.strip()}_{car.model.strip()}",
        }
    ])


def inverse_log_price(pred: float) -> float:
    return float(np.expm1(pred))
