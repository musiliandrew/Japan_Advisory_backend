from typing import Literal
from pydantic import BaseModel

Decision = Literal['IMPORT', 'DO NOT IMPORT']


class PredictPriceResponse(BaseModel):
    predicted_price_usd: float
    model_version: str


class ImportCostBreakdown(BaseModel):
    cif_usd: float
    cif_kes: float
    usd_to_kes_rate_used: float
    import_duty_kes: float
    excise_duty_kes: float
    vat_kes: float
    idf_kes: float
    rdl_kes: float
    clearing_fees_kes: float
    total_taxes_kes: float
    landed_cost_kes: float


class ImportCostResponse(BaseModel):
    predicted_price_usd: float
    breakdown: ImportCostBreakdown


class ROIAnalysisResponse(BaseModel):
    kenya_market_price_kes: float
    landed_cost_kes: float
    profit_loss_kes: float
    roi_percent: float
    decision: Decision


class FullAnalysisResponse(BaseModel):
    predicted_price_usd: float
    model_version: str
    kenya_market_price_kes: float
    landed_cost_kes: float
    profit_loss_kes: float
    roi_percent: float
    decision: Decision
    confidence_summary: str
    breakdown: ImportCostBreakdown


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
