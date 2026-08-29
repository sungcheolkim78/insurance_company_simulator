import pytest

from app.engine.config import DEFAULT_PRODUCT_CONFIGS
from app.engine.csm import compute_csm_initial
from app.engine.types import ProductCode


def test_compute_csm_initial_zero_count_returns_zero():
    result = compute_csm_initial(
        DEFAULT_PRODUCT_CONFIGS[ProductCode.WHOLE_LIFE],
        pricing_multiplier=1.0,
        underwriting_strictness=0.3,
        count=0,
        commission_rate=0.3,
        market_rate_annual=0.03,
    )
    assert result.csm_balance == 0.0
    assert result.onerous_loss == 0.0
    assert result.periods_remaining == 0


def test_compute_csm_initial_savings_uses_maturity_turns_as_horizon():
    result = compute_csm_initial(
        DEFAULT_PRODUCT_CONFIGS[ProductCode.SAVINGS],
        pricing_multiplier=1.0,
        underwriting_strictness=0.0,
        count=100,
        commission_rate=0.45,
        market_rate_annual=0.03,
    )
    assert result.periods_remaining == 60
    assert result.csm_balance > 0
    assert result.onerous_loss == 0.0
    assert result.straight_line_release == pytest.approx(result.csm_balance / 60)
    assert result.locked_in_rate_monthly == pytest.approx(0.03 / 12)


def test_compute_csm_initial_whole_life_horizon_capped():
    result = compute_csm_initial(
        DEFAULT_PRODUCT_CONFIGS[ProductCode.WHOLE_LIFE],
        pricing_multiplier=1.0,
        underwriting_strictness=0.3,
        count=1000,
        commission_rate=0.3,
        market_rate_annual=0.03,
    )
    assert 1 <= result.periods_remaining <= 600
    assert result.csm_balance > 0


def test_compute_csm_initial_onerous_when_commission_exceeds_margin():
    result = compute_csm_initial(
        DEFAULT_PRODUCT_CONFIGS[ProductCode.WHOLE_LIFE],
        pricing_multiplier=1.0,
        underwriting_strictness=0.3,
        count=1,
        commission_rate=50.0,  # absurdly high commission forces a loss
        market_rate_annual=0.03,
    )
    assert result.csm_balance == 0.0
    assert result.onerous_loss > 0.0
