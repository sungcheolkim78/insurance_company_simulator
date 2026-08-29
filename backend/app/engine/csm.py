import math
from dataclasses import dataclass

from .config import CSM_RISK_ADJUSTMENT_COEF, CSM_WHOLE_LIFE_HORIZON_CAP_TURNS
from .products import effective_cost_rate_annual, gross_premium_per_policy_monthly, lapse_rate_monthly
from .types import ProductCode, ProductConfig


@dataclass
class CsmInitialResult:
    csm_balance: float
    onerous_loss: float
    locked_in_rate_monthly: float
    straight_line_release: float
    periods_remaining: int


def compute_csm_initial(
    product: ProductConfig,
    pricing_multiplier: float,
    underwriting_strictness: float,
    count: float,
    commission_rate: float,
    market_rate_annual: float,
) -> CsmInitialResult:
    if count <= 0:
        return CsmInitialResult(0.0, 0.0, 0.0, 0.0, 0)

    r_lock_monthly = market_rate_annual / 12
    lapse_monthly = lapse_rate_monthly(product, pricing_multiplier)
    if product.code == ProductCode.WHOLE_LIFE:
        mortality_monthly = effective_cost_rate_annual(product, 0, underwriting_strictness) / 12
    else:
        mortality_monthly = 0.0
    q_lock = mortality_monthly + lapse_monthly

    if product.maturity_turns is not None:
        n_periods = product.maturity_turns
    elif q_lock > 0:
        n_periods = min(math.ceil(1 / q_lock), CSM_WHOLE_LIFE_HORIZON_CAP_TURNS)
    else:
        n_periods = CSM_WHOLE_LIFE_HORIZON_CAP_TURNS
    n_periods = max(n_periods, 1)

    survivorship = 1.0
    discount = 1.0
    pv_margin_per_policy = 0.0
    pv_risk_per_policy = 0.0
    for t in range(n_periods):
        premium_t = gross_premium_per_policy_monthly(product, t, pricing_multiplier, underwriting_strictness)
        pv_margin_per_policy += survivorship * premium_t * (1 - product.reserve_accrual_ratio) / discount
        if product.code == ProductCode.WHOLE_LIFE:
            claim_cost_t = (effective_cost_rate_annual(product, t, underwriting_strictness) / 12) * product.unit_size
            pv_risk_per_policy += survivorship * claim_cost_t / discount
        survivorship *= 1 - q_lock
        discount *= 1 + r_lock_monthly

    risk_adjustment_per_policy = CSM_RISK_ADJUSTMENT_COEF * pv_risk_per_policy
    day0_premium = gross_premium_per_policy_monthly(product, 0, pricing_multiplier, underwriting_strictness)
    commission_expense_cohort = count * day0_premium * commission_rate

    gross_csm = count * (pv_margin_per_policy - risk_adjustment_per_policy) - commission_expense_cohort
    csm_balance = max(0.0, gross_csm)
    onerous_loss = max(0.0, -gross_csm)

    return CsmInitialResult(
        csm_balance=csm_balance,
        onerous_loss=onerous_loss,
        locked_in_rate_monthly=r_lock_monthly,
        straight_line_release=csm_balance / n_periods,
        periods_remaining=n_periods,
    )


def step_csm_cohort(
    csm_balance: float,
    locked_in_rate_monthly: float,
    straight_line_release: float,
    periods_remaining: int,
    is_closing: bool,
) -> tuple[float, float]:
    accreted = csm_balance * (1 + locked_in_rate_monthly)
    if is_closing or periods_remaining <= 1:
        return 0.0, accreted
    release = min(accreted, straight_line_release)
    return accreted - release, release
