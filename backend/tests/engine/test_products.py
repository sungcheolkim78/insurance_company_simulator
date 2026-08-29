import pytest

from app.engine.config import DEFAULT_PRODUCT_CONFIGS
from app.engine.products import (
    compute_new_business,
    effective_cost_rate_annual,
    gross_premium_per_policy_monthly,
)
from app.engine.types import ChannelCode, Decision, ProductCode


def base_decision() -> Decision:
    return Decision(
        pricing_multiplier={ProductCode.WHOLE_LIFE: 1.0, ProductCode.SAVINGS: 1.0},
        underwriting_strictness={ProductCode.WHOLE_LIFE: 0.3, ProductCode.SAVINGS: 0.0},
        commission_rate={ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 0.45},
        marketing_spend={ChannelCode.CAPTIVE: 10_000_000, ChannelCode.GA: 15_000_000},
        asset_allocation={"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        dividend_payout=0.0,
    )


def test_effective_cost_rate_annual_applies_aging_and_underwriting():
    wl = DEFAULT_PRODUCT_CONFIGS[ProductCode.WHOLE_LIFE]
    assert effective_cost_rate_annual(wl, 0, 0.3) == pytest.approx(0.00182)
    assert effective_cost_rate_annual(wl, 12, 0.3) == pytest.approx(0.0018746000000000001)


def test_gross_premium_per_policy_monthly():
    wl = DEFAULT_PRODUCT_CONFIGS[ProductCode.WHOLE_LIFE]
    assert gross_premium_per_policy_monthly(wl, 0, 1.0, 0.3) == pytest.approx(17441.666666666668)


def test_compute_new_business_matches_expected_counts():
    results = {(p, c): n for p, c, n in compute_new_business(base_decision())}
    assert results[(ProductCode.WHOLE_LIFE, ChannelCode.CAPTIVE)] == 26
    assert results[(ProductCode.WHOLE_LIFE, ChannelCode.GA)] == 28
    assert results[(ProductCode.SAVINGS, ChannelCode.CAPTIVE)] == 20
    assert results[(ProductCode.SAVINGS, ChannelCode.GA)] == 48
