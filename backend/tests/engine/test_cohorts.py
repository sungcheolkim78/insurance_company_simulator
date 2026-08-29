import pytest

from app.engine.cohorts import step_cohort
from app.engine.types import ChannelCode, CohortState, Decision, ProductCode


def base_decision() -> Decision:
    return Decision(
        pricing_multiplier={ProductCode.WHOLE_LIFE: 1.0, ProductCode.SAVINGS: 1.0},
        underwriting_strictness={ProductCode.WHOLE_LIFE: 0.3, ProductCode.SAVINGS: 0.0},
        commission_rate={ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 0.45},
        marketing_spend={ChannelCode.CAPTIVE: 10_000_000, ChannelCode.GA: 15_000_000},
        asset_allocation={"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        dividend_payout=0.0,
    )


def test_step_cohort_whole_life_applies_mortality_and_reserve_accrual():
    cohort = CohortState(
        product=ProductCode.WHOLE_LIFE,
        channel=ChannelCode.CAPTIVE,
        issue_turn=0,
        in_force_count=1000.0,
        unit_size=100_000_000,
        reserve_balance=0.0,
    )
    updated, flows = step_cohort(cohort, base_decision(), current_turn=1, portfolio_return_monthly=0.0025)

    assert updated is not None
    assert updated.in_force_count == pytest.approx(995.6812926157512)
    assert updated.reserve_balance == pytest.approx(10490809.513167156)
    assert flows.premium_income == pytest.approx(17484682.52194526)
    assert flows.death_claims == pytest.approx(15204071.758213272)
    assert flows.surrender_payouts == pytest.approx(0.0)
    assert flows.deaths == pytest.approx(0.15204071758213272)
    assert flows.lapses == pytest.approx(4.166666666666667)


def test_step_cohort_savings_has_no_mortality_but_credits_interest():
    cohort = CohortState(
        product=ProductCode.SAVINGS,
        channel=ChannelCode.GA,
        issue_turn=0,
        in_force_count=500.0,
        unit_size=60_000_000,
        reserve_balance=0.0,
    )
    updated, flows = step_cohort(cohort, base_decision(), current_turn=1, portfolio_return_monthly=0.0025)

    assert updated is not None
    assert updated.in_force_count == pytest.approx(496.6666666666667)
    assert updated.reserve_balance == pytest.approx(60899825.88866746)
    assert flows.premium_income == pytest.approx(67666473.2096305)
    assert flows.death_claims == pytest.approx(0.0)
    assert flows.deaths == pytest.approx(0.0)
    assert flows.lapses == pytest.approx(3.3333333333333335)


def test_step_cohort_matures_and_closes():
    cohort = CohortState(
        product=ProductCode.SAVINGS,
        channel=ChannelCode.GA,
        issue_turn=0,
        in_force_count=100.0,
        unit_size=60_000_000,
        reserve_balance=500_000_000.0,
    )
    updated, flows = step_cohort(cohort, base_decision(), current_turn=60, portfolio_return_monthly=0.0025)

    assert updated is None
    assert flows.maturity_payouts > 0
