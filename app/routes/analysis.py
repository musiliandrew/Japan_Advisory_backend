from fastapi import APIRouter, Query

from app.config import settings
from app.schemas.car import PredictPriceRequest, ImportCostRequest, ROIAnalysisRequest, FullAnalysisRequest
from app.schemas.responses import PredictPriceResponse, ImportCostResponse, ROIAnalysisResponse, FullAnalysisResponse
from app.services.analysis_service import predict_price, run_roi_analysis, run_full_analysis
from app.services.cost_engine import compute_import_cost
from app.services.inventory_service import get_dashboard_data, get_vehicles

router = APIRouter(tags=['analysis'])


@router.get('/vehicles')
def vehicles_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    source: str | None = Query(default=None),
    profitable_only: bool = Query(default=False),
    sort_by: str = Query(default='scraped_at'),
    sort_dir: str = Query(default='desc'),
) -> dict:
    return get_vehicles(
        page=page,
        page_size=page_size,
        source=source,
        profitable_only=profitable_only,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get('/dashboard-data')
def dashboard_data_endpoint() -> dict:
    return get_dashboard_data()


@router.post('/predict-price', response_model=PredictPriceResponse)
def predict_price_endpoint(payload: PredictPriceRequest) -> PredictPriceResponse:
    predicted = predict_price(payload.car)
    return PredictPriceResponse(predicted_price_usd=predicted, model_version=settings.model_version)


@router.post('/import-cost', response_model=ImportCostResponse)
def import_cost_endpoint(payload: ImportCostRequest) -> ImportCostResponse:
    predicted = payload.predicted_price_usd if payload.predicted_price_usd is not None else predict_price(payload.car)
    breakdown = compute_import_cost(predicted, payload.car.engine_cc, payload.assumptions)
    return ImportCostResponse(predicted_price_usd=round(predicted, 2), breakdown=breakdown)


@router.post('/roi-analysis', response_model=ROIAnalysisResponse)
def roi_analysis_endpoint(payload: ROIAnalysisRequest) -> ROIAnalysisResponse:
    return run_roi_analysis(payload.car, payload.kenya_market_price_kes, payload.predicted_price_usd, payload.assumptions)


@router.post('/full-analysis', response_model=FullAnalysisResponse)
def full_analysis_endpoint(payload: FullAnalysisRequest) -> FullAnalysisResponse:
    return run_full_analysis(payload.car, payload.kenya_market_price_kes, payload.assumptions)
