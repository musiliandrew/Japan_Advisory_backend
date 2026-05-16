from app.config import settings
from app.schemas.car import CarFeatures, CostAssumptions
from app.schemas.responses import ROIAnalysisResponse, FullAnalysisResponse
from app.services.cost_engine import compute_import_cost
from app.services.feature_engineering import to_model_frame
from app.services.model_service import model_service


def predict_price(car: CarFeatures) -> float:
    return model_service.predict_price_usd(to_model_frame(car))


def roi_decision(roi_percent: float) -> str:
    return 'IMPORT' if roi_percent > 0 else 'DO NOT IMPORT'


def run_roi_analysis(
    car: CarFeatures,
    kenya_market_price_kes: float,
    predicted_price_usd: float | None = None,
    assumptions: CostAssumptions | None = None,
) -> ROIAnalysisResponse:
    pred = predicted_price_usd if predicted_price_usd is not None else predict_price(car)
    breakdown = compute_import_cost(pred, car.engine_cc, assumptions)
    landed = breakdown.landed_cost_kes
    profit_loss = kenya_market_price_kes - landed
    roi = (profit_loss / landed * 100.0) if landed > 0 else 0.0

    return ROIAnalysisResponse(
        kenya_market_price_kes=round(kenya_market_price_kes, 2),
        landed_cost_kes=round(landed, 2),
        profit_loss_kes=round(profit_loss, 2),
        roi_percent=round(roi, 2),
        decision=roi_decision(roi),
    )


def run_full_analysis(car: CarFeatures, kenya_market_price_kes: float, assumptions: CostAssumptions | None = None) -> FullAnalysisResponse:
    pred = predict_price(car)
    breakdown = compute_import_cost(pred, car.engine_cc, assumptions)
    roi = run_roi_analysis(
        car=car,
        kenya_market_price_kes=kenya_market_price_kes,
        predicted_price_usd=pred,
        assumptions=assumptions,
    )

    return FullAnalysisResponse(
        predicted_price_usd=pred,
        model_version=settings.model_version,
        kenya_market_price_kes=roi.kenya_market_price_kes,
        landed_cost_kes=roi.landed_cost_kes,
        profit_loss_kes=roi.profit_loss_kes,
        roi_percent=roi.roi_percent,
        decision=roi.decision,
        confidence_summary='Confidence is highest when input distribution matches notebook training data.',
        breakdown=breakdown,
    )
