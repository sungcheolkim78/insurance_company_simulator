import numpy as np
import pytest

from app.engine.turn import run_turn
from app.engine.types import AssetBalances, ChannelCode, Decision, MarketState, ProductCode, StockRegime


def base_decision() -> Decision:
    return Decision(
        pricing_multiplier={ProductCode.WHOLE_LIFE: 1.0, ProductCode.SAVINGS: 1.0},
        underwriting_strictness={ProductCode.WHOLE_LIFE: 0.3, ProductCode.SAVINGS: 0.0},
        commission_rate={ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 0.45},
        marketing_spend={ChannelCode.CAPTIVE: 10_000_000, ChannelCode.GA: 15_000_000},
        asset_allocation={"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        dividend_payout=0.0,
    )


def test_run_turn_matches_reference_calculation():
    rng = np.random.default_rng(42)
    market = MarketState(turn=0, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=None)
    assets = AssetBalances(deposit=3_000_000_000.0, bond=4_000_000_000.0, stock=3_000_000_000.0)

    result = run_turn(0, [], market, assets, 10_000_000_000.0, base_decision(), rng)

    assert result.snapshot.turn == 1
    assert result.market_state.interest_rate == pytest.approx(0.030609434159508862)
    assert len(result.cohorts) == 4
    assert result.snapshot.premium_income == pytest.approx(10121850.0)
    assert result.snapshot.investment_income == pytest.approx(121659646.75648837)
    assert result.snapshot.death_claims == pytest.approx(819000.0)
    assert result.snapshot.commission_expense == pytest.approx(4081810.0)
    assert result.snapshot.marketing_expense == pytest.approx(25000000)
    assert result.snapshot.opex == pytest.approx(5480658.723013548)
    assert result.snapshot.reserve_change == pytest.approx(8827110.0)
    assert result.snapshot.net_income == pytest.approx(87572918.03347482)
    assert result.snapshot.equity == pytest.approx(10087572918.033474)
    assert result.assets.deposit == pytest.approx(2998899579.35593)
    assert result.assets.bond == pytest.approx(4000195279.8070974)
    assert result.assets.stock == pytest.approx(3097305168.870447)


def test_run_turn_preserves_accounting_identity_across_turns():
    rng = np.random.default_rng(42)
    market = MarketState(turn=0, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=None)
    assets = AssetBalances(deposit=3_000_000_000.0, bond=4_000_000_000.0, stock=3_000_000_000.0)
    equity = 10_000_000_000.0
    cohorts = []
    decision = base_decision()

    for turn in range(5):
        result = run_turn(turn, cohorts, market, assets, equity, decision, rng)
        total_reserve = sum(c.reserve_balance for c in result.cohorts)
        assert result.assets.total == pytest.approx(total_reserve + result.snapshot.equity, rel=1e-9)
        market, assets, equity, cohorts = result.market_state, result.assets, result.snapshot.equity, result.cohorts
