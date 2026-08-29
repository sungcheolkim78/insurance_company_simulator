import numpy as np

from .config import (
    DEPOSIT_RATE_SPREAD,
    LONG_RUN_RATE,
    RATE_NOISE_STD,
    RATE_REVERSION_SPEED,
    REGIME_PARAMS,
    REGIME_TRANSITIONS,
)
from .types import MarketState, StockRegime


def _next_regime(current: StockRegime, rng: np.random.Generator) -> StockRegime:
    options = REGIME_TRANSITIONS[current]
    regimes = list(options.keys())
    probs = list(options.values())
    return regimes[rng.choice(len(regimes), p=probs)]


def advance_market_state(prev: MarketState, rng: np.random.Generator) -> MarketState:
    noise = rng.normal(0, RATE_NOISE_STD)
    rate = prev.interest_rate + RATE_REVERSION_SPEED * (LONG_RUN_RATE - prev.interest_rate) + noise
    rate = max(0.0, rate)

    regime = _next_regime(prev.stock_regime, rng)
    drift, vol = REGIME_PARAMS[regime]
    stock_return = drift + vol * rng.normal(0, 1)

    return MarketState(turn=prev.turn + 1, interest_rate=rate, stock_regime=regime, stock_return_realized=stock_return)


def deposit_monthly_return(market: MarketState) -> float:
    return max(0.001, market.interest_rate - DEPOSIT_RATE_SPREAD) / 12


def bond_monthly_return(market: MarketState) -> float:
    return market.interest_rate / 12


def stock_monthly_return(market: MarketState) -> float:
    assert market.stock_return_realized is not None
    return market.stock_return_realized
