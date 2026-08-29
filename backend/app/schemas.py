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
