import pytest

from app.engine.config import DEFAULT_PRODUCT_CONFIGS
from app.engine.csm import compute_csm_initial, step_csm_cohort
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
        commission_rate=100.0,  # far above the ~55 breakeven for this product/strictness — forces a loss
        market_rate_annual=0.03,
    )
    assert result.csm_balance == 0.0
    assert result.onerous_loss > 0.0


def test_step_csm_cohort_accretes_then_releases_straight_line():
    new_balance, release = step_csm_cohort(
        csm_balance=1200.0,
        locked_in_rate_monthly=0.0025,
        straight_line_release=100.0,
        periods_remaining=12,
        is_closing=False,
    )
    accreted = 1200.0 * 1.0025
    assert release == pytest.approx(100.0)
    assert new_balance == pytest.approx(accreted - 100.0)


def test_step_csm_cohort_caps_release_at_available_balance():
    new_balance, release = step_csm_cohort(
        csm_balance=50.0,
        locked_in_rate_monthly=0.0,
        straight_line_release=100.0,
        periods_remaining=2,
        is_closing=False,
    )
    assert release == pytest.approx(50.0)
    assert new_balance == pytest.approx(0.0)


def test_step_csm_cohort_releases_full_balance_when_closing():
    new_balance, release = step_csm_cohort(
        csm_balance=1000.0,
        locked_in_rate_monthly=0.0025,
        straight_line_release=50.0,
        periods_remaining=20,
        is_closing=True,
    )
    assert release == pytest.approx(1000.0 * 1.0025)
    assert new_balance == pytest.approx(0.0)


def test_step_csm_cohort_releases_full_balance_on_last_period():
    new_balance, release = step_csm_cohort(
        csm_balance=100.0,
        locked_in_rate_monthly=0.0,
        straight_line_release=100.0,
        periods_remaining=1,
        is_closing=False,
    )
    assert release == pytest.approx(100.0)
    assert new_balance == pytest.approx(0.0)
