import numpy as np
import pytest

from app.engine.turn import run_turn
from app.engine.types import AssetBalances, ChannelCode, Decision, GameStatus, MarketState, ProductCode, StockRegime


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
    assert result.snapshot.net_income == pytest.approx(-1956478.5450022668)
    assert result.snapshot.equity == pytest.approx(9998043521.454998)
    assert result.assets.deposit == pytest.approx(2998899579.35593)
    assert result.assets.bond == pytest.approx(4000195279.8070974)
    assert result.assets.stock == pytest.approx(3097305168.870447)
    assert result.snapshot.interest_rate == pytest.approx(0.030609434159508862)
    assert result.snapshot.stock_regime == "normal"
    assert result.snapshot.total_in_force == pytest.approx(121.31347666666667)
    assert result.snapshot.deaths_count == pytest.approx(0.00819)
    assert result.snapshot.lapses_count == pytest.approx(0.6783333333333333)
    assert result.snapshot.new_policies_by_product == {"whole_life": 54, "savings": 68}
    assert result.snapshot.new_policies_by_channel == {"captive": 46, "ga": 76}
    assert result.snapshot.premium_income_by_product["whole_life"] == pytest.approx(941850.0)
    assert result.snapshot.premium_income_by_product["savings"] == pytest.approx(9180000.0)
    assert result.snapshot.new_business_premium_by_channel["captive"] == pytest.approx(3153483.3333333335)
    assert result.snapshot.commission_expense_by_channel["ga"] == pytest.approx(3135765.0)
    assert result.snapshot.total_csm > 0
    # csm_new_business is the pre-accretion CSM at issuance; total_csm + csm_release is the
    # post-accretion split (balance remaining + released) after one turn of interest accretion
    # at interest_rate/12, since all 4 cohorts are brand new this turn (issued and stepped
    # forward once in the same turn).
    assert result.snapshot.csm_new_business * (
        1 + result.snapshot.interest_rate / 12
    ) == pytest.approx(result.snapshot.total_csm + result.snapshot.csm_release, rel=1e-9)
    assert result.snapshot.onerous_loss == pytest.approx(0.0)


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
        total_csm = sum(c.csm_balance for c in result.cohorts)
        assert result.assets.total == pytest.approx(total_reserve + total_csm + result.snapshot.equity, rel=1e-9)
        market, assets, equity, cohorts = result.market_state, result.assets, result.snapshot.equity, result.cohorts


def test_run_turn_onerous_loss_breaks_identity_by_exactly_its_own_amount():
    """Regression test for the CSM final-review finding on unbounded commission_rate.

    The balance-sheet identity AssetsTotal == TotalReserve + TotalCSM + Equity (asserted
    for the normal case in test_run_turn_preserves_accounting_identity_across_turns) only
    holds when onerous_loss == 0: an onerous cohort's CSM is clamped to 0 rather than going
    negative, so onerous_loss reduces net_income/equity with no offsetting liability. The
    API schema (TurnRequest in app/schemas.py) now caps commission_rate at 2.0, comfortably
    below the empirical onerous breakeven (~4.95 for savings, ~52 for whole_life at default
    params) — so real players can never reach this path. The engine's Decision dataclass
    itself enforces no such cap, so this test drives run_turn directly with a commission_rate
    far outside the API's allowed range to pin down *exactly* how the identity breaks: the
    gap between assets and (reserve + csm + equity) must equal onerous_loss precisely, with
    nothing else silently absorbing or hiding the loss. A future change to onerous handling
    that lets some of it vanish unaccounted-for (or leak into a different bucket) will fail
    this test.
    """
    rng = np.random.default_rng(42)
    market = MarketState(turn=0, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=None)
    assets = AssetBalances(deposit=3_000_000_000.0, bond=4_000_000_000.0, stock=3_000_000_000.0)
    decision = base_decision()
    # 6.0 is far above the API's 2.0 cap and above the ~4.95 savings breakeven, so the
    # savings/GA cohort issued this turn goes onerous.
    decision.commission_rate = {ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 6.0}

    result = run_turn(0, [], market, assets, 10_000_000_000.0, decision, rng)

    assert result.snapshot.onerous_loss > 0.0
    total_csm = sum(c.csm_balance for c in result.cohorts)
    total_reserve = sum(c.reserve_balance for c in result.cohorts)
    gap = result.assets.total - (total_reserve + total_csm + result.snapshot.equity)
    assert gap == pytest.approx(result.snapshot.onerous_loss, rel=1e-6)


def test_run_turn_marks_completed_at_game_length():
    rng = np.random.default_rng(42)
    market = MarketState(turn=119, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=0.01)
    assets = AssetBalances(deposit=5_000_000_000.0, bond=3_000_000_000.0, stock=2_000_000_000.0)

    result = run_turn(119, [], market, assets, 10_000_000_000.0, base_decision(), rng)

    assert result.snapshot.turn == 120
    assert result.snapshot.status == GameStatus.COMPLETED


def test_run_turn_respects_custom_game_length_turns():
    rng = np.random.default_rng(42)
    market_119 = MarketState(turn=119, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=0.01)
    assets = AssetBalances(deposit=5_000_000_000.0, bond=3_000_000_000.0, stock=2_000_000_000.0)

    not_yet = run_turn(119, [], market_119, assets, 10_000_000_000.0, base_decision(), rng, game_length_turns=200)
    assert not_yet.snapshot.turn == 120
    assert not_yet.snapshot.status == GameStatus.RUNNING

    rng2 = np.random.default_rng(42)
    market_199 = MarketState(turn=199, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=0.01)
    at_length = run_turn(199, [], market_199, assets, 10_000_000_000.0, base_decision(), rng2, game_length_turns=200)
    assert at_length.snapshot.turn == 200
    assert at_length.snapshot.status == GameStatus.COMPLETED
