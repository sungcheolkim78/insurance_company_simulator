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
    game_length_turns: int = 120
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
    csm_balance: float = 0.0
    csm_locked_in_rate_monthly: float = 0.0
    csm_straight_line_release: float = 0.0
    csm_periods_remaining: int = 0


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
    interest_rate: float
    stock_regime: str
    stock_return_realized: float | None = None
    total_in_force: float
    deaths_count: float
    lapses_count: float
    new_policies_by_product: dict = Field(sa_column=Column(JSON))
    new_policies_by_channel: dict = Field(sa_column=Column(JSON))
    premium_income_by_product: dict = Field(sa_column=Column(JSON))
    new_business_premium_by_channel: dict = Field(sa_column=Column(JSON))
    commission_expense_by_channel: dict = Field(sa_column=Column(JSON))
    total_csm: float
    csm_change: float
    csm_release: float
    csm_new_business: float
    onerous_loss: float
