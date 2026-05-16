from typing import Literal
from pydantic import BaseModel, Field

FuelType = Literal['Petrol', 'Diesel', 'Hybrid', 'Electric']
TransmissionType = Literal['Automatic', 'Manual', 'CVT']
BodyType = Literal['Sedan', 'SUV', 'Hatchback', 'Wagon', 'Truck', 'Coupe', 'Van']
DriveType = Literal['2WD', '4WD', 'AWD']
SourcePlatform = Literal['BeForward', 'SBT Japan', 'Trust Motor', 'CardealPage', 'Other']


class CarFeatures(BaseModel):
    make: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    year: int = Field(..., ge=1990, le=2030)
    mileage_km: float = Field(..., ge=0)
    engine_cc: int = Field(..., ge=600, le=8000)
    fuel_type: FuelType
    transmission: TransmissionType
    body_type: BodyType
    drive_type: DriveType
    source_platform: SourcePlatform = 'Other'


class CostAssumptions(BaseModel):
    shipping_usd: float | None = Field(default=None, ge=0)
    insurance_rate: float | None = Field(default=None, ge=0)
    clearing_fee_kes: float | None = Field(default=None, ge=0)


class PredictPriceRequest(BaseModel):
    car: CarFeatures


class ImportCostRequest(BaseModel):
    car: CarFeatures
    predicted_price_usd: float | None = Field(default=None, ge=0)
    assumptions: CostAssumptions | None = None


class ROIAnalysisRequest(BaseModel):
    car: CarFeatures
    kenya_market_price_kes: float = Field(..., ge=0)
    predicted_price_usd: float | None = Field(default=None, ge=0)
    assumptions: CostAssumptions | None = None


class FullAnalysisRequest(BaseModel):
    car: CarFeatures
    kenya_market_price_kes: float = Field(..., ge=0)
    assumptions: CostAssumptions | None = None
