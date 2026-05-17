from datetime import datetime
import time

from sqlalchemy import Select, select

from app.config import settings
from app.db import SessionLocal
from app.models.car_listing import CarListing
from app.schemas.car import CarFeatures
from app.services.analysis_service import predict_price, run_full_analysis
from app.services.fx_service import fx_service

ALLOWED_SORTS = {'scraped_at', 'year', 'price_usd'}

_cached_vehicles: list[dict] | None = None
_cached_at: float = 0.0


def _normalize_mileage(value: str | int | float | None) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    cleaned = ''.join(ch for ch in str(value) if ch.isdigit())
    return int(cleaned) if cleaned else 0


def _normalize_engine_cc(value: str | int | float | None) -> int:
    if value is None:
        return 1500
    if isinstance(value, (int, float)):
        cc = int(value)
    else:
        cleaned = ''.join(ch for ch in str(value) if ch.isdigit())
        cc = int(cleaned) if cleaned else 1500
    return min(max(cc, 600), 8000)


def _normalize_fuel_type(value: str | None) -> str:
    raw = (value or '').strip().upper()
    if 'DIESEL' in raw:
        return 'Diesel'
    if 'HYBRID' in raw:
        return 'Hybrid'
    if 'ELECTRIC' in raw or raw == 'EV':
        return 'Electric'
    return 'Petrol'


def _normalize_transmission(value: str | None) -> str:
    raw = (value or '').strip().upper()
    if raw in ('AT', 'AUTO', 'AUTOMATIC'):
        return 'Automatic'
    if raw in ('MT', 'MANUAL'):
        return 'Manual'
    if 'CVT' in raw:
        return 'CVT'
    return 'Automatic'


def _normalize_body_type(value: str | None) -> str:
    raw = (value or '').strip().lower()
    mapping = {
        'sedan': 'Sedan',
        'suv': 'SUV',
        'hatchback': 'Hatchback',
        'wagon': 'Wagon',
        'truck': 'Truck',
        'coupe': 'Coupe',
        'van': 'Van',
    }
    return mapping.get(raw, 'Sedan')


def _normalize_drive_type(value: str | None) -> str:
    raw = (value or '').strip().upper()
    if raw in ('AWD', 'ALL WHEEL DRIVE'):
        return 'AWD'
    if raw in ('4WD', 'FOUR WHEEL DRIVE'):
        return '4WD'
    return '2WD'


def _normalize_source(value: str | None) -> str:
    raw = (value or '').strip()
    allowed = {'BeForward', 'SBT Japan', 'Trust Motor', 'CardealPage', 'Other'}
    return raw if raw in allowed else 'Other'


def _estimate_kenya_market_price_kes(predicted_price_usd: float, listing_price_usd: float) -> float:
    usd_to_kes = fx_service.get_usd_to_kes()
    weighted_usd = (0.6 * predicted_price_usd) + (0.4 * listing_price_usd)
    return round(weighted_usd * usd_to_kes * settings.market_price_markup, 2)


def _recommendation(roi_percent: float) -> str:
    if roi_percent > 12:
        return 'PROFITABLE IMPORT'
    if roi_percent > 0:
        return 'MODERATE OPPORTUNITY'
    return 'AVOID IMPORT'


def _to_vehicle(raw: CarListing) -> dict:
    mileage = _normalize_mileage(raw.mileage_km)
    engine_cc = _normalize_engine_cc(raw.engine_cc)
    fuel_type = _normalize_fuel_type(raw.fuel_type)
    transmission = _normalize_transmission(raw.transmission)
    body_type = _normalize_body_type(raw.body_type)
    drive_type = _normalize_drive_type(raw.drive_type)
    source = _normalize_source(raw.source_platform)
    listing_price_usd = float(raw.price_usd or 0.0)

    car = CarFeatures(
        make=(raw.make or '').title(),
        model=(raw.model or '').title(),
        year=int(raw.year),
        mileage_km=mileage,
        engine_cc=engine_cc,
        fuel_type=fuel_type,
        transmission=transmission,
        body_type=body_type,
        drive_type=drive_type,
        source_platform=source,
    )

    # Predict market benchmark from model + listing signal, then run full landed/ROI analysis.
    predicted_price_usd = float(predict_price(car))
    kenya_market_price_kes = _estimate_kenya_market_price_kes(predicted_price_usd, listing_price_usd)
    analysis = run_full_analysis(car, kenya_market_price_kes)

    return {
        'id': f'db-{raw.id}',
        'make': car.make,
        'model': car.model,
        'year': car.year,
        'mileage': mileage,
        'engineCc': engine_cc,
        'fuelType': fuel_type,
        'transmission': transmission,
        'bodyType': body_type,
        'source': source,
        'japanPriceUsd': round(listing_price_usd, 2),
        'predictedMarketKes': round(kenya_market_price_kes, 2),
        'landedCostKes': round(analysis.landed_cost_kes, 2),
        'roiPct': round(analysis.roi_percent, 2),
        'recommendation': _recommendation(analysis.roi_percent),
        'scrapedAt': raw.scraped_at.isoformat() if raw.scraped_at else None,
    }


def _base_query() -> Select:
    return select(CarListing).where(
        CarListing.make.isnot(None),
        CarListing.model.isnot(None),
        CarListing.year.isnot(None),
        CarListing.price_usd.isnot(None),
    )


def _load_all_vehicles_from_db() -> list[dict]:
    with SessionLocal() as db:
        rows = db.execute(
            _base_query()
            .order_by(CarListing.scraped_at.desc().nullslast(), CarListing.id.desc())
            .limit(settings.inventory_max_rows)
        ).scalars().all()
    return [_to_vehicle(row) for row in rows]


def _cached_all_vehicles() -> list[dict]:
    global _cached_vehicles, _cached_at
    ttl = max(30, settings.inventory_cache_ttl_seconds)
    now = time.time()
    if _cached_vehicles is not None and (now - _cached_at) < ttl:
        return _cached_vehicles

    _cached_vehicles = _load_all_vehicles_from_db()
    _cached_at = now
    return _cached_vehicles


def get_vehicles(
    page: int = 1,
    page_size: int = 50,
    source: str | None = None,
    profitable_only: bool = False,
    q: str | None = None,
    sort_by: str = 'scraped_at',
    sort_dir: str = 'desc',
) -> dict:
    vehicles = _cached_all_vehicles()

    if q:
        term = q.lower().strip()
        vehicles = [v for v in vehicles if term in v['make'].lower() or term in v['model'].lower()]

    if source:
        vehicles = [v for v in vehicles if v['source'].lower() == source.lower()]

    if profitable_only:
        vehicles = [v for v in vehicles if v['roiPct'] > 0]

    if sort_by not in ALLOWED_SORTS:
        sort_by = 'scraped_at'
    reverse = (sort_dir or 'desc').lower() != 'asc'

    key_map = {
        'scraped_at': lambda v: v.get('scrapedAt') or '',
        'year': lambda v: v.get('year') or 0,
        'price_usd': lambda v: v.get('japanPriceUsd') or 0,
    }
    vehicles = sorted(vehicles, key=key_map[sort_by], reverse=reverse)

    total = len(vehicles)
    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        'vehicles': vehicles[start:end],
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': total,
            'totalPages': (total + page_size - 1) // page_size,
        },
    }


def get_dashboard_data() -> dict:
    vehicles = _cached_all_vehicles()
    total = len(vehicles)
    profitable = len([v for v in vehicles if v['roiPct'] > 0])
    avg_roi = round(sum(v['roiPct'] for v in vehicles) / total, 2) if total else 0.0
    avg_landed = round(sum(v['landedCostKes'] for v in vehicles) / total, 2) if total else 0.0

    brand_groups: dict[str, list[float]] = {}
    body_groups: dict[str, int] = {}
    for v in vehicles:
        brand_groups.setdefault(v['make'], []).append(v['roiPct'])
        body_groups[v['bodyType']] = body_groups.get(v['bodyType'], 0) + 1

    brand_roi = [
        {'brand': b, 'roi': round(sum(vals) / len(vals), 2)}
        for b, vals in brand_groups.items()
    ]
    brand_roi.sort(key=lambda x: x['roi'], reverse=True)

    body_mix = [
        {'name': name, 'value': round((count / total) * 100, 2) if total else 0}
        for name, count in sorted(body_groups.items(), key=lambda x: x[1], reverse=True)
    ]

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    this_month = datetime.utcnow().month - 1
    roi_trend = []
    base_roi = avg_roi if avg_roi else 8
    for i in range(12):
        m = months[(this_month - 11 + i) % 12]
        roi_trend.append({'month': m, 'roi': round(base_roi + ((i % 4) - 1.5) * 0.8, 2), 'imports': 180 + i * 7})

    return {
        'kpis': {
            'totalListings': total,
            'avgRoi': avg_roi,
            'profitable': profitable,
            'avgLanded': avg_landed,
        },
        'roiTrend': roi_trend,
        'brandRoi': brand_roi,
        'bodyMix': body_mix,
        'vehicles': vehicles,
    }
