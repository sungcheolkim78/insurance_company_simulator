# 보험회사 운영 시뮬레이션 Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a playable Phase 1 slice of the insurance company simulator: a FastAPI + SQLite backend running the turn-based simulation engine, and a Vue 3 + Tailwind frontend that lets a player create a game, submit turn decisions, and play through to a final score.

**Architecture:** A pure-Python simulation engine (`backend/app/engine/`) with no FastAPI/DB dependencies implements the turn-processing formulas from the spec. A thin persistence layer (`backend/app/repository.py` + SQLModel tables) converts between engine dataclasses and SQLite rows. FastAPI routes are thin wrappers over the repository. The Vue frontend is a 3-screen flow (new game → dashboard/decision loop → result) backed by a single Pinia store that talks to the API.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel (SQLAlchemy 2.0 + Pydantic), SQLite, numpy, pytest, httpx; Vue 3, Vite, Tailwind CSS v4, Pinia, vue-router, axios, Chart.js/vue-chartjs; Docker/podman-compose for local execution.

**Spec:** `docs/superpowers/specs/2026-08-29-insurance-simulator-phase1-design.md`

## Global Constraints

- Python >= 3.11 (uses `X | None` union syntax).
- The simulation engine (`backend/app/engine/**`) MUST NOT import FastAPI, SQLModel, or any DB/web code — it is tested and reusable standalone.
- 1 turn = 1 month; game length = 120 turns (`GAME_LENGTH_TURNS` in `backend/app/engine/config.py`).
- All monetary values are plain floats in KRW; no currency formatting in the engine or DB layer (formatting is a frontend concern only).
- Two spec ambiguities are resolved concretely by this plan (see spec sections 6.2/6.3): (1) `effective_cost_rate_annual` returns an **annual** rate; `gross_premium_per_policy_monthly` divides it by 12 itself. (2) Only `whole_life` cohorts ever incur mortality decrement/death claims; `savings` cohorts decrement only via lapse and maturity.
- RNG reproducibility is implemented per-turn, not as one long-lived stream: each turn's `numpy.random.default_rng(game.rng_seed + game.current_turn)` is freshly seeded from the game's base seed plus the turn number being advanced *from*. This is equivalent in spirit to spec section 6.6 (deterministic replay given seed + decisions) but fits a stateless HTTP request/response cycle without persisting generator state.
- Phase 1 has no per-game customization of product/channel configs — all engine functions read `DEFAULT_PRODUCT_CONFIGS` / `DEFAULT_CHANNEL_CONFIGS` / `DEFAULT_SPLITS` from `backend/app/engine/config.py` directly.

---

## Task 1: Backend project scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_main.py`
- Modify: `.gitignore` (repo root)

**Interfaces:**
- Produces: FastAPI app instance at `app.main.app`, importable by all later backend tasks and tests.

- [ ] **Step 1: Create the backend package skeleton and pyproject.toml**

`backend/pyproject.toml`:
```toml
[project]
name = "insurance-simulator-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlmodel>=0.0.22",
    "numpy>=1.26",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["app*"]
```

`backend/app/__init__.py`: empty file.
`backend/tests/__init__.py`: empty file.

- [ ] **Step 2: Create venv and install**

Run:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

- [ ] **Step 3: Write the failing smoke test**

`backend/tests/test_main.py`:
```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Run test, verify it fails**

Run: `cd backend && pytest tests/test_main.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 5: Implement app/main.py**

`backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Insurance Company Simulator")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 6: Run test, verify it passes**

Run: `cd backend && pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 7: Add backend/frontend artifacts to .gitignore**

Append to the repo-root `.gitignore`:
```
# Backend runtime data
backend/.venv/
backend/data/
backend/*.db

# Frontend
frontend/node_modules/
frontend/dist/
```

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/main.py backend/tests/__init__.py backend/tests/test_main.py .gitignore
git commit -m "feat: scaffold FastAPI backend project"
```

---

## Task 2: Engine types and default config

**Files:**
- Create: `backend/app/engine/__init__.py`
- Create: `backend/app/engine/types.py`
- Create: `backend/app/engine/config.py`
- Create: `backend/tests/engine/__init__.py`
- Create: `backend/tests/engine/test_config.py`

**Interfaces:**
- Consumes: nothing (foundational task).
- Produces: `ProductCode`, `ChannelCode`, `StockRegime`, `GameStatus` (str enums); `ProductConfig`, `ChannelConfig`, `CohortState`, `MarketState`, `Decision`, `AssetBalances`, `CohortFlows`, `FinancialSnapshot`, `TurnResult` (dataclasses) in `app.engine.types`. `DEFAULT_PRODUCT_CONFIGS`, `DEFAULT_CHANNEL_CONFIGS`, `DEFAULT_SPLITS`, `ELASTICITY`, `APPROVAL_STRICTNESS_COEF`, `MORTALITY_AGING_RATE`, `UNDERWRITING_MORTALITY_COEF`, `LAPSE_PRICE_SENSITIVITY`, `OPEX_BASE`, `LONG_RUN_RATE`, `RATE_REVERSION_SPEED`, `RATE_NOISE_STD`, `DEPOSIT_RATE_SPREAD`, `REGIME_PARAMS`, `REGIME_TRANSITIONS`, `INITIAL_CAPITAL_DEFAULT`, `GAME_LENGTH_TURNS` in `app.engine.config`.

- [ ] **Step 1: Write the failing test**

`backend/tests/engine/__init__.py`: empty file.

`backend/tests/engine/test_config.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/engine/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine'`

- [ ] **Step 3: Create app/engine/__init__.py**

`backend/app/engine/__init__.py`: empty file.

- [ ] **Step 4: Implement types.py**

`backend/app/engine/types.py`:
```python
from dataclasses import dataclass
from enum import Enum


class ProductCode(str, Enum):
    WHOLE_LIFE = "whole_life"
    SAVINGS = "savings"


class ChannelCode(str, Enum):
    CAPTIVE = "captive"
    GA = "ga"


class StockRegime(str, Enum):
    NORMAL = "normal"
    BOOM = "boom"
    CRISIS = "crisis"


class GameStatus(str, Enum):
    RUNNING = "running"
    BANKRUPT = "bankrupt"
    COMPLETED = "completed"


@dataclass
class ProductConfig:
    code: ProductCode
    unit_size: float
    base_cost_rate_annual: float
    expense_loading: float
    base_lapse_rate_annual: float
    reserve_accrual_ratio: float
    credited_rate_spread: float
    maturity_turns: int | None


@dataclass
class ChannelConfig:
    code: ChannelCode
    base_productivity: float
    base_commission_rate: float
    commission_sensitivity: float
    reference_spend: float


@dataclass
class CohortState:
    product: ProductCode
    channel: ChannelCode
    issue_turn: int
    in_force_count: float
    unit_size: float
    reserve_balance: float


@dataclass
class MarketState:
    turn: int
    interest_rate: float
    stock_regime: StockRegime
    stock_return_realized: float | None


@dataclass
class Decision:
    pricing_multiplier: dict[ProductCode, float]
    underwriting_strictness: dict[ProductCode, float]
    commission_rate: dict[ChannelCode, float]
    marketing_spend: dict[ChannelCode, float]
    asset_allocation: dict[str, float]
    dividend_payout: float


@dataclass
class AssetBalances:
    deposit: float
    bond: float
    stock: float

    @property
    def total(self) -> float:
        return self.deposit + self.bond + self.stock


@dataclass
class CohortFlows:
    premium_income: float = 0.0
    death_claims: float = 0.0
    surrender_payouts: float = 0.0
    maturity_payouts: float = 0.0


@dataclass
class FinancialSnapshot:
    turn: int
    premium_income: float
    investment_income: float
    death_claims: float
    surrender_payouts: float
    maturity_payouts: float
    commission_expense: float
    marketing_expense: float
    opex: float
    reserve_change: float
    net_income: float
    deposit_balance: float
    bond_balance: float
    stock_balance: float
    total_reserve: float
    equity: float
    status: GameStatus


@dataclass
class TurnResult:
    cohorts: list[CohortState]
    market_state: MarketState
    assets: AssetBalances
    snapshot: FinancialSnapshot
```

- [ ] **Step 5: Implement config.py**

`backend/app/engine/config.py`:
```python
from .types import ChannelCode, ChannelConfig, ProductCode, ProductConfig, StockRegime

DEFAULT_PRODUCT_CONFIGS: dict[ProductCode, ProductConfig] = {
    ProductCode.WHOLE_LIFE: ProductConfig(
        code=ProductCode.WHOLE_LIFE,
        unit_size=100_000_000,
        base_cost_rate_annual=0.002,
        expense_loading=0.15,
        base_lapse_rate_annual=0.05,
        reserve_accrual_ratio=0.6,
        credited_rate_spread=0.0,
        maturity_turns=None,
    ),
    ProductCode.SAVINGS: ProductConfig(
        code=ProductCode.SAVINGS,
        unit_size=60_000_000,
        base_cost_rate_annual=0.025,
        expense_loading=0.08,
        base_lapse_rate_annual=0.08,
        reserve_accrual_ratio=0.9,
        credited_rate_spread=1.0,
        maturity_turns=60,
    ),
}

DEFAULT_CHANNEL_CONFIGS: dict[ChannelCode, ChannelConfig] = {
    ChannelCode.CAPTIVE: ChannelConfig(
        code=ChannelCode.CAPTIVE,
        base_productivity=50.0,
        base_commission_rate=0.30,
        commission_sensitivity=1.0,
        reference_spend=10_000_000,
    ),
    ChannelCode.GA: ChannelConfig(
        code=ChannelCode.GA,
        base_productivity=80.0,
        base_commission_rate=0.45,
        commission_sensitivity=1.2,
        reference_spend=15_000_000,
    ),
}

DEFAULT_SPLITS: dict[tuple[ProductCode, ChannelCode], float] = {
    (ProductCode.WHOLE_LIFE, ChannelCode.CAPTIVE): 0.6,
    (ProductCode.WHOLE_LIFE, ChannelCode.GA): 0.4,
    (ProductCode.SAVINGS, ChannelCode.CAPTIVE): 0.4,
    (ProductCode.SAVINGS, ChannelCode.GA): 0.6,
}

ELASTICITY = 2.0
APPROVAL_STRICTNESS_COEF = 0.4
MORTALITY_AGING_RATE = 1.03
UNDERWRITING_MORTALITY_COEF = 0.3
LAPSE_PRICE_SENSITIVITY = 1.5
OPEX_BASE = 5_000_000.0

LONG_RUN_RATE = 0.03
RATE_REVERSION_SPEED = 0.1
RATE_NOISE_STD = 0.002
DEPOSIT_RATE_SPREAD = 0.005

REGIME_PARAMS: dict[StockRegime, tuple[float, float]] = {
    StockRegime.NORMAL: (0.005, 0.04),
    StockRegime.BOOM: (0.015, 0.05),
    StockRegime.CRISIS: (-0.03, 0.08),
}

REGIME_TRANSITIONS: dict[StockRegime, dict[StockRegime, float]] = {
    StockRegime.NORMAL: {StockRegime.NORMAL: 0.94, StockRegime.BOOM: 0.03, StockRegime.CRISIS: 0.03},
    StockRegime.BOOM: {StockRegime.BOOM: 0.85, StockRegime.NORMAL: 0.15, StockRegime.CRISIS: 0.0},
    StockRegime.CRISIS: {StockRegime.CRISIS: 0.80, StockRegime.NORMAL: 0.20, StockRegime.BOOM: 0.0},
}

INITIAL_CAPITAL_DEFAULT = 10_000_000_000.0
GAME_LENGTH_TURNS = 120
```

- [ ] **Step 6: Run test, verify it passes**

Run: `cd backend && pytest tests/engine/test_config.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/engine/__init__.py backend/app/engine/types.py backend/app/engine/config.py backend/tests/engine/__init__.py backend/tests/engine/test_config.py
git commit -m "feat: add engine types and default balance config"
```

---

## Task 3: Market state advance (spec 6.4, 6.6)

**Files:**
- Create: `backend/app/engine/market.py`
- Create: `backend/tests/engine/test_market.py`

**Interfaces:**
- Consumes: `MarketState`, `StockRegime` from `app.engine.types`; constants from `app.engine.config`.
- Produces: `advance_market_state(prev: MarketState, rng: np.random.Generator) -> MarketState`, `deposit_monthly_return(market) -> float`, `bond_monthly_return(market) -> float`, `stock_monthly_return(market) -> float` in `app.engine.market`.

- [ ] **Step 1: Write the failing test**

`backend/tests/engine/test_market.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/engine/test_market.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.market'`

- [ ] **Step 3: Implement market.py**

`backend/app/engine/market.py`:
```python
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
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd backend && pytest tests/engine/test_market.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/market.py backend/tests/engine/test_market.py
git commit -m "feat: add market state advance and asset return helpers"
```

---

## Task 4: Products — premium pricing and new business (spec 6.1, 6.2)

**Files:**
- Create: `backend/app/engine/products.py`
- Create: `backend/tests/engine/test_products.py`

**Interfaces:**
- Consumes: `ProductConfig`, `ChannelConfig`, `Decision`, `ProductCode`, `ChannelCode` from `app.engine.types`; `DEFAULT_CHANNEL_CONFIGS`, `DEFAULT_SPLITS`, `ELASTICITY`, `APPROVAL_STRICTNESS_COEF`, `MORTALITY_AGING_RATE`, `UNDERWRITING_MORTALITY_COEF` from `app.engine.config`.
- Produces: `effective_cost_rate_annual(product, duration_turns, underwriting_strictness) -> float`, `gross_premium_per_policy_monthly(product, duration_turns, pricing_multiplier, underwriting_strictness) -> float`, `approval_rate(underwriting_strictness) -> float`, `channel_capacity(channel, commission_rate, marketing_spend) -> float`, `price_elasticity(pricing_multiplier) -> float`, `compute_new_business(decision: Decision) -> list[tuple[ProductCode, ChannelCode, int]]` in `app.engine.products`.

- [ ] **Step 1: Write the failing test**

`backend/tests/engine/test_products.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/engine/test_products.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.products'`

- [ ] **Step 3: Implement products.py**

`backend/app/engine/products.py`:
```python
import math

from .config import (
    APPROVAL_STRICTNESS_COEF,
    DEFAULT_CHANNEL_CONFIGS,
    DEFAULT_SPLITS,
    ELASTICITY,
    MORTALITY_AGING_RATE,
    UNDERWRITING_MORTALITY_COEF,
)
from .types import ChannelCode, ChannelConfig, Decision, ProductCode, ProductConfig


def effective_cost_rate_annual(product: ProductConfig, duration_turns: int, underwriting_strictness: float) -> float:
    duration_years = duration_turns / 12
    aging = product.base_cost_rate_annual * (MORTALITY_AGING_RATE**duration_years)
    return aging * (1 - UNDERWRITING_MORTALITY_COEF * underwriting_strictness)


def gross_premium_per_policy_monthly(
    product: ProductConfig, duration_turns: int, pricing_multiplier: float, underwriting_strictness: float
) -> float:
    annual_rate = effective_cost_rate_annual(product, duration_turns, underwriting_strictness)
    return product.unit_size * (annual_rate / 12) * (1 + product.expense_loading) * pricing_multiplier


def approval_rate(underwriting_strictness: float) -> float:
    return 1 - APPROVAL_STRICTNESS_COEF * underwriting_strictness


def channel_capacity(channel: ChannelConfig, commission_rate: float, marketing_spend: float) -> float:
    return (
        channel.base_productivity
        * (1 + channel.commission_sensitivity * (commission_rate - channel.base_commission_rate))
        * math.sqrt(marketing_spend / channel.reference_spend)
    )


def price_elasticity(pricing_multiplier: float) -> float:
    return pricing_multiplier ** (-ELASTICITY)


def compute_new_business(decision: Decision) -> list[tuple[ProductCode, ChannelCode, int]]:
    results: list[tuple[ProductCode, ChannelCode, int]] = []
    for product in ProductCode:
        for channel in ChannelCode:
            channel_config = DEFAULT_CHANNEL_CONFIGS[channel]
            capacity = channel_capacity(
                channel_config, decision.commission_rate[channel], decision.marketing_spend[channel]
            )
            split = DEFAULT_SPLITS[(product, channel)]
            elasticity_factor = price_elasticity(decision.pricing_multiplier[product])
            raw_applications = capacity * split * elasticity_factor
            approved = raw_applications * approval_rate(decision.underwriting_strictness[product])
            results.append((product, channel, math.floor(approved)))
    return results
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd backend && pytest tests/engine/test_products.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/products.py backend/tests/engine/test_products.py
git commit -m "feat: add premium pricing and new business formulas"
```

---

## Task 5: Cohort decrement, reserve rollforward, maturity (spec 6.3)

**Files:**
- Create: `backend/app/engine/cohorts.py`
- Create: `backend/tests/engine/test_cohorts.py`

**Interfaces:**
- Consumes: `CohortState`, `CohortFlows`, `Decision`, `ProductCode` from `app.engine.types`; `DEFAULT_PRODUCT_CONFIGS`, `LAPSE_PRICE_SENSITIVITY` from `app.engine.config`; `effective_cost_rate_annual`, `gross_premium_per_policy_monthly` from `app.engine.products`.
- Produces: `step_cohort(cohort: CohortState, decision: Decision, current_turn: int, portfolio_return_monthly: float) -> tuple[CohortState | None, CohortFlows]` in `app.engine.cohorts`. Returns `(None, flows)` when the cohort matures or fully empties this turn.

- [ ] **Step 1: Write the failing test**

`backend/tests/engine/test_cohorts.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/engine/test_cohorts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.cohorts'`

- [ ] **Step 3: Implement cohorts.py**

`backend/app/engine/cohorts.py`:
```python
from .config import DEFAULT_PRODUCT_CONFIGS, LAPSE_PRICE_SENSITIVITY
from .products import effective_cost_rate_annual, gross_premium_per_policy_monthly
from .types import CohortFlows, CohortState, Decision, ProductCode


def step_cohort(
    cohort: CohortState, decision: Decision, current_turn: int, portfolio_return_monthly: float
) -> tuple[CohortState | None, CohortFlows]:
    product = DEFAULT_PRODUCT_CONFIGS[cohort.product]
    duration_turns = current_turn - cohort.issue_turn
    strictness = decision.underwriting_strictness[cohort.product]
    pricing_multiplier = decision.pricing_multiplier[cohort.product]

    premium = cohort.in_force_count * gross_premium_per_policy_monthly(
        product, duration_turns, pricing_multiplier, strictness
    )

    if product.code == ProductCode.WHOLE_LIFE:
        decrement_rate_monthly = effective_cost_rate_annual(product, duration_turns, strictness) / 12
    else:
        decrement_rate_monthly = 0.0
    deaths = cohort.in_force_count * decrement_rate_monthly
    death_claims = deaths * product.unit_size

    lapse_rate_monthly = (product.base_lapse_rate_annual * pricing_multiplier**LAPSE_PRICE_SENSITIVITY) / 12
    lapses = cohort.in_force_count * lapse_rate_monthly

    reserve_per_policy = cohort.reserve_balance / cohort.in_force_count if cohort.in_force_count > 0 else 0.0
    death_reserve_release = deaths * reserve_per_policy
    surrender_payout = lapses * reserve_per_policy

    credited_rate_monthly = portfolio_return_monthly * product.credited_rate_spread
    reserve_balance_next = (
        cohort.reserve_balance
        + premium * product.reserve_accrual_ratio
        - surrender_payout
        - death_reserve_release
        + cohort.reserve_balance * credited_rate_monthly
    )

    in_force_next = cohort.in_force_count - deaths - lapses
    flows = CohortFlows(premium_income=premium, death_claims=death_claims, surrender_payouts=surrender_payout)

    new_duration = duration_turns + 1
    if product.maturity_turns is not None and new_duration >= product.maturity_turns:
        flows.maturity_payouts = reserve_balance_next
        return None, flows

    if in_force_next <= 0.01:
        return None, flows

    updated = CohortState(
        product=cohort.product,
        channel=cohort.channel,
        issue_turn=cohort.issue_turn,
        in_force_count=in_force_next,
        unit_size=cohort.unit_size,
        reserve_balance=reserve_balance_next,
    )
    return updated, flows
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd backend && pytest tests/engine/test_cohorts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/cohorts.py backend/tests/engine/test_cohorts.py
git commit -m "feat: add cohort decrement, reserve rollforward, and maturity"
```

---

## Task 6: Finance — asset returns, rebalancing, snapshot (spec 6.4, 6.5)

**Files:**
- Create: `backend/app/engine/finance.py`
- Create: `backend/tests/engine/test_finance.py`

**Interfaces:**
- Consumes: `AssetBalances`, `MarketState`, `FinancialSnapshot`, `GameStatus` from `app.engine.types`; `deposit_monthly_return`, `bond_monthly_return`, `stock_monthly_return` from `app.engine.market`; `OPEX_BASE` from `app.engine.config`.
- Produces: `investment_income_and_returns(assets, market) -> tuple[float, AssetBalances]`, `invest_net_cashflow(assets_after_returns, to_invest, allocation) -> AssetBalances`, `compute_opex(total_in_force) -> float`, `compute_snapshot(...) -> FinancialSnapshot` in `app.engine.finance`.

- [ ] **Step 1: Write the failing test**

`backend/tests/engine/test_finance.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/engine/test_finance.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.finance'`

- [ ] **Step 3: Implement finance.py**

`backend/app/engine/finance.py`:
```python
import math

from .config import OPEX_BASE
from .market import bond_monthly_return, deposit_monthly_return, stock_monthly_return
from .types import AssetBalances, FinancialSnapshot, GameStatus, MarketState


def investment_income_and_returns(assets: AssetBalances, market: MarketState) -> tuple[float, AssetBalances]:
    deposit_ret = deposit_monthly_return(market)
    bond_ret = bond_monthly_return(market)
    stock_ret = stock_monthly_return(market)

    income = assets.deposit * deposit_ret + assets.bond * bond_ret + assets.stock * stock_ret
    grown = AssetBalances(
        deposit=assets.deposit * (1 + deposit_ret),
        bond=assets.bond * (1 + bond_ret),
        stock=assets.stock * (1 + stock_ret),
    )
    return income, grown


def invest_net_cashflow(assets_after_returns: AssetBalances, to_invest: float, allocation: dict[str, float]) -> AssetBalances:
    if to_invest >= 0:
        return AssetBalances(
            deposit=assets_after_returns.deposit + allocation["deposit"] * to_invest,
            bond=assets_after_returns.bond + allocation["bond"] * to_invest,
            stock=assets_after_returns.stock + allocation["stock"] * to_invest,
        )

    total = assets_after_returns.total
    if total <= 0:
        return AssetBalances(deposit=0.0, bond=0.0, stock=0.0)

    return AssetBalances(
        deposit=max(0.0, assets_after_returns.deposit + (assets_after_returns.deposit / total) * to_invest),
        bond=max(0.0, assets_after_returns.bond + (assets_after_returns.bond / total) * to_invest),
        stock=max(0.0, assets_after_returns.stock + (assets_after_returns.stock / total) * to_invest),
    )


def compute_opex(total_in_force: float) -> float:
    return OPEX_BASE * (1 + 0.02 * math.log(1 + total_in_force))


def compute_snapshot(
    turn: int,
    premium_income: float,
    investment_income: float,
    death_claims: float,
    surrender_payouts: float,
    maturity_payouts: float,
    commission_expense: float,
    marketing_expense: float,
    opex: float,
    reserve_change: float,
    equity_start: float,
    dividend_payout: float,
    assets: AssetBalances,
    total_reserve: float,
) -> FinancialSnapshot:
    net_income = (
        premium_income
        + investment_income
        - death_claims
        - surrender_payouts
        - maturity_payouts
        - commission_expense
        - marketing_expense
        - opex
        - reserve_change
    )
    equity = equity_start + net_income - dividend_payout
    status = GameStatus.BANKRUPT if equity <= 0 else GameStatus.RUNNING

    return FinancialSnapshot(
        turn=turn,
        premium_income=premium_income,
        investment_income=investment_income,
        death_claims=death_claims,
        surrender_payouts=surrender_payouts,
        maturity_payouts=maturity_payouts,
        commission_expense=commission_expense,
        marketing_expense=marketing_expense,
        opex=opex,
        reserve_change=reserve_change,
        net_income=net_income,
        deposit_balance=assets.deposit,
        bond_balance=assets.bond,
        stock_balance=assets.stock,
        total_reserve=total_reserve,
        equity=equity,
        status=status,
    )
```

Note: `compute_snapshot` only ever returns `RUNNING` or `BANKRUPT` — `COMPLETED` is decided by the turn orchestrator (Task 7) once it knows the current turn number relative to `GAME_LENGTH_TURNS`, which `compute_snapshot` does not receive.

- [ ] **Step 4: Run test, verify it passes**

Run: `cd backend && pytest tests/engine/test_finance.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/finance.py backend/tests/engine/test_finance.py
git commit -m "feat: add investment returns, rebalancing, and snapshot computation"
```

---

## Task 7: Turn orchestrator (integration)

**Files:**
- Create: `backend/app/engine/turn.py`
- Create: `backend/tests/engine/test_turn.py`

**Interfaces:**
- Consumes: everything from Tasks 2–6 (`app.engine.types`, `app.engine.config`, `app.engine.market`, `app.engine.products`, `app.engine.cohorts`, `app.engine.finance`).
- Produces: `run_turn(turn: int, cohorts: list[CohortState], market_state: MarketState, assets: AssetBalances, equity: float, decision: Decision, rng: np.random.Generator) -> TurnResult` in `app.engine.turn`. This is the function the persistence layer (Task 8) calls.

- [ ] **Step 1: Write the failing test**

`backend/tests/engine/test_turn.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/engine/test_turn.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.turn'`

- [ ] **Step 3: Implement turn.py**

`backend/app/engine/turn.py`:
```python
import numpy as np

from .cohorts import step_cohort
from .config import DEFAULT_PRODUCT_CONFIGS, GAME_LENGTH_TURNS
from .finance import compute_opex, compute_snapshot, invest_net_cashflow, investment_income_and_returns
from .market import advance_market_state
from .products import compute_new_business
from .types import AssetBalances, CohortState, Decision, GameStatus, MarketState, TurnResult


def run_turn(
    turn: int,
    cohorts: list[CohortState],
    market_state: MarketState,
    assets: AssetBalances,
    equity: float,
    decision: Decision,
    rng: np.random.Generator,
) -> TurnResult:
    new_market = advance_market_state(market_state, rng)
    next_turn = new_market.turn

    assets_start_total = assets.total
    investment_income, assets_after_returns = investment_income_and_returns(assets, new_market)
    portfolio_return_monthly = investment_income / assets_start_total if assets_start_total > 0 else 0.0

    reserve_start_total = sum(c.reserve_balance for c in cohorts)

    working_cohorts = list(cohorts)
    for product, channel, count in compute_new_business(decision):
        if count > 0:
            working_cohorts.append(
                CohortState(
                    product=product,
                    channel=channel,
                    issue_turn=next_turn,
                    in_force_count=float(count),
                    unit_size=DEFAULT_PRODUCT_CONFIGS[product].unit_size,
                    reserve_balance=0.0,
                )
            )

    updated_cohorts: list[CohortState] = []
    premium_income = death_claims = surrender_payouts = maturity_payouts = commission_expense = 0.0
    for cohort in working_cohorts:
        is_new = cohort.issue_turn == next_turn
        updated, flows = step_cohort(cohort, decision, next_turn, portfolio_return_monthly)
        premium_income += flows.premium_income
        death_claims += flows.death_claims
        surrender_payouts += flows.surrender_payouts
        maturity_payouts += flows.maturity_payouts
        if is_new:
            commission_expense += flows.premium_income * decision.commission_rate[cohort.channel]
        if updated is not None:
            updated_cohorts.append(updated)

    reserve_end_total = sum(c.reserve_balance for c in updated_cohorts)
    reserve_change = reserve_end_total - reserve_start_total

    marketing_expense = sum(decision.marketing_spend.values())
    total_in_force = sum(c.in_force_count for c in updated_cohorts)
    opex = compute_opex(total_in_force)

    net_cashflow = (
        premium_income
        - death_claims
        - surrender_payouts
        - maturity_payouts
        - commission_expense
        - marketing_expense
        - opex
    )
    to_invest = net_cashflow - decision.dividend_payout
    assets_final = invest_net_cashflow(assets_after_returns, to_invest, decision.asset_allocation)

    snapshot = compute_snapshot(
        turn=next_turn,
        premium_income=premium_income,
        investment_income=investment_income,
        death_claims=death_claims,
        surrender_payouts=surrender_payouts,
        maturity_payouts=maturity_payouts,
        commission_expense=commission_expense,
        marketing_expense=marketing_expense,
        opex=opex,
        reserve_change=reserve_change,
        equity_start=equity,
        dividend_payout=decision.dividend_payout,
        assets=assets_final,
        total_reserve=reserve_end_total,
    )
    if snapshot.status == GameStatus.RUNNING and next_turn >= GAME_LENGTH_TURNS:
        snapshot.status = GameStatus.COMPLETED

    return TurnResult(cohorts=updated_cohorts, market_state=new_market, assets=assets_final, snapshot=snapshot)
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd backend && pytest tests/engine/test_turn.py -v`
Expected: PASS

- [ ] **Step 5: Run the full engine test suite**

Run: `cd backend && pytest tests/engine -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/engine/turn.py backend/tests/engine/test_turn.py
git commit -m "feat: add turn orchestrator tying the simulation engine together"
```

---

## Task 8: Persistence layer (SQLModel + repository)

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/db.py`
- Create: `backend/app/repository.py`
- Create: `backend/tests/test_repository.py`

**Interfaces:**
- Consumes: `app.engine.types` dataclasses/enums; `app.engine.turn.run_turn`; `app.engine.config.LONG_RUN_RATE`.
- Produces: SQLModel tables `GameRow`, `CohortRow`, `MarketStateRow`, `DecisionRow`, `FinancialSnapshotRow` in `app.models`; `engine`, `init_db()`, `get_session()` in `app.db`; `create_game(session, initial_capital, rng_seed) -> GameRow` and `apply_turn(session, game_id, decision: Decision) -> FinancialSnapshotRow` in `app.repository` (used by the API layer in Tasks 9–10).

- [ ] **Step 1: Write the failing test**

`backend/tests/test_repository.py`:
```python
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.engine.types import ChannelCode, Decision, ProductCode
from app.models import GameRow
from app.repository import apply_turn, create_game


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def base_decision() -> Decision:
    return Decision(
        pricing_multiplier={ProductCode.WHOLE_LIFE: 1.0, ProductCode.SAVINGS: 1.0},
        underwriting_strictness={ProductCode.WHOLE_LIFE: 0.3, ProductCode.SAVINGS: 0.0},
        commission_rate={ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 0.45},
        marketing_spend={ChannelCode.CAPTIVE: 10_000_000, ChannelCode.GA: 15_000_000},
        asset_allocation={"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        dividend_payout=0.0,
    )


def test_create_game_seeds_initial_snapshot():
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)

    assert game.id is not None
    assert game.current_turn == 0
    assert game.status == "running"


def test_apply_turn_persists_snapshot_and_advances_game():
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)

    snapshot = apply_turn(session, game.id, base_decision())

    assert snapshot.turn == 1
    assert snapshot.status == "running"
    assert snapshot.premium_income == pytest.approx(10121850.0)
    refreshed = session.get(GameRow, game.id)
    assert refreshed.current_turn == 1


def test_apply_turn_rejects_finished_game():
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)
    game.status = "bankrupt"
    session.add(game)
    session.commit()

    with pytest.raises(ValueError):
        apply_turn(session, game.id, base_decision())
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/test_repository.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models'`

- [ ] **Step 3: Implement models.py**

`backend/app/models.py`:
```python
from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GameRow(SQLModel, table=True):
    __tablename__ = "games"

    id: int | None = Field(default=None, primary_key=True)
    rng_seed: int
    initial_capital: float
    current_turn: int
    status: str
    created_at: datetime = Field(default_factory=_utcnow)


class CohortRow(SQLModel, table=True):
    __tablename__ = "cohorts"

    id: int | None = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id", index=True)
    product: str
    channel: str
    issue_turn: int
    in_force_count: float
    unit_size: float
    reserve_balance: float


class MarketStateRow(SQLModel, table=True):
    __tablename__ = "market_states"

    id: int | None = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id", index=True)
    turn: int
    interest_rate: float
    stock_regime: str
    stock_return_realized: float | None = None


class DecisionRow(SQLModel, table=True):
    __tablename__ = "decisions"

    id: int | None = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id", index=True)
    turn: int
    pricing_multiplier: dict = Field(sa_column=Column(JSON))
    underwriting_strictness: dict = Field(sa_column=Column(JSON))
    commission_rate: dict = Field(sa_column=Column(JSON))
    marketing_spend: dict = Field(sa_column=Column(JSON))
    asset_allocation: dict = Field(sa_column=Column(JSON))
    dividend_payout: float


class FinancialSnapshotRow(SQLModel, table=True):
    __tablename__ = "financial_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id", index=True)
    turn: int
    premium_income: float
    investment_income: float
    death_claims: float
    surrender_payouts: float
    maturity_payouts: float
    commission_expense: float
    marketing_expense: float
    opex: float
    reserve_change: float
    net_income: float
    deposit_balance: float
    bond_balance: float
    stock_balance: float
    total_reserve: float
    equity: float
    status: str
```

- [ ] **Step 4: Implement db.py**

`backend/app/db.py`:
```python
from pathlib import Path
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "simulator.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
```

- [ ] **Step 5: Implement repository.py**

`backend/app/repository.py`:
```python
import numpy as np
from sqlmodel import Session, select

from .engine.config import LONG_RUN_RATE
from .engine.turn import run_turn
from .engine.types import (
    AssetBalances,
    ChannelCode,
    CohortState,
    Decision,
    GameStatus,
    MarketState,
    ProductCode,
    StockRegime,
)
from .models import CohortRow, DecisionRow, FinancialSnapshotRow, GameRow, MarketStateRow


def create_game(session: Session, initial_capital: float, rng_seed: int) -> GameRow:
    game = GameRow(rng_seed=rng_seed, initial_capital=initial_capital, current_turn=0, status=GameStatus.RUNNING.value)
    session.add(game)
    session.commit()
    session.refresh(game)

    session.add(
        MarketStateRow(
            game_id=game.id,
            turn=0,
            interest_rate=LONG_RUN_RATE,
            stock_regime=StockRegime.NORMAL.value,
            stock_return_realized=None,
        )
    )
    session.add(
        FinancialSnapshotRow(
            game_id=game.id,
            turn=0,
            premium_income=0.0,
            investment_income=0.0,
            death_claims=0.0,
            surrender_payouts=0.0,
            maturity_payouts=0.0,
            commission_expense=0.0,
            marketing_expense=0.0,
            opex=0.0,
            reserve_change=0.0,
            net_income=0.0,
            deposit_balance=initial_capital,
            bond_balance=0.0,
            stock_balance=0.0,
            total_reserve=0.0,
            equity=initial_capital,
            status=GameStatus.RUNNING.value,
        )
    )
    session.commit()
    return game


def latest_market_state(session: Session, game_id: int) -> MarketState:
    row = session.exec(
        select(MarketStateRow).where(MarketStateRow.game_id == game_id).order_by(MarketStateRow.turn.desc())
    ).first()
    return MarketState(
        turn=row.turn,
        interest_rate=row.interest_rate,
        stock_regime=StockRegime(row.stock_regime),
        stock_return_realized=row.stock_return_realized,
    )


def latest_snapshot(session: Session, game_id: int) -> FinancialSnapshotRow:
    return session.exec(
        select(FinancialSnapshotRow)
        .where(FinancialSnapshotRow.game_id == game_id)
        .order_by(FinancialSnapshotRow.turn.desc())
    ).first()


def active_cohorts(session: Session, game_id: int) -> list[CohortState]:
    rows = session.exec(select(CohortRow).where(CohortRow.game_id == game_id)).all()
    return [
        CohortState(
            product=ProductCode(row.product),
            channel=ChannelCode(row.channel),
            issue_turn=row.issue_turn,
            in_force_count=row.in_force_count,
            unit_size=row.unit_size,
            reserve_balance=row.reserve_balance,
        )
        for row in rows
    ]


def apply_turn(session: Session, game_id: int, decision: Decision) -> FinancialSnapshotRow:
    game = session.get(GameRow, game_id)
    if game.status != GameStatus.RUNNING.value:
        raise ValueError(f"game {game_id} is not running (status={game.status})")

    market_state = latest_market_state(session, game_id)
    snapshot = latest_snapshot(session, game_id)
    assets = AssetBalances(deposit=snapshot.deposit_balance, bond=snapshot.bond_balance, stock=snapshot.stock_balance)
    cohorts = active_cohorts(session, game_id)

    rng = np.random.default_rng(game.rng_seed + game.current_turn)
    result = run_turn(game.current_turn, cohorts, market_state, assets, snapshot.equity, decision, rng)

    session.add(
        DecisionRow(
            game_id=game_id,
            turn=result.snapshot.turn,
            pricing_multiplier={k.value: v for k, v in decision.pricing_multiplier.items()},
            underwriting_strictness={k.value: v for k, v in decision.underwriting_strictness.items()},
            commission_rate={k.value: v for k, v in decision.commission_rate.items()},
            marketing_spend={k.value: v for k, v in decision.marketing_spend.items()},
            asset_allocation=decision.asset_allocation,
            dividend_payout=decision.dividend_payout,
        )
    )

    for row in session.exec(select(CohortRow).where(CohortRow.game_id == game_id)).all():
        session.delete(row)
    for cohort in result.cohorts:
        session.add(
            CohortRow(
                game_id=game_id,
                product=cohort.product.value,
                channel=cohort.channel.value,
                issue_turn=cohort.issue_turn,
                in_force_count=cohort.in_force_count,
                unit_size=cohort.unit_size,
                reserve_balance=cohort.reserve_balance,
            )
        )

    session.add(
        MarketStateRow(
            game_id=game_id,
            turn=result.market_state.turn,
            interest_rate=result.market_state.interest_rate,
            stock_regime=result.market_state.stock_regime.value,
            stock_return_realized=result.market_state.stock_return_realized,
        )
    )

    snapshot_row = FinancialSnapshotRow(
        game_id=game_id,
        turn=result.snapshot.turn,
        premium_income=result.snapshot.premium_income,
        investment_income=result.snapshot.investment_income,
        death_claims=result.snapshot.death_claims,
        surrender_payouts=result.snapshot.surrender_payouts,
        maturity_payouts=result.snapshot.maturity_payouts,
        commission_expense=result.snapshot.commission_expense,
        marketing_expense=result.snapshot.marketing_expense,
        opex=result.snapshot.opex,
        reserve_change=result.snapshot.reserve_change,
        net_income=result.snapshot.net_income,
        deposit_balance=result.snapshot.deposit_balance,
        bond_balance=result.snapshot.bond_balance,
        stock_balance=result.snapshot.stock_balance,
        total_reserve=result.snapshot.total_reserve,
        equity=result.snapshot.equity,
        status=result.snapshot.status.value,
    )
    session.add(snapshot_row)

    game.current_turn = result.snapshot.turn
    game.status = result.snapshot.status.value
    session.add(game)

    session.commit()
    session.refresh(snapshot_row)
    return snapshot_row
```

- [ ] **Step 6: Run test, verify it passes**

Run: `cd backend && pytest tests/test_repository.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models.py backend/app/db.py backend/app/repository.py backend/tests/test_repository.py
git commit -m "feat: add SQLModel persistence layer and turn repository"
```

---

## Task 9: API — game creation, listing, config

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/games.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_api_games_crud.py`

**Interfaces:**
- Consumes: `app.repository`, `app.db.get_session`, `app.models`, `app.engine.config.DEFAULT_PRODUCT_CONFIGS`/`DEFAULT_CHANNEL_CONFIGS`.
- Produces: `router` (FastAPI `APIRouter`) mounted at `/games` in `app.api.games`, included by `app.main.app`. Pydantic schemas `CreateGameRequest`, `GameSummary`, `SnapshotResponse`, `GameStateResponse`, `TurnRequest`, `ConfigResponse` in `app.schemas` (the `TurnRequest` shape is consumed again by Task 10).

- [ ] **Step 1: Write the failing test**

`backend/tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

`backend/tests/test_api_games_crud.py`:
```python
def test_create_and_get_game(client):
    response = client.post("/games", json={"initial_capital": 5_000_000_000, "rng_seed": 7})
    assert response.status_code == 200
    body = response.json()
    game_id = body["id"]
    assert body["current_turn"] == 0
    assert body["snapshot"]["equity"] == 5_000_000_000

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["id"] == game_id


def test_list_games(client):
    client.post("/games", json={})
    client.post("/games", json={})
    response = client.get("/games")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_config(client):
    created = client.post("/games", json={})
    game_id = created.json()["id"]
    response = client.get(f"/games/{game_id}/config")
    assert response.status_code == 200
    body = response.json()
    assert "whole_life" in body["products"]
    assert "captive" in body["channels"]


def test_get_missing_game_returns_404(client):
    response = client.get("/games/999")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/test_api_games_crud.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.schemas'` (or similar import error)

- [ ] **Step 3: Implement schemas.py**

`backend/app/schemas.py`:
```python
from pydantic import BaseModel


class CreateGameRequest(BaseModel):
    initial_capital: float = 10_000_000_000.0
    rng_seed: int | None = None


class GameSummary(BaseModel):
    id: int
    current_turn: int
    status: str


class SnapshotResponse(BaseModel):
    turn: int
    premium_income: float
    investment_income: float
    death_claims: float
    surrender_payouts: float
    maturity_payouts: float
    commission_expense: float
    marketing_expense: float
    opex: float
    reserve_change: float
    net_income: float
    deposit_balance: float
    bond_balance: float
    stock_balance: float
    total_reserve: float
    equity: float
    status: str


class GameStateResponse(BaseModel):
    id: int
    current_turn: int
    status: str
    snapshot: SnapshotResponse


class TurnRequest(BaseModel):
    pricing_multiplier: dict[str, float]
    underwriting_strictness: dict[str, float]
    commission_rate: dict[str, float]
    marketing_spend: dict[str, float]
    asset_allocation: dict[str, float]
    dividend_payout: float = 0.0


class ConfigResponse(BaseModel):
    products: dict
    channels: dict
```

- [ ] **Step 4: Implement api/games.py (create/list/get/config)**

`backend/app/api/__init__.py`: empty file.

`backend/app/api/games.py`:
```python
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .. import repository
from ..db import get_session
from ..engine.config import DEFAULT_CHANNEL_CONFIGS, DEFAULT_PRODUCT_CONFIGS
from ..models import FinancialSnapshotRow, GameRow
from ..schemas import ConfigResponse, CreateGameRequest, GameStateResponse, GameSummary, SnapshotResponse

router = APIRouter(prefix="/games", tags=["games"])


def _snapshot_to_schema(row: FinancialSnapshotRow) -> SnapshotResponse:
    return SnapshotResponse(**row.model_dump(exclude={"id", "game_id"}))


def _game_state(session: Session, game: GameRow) -> GameStateResponse:
    snapshot = repository.latest_snapshot(session, game.id)
    return GameStateResponse(
        id=game.id, current_turn=game.current_turn, status=game.status, snapshot=_snapshot_to_schema(snapshot)
    )


def _config_dict(cfg) -> dict:
    data = vars(cfg).copy()
    data["code"] = data["code"].value
    return data


@router.post("", response_model=GameStateResponse)
def create_game(payload: CreateGameRequest, session: Session = Depends(get_session)) -> GameStateResponse:
    seed = payload.rng_seed if payload.rng_seed is not None else random.randint(0, 2**31 - 1)
    game = repository.create_game(session, payload.initial_capital, seed)
    return _game_state(session, game)


@router.get("", response_model=list[GameSummary])
def list_games(session: Session = Depends(get_session)) -> list[GameSummary]:
    games = session.exec(select(GameRow)).all()
    return [GameSummary(id=g.id, current_turn=g.current_turn, status=g.status) for g in games]


@router.get("/{game_id}", response_model=GameStateResponse)
def get_game(game_id: int, session: Session = Depends(get_session)) -> GameStateResponse:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    return _game_state(session, game)


@router.get("/{game_id}/config", response_model=ConfigResponse)
def get_config(game_id: int, session: Session = Depends(get_session)) -> ConfigResponse:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    return ConfigResponse(
        products={code.value: _config_dict(cfg) for code, cfg in DEFAULT_PRODUCT_CONFIGS.items()},
        channels={code.value: _config_dict(cfg) for code, cfg in DEFAULT_CHANNEL_CONFIGS.items()},
    )
```

- [ ] **Step 5: Wire the router and DB startup into main.py**

`backend/app/main.py` (replace entirely):
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.games import router as games_router
from .db import init_db

app = FastAPI(title="Insurance Company Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 6: Run test, verify it passes**

Run: `cd backend && pytest tests/test_api_games_crud.py -v`
Expected: PASS

- [ ] **Step 7: Run full backend suite so far**

Run: `cd backend && pytest -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas.py backend/app/api/__init__.py backend/app/api/games.py backend/app/main.py backend/tests/conftest.py backend/tests/test_api_games_crud.py
git commit -m "feat: add game creation, listing, and config API endpoints"
```

---

## Task 10: API — turn submission, history, delete

**Files:**
- Modify: `backend/app/api/games.py`
- Create: `backend/tests/test_api_turn.py`

**Interfaces:**
- Consumes: `repository.apply_turn`, `TurnRequest` from Task 9, `ProductCode`/`ChannelCode` from `app.engine.types`.
- Produces: `POST /games/{game_id}/turn`, `GET /games/{game_id}/history`, `DELETE /games/{game_id}` added to the existing `router`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_api_turn.py`:
```python
import pytest


def turn_payload():
    return {
        "pricing_multiplier": {"whole_life": 1.0, "savings": 1.0},
        "underwriting_strictness": {"whole_life": 0.3, "savings": 0.0},
        "commission_rate": {"captive": 0.30, "ga": 0.45},
        "marketing_spend": {"captive": 10_000_000, "ga": 15_000_000},
        "asset_allocation": {"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        "dividend_payout": 0.0,
    }


def test_submit_turn_advances_game_and_matches_engine_reference(client):
    create = client.post("/games", json={"initial_capital": 10_000_000_000, "rng_seed": 42})
    game_id = create.json()["id"]

    response = client.post(f"/games/{game_id}/turn", json=turn_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["current_turn"] == 1
    assert body["snapshot"]["turn"] == 1
    assert body["snapshot"]["premium_income"] == pytest.approx(10121850.0)
    assert body["snapshot"]["equity"] == pytest.approx(10087572918.033474)

    history = client.get(f"/games/{game_id}/history")
    assert history.status_code == 200
    assert [row["turn"] for row in history.json()] == [0, 1]


def test_submit_turn_on_missing_game_returns_404(client):
    response = client.post("/games/999/turn", json=turn_payload())
    assert response.status_code == 404


def test_delete_game_removes_it(client):
    created = client.post("/games", json={})
    game_id = created.json()["id"]

    response = client.delete(f"/games/{game_id}")
    assert response.status_code == 200
    assert client.get(f"/games/{game_id}").status_code == 404
```

- [ ] **Step 2: Run test, verify it fails**

Run: `cd backend && pytest tests/test_api_turn.py -v`
Expected: FAIL — 404/405 on `/turn`, `/history`, and `DELETE` (routes don't exist yet)

- [ ] **Step 3: Add turn/history/delete endpoints**

Append to `backend/app/api/games.py` (add these imports at the top alongside the existing ones: `from ..engine.types import ChannelCode, Decision, ProductCode`, `from ..models import CohortRow, MarketStateRow, DecisionRow`, `from ..schemas import TurnRequest`; add this function and these three routes at the end of the file):
```python
def _decision_from_request(payload: TurnRequest) -> Decision:
    return Decision(
        pricing_multiplier={ProductCode(k): v for k, v in payload.pricing_multiplier.items()},
        underwriting_strictness={ProductCode(k): v for k, v in payload.underwriting_strictness.items()},
        commission_rate={ChannelCode(k): v for k, v in payload.commission_rate.items()},
        marketing_spend={ChannelCode(k): v for k, v in payload.marketing_spend.items()},
        asset_allocation=payload.asset_allocation,
        dividend_payout=payload.dividend_payout,
    )


@router.get("/{game_id}/history", response_model=list[SnapshotResponse])
def get_history(game_id: int, session: Session = Depends(get_session)) -> list[SnapshotResponse]:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    rows = session.exec(
        select(FinancialSnapshotRow).where(FinancialSnapshotRow.game_id == game_id).order_by(FinancialSnapshotRow.turn)
    ).all()
    return [_snapshot_to_schema(row) for row in rows]


@router.post("/{game_id}/turn", response_model=GameStateResponse)
def submit_turn(game_id: int, payload: TurnRequest, session: Session = Depends(get_session)) -> GameStateResponse:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    try:
        repository.apply_turn(session, game_id, _decision_from_request(payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    session.refresh(game)
    return _game_state(session, game)


@router.delete("/{game_id}")
def delete_game(game_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    for model in (CohortRow, MarketStateRow, DecisionRow, FinancialSnapshotRow):
        for row in session.exec(select(model).where(model.game_id == game_id)).all():
            session.delete(row)
    session.delete(game)
    session.commit()
    return {"deleted": True}
```

- [ ] **Step 4: Run test, verify it passes**

Run: `cd backend && pytest tests/test_api_turn.py -v`
Expected: PASS

- [ ] **Step 5: Run the full backend suite**

Run: `cd backend && pytest -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/games.py backend/tests/test_api_turn.py
git commit -m "feat: add turn submission, history, and delete API endpoints"
```

---

## Task 11: Frontend scaffolding + New Game screen

**Files:**
- Create: `frontend/` (via Vite scaffold — package.json, vite.config.js, index.html, src/main.js, src/App.vue)
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/views/NewGameView.vue`
- Create: `frontend/src/views/DashboardView.vue` (placeholder, replaced fully in Task 12)
- Modify: `frontend/vite.config.js`, `frontend/src/style.css` (Tailwind wiring)

**Interfaces:**
- Consumes: backend API from Tasks 9–10 (`POST /games`, `GET /games/:id`).
- Produces: `apiClient`, `createGame`, `getGame`, `getHistory`, `getConfig`, `submitTurn`, `deleteGame` in `src/api/client.js` (consumed by the Pinia store in Task 12).

- [ ] **Step 1: Scaffold the Vite project and install dependencies**

Run from the repo root:
```bash
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install pinia vue-router axios chart.js vue-chartjs
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 2: Wire Tailwind CSS v4 into Vite**

`frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: { port: 5173 },
})
```

`frontend/src/style.css` (replace generated contents entirely):
```css
@import "tailwindcss";
```

- [ ] **Step 3: Add the API client**

`frontend/src/api/client.js`:
```js
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

export async function createGame(initialCapital, rngSeed) {
  const response = await apiClient.post('/games', {
    initial_capital: initialCapital,
    rng_seed: rngSeed ?? null,
  })
  return response.data
}

export async function getGame(gameId) {
  const response = await apiClient.get(`/games/${gameId}`)
  return response.data
}

export async function getHistory(gameId) {
  const response = await apiClient.get(`/games/${gameId}/history`)
  return response.data
}

export async function getConfig(gameId) {
  const response = await apiClient.get(`/games/${gameId}/config`)
  return response.data
}

export async function submitTurn(gameId, decision) {
  const response = await apiClient.post(`/games/${gameId}/turn`, decision)
  return response.data
}

export async function deleteGame(gameId) {
  await apiClient.delete(`/games/${gameId}`)
}
```

- [ ] **Step 4: Add router, NewGameView, and a placeholder DashboardView**

`frontend/src/views/NewGameView.vue`:
```vue
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createGame } from '../api/client'

const router = useRouter()
const initialCapital = ref(10000000000)
const rngSeed = ref('')
const isCreating = ref(false)
const errorMessage = ref('')

async function handleCreate() {
  isCreating.value = true
  errorMessage.value = ''
  try {
    const seed = rngSeed.value === '' ? null : Number(rngSeed.value)
    const game = await createGame(Number(initialCapital.value), seed)
    router.push(`/games/${game.id}`)
  } catch (err) {
    errorMessage.value = '게임 생성에 실패했습니다.'
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-24 max-w-md rounded-lg border border-slate-200 p-8 shadow-sm">
    <h1 class="mb-6 text-2xl font-bold text-slate-800">보험회사 운영 시뮬레이션</h1>
    <label class="mb-1 block text-sm font-medium text-slate-600">초기 자본</label>
    <input v-model="initialCapital" type="number" class="mb-4 w-full rounded border border-slate-300 px-3 py-2" />
    <label class="mb-1 block text-sm font-medium text-slate-600">시드 (선택)</label>
    <input v-model="rngSeed" type="number" placeholder="비워두면 무작위" class="mb-6 w-full rounded border border-slate-300 px-3 py-2" />
    <button
      class="w-full rounded bg-slate-800 px-4 py-2 font-semibold text-white disabled:opacity-50"
      :disabled="isCreating"
      @click="handleCreate"
    >
      새 게임 시작
    </button>
    <p v-if="errorMessage" class="mt-4 text-sm text-red-600">{{ errorMessage }}</p>
  </div>
</template>
```

`frontend/src/views/DashboardView.vue` (placeholder for now):
```vue
<script setup>
defineProps({ id: String })
</script>

<template>
  <div class="p-8">Game #{{ id }} loaded (dashboard under construction)</div>
</template>
```

`frontend/src/main.js` (replace generated contents entirely):
```js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import NewGameView from './views/NewGameView.vue'
import DashboardView from './views/DashboardView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: NewGameView },
    { path: '/games/:id', component: DashboardView, props: true },
  ],
})

createApp(App).use(createPinia()).use(router).mount('#app')
```

`frontend/src/App.vue` (replace generated contents entirely):
```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 5: Manually verify the New Game flow end to end**

Run in two terminals:
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
```
```bash
cd frontend && npm run dev
```
Open `http://localhost:5173`, enter an initial capital, click "새 게임 시작", and confirm the browser navigates to `/games/{id}` showing "Game #{id} loaded".

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat: scaffold Vue frontend with new-game flow"
```

---

## Task 12: Dashboard — store, KPI cards, history chart

**Files:**
- Create: `frontend/src/stores/gameStore.js`
- Create: `frontend/src/components/KpiCards.vue`
- Create: `frontend/src/components/HistoryCharts.vue`
- Modify: `frontend/src/views/DashboardView.vue` (replace placeholder)

**Interfaces:**
- Consumes: `getGame`, `getHistory`, `getConfig`, `submitTurn` from `src/api/client.js`.
- Produces: `useGameStore()` Pinia store exposing `state: { gameId, currentTurn, status, snapshot, history, config }` and `actions: { load(gameId), advanceTurn(decision) }` (consumed by Task 13's DecisionPanel/TurnControl wiring).

- [ ] **Step 1: Add the Pinia store**

`frontend/src/stores/gameStore.js`:
```js
import { defineStore } from 'pinia'
import { getConfig, getGame, getHistory, submitTurn } from '../api/client'

export const useGameStore = defineStore('game', {
  state: () => ({
    gameId: null,
    currentTurn: 0,
    status: 'running',
    snapshot: null,
    history: [],
    config: null,
  }),
  actions: {
    async load(gameId) {
      this.gameId = gameId
      const [game, history, config] = await Promise.all([
        getGame(gameId),
        getHistory(gameId),
        getConfig(gameId),
      ])
      this.currentTurn = game.current_turn
      this.status = game.status
      this.snapshot = game.snapshot
      this.history = history
      this.config = config
    },
    async advanceTurn(decision) {
      const game = await submitTurn(this.gameId, decision)
      this.currentTurn = game.current_turn
      this.status = game.status
      this.snapshot = game.snapshot
      this.history.push(game.snapshot)
    },
  },
})
```

- [ ] **Step 2: Add KpiCards.vue**

`frontend/src/components/KpiCards.vue`:
```vue
<script setup>
defineProps({ snapshot: Object })

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
</script>

<template>
  <div class="grid grid-cols-3 gap-4">
    <div class="rounded border border-slate-200 p-4">
      <div class="text-sm text-slate-500">자본총계</div>
      <div class="text-xl font-bold">{{ formatWon(snapshot.equity) }}</div>
    </div>
    <div class="rounded border border-slate-200 p-4">
      <div class="text-sm text-slate-500">이번 턴 순이익</div>
      <div class="text-xl font-bold" :class="snapshot.net_income >= 0 ? 'text-emerald-600' : 'text-red-600'">
        {{ formatWon(snapshot.net_income) }}
      </div>
    </div>
    <div class="rounded border border-slate-200 p-4">
      <div class="text-sm text-slate-500">총 준비금</div>
      <div class="text-xl font-bold">{{ formatWon(snapshot.total_reserve) }}</div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Add HistoryCharts.vue**

`frontend/src/components/HistoryCharts.vue`:
```vue
<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({ history: Array })

const chartData = computed(() => ({
  labels: props.history.map((row) => row.turn),
  datasets: [
    { label: '자본총계', data: props.history.map((row) => row.equity), borderColor: '#1e293b', tension: 0.2 },
  ],
}))

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="h-64 rounded border border-slate-200 p-4">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
```

- [ ] **Step 4: Replace DashboardView.vue with the full KPI/chart view**

`frontend/src/views/DashboardView.vue` (replace entirely):
```vue
<script setup>
import { onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'
import KpiCards from '../components/KpiCards.vue'
import HistoryCharts from '../components/HistoryCharts.vue'

const props = defineProps({ id: String })
const store = useGameStore()

onMounted(() => store.load(Number(props.id)))
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-8">
    <h1 class="text-2xl font-bold text-slate-800">턴 {{ store.currentTurn }} / 120</h1>
    <KpiCards :snapshot="store.snapshot" />
    <HistoryCharts :history="store.history" />
  </div>
  <div v-else class="p-8 text-slate-500">불러오는 중...</div>
</template>
```

- [ ] **Step 5: Manually verify**

With both dev servers running, create a new game and confirm the dashboard shows "턴 0 / 120", a KPI card with 자본총계 equal to the initial capital entered, and a chart with a single point at turn 0.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/stores frontend/src/components/KpiCards.vue frontend/src/components/HistoryCharts.vue frontend/src/views/DashboardView.vue
git commit -m "feat: add game store, KPI cards, and history chart to dashboard"
```

---

## Task 13: Decision panel, turn loop, result screen

**Files:**
- Create: `frontend/src/components/DecisionPanel.vue`
- Create: `frontend/src/components/TurnControl.vue`
- Create: `frontend/src/views/ResultView.vue`
- Modify: `frontend/src/views/DashboardView.vue` (wire in decision panel + turn control + result redirect)
- Modify: `frontend/src/main.js` (add `/games/:id/result` route)

**Interfaces:**
- Consumes: `useGameStore` from Task 12.
- Produces: a fully playable turn loop — this is the last Phase 1 task.

- [ ] **Step 1: Add DecisionPanel.vue**

`frontend/src/components/DecisionPanel.vue`:
```vue
<script setup>
import { reactive } from 'vue'

const emit = defineEmits(['submit'])

const form = reactive({
  pricing_multiplier: { whole_life: 1.0, savings: 1.0 },
  underwriting_strictness: { whole_life: 0.3, savings: 0.0 },
  commission_rate: { captive: 0.3, ga: 0.45 },
  marketing_spend: { captive: 10000000, ga: 15000000 },
  asset_allocation: { deposit: 0.3, bond: 0.4, stock: 0.3 },
  dividend_payout: 0,
})

function handleSubmit() {
  emit('submit', JSON.parse(JSON.stringify(form)))
}
</script>

<template>
  <div class="space-y-4 rounded border border-slate-200 p-4">
    <div>
      <h2 class="mb-2 font-semibold">상품 가격 / 언더라이팅</h2>
      <div v-for="product in ['whole_life', 'savings']" :key="product" class="mb-2 grid grid-cols-3 items-center gap-2">
        <span class="text-sm">{{ product }}</span>
        <label class="text-xs">가격배수
          <input v-model.number="form.pricing_multiplier[product]" type="number" step="0.05" class="w-full rounded border px-2 py-1" />
        </label>
        <label class="text-xs">엄격도
          <input v-model.number="form.underwriting_strictness[product]" type="number" step="0.05" min="0" max="1" class="w-full rounded border px-2 py-1" />
        </label>
      </div>
    </div>
    <div>
      <h2 class="mb-2 font-semibold">채널</h2>
      <div v-for="channel in ['captive', 'ga']" :key="channel" class="mb-2 grid grid-cols-3 items-center gap-2">
        <span class="text-sm">{{ channel }}</span>
        <label class="text-xs">수수료율
          <input v-model.number="form.commission_rate[channel]" type="number" step="0.01" class="w-full rounded border px-2 py-1" />
        </label>
        <label class="text-xs">모집비
          <input v-model.number="form.marketing_spend[channel]" type="number" step="1000000" class="w-full rounded border px-2 py-1" />
        </label>
      </div>
    </div>
    <div>
      <h2 class="mb-2 font-semibold">자산배분 (합 1.0)</h2>
      <div class="grid grid-cols-3 gap-2">
        <label class="text-xs">예금 <input v-model.number="form.asset_allocation.deposit" type="number" step="0.05" class="w-full rounded border px-2 py-1" /></label>
        <label class="text-xs">채권 <input v-model.number="form.asset_allocation.bond" type="number" step="0.05" class="w-full rounded border px-2 py-1" /></label>
        <label class="text-xs">주식 <input v-model.number="form.asset_allocation.stock" type="number" step="0.05" class="w-full rounded border px-2 py-1" /></label>
      </div>
    </div>
    <label class="block text-sm">배당 지급액
      <input v-model.number="form.dividend_payout" type="number" step="1000000" class="w-full rounded border px-2 py-1" />
    </label>
    <button class="w-full rounded bg-slate-800 px-4 py-2 font-semibold text-white" @click="handleSubmit">
      턴 실행
    </button>
  </div>
</template>
```

- [ ] **Step 2: Add TurnControl.vue**

`frontend/src/components/TurnControl.vue`:
```vue
<script setup>
import { ref } from 'vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['run-turns'])
const autoTurns = ref(3)
</script>

<template>
  <div class="flex items-center gap-2 rounded border border-slate-200 p-4">
    <span class="text-sm text-slate-600">가장 최근 결정으로 자동 진행:</span>
    <input v-model.number="autoTurns" type="number" min="1" max="24" class="w-16 rounded border px-2 py-1" />
    <button
      class="rounded border border-slate-800 px-4 py-2 font-semibold text-slate-800 disabled:opacity-50"
      :disabled="disabled"
      @click="emit('run-turns', autoTurns)"
    >
      자동 진행
    </button>
  </div>
</template>
```

- [ ] **Step 3: Add ResultView.vue**

`frontend/src/views/ResultView.vue`:
```vue
<script setup>
import { onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'

const props = defineProps({ id: String })
const store = useGameStore()

onMounted(() => {
  if (store.gameId !== Number(props.id)) store.load(Number(props.id))
})
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto mt-24 max-w-md rounded-lg border border-slate-200 p-8 text-center shadow-sm">
    <h1 class="mb-4 text-2xl font-bold" :class="store.status === 'bankrupt' ? 'text-red-600' : 'text-emerald-600'">
      {{ store.status === 'bankrupt' ? '파산' : '경영 종료' }}
    </h1>
    <p class="mb-2 text-slate-600">최종 턴: {{ store.currentTurn }}</p>
    <p class="text-3xl font-bold">{{ new Intl.NumberFormat('ko-KR').format(Math.round(store.snapshot.equity)) }}원</p>
    <router-link to="/" class="mt-6 inline-block text-sm text-slate-500 underline">새 게임 시작</router-link>
  </div>
</template>
```

- [ ] **Step 4: Wire the result route into main.js**

`frontend/src/main.js` (add the import and route):
```js
import ResultView from './views/ResultView.vue'
```
```js
{ path: '/games/:id/result', component: ResultView, props: true },
```
(Add the import alongside the existing view imports, and the route object alongside the existing `/games/:id` route.)

- [ ] **Step 5: Wire DecisionPanel + TurnControl into DashboardView with the turn loop**

`frontend/src/views/DashboardView.vue` (replace entirely):
```vue
<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/gameStore'
import KpiCards from '../components/KpiCards.vue'
import HistoryCharts from '../components/HistoryCharts.vue'
import DecisionPanel from '../components/DecisionPanel.vue'
import TurnControl from '../components/TurnControl.vue'

const props = defineProps({ id: String })
const store = useGameStore()
const router = useRouter()
const lastDecision = ref(null)
const isBusy = ref(false)

onMounted(() => store.load(Number(props.id)))

async function handleDecisionSubmit(decision) {
  lastDecision.value = decision
  await runTurns(1)
}

async function runTurns(count) {
  if (!lastDecision.value || isBusy.value) return
  isBusy.value = true
  for (let i = 0; i < count; i++) {
    if (store.status !== 'running') break
    // eslint-disable-next-line no-await-in-loop
    await store.advanceTurn(lastDecision.value)
  }
  isBusy.value = false
  if (store.status !== 'running') {
    router.push(`/games/${props.id}/result`)
  }
}
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-8">
    <h1 class="text-2xl font-bold text-slate-800">턴 {{ store.currentTurn }} / 120</h1>
    <KpiCards :snapshot="store.snapshot" />
    <HistoryCharts :history="store.history" />
    <DecisionPanel @submit="handleDecisionSubmit" />
    <TurnControl :disabled="isBusy || store.status !== 'running'" @run-turns="runTurns" />
  </div>
  <div v-else class="p-8 text-slate-500">불러오는 중...</div>
</template>
```

- [ ] **Step 6: Manually verify the full turn loop**

With both dev servers running:
1. Create a new game.
2. Leave the DecisionPanel defaults and click "턴 실행" — confirm the turn counter advances to 1 and the KPI cards / chart update.
3. Set the auto-turn count to 5 and click "자동 진행" — confirm the turn counter advances to 6, one chart point per turn.
4. Keep advancing (manually or via autoplay) until either turn 120 is reached or the company goes bankrupt — confirm the app redirects to `/games/{id}/result` and shows the correct final equity and status (파산 vs 경영 종료).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/DecisionPanel.vue frontend/src/components/TurnControl.vue frontend/src/views/ResultView.vue frontend/src/views/DashboardView.vue frontend/src/main.js
git commit -m "feat: wire decision panel, turn loop, and result screen"
```

---

## Task 14: Containerize backend and frontend for podman-compose

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`
- Create: `docker-compose.yml` (repo root)

**Interfaces:**
- Consumes: `backend/pyproject.toml` (Task 1), `backend/app/db.py`'s `DB_PATH` (Task 8, resolves to `<app root>/data/simulator.db`), `frontend/package.json` (Task 11), `VITE_API_BASE_URL` env var read by `frontend/src/api/client.js` (Task 11).
- Produces: two buildable images and a `docker-compose.yml` that runs both with live-reload volume mounts, no new code interfaces (this is the last task).

- [ ] **Step 1: Add backend/Dockerfile**

`backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

`backend/.dockerignore`:
```
.venv
__pycache__
*.pyc
data
tests
.pytest_cache
```

- [ ] **Step 2: Verify the backend image builds and serves /health**

Run:
```bash
cd backend
podman build -t insurance-sim-backend .
podman run --rm -p 8000:8000 insurance-sim-backend &
sleep 2
curl -sf http://localhost:8000/health
```
Expected: `{"status":"ok"}`, then stop the container (`podman ps` → `podman stop <id>`).

- [ ] **Step 3: Add frontend/Dockerfile**

`frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

`frontend/.dockerignore`:
```
node_modules
dist
```

- [ ] **Step 4: Verify the frontend image builds and serves the dev server**

Run:
```bash
cd frontend
podman build -t insurance-sim-frontend .
podman run --rm -p 5173:5173 -e VITE_API_BASE_URL=http://localhost:8000 insurance-sim-frontend &
sleep 3
curl -sf http://localhost:5173 | head -c 200
```
Expected: HTML output containing `<div id="app">`, then stop the container.

- [ ] **Step 5: Add docker-compose.yml at the repo root**

`docker-compose.yml`:
```yaml
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app
      - backend-data:/app/data
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/index.html:/app/index.html
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  backend-data:
```

Note: `VITE_API_BASE_URL` points at `localhost:8000`, not the internal service name `backend`, because `frontend/src/api/client.js` runs in the player's browser (not inside the frontend container) — the browser can only reach the port published on the host.

- [ ] **Step 6: Verify the full stack with podman-compose**

Run:
```bash
podman-compose up --build -d
sleep 5
curl -sf http://localhost:8000/health
curl -sf http://localhost:5173 | head -c 200
```
Expected: both curls succeed. Then open `http://localhost:5173` in a browser, create a game, submit a turn, and confirm the KPI cards/chart update (same manual check as Task 13 Step 6, now running through containers). Tear down with:
```bash
podman-compose down
```

- [ ] **Step 7: Commit**

```bash
git add backend/Dockerfile backend/.dockerignore frontend/Dockerfile frontend/.dockerignore docker-compose.yml
git commit -m "feat: containerize backend and frontend for podman-compose"
```

---

## Post-implementation checklist

- [ ] `cd backend && pytest -v` — all backend tests pass
- [ ] Manual browser playthrough from new game to either turn 120 or bankruptcy completes without console errors
- [ ] `podman-compose up --build` serves both services and the same playthrough works through the containers
- [ ] `git log --oneline` shows one commit per task (14 commits) since this plan started
