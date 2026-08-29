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
    csm_balance: float = 0.0
    csm_locked_in_rate_monthly: float = 0.0
    csm_straight_line_release: float = 0.0
    csm_periods_remaining: int = 0


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
    deaths: float = 0.0
    lapses: float = 0.0
    csm_release: float = 0.0


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
    interest_rate: float
    stock_regime: str
    stock_return_realized: float | None
    total_in_force: float
    deaths_count: float
    lapses_count: float
    new_policies_by_product: dict[str, int]
    new_policies_by_channel: dict[str, int]
    premium_income_by_product: dict[str, float]
    new_business_premium_by_channel: dict[str, float]
    commission_expense_by_channel: dict[str, float]
    total_csm: float
    csm_change: float
    csm_release: float
    csm_new_business: float
    onerous_loss: float


@dataclass
class TurnResult:
    cohorts: list[CohortState]
    market_state: MarketState
    assets: AssetBalances
    snapshot: FinancialSnapshot
