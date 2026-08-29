import pytest

from app.engine.config import DEFAULT_SPLITS, REGIME_TRANSITIONS
from app.engine.types import ProductCode, StockRegime


def test_splits_sum_to_one_per_product():
    for product in ProductCode:
        total = sum(v for (p, _c), v in DEFAULT_SPLITS.items() if p == product)
        assert total == pytest.approx(1.0)


def test_regime_transitions_sum_to_one():
    for regime in StockRegime:
        assert sum(REGIME_TRANSITIONS[regime].values()) == pytest.approx(1.0)
