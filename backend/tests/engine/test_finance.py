import pytest

from app.engine.finance import compute_snapshot, invest_net_cashflow, investment_income_and_returns
from app.engine.types import AssetBalances, GameStatus, MarketState, StockRegime


def test_investment_income_and_returns():
    assets = AssetBalances(deposit=1_000_000_000.0, bond=2_000_000_000.0, stock=1_000_000_000.0)
    market = MarketState(turn=1, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=0.02)

    income, grown = investment_income_and_returns(assets, market)

    assert income == pytest.approx(27083333.333333332)
    assert grown.deposit == pytest.approx(1002083333.3333335)
    assert grown.bond == pytest.approx(2005000000.0)
    assert grown.stock == pytest.approx(1020000000.0)


def test_invest_net_cashflow_positive_uses_target_allocation():
    assets = AssetBalances(deposit=100.0, bond=200.0, stock=200.0)
    result = invest_net_cashflow(assets, 100.0, {"deposit": 0.3, "bond": 0.4, "stock": 0.3})
    assert result.deposit == pytest.approx(130.0)
    assert result.bond == pytest.approx(240.0)
    assert result.stock == pytest.approx(230.0)


def test_invest_net_cashflow_negative_draws_down_proportionally():
    assets = AssetBalances(deposit=100.0, bond=200.0, stock=200.0)
    result = invest_net_cashflow(assets, -100.0, {"deposit": 0.3, "bond": 0.4, "stock": 0.3})
    assert result.deposit == pytest.approx(80.0)
    assert result.bond == pytest.approx(160.0)
    assert result.stock == pytest.approx(160.0)


def test_compute_snapshot_running_status():
    snapshot = compute_snapshot(
        turn=1,
        premium_income=10_000_000.0,
        investment_income=27_083_333.33,
        death_claims=1_000_000.0,
        surrender_payouts=500_000.0,
        maturity_payouts=0.0,
        commission_expense=2_000_000.0,
        marketing_expense=25_000_000.0,
        opex=5_000_000.0,
        reserve_change=3_000_000.0,
        equity_start=10_000_000_000.0,
        dividend_payout=0.0,
        assets=AssetBalances(deposit=1.0, bond=2.0, stock=3.0),
        total_reserve=8_000_000.0,
    )
    assert snapshot.net_income == pytest.approx(583333.33, rel=1e-6)
    assert snapshot.equity == pytest.approx(10_000_583_333.33, rel=1e-9)
    assert snapshot.status == GameStatus.RUNNING


def test_compute_snapshot_bankrupt_status():
    snapshot = compute_snapshot(
        turn=1,
        premium_income=0.0,
        investment_income=0.0,
        death_claims=0.0,
        surrender_payouts=0.0,
        maturity_payouts=0.0,
        commission_expense=0.0,
        marketing_expense=5_000_000.0,
        opex=0.0,
        reserve_change=0.0,
        equity_start=1_000_000.0,
        dividend_payout=0.0,
        assets=AssetBalances(deposit=0.0, bond=0.0, stock=0.0),
        total_reserve=0.0,
    )
    # marketing_expense alone exceeds equity_start, driving net_income and equity negative
    assert snapshot.net_income == pytest.approx(-5_000_000.0)
    assert snapshot.equity == pytest.approx(-4_000_000.0)
    assert snapshot.status == GameStatus.BANKRUPT
