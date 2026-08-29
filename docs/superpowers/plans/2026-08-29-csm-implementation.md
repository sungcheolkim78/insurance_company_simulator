# CSM (Contractual Service Margin) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce an IFRS17-inspired Contractual Service Margin (CSM) mechanic into the simulation engine — new-business future profit margin is deferred into a per-cohort liability at issuance and released into net income turn-by-turn (straight-line) instead of being recognized immediately, with onerous-contract loss recognition and full monitoring/statement visibility.

**Architecture:** New pure module `backend/app/engine/csm.py` provides two deterministic functions: `compute_csm_initial` (day-0 recognition, using a closed-form PV projection over a locked-in survivorship/discount schedule) and `step_csm_cohort` (per-turn interest accretion + straight-line release, with full release on cohort closure). These are wired into the existing cohort/turn pipeline (`cohorts.py`, `turn.py`, `finance.py`) without changing any existing cash-flow formula — `NetIncome` gets two new subtracted terms (`CSMChange`, `OnerousLoss`), and the balance sheet identity becomes `AssetsTotal = TotalReserve + TotalCSM + Equity`. Every new/changed field flows through `types.py` → `models.py`/`schemas.py`/`repository.py` → the two frontend components already showing financial data (`MonitoringPanel.vue`, `FinancialStatements.vue`).

**Tech Stack:** Python 3.11 / FastAPI / SQLModel (backend, pure-Python engine layer under `backend/app/engine/`), Vue 3 `<script setup>` / Pinia (frontend). Tests via pytest (`backend/.venv/bin/pytest`). Local verification via `podman-compose` (no other Docker/Podman commands without asking first — the dev DB volume was already reset once this session with the user's explicit sign-off; do the same before this task's schema change).

**Spec:** `docs/simulation/simulation_formulas.md` — §6.1 (CSM initial recognition & rollforward), §6.3 (P&L rows), §6.4 (balance sheet identity), §7.4 (new config constants), §8.6 (monitoring KPIs). Read §6.1 in full before starting Task 3.

## Global Constraints

- `backend/app/engine/` stays pure Python + numpy only — no FastAPI/SQLModel/DB imports (per `CLAUDE.md`).
- All engine functions must be deterministic given their inputs (no direct RNG calls inside `csm.py` — `compute_new_business`/`run_turn` already isolate randomness in `market.py`).
- New `CohortState`/`CohortFlows` fields must have defaults (`= 0.0` / `= 0`) so every existing call site (tests, `repository.py`) that doesn't yet know about CSM keeps compiling unchanged.
- Never invent or hand-wave a numeric test expectation — every assertion in this plan is either hand-computable (shown inline) or is produced by running a provided script and pasting the real output (matching this repo's existing test style, e.g. `test_run_turn_matches_reference_calculation`).
- Changing the DB schema again means the `podman-compose` dev volume (`insurance_company_simulator_backend-data`) needs to be recreated, exactly like earlier this session — **ask the user before deleting it** (do not assume standing approval carries over).

---

### Task 1: CSM config constants

**Files:**
- Modify: `backend/app/engine/config.py`

**Interfaces:**
- Produces: `CSM_RISK_ADJUSTMENT_COEF: float`, `CSM_WHOLE_LIFE_HORIZON_CAP_TURNS: int` — consumed by Task 3's `csm.py`.

- [ ] **Step 1: Add the two new constants**

At the end of `backend/app/engine/config.py`, after `GAME_LENGTH_TURNS = 120`, add:

```python
CSM_RISK_ADJUSTMENT_COEF = 0.05
CSM_WHOLE_LIFE_HORIZON_CAP_TURNS = 600
```

- [ ] **Step 2: Verify nothing broke**

Run: `cd backend && .venv/bin/pytest -q`
Expected: `33 passed` (same as before — this is an additive, unused-so-far change).

- [ ] **Step 3: Commit**

```bash
git add backend/app/engine/config.py
git commit -m "feat(csm): add CSM risk-adjustment and horizon-cap constants"
```

---

### Task 2: Extend engine dataclasses with CSM fields

**Files:**
- Modify: `backend/app/engine/types.py`

**Interfaces:**
- Produces: `CohortState.csm_balance/csm_locked_in_rate_monthly/csm_straight_line_release/csm_periods_remaining`, `CohortFlows.csm_release`, `FinancialSnapshot.total_csm/csm_change/csm_release/csm_new_business/onerous_loss` — consumed by Tasks 4-7.

- [ ] **Step 1: Add CSM fields to `CohortState`**

In `backend/app/engine/types.py`, find:

```python
@dataclass
class CohortState:
    product: ProductCode
    channel: ChannelCode
    issue_turn: int
    in_force_count: float
    unit_size: float
    reserve_balance: float
```

Replace with:

```python
@dataclass
class CohortState:
    product: ProductCode
    channel: ChannelCode
    issue_turn: int
    in_force_count: float
    unit_size: float
    reserve_balance: float
    csm_balance: float = 0.0
    csm_locked_in_rate_monthly: float = 0.0
    csm_straight_line_release: float = 0.0
    csm_periods_remaining: int = 0
```

- [ ] **Step 2: Add `csm_release` to `CohortFlows`**

Find:

```python
@dataclass
class CohortFlows:
    premium_income: float = 0.0
    death_claims: float = 0.0
    surrender_payouts: float = 0.0
    maturity_payouts: float = 0.0
    deaths: float = 0.0
    lapses: float = 0.0
```

Replace with:

```python
@dataclass
class CohortFlows:
    premium_income: float = 0.0
    death_claims: float = 0.0
    surrender_payouts: float = 0.0
    maturity_payouts: float = 0.0
    deaths: float = 0.0
    lapses: float = 0.0
    csm_release: float = 0.0
```

- [ ] **Step 3: Add CSM fields to `FinancialSnapshot`**

Find the end of the `FinancialSnapshot` dataclass (it currently ends with `commission_expense_by_channel: dict[str, float]`). Add these five fields after it:

```python
    total_csm: float
    csm_change: float
    csm_release: float
    csm_new_business: float
    onerous_loss: float
```

- [ ] **Step 4: Verify existing tests still fail only where expected**

Run: `cd backend && .venv/bin/pytest -q`
Expected: `test_finance.py::test_compute_snapshot_running_status` and `test_compute_snapshot_bankrupt_status` FAIL with `TypeError: compute_snapshot() missing 5 required positional arguments` (since `FinancialSnapshot` now needs 5 more fields but `compute_snapshot` doesn't pass them yet). All other tests still pass — `CohortState`/`CohortFlows` changes are backward-compatible thanks to the defaults.

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/types.py
git commit -m "feat(csm): add CSM fields to engine dataclasses"
```

---

### Task 3: `compute_csm_initial` — CSM day-0 recognition

**Files:**
- Create: `backend/app/engine/csm.py`
- Test: `backend/tests/engine/test_csm.py`

**Interfaces:**
- Consumes: `ProductConfig` (from `types.py`), `gross_premium_per_policy_monthly`/`effective_cost_rate_annual` (from `products.py`), `CSM_RISK_ADJUSTMENT_COEF`/`CSM_WHOLE_LIFE_HORIZON_CAP_TURNS`/`LAPSE_PRICE_SENSITIVITY` (from `config.py`).
- Produces: `CsmInitialResult` dataclass (`csm_balance`, `onerous_loss`, `locked_in_rate_monthly`, `straight_line_release`, `periods_remaining`) and `compute_csm_initial(product, pricing_multiplier, underwriting_strictness, count, commission_rate, market_rate_annual) -> CsmInitialResult` — consumed by Task 6 (`turn.py`).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/engine/test_csm.py`:

```python
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
        commission_rate=100.0,  # far above the ~55 breakeven for this product/strictness — forces a loss
        market_rate_annual=0.03,
    )
    assert result.csm_balance == 0.0
    assert result.onerous_loss > 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/engine/test_csm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.csm'`

- [ ] **Step 3: Implement `csm.py`**

Create `backend/app/engine/csm.py`:

```python
import math
from dataclasses import dataclass

from .config import CSM_RISK_ADJUSTMENT_COEF, CSM_WHOLE_LIFE_HORIZON_CAP_TURNS, LAPSE_PRICE_SENSITIVITY
from .products import effective_cost_rate_annual, gross_premium_per_policy_monthly
from .types import ProductCode, ProductConfig


@dataclass
class CsmInitialResult:
    csm_balance: float
    onerous_loss: float
    locked_in_rate_monthly: float
    straight_line_release: float
    periods_remaining: int


def _lapse_rate_monthly(product: ProductConfig, pricing_multiplier: float) -> float:
    return (product.base_lapse_rate_annual * pricing_multiplier**LAPSE_PRICE_SENSITIVITY) / 12


def compute_csm_initial(
    product: ProductConfig,
    pricing_multiplier: float,
    underwriting_strictness: float,
    count: float,
    commission_rate: float,
    market_rate_annual: float,
) -> CsmInitialResult:
    if count <= 0:
        return CsmInitialResult(0.0, 0.0, 0.0, 0.0, 0)

    r_lock_monthly = market_rate_annual / 12
    lapse_monthly = _lapse_rate_monthly(product, pricing_multiplier)
    if product.code == ProductCode.WHOLE_LIFE:
        mortality_monthly = effective_cost_rate_annual(product, 0, underwriting_strictness) / 12
    else:
        mortality_monthly = 0.0
    q_lock = mortality_monthly + lapse_monthly

    if product.maturity_turns is not None:
        n_periods = product.maturity_turns
    elif q_lock > 0:
        n_periods = min(math.ceil(1 / q_lock), CSM_WHOLE_LIFE_HORIZON_CAP_TURNS)
    else:
        n_periods = CSM_WHOLE_LIFE_HORIZON_CAP_TURNS
    n_periods = max(n_periods, 1)

    survivorship = 1.0
    discount = 1.0
    pv_margin_per_policy = 0.0
    pv_risk_per_policy = 0.0
    for t in range(n_periods):
        premium_t = gross_premium_per_policy_monthly(product, t, pricing_multiplier, underwriting_strictness)
        pv_margin_per_policy += survivorship * premium_t * (1 - product.reserve_accrual_ratio) / discount
        if product.code == ProductCode.WHOLE_LIFE:
            claim_cost_t = (effective_cost_rate_annual(product, t, underwriting_strictness) / 12) * product.unit_size
            pv_risk_per_policy += survivorship * claim_cost_t / discount
        survivorship *= 1 - q_lock
        discount *= 1 + r_lock_monthly

    risk_adjustment_per_policy = CSM_RISK_ADJUSTMENT_COEF * pv_risk_per_policy
    day0_premium = gross_premium_per_policy_monthly(product, 0, pricing_multiplier, underwriting_strictness)
    commission_expense_cohort = count * day0_premium * commission_rate

    gross_csm = count * (pv_margin_per_policy - risk_adjustment_per_policy) - commission_expense_cohort
    csm_balance = max(0.0, gross_csm)
    onerous_loss = max(0.0, -gross_csm)

    return CsmInitialResult(
        csm_balance=csm_balance,
        onerous_loss=onerous_loss,
        locked_in_rate_monthly=r_lock_monthly,
        straight_line_release=csm_balance / n_periods,
        periods_remaining=n_periods,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/engine/test_csm.py -v`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/csm.py backend/tests/engine/test_csm.py
git commit -m "feat(csm): implement CSM day-0 initial recognition"
```

---

### Task 4: `step_csm_cohort` — per-turn rollforward

**Files:**
- Modify: `backend/app/engine/csm.py`
- Test: `backend/tests/engine/test_csm.py`

**Interfaces:**
- Produces: `step_csm_cohort(csm_balance, locked_in_rate_monthly, straight_line_release, periods_remaining, is_closing) -> tuple[float, float]` (returns `(new_csm_balance, csm_release)`) — consumed by Task 5 (`cohorts.py`).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/engine/test_csm.py`:

```python
from app.engine.csm import step_csm_cohort


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/engine/test_csm.py -v`
Expected: FAIL with `ImportError: cannot import name 'step_csm_cohort'`

- [ ] **Step 3: Implement `step_csm_cohort`**

Append to `backend/app/engine/csm.py`:

```python
def step_csm_cohort(
    csm_balance: float,
    locked_in_rate_monthly: float,
    straight_line_release: float,
    periods_remaining: int,
    is_closing: bool,
) -> tuple[float, float]:
    accreted = csm_balance * (1 + locked_in_rate_monthly)
    if is_closing or periods_remaining <= 1:
        return 0.0, accreted
    release = min(accreted, straight_line_release)
    return accreted - release, release
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/engine/test_csm.py -v`
Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/csm.py backend/tests/engine/test_csm.py
git commit -m "feat(csm): implement CSM per-turn rollforward"
```

---

### Task 5: Wire CSM rollforward into `cohorts.step_cohort`

**Files:**
- Modify: `backend/app/engine/cohorts.py`
- Modify: `backend/tests/engine/test_cohorts.py`

**Interfaces:**
- Consumes: `step_csm_cohort` (Task 4).
- Produces: `step_cohort` now also returns a `CohortState` with rolled-forward CSM fields, and `CohortFlows.csm_release` populated — consumed by Task 6 (`turn.py`'s aggregation).

- [ ] **Step 1: Write the failing test**

Open `backend/tests/engine/test_cohorts.py`. Add this test (it exercises an existing in-force cohort — as opposed to a brand-new one — carrying a CSM balance from a prior turn):

```python
def test_step_cohort_rolls_forward_existing_csm_balance():
    cohort = CohortState(
        product=ProductCode.WHOLE_LIFE,
        channel=ChannelCode.CAPTIVE,
        issue_turn=0,
        in_force_count=1000.0,
        unit_size=100_000_000,
        reserve_balance=10_000_000.0,
        csm_balance=1_200_000.0,
        csm_locked_in_rate_monthly=0.0025,
        csm_straight_line_release=10_000.0,
        csm_periods_remaining=120,
    )
    updated, flows = step_cohort(cohort, base_decision(), current_turn=1, portfolio_return_monthly=0.0025)

    assert updated is not None
    assert flows.csm_release == pytest.approx(10_000.0)
    assert updated.csm_balance == pytest.approx(1_200_000.0 * 1.0025 - 10_000.0)
    assert updated.csm_periods_remaining == 119


def test_step_cohort_releases_full_csm_balance_on_maturity():
    cohort = CohortState(
        product=ProductCode.SAVINGS,
        channel=ChannelCode.GA,
        issue_turn=0,
        in_force_count=100.0,
        unit_size=60_000_000,
        reserve_balance=500_000_000.0,
        csm_balance=5_000_000.0,
        csm_locked_in_rate_monthly=0.0025,
        csm_straight_line_release=100_000.0,
        csm_periods_remaining=1,
    )
    updated, flows = step_cohort(cohort, base_decision(), current_turn=60, portfolio_return_monthly=0.0025)

    assert updated is None
    assert flows.csm_release == pytest.approx(5_000_000.0 * 1.0025)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/engine/test_cohorts.py -v`
Expected: FAIL — `flows.csm_release` is `0.0` (not yet wired up), so both new assertions fail.

- [ ] **Step 3: Wire CSM rollforward into `step_cohort`**

In `backend/app/engine/cohorts.py`, add the import:

```python
from .csm import step_csm_cohort
```

Then replace the tail of `step_cohort` — from `in_force_next = cohort.in_force_count - deaths - lapses` to the end of the function — with:

```python
    in_force_next = cohort.in_force_count - deaths - lapses
    new_duration = duration_turns + 1
    is_maturing = product.maturity_turns is not None and new_duration >= product.maturity_turns
    is_closing = is_maturing or in_force_next <= 0.01

    new_csm_balance, csm_release = step_csm_cohort(
        cohort.csm_balance,
        cohort.csm_locked_in_rate_monthly,
        cohort.csm_straight_line_release,
        cohort.csm_periods_remaining,
        is_closing,
    )

    flows = CohortFlows(
        premium_income=premium,
        death_claims=death_claims,
        surrender_payouts=surrender_payout,
        deaths=deaths,
        lapses=lapses,
        csm_release=csm_release,
    )

    if is_maturing:
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
        csm_balance=new_csm_balance,
        csm_locked_in_rate_monthly=cohort.csm_locked_in_rate_monthly,
        csm_straight_line_release=cohort.csm_straight_line_release,
        csm_periods_remaining=cohort.csm_periods_remaining - 1,
    )
    return updated, flows
```

(This removes the old duplicate `new_duration`/`flows = CohortFlows(...)` lines further up in the function body — make sure there is only one definition of each after this edit.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/engine/test_cohorts.py -v`
Expected: all tests pass, including the two new ones and the pre-existing ones (their `csm_release`/`csm_balance` default to `0.0` since those cohorts are constructed without CSM fields, which is harmless).

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/cohorts.py backend/tests/engine/test_cohorts.py
git commit -m "feat(csm): roll forward CSM balance inside step_cohort"
```

---

### Task 6: Wire CSM initial recognition + net-income impact into `turn.py`/`finance.py`

**Files:**
- Modify: `backend/app/engine/turn.py`
- Modify: `backend/app/engine/finance.py`
- Modify: `backend/tests/engine/test_finance.py`
- Modify: `backend/tests/engine/test_turn.py`

**Interfaces:**
- Consumes: `compute_csm_initial` (Task 3), `CohortFlows.csm_release`/`CohortState.csm_*` (Task 5).
- Produces: `FinancialSnapshot.total_csm/csm_change/csm_release/csm_new_business/onerous_loss` populated on every `run_turn()` result — consumed by Task 7 (persistence) and Tasks 9-10 (frontend).

- [ ] **Step 1: Update `compute_snapshot`'s failing tests first**

In `backend/tests/engine/test_finance.py`, update both `compute_snapshot(...)` calls to pass the 5 new required arguments and assert the new net-income formula. Replace:

```python
        interest_rate=0.03,
        stock_regime="normal",
        stock_return_realized=0.01,
        total_in_force=1000.0,
        deaths_count=1.0,
        lapses_count=2.0,
        new_policies_by_product={"whole_life": 0, "savings": 0},
        new_policies_by_channel={"captive": 0, "ga": 0},
        premium_income_by_product={"whole_life": 10_000_000.0, "savings": 0.0},
        new_business_premium_by_channel={"captive": 0.0, "ga": 0.0},
        commission_expense_by_channel={"captive": 2_000_000.0, "ga": 0.0},
    )
    assert snapshot.net_income == pytest.approx(583333.33, rel=1e-6)
    assert snapshot.equity == pytest.approx(10_000_583_333.33, rel=1e-9)
    assert snapshot.status == GameStatus.RUNNING
```

with:

```python
        interest_rate=0.03,
        stock_regime="normal",
        stock_return_realized=0.01,
        total_in_force=1000.0,
        deaths_count=1.0,
        lapses_count=2.0,
        new_policies_by_product={"whole_life": 0, "savings": 0},
        new_policies_by_channel={"captive": 0, "ga": 0},
        premium_income_by_product={"whole_life": 10_000_000.0, "savings": 0.0},
        new_business_premium_by_channel={"captive": 0.0, "ga": 0.0},
        commission_expense_by_channel={"captive": 2_000_000.0, "ga": 0.0},
        total_csm=90_000.0,
        csm_change=50_000.0,
        csm_release=5_000.0,
        csm_new_business=55_000.0,
        onerous_loss=0.0,
    )
    assert snapshot.net_income == pytest.approx(533333.33, rel=1e-6)
    assert snapshot.equity == pytest.approx(10_000_533_333.33, rel=1e-9)
    assert snapshot.status == GameStatus.RUNNING
```

And replace the second call's tail:

```python
        dividend_payout=0.0,
        assets=AssetBalances(deposit=0.0, bond=0.0, stock=0.0),
        total_reserve=0.0,
        interest_rate=0.03,
        stock_regime="normal",
        stock_return_realized=None,
        total_in_force=0.0,
        deaths_count=0.0,
        lapses_count=0.0,
        new_policies_by_product={"whole_life": 0, "savings": 0},
        new_policies_by_channel={"captive": 0, "ga": 0},
        premium_income_by_product={"whole_life": 0.0, "savings": 0.0},
        new_business_premium_by_channel={"captive": 0.0, "ga": 0.0},
        commission_expense_by_channel={"captive": 0.0, "ga": 0.0},
    )
    # marketing_expense alone exceeds equity_start, driving net_income and equity negative
```

with:

```python
        dividend_payout=0.0,
        assets=AssetBalances(deposit=0.0, bond=0.0, stock=0.0),
        total_reserve=0.0,
        interest_rate=0.03,
        stock_regime="normal",
        stock_return_realized=None,
        total_in_force=0.0,
        deaths_count=0.0,
        lapses_count=0.0,
        new_policies_by_product={"whole_life": 0, "savings": 0},
        new_policies_by_channel={"captive": 0, "ga": 0},
        premium_income_by_product={"whole_life": 0.0, "savings": 0.0},
        new_business_premium_by_channel={"captive": 0.0, "ga": 0.0},
        commission_expense_by_channel={"captive": 0.0, "ga": 0.0},
        total_csm=0.0,
        csm_change=0.0,
        csm_release=0.0,
        csm_new_business=0.0,
        onerous_loss=0.0,
    )
    # marketing_expense alone exceeds equity_start, driving net_income and equity negative
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/engine/test_finance.py -v`
Expected: FAIL — `compute_snapshot()` doesn't accept these new kwargs yet.

- [ ] **Step 3: Update `compute_snapshot`**

In `backend/app/engine/finance.py`, add the 5 new parameters to `compute_snapshot`'s signature (after `total_reserve: float,`):

```python
    total_csm: float,
    csm_change: float,
    csm_release: float,
    csm_new_business: float,
    onerous_loss: float,
```

Update the `net_income` calculation:

```python
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
        - csm_change
        - onerous_loss
    )
```

And add the 5 fields to the returned `FinancialSnapshot(...)` call (after `total_reserve=total_reserve,`):

```python
        total_csm=total_csm,
        csm_change=csm_change,
        csm_release=csm_release,
        csm_new_business=csm_new_business,
        onerous_loss=onerous_loss,
```

- [ ] **Step 4: Run finance tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/engine/test_finance.py -v`
Expected: `6 passed`

- [ ] **Step 5: Wire CSM into `turn.py`**

In `backend/app/engine/turn.py`, add the import:

```python
from .csm import compute_csm_initial
```

Replace the new-business loop:

```python
    new_policies_by_product = {p.value: 0 for p in ProductCode}
    new_policies_by_channel = {c.value: 0 for c in ChannelCode}
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
            new_policies_by_product[product.value] += count
            new_policies_by_channel[channel.value] += count
```

with:

```python
    new_policies_by_product = {p.value: 0 for p in ProductCode}
    new_policies_by_channel = {c.value: 0 for c in ChannelCode}
    total_csm_new_business = 0.0
    total_onerous_loss = 0.0
    working_cohorts = list(cohorts)
    for product, channel, count in compute_new_business(decision):
        if count > 0:
            csm_initial = compute_csm_initial(
                DEFAULT_PRODUCT_CONFIGS[product],
                decision.pricing_multiplier[product],
                decision.underwriting_strictness[product],
                count=count,
                commission_rate=decision.commission_rate[channel],
                market_rate_annual=new_market.interest_rate,
            )
            working_cohorts.append(
                CohortState(
                    product=product,
                    channel=channel,
                    issue_turn=next_turn,
                    in_force_count=float(count),
                    unit_size=DEFAULT_PRODUCT_CONFIGS[product].unit_size,
                    reserve_balance=0.0,
                    csm_balance=csm_initial.csm_balance,
                    csm_locked_in_rate_monthly=csm_initial.locked_in_rate_monthly,
                    csm_straight_line_release=csm_initial.straight_line_release,
                    csm_periods_remaining=csm_initial.periods_remaining,
                )
            )
            new_policies_by_product[product.value] += count
            new_policies_by_channel[channel.value] += count
            total_csm_new_business += csm_initial.csm_balance
            total_onerous_loss += csm_initial.onerous_loss
```

Add, right before `reserve_start_total = sum(c.reserve_balance for c in cohorts)`:

```python
    total_csm_start = sum(c.csm_balance for c in cohorts)
```

In the main per-cohort loop, add CSM release aggregation alongside the other flow aggregations. Find:

```python
        deaths_count += flows.deaths
        lapses_count += flows.lapses
```

and add directly after it:

```python
        total_csm_release += flows.csm_release
```

(add `total_csm_release = 0.0` to the same initializer line as `deaths_count = lapses_count = 0.0`, i.e. change it to `deaths_count = lapses_count = total_csm_release = 0.0`).

After the loop, alongside the existing `reserve_end_total`/`reserve_change` computation, add:

```python
    total_csm_end = sum(c.csm_balance for c in updated_cohorts)
    csm_change = total_csm_end - total_csm_start
```

Finally, update the `compute_snapshot(...)` call to pass the 5 new arguments (after `total_reserve=reserve_end_total,`):

```python
        total_csm=total_csm_end,
        csm_change=csm_change,
        csm_release=total_csm_release,
        csm_new_business=total_csm_new_business,
        onerous_loss=total_onerous_loss,
```

- [ ] **Step 6: Compute the real expected values for `test_turn.py`**

The existing `test_run_turn_matches_reference_calculation` assertions for `net_income`/`equity`/asset balances will now be wrong (CSM changes them). Run this script from `backend/` to get the real post-CSM numbers:

```bash
.venv/bin/python -c "
import numpy as np
from app.engine.turn import run_turn
from app.engine.types import AssetBalances, ChannelCode, Decision, MarketState, ProductCode, StockRegime

def base_decision():
    return Decision(
        pricing_multiplier={ProductCode.WHOLE_LIFE: 1.0, ProductCode.SAVINGS: 1.0},
        underwriting_strictness={ProductCode.WHOLE_LIFE: 0.3, ProductCode.SAVINGS: 0.0},
        commission_rate={ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 0.45},
        marketing_spend={ChannelCode.CAPTIVE: 10_000_000, ChannelCode.GA: 15_000_000},
        asset_allocation={'deposit': 0.3, 'bond': 0.4, 'stock': 0.3},
        dividend_payout=0.0,
    )

rng = np.random.default_rng(42)
market = MarketState(turn=0, interest_rate=0.03, stock_regime=StockRegime.NORMAL, stock_return_realized=None)
assets = AssetBalances(deposit=3_000_000_000.0, bond=4_000_000_000.0, stock=3_000_000_000.0)
result = run_turn(0, [], market, assets, 10_000_000_000.0, base_decision(), rng)
s = result.snapshot
for name in ['premium_income','investment_income','death_claims','commission_expense','marketing_expense','opex','reserve_change','total_csm','csm_change','csm_release','csm_new_business','onerous_loss','net_income','equity']:
    print(name, getattr(s, name))
print('deposit', result.assets.deposit)
print('bond', result.assets.bond)
print('stock', result.assets.stock)
"
```

In `backend/tests/engine/test_turn.py`, update `test_run_turn_matches_reference_calculation`'s assertions for `net_income`, `equity`, `result.assets.deposit`, `result.assets.bond`, `result.assets.stock` to the values the script printed (the other assertions — `premium_income`, `investment_income`, `death_claims`, `commission_expense`, `marketing_expense`, `opex`, `reserve_change` — are unaffected by CSM and stay as they are). Add new assertions right after the existing `commission_expense_by_channel["ga"]` assertion:

```python
    assert result.snapshot.total_csm > 0
    assert result.snapshot.csm_new_business == pytest.approx(result.snapshot.total_csm + result.snapshot.csm_release, rel=1e-9)
    assert result.snapshot.onerous_loss == pytest.approx(0.0)
```

(The second assertion holds because `csm_change = total_csm_end − 0` on turn 1, and `total_csm_end = csm_new_business − csm_release` since all 4 cohorts are brand new this turn.)

Also update `test_run_turn_preserves_accounting_identity_across_turns` — the accounting identity now includes CSM. Replace:

```python
        total_reserve = sum(c.reserve_balance for c in result.cohorts)
        assert result.assets.total == pytest.approx(total_reserve + result.snapshot.equity, rel=1e-9)
```

with:

```python
        total_reserve = sum(c.reserve_balance for c in result.cohorts)
        total_csm = sum(c.csm_balance for c in result.cohorts)
        assert result.assets.total == pytest.approx(total_reserve + total_csm + result.snapshot.equity, rel=1e-9)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/engine -v`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/engine/turn.py backend/app/engine/finance.py backend/tests/engine/test_finance.py backend/tests/engine/test_turn.py
git commit -m "feat(csm): defer new-business margin into CSM and subtract from net income"
```

---

### Task 7: Persist CSM fields (models, schemas, repository)

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/tests/test_repository.py`

**Interfaces:**
- Consumes: `CohortState.csm_*` (Task 2/5), `FinancialSnapshot.total_csm/csm_change/csm_release/csm_new_business/onerous_loss` (Task 6).
- Produces: `CohortRow`/`FinancialSnapshotRow` columns and `SnapshotResponse` fields — consumed by Task 8 (API smoke test) and Tasks 9-10 (frontend).

- [ ] **Step 1: Add columns to `CohortRow`**

In `backend/app/models.py`, add to `CohortRow` (after `reserve_balance: float`):

```python
    csm_balance: float = 0.0
    csm_locked_in_rate_monthly: float = 0.0
    csm_straight_line_release: float = 0.0
    csm_periods_remaining: int = 0
```

- [ ] **Step 2: Add columns to `FinancialSnapshotRow`**

Add to `FinancialSnapshotRow` (after `commission_expense_by_channel: dict = Field(sa_column=Column(JSON))`):

```python
    total_csm: float
    csm_change: float
    csm_release: float
    csm_new_business: float
    onerous_loss: float
```

- [ ] **Step 3: Add fields to `SnapshotResponse`**

In `backend/app/schemas.py`, add to `SnapshotResponse` (after `commission_expense_by_channel: dict[str, float]`):

```python
    total_csm: float
    csm_change: float
    csm_release: float
    csm_new_business: float
    onerous_loss: float
```

- [ ] **Step 4: Update `repository.py`'s `active_cohorts` to read CSM fields**

In `backend/app/repository.py`, in `active_cohorts`, update the `CohortState(...)` construction to include:

```python
            csm_balance=row.csm_balance,
            csm_locked_in_rate_monthly=row.csm_locked_in_rate_monthly,
            csm_straight_line_release=row.csm_straight_line_release,
            csm_periods_remaining=row.csm_periods_remaining,
```

- [ ] **Step 5: Update `apply_turn`'s cohort-row writes**

In `apply_turn`, the loop that rebuilds `CohortRow` entries from `result.cohorts` should also persist CSM fields. Update the `CohortRow(...)` construction to include:

```python
                csm_balance=cohort.csm_balance,
                csm_locked_in_rate_monthly=cohort.csm_locked_in_rate_monthly,
                csm_straight_line_release=cohort.csm_straight_line_release,
                csm_periods_remaining=cohort.csm_periods_remaining,
```

- [ ] **Step 6: Update `apply_turn`'s snapshot-row write**

Update the `FinancialSnapshotRow(...)` construction in `apply_turn` to include:

```python
        total_csm=result.snapshot.total_csm,
        csm_change=result.snapshot.csm_change,
        csm_release=result.snapshot.csm_release,
        csm_new_business=result.snapshot.csm_new_business,
        onerous_loss=result.snapshot.onerous_loss,
```

- [ ] **Step 7: Update `create_game`'s initial snapshot**

In `create_game`, add to the initial `FinancialSnapshotRow(...)`:

```python
            total_csm=0.0,
            csm_change=0.0,
            csm_release=0.0,
            csm_new_business=0.0,
            onerous_loss=0.0,
```

- [ ] **Step 8: Run repository tests**

Run: `cd backend && .venv/bin/pytest tests/test_repository.py -v`
Expected: all pass (existing assertions are unaffected; the new columns just have to not break construction).

- [ ] **Step 9: Add a CSM-specific repository assertion**

In `backend/tests/test_repository.py`, add to `test_apply_turn_persists_snapshot_and_advances_game`, right after the existing `assert snapshot.premium_income == pytest.approx(10121850.0)`:

```python
    assert snapshot.total_csm > 0
```

- [ ] **Step 10: Run the full backend test suite**

Run: `cd backend && .venv/bin/pytest -q`
Expected: all pass, zero failures.

- [ ] **Step 11: Commit**

```bash
git add backend/app/models.py backend/app/schemas.py backend/app/repository.py backend/tests/test_repository.py
git commit -m "feat(csm): persist CSM fields through DB models and API schema"
```

---

### Task 8: Reset dev DB and smoke-test the API

**Files:** none (operational verification only)

- [ ] **Step 1: Ask the user before touching the podman-compose data volume**

This task changes the DB schema again (new columns on `cohorts` and `financial_snapshots`, no migration tool in this project). Ask the user: "CSM 스키마 변경으로 `insurance_company_simulator_backend-data` 볼륨을 다시 삭제하고 재생성해도 될까요?" — do not proceed to Step 2 until they say yes (mirror exactly how this was handled earlier in the session; do not assume standing approval).

- [ ] **Step 2: Recreate the stack**

```bash
podman-compose down
podman volume rm insurance_company_simulator_backend-data
podman-compose up --build -d
```

- [ ] **Step 3: Smoke-test via curl**

```bash
sleep 3
curl -s -X POST http://localhost:8000/games -H 'Content-Type: application/json' -d '{"initial_capital": 10000000000, "rng_seed": 42}'
```

Expected: JSON response includes `"total_csm":0.0,"csm_change":0.0,...` on the turn-0 snapshot.

```bash
curl -s -X POST http://localhost:8000/games/1/turn -H 'Content-Type: application/json' -d '{
  "pricing_multiplier": {"whole_life": 1.0, "savings": 1.0},
  "underwriting_strictness": {"whole_life": 0.3, "savings": 0.0},
  "commission_rate": {"captive": 0.3, "ga": 0.45},
  "marketing_spend": {"captive": 10000000, "ga": 15000000},
  "asset_allocation": {"deposit": 0.3, "bond": 0.4, "stock": 0.3},
  "dividend_payout": 0
}' | python3 -m json.tool
```

Expected: `total_csm` in the response is now a large positive number (new business was just issued), `csm_new_business` roughly equals `total_csm + csm_release`, `onerous_loss` is `0.0`.

- [ ] **Step 4: No commit** (operational step, nothing to commit).

---

### Task 9: Frontend — CSM section in `MonitoringPanel.vue`

**Files:**
- Modify: `frontend/src/components/MonitoringPanel.vue`

**Interfaces:**
- Consumes: `snapshot.total_csm`, `snapshot.csm_release`, `snapshot.csm_new_business`, `snapshot.onerous_loss`, `snapshot.equity` (all already flowing through `props.snapshot` from Task 7).

- [ ] **Step 1: Add a computed CSM/Equity ratio**

In `frontend/src/components/MonitoringPanel.vue`, in the `<script setup>` block, add near the other ratio computeds (e.g. next to `solvencyProxy`):

```js
const csmToEquityRatio = computed(() => safeDiv(props.snapshot.total_csm, props.snapshot.equity))
```

- [ ] **Step 2: Add the CSM card to the template**

Add this new card block right after the closing `</div>` of the "재무건전성" card (the last card in the template, before the final closing `</div>` of the component):

```html
    <div class="rounded border border-slate-200 p-4">
      <h2 class="mb-3 font-semibold text-slate-800">계약서비스마진 (CSM)</h2>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">총 CSM 잔액</div>
          <div class="font-bold">{{ formatWon(snapshot.total_csm) }}</div>
        </div>
        <div>
          <div class="text-slate-500">이번 턴 CSM 환입액</div>
          <div class="font-bold">{{ formatWon(snapshot.csm_release) }}</div>
        </div>
        <div>
          <div class="text-slate-500">신규 CSM 설정액</div>
          <div class="font-bold">{{ formatWon(snapshot.csm_new_business) }}</div>
        </div>
        <div>
          <div class="text-slate-500">CSM / 자본총계</div>
          <div class="font-bold">{{ formatPct(csmToEquityRatio, 1) }}</div>
        </div>
        <div class="col-span-2">
          <div class="text-slate-500">손실부담계약손실 (이번 턴)</div>
          <div class="font-bold" :class="snapshot.onerous_loss > 0 ? 'text-red-600' : 'text-slate-800'">
            {{ formatWon(snapshot.onerous_loss) }}
          </div>
        </div>
      </div>
    </div>
```

- [ ] **Step 3: Manually verify in the browser**

With the dev stack up (from Task 8), navigate to `http://localhost:5173/games/1` and confirm the new "계약서비스마진 (CSM)" card renders with non-zero values after submitting a turn. If the Vite dev server doesn't pick up the file change (a known issue with this project's bind-mounted volume on this machine), run `podman restart insurance_company_simulator_frontend_1` and reload.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/MonitoringPanel.vue
git commit -m "feat(csm): show CSM metrics in the monitoring panel"
```

---

### Task 10: Frontend — CSM rows in `FinancialStatements.vue`

**Files:**
- Modify: `frontend/src/components/FinancialStatements.vue`

**Interfaces:**
- Consumes: `snapshot.csm_change`, `snapshot.onerous_loss`, `snapshot.total_csm` (Task 7).

- [ ] **Step 1: Add CSM rows to the P&L table**

In `frontend/src/components/FinancialStatements.vue`, in the 손익계산서 `<table>`, insert two new rows right after the `책임준비금전입액` row and before the `당기순이익` row:

```html
          <tr><td class="pt-1">CSM 순증감</td><td class="pt-1 text-right">{{ formatWon(snapshot.csm_change) }}</td></tr>
          <tr><td>손실부담계약손실</td><td class="text-right">{{ formatWon(snapshot.onerous_loss) }}</td></tr>
```

- [ ] **Step 2: Add the CSM row to the balance sheet table**

In the 재무상태표 `<table>`, insert a new row right after the `책임준비금` row, still inside the "부채" group:

```html
          <tr><td class="pl-3">계약서비스마진 (CSM)</td><td class="text-right">{{ formatWon(snapshot.total_csm) }}</td></tr>
```

- [ ] **Step 3: Manually verify the identity holds**

With the dev stack up, submit a turn in the browser and confirm (via the displayed numbers): `자산총계 == 책임준비금 + 계약서비스마진 + 자본총계`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/FinancialStatements.vue
git commit -m "feat(csm): show CSM in the P&L and balance sheet"
```

---

### Task 11: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd backend && .venv/bin/pytest -q`
Expected: all pass, zero failures.

- [ ] **Step 2: Drive the app through a browser (Playwright)**

Navigate to `http://localhost:5173/games/1` (or create a fresh game), submit at least 3 turns through the UI (not curl), and screenshot the full page. Confirm:
- The "계약서비스마진 (CSM)" monitoring card shows a growing 총 CSM 잔액 across turns, with 이번 턴 CSM 환입액 > 0 from turn 2 onward (turn 1's cohorts start releasing from turn 2).
- The P&L's `CSM 순증감` row and the balance sheet's `계약서비스마진` row are both present and the balance sheet identity (자산총계 = 책임준비금 + CSM + 자본총계) holds to the displayed precision.
- No errors in the browser console (`mcp__plugin_playwright_playwright__browser_console_messages` with `level: "error"`, `all: true`).

- [ ] **Step 3: Confirm no regressions in the rest of the dashboard**

Confirm the KPI cards, history chart, decision panel, turn control, and "게임 종료 & 새 시뮬레이션" button all still work as they did before this feature (these were not touched by this plan, but this project's dev server has previously required a container restart to pick up frontend changes — verify the whole page, not just the new cards).

- [ ] **Step 4: No commit** (verification only — this task should surface problems, not create new changes).
