from app.config import settings
from app.schemas.car import CostAssumptions
from app.schemas.responses import ImportCostBreakdown
from app.services.fx_service import fx_service


def compute_import_cost(predicted_price_usd: float, engine_cc: int, assumptions: CostAssumptions | None = None) -> ImportCostBreakdown:
    shipping_usd = assumptions.shipping_usd if assumptions and assumptions.shipping_usd is not None else settings.shipping_usd
    insurance_rate = assumptions.insurance_rate if assumptions and assumptions.insurance_rate is not None else settings.insurance_rate
    clearing_fee_kes = assumptions.clearing_fee_kes if assumptions and assumptions.clearing_fee_kes is not None else settings.clearing_fee_kes

    usd_to_kes_rate = fx_service.get_usd_to_kes()
    insurance_usd = predicted_price_usd * insurance_rate
    cif_usd = predicted_price_usd + shipping_usd + insurance_usd
    cif_kes = cif_usd * usd_to_kes_rate

    import_duty = 0.25 * cif_kes
    excise_rate = 0.20 if engine_cc <= 1500 else 0.25
    excise_duty = excise_rate * (cif_kes + import_duty)
    vat = 0.16 * (cif_kes + import_duty + excise_duty)
    idf = 0.035 * cif_kes
    rdl = 0.02 * cif_kes

    total_taxes = import_duty + excise_duty + vat + idf + rdl
    landed_cost = cif_kes + total_taxes + clearing_fee_kes

    return ImportCostBreakdown(
        cif_usd=round(cif_usd, 2),
        cif_kes=round(cif_kes, 2),
        usd_to_kes_rate_used=round(usd_to_kes_rate, 6),
        import_duty_kes=round(import_duty, 2),
        excise_duty_kes=round(excise_duty, 2),
        vat_kes=round(vat, 2),
        idf_kes=round(idf, 2),
        rdl_kes=round(rdl, 2),
        clearing_fees_kes=round(clearing_fee_kes, 2),
        total_taxes_kes=round(total_taxes, 2),
        landed_cost_kes=round(landed_cost, 2),
    )
