import numpy as np
import pytest

from app.engine.market import (
    advance_market_state,
    bond_monthly_return,
    deposit_monthly_return,
    stock_monthly_return,
)
from app.engine.types import MarketState, StockRegime


def test_advance_market_state_is_deterministic_given_seed():
    rng = np.random.default_rng(42)
    state = MarketState(turn=0, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=None)

    state = advance_market_state(state, rng)
    assert state.turn == 1
    assert state.interest_rate == pytest.approx(0.030609434159508862)
    assert state.stock_regime == StockRegime.NORMAL
    assert state.stock_return_realized == pytest.approx(0.03501804783225829)

    state = advance_market_state(state, rng)
    assert state.turn == 2
    assert state.interest_rate == pytest.approx(0.03242962017634041)
    assert state.stock_return_realized == pytest.approx(-0.047087180274492726)


def test_asset_return_helpers():
    market = MarketState(turn=1, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=0.05)
    assert deposit_monthly_return(market) == pytest.approx((0.03 - 0.005) / 12)
    assert bond_monthly_return(market) == pytest.approx(0.03 / 12)
    assert stock_monthly_return(market) == pytest.approx(0.05)
