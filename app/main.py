from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app.models.car_listing import CarListing
from app.routes.analysis import router as analysis_router
from app.schemas.responses import HealthResponse
from app.services.fx_service import fx_service

app = FastAPI(title=settings.app_name, version=settings.app_version)

origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)



@app.get('/health', response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status='ok', app=settings.app_name, version=settings.app_version)


@app.get('/fx-rate')
def fx_rate() -> dict[str, float | str]:
    return {
        'pair': 'USD/KES',
        'rate': round(fx_service.get_usd_to_kes(), 6),
    }


Base.metadata.create_all(bind=engine)
app.include_router(analysis_router)
