from pydantic import BaseModel, field_validator

PRODUCT_KEYS = {"whole_life", "savings"}
CHANNEL_KEYS = {"captive", "ga"}
ASSET_KEYS = {"deposit", "bond", "stock"}


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

    @field_validator("pricing_multiplier")
    @classmethod
    def _pricing_multiplier_positive(cls, value: dict[str, float]) -> dict[str, float]:
        for v in value.values():
            if v <= 0:
                raise ValueError("pricing_multiplier values must be greater than 0")
        return value

    @field_validator("underwriting_strictness")
    @classmethod
    def _strictness_range(cls, value: dict[str, float]) -> dict[str, float]:
        for v in value.values():
            if not 0.0 <= v <= 1.0:
                raise ValueError("underwriting_strictness values must be between 0 and 1")
        return value

    @field_validator("commission_rate", "marketing_spend")
    @classmethod
    def _non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        for v in value.values():
            if v < 0:
                raise ValueError("values must be non-negative")
        return value

    @field_validator("commission_rate")
    @classmethod
    def _commission_rate_upper_bound(cls, value: dict[str, float]) -> dict[str, float]:
        # The balance-sheet identity AssetsTotal == TotalReserve + TotalCSM + Equity (see
        # docs/simulation/simulation_formulas.md §6.1.3) only holds when onerous_loss == 0.
        # A commission_rate far above the documented 0.1-0.8 play range can push a cohort's
        # CSM negative at issuance (onerous), which breaks that identity. 2.0 is comfortably
        # above legitimate play and comfortably below the empirical onerous breakeven
        # (~4.95 for savings, ~52 for whole_life at default params).
        for v in value.values():
            if v > 2.0:
                raise ValueError("commission_rate values must not exceed 2.0")
        return value

    @field_validator("dividend_payout")
    @classmethod
    def _dividend_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("dividend_payout must be non-negative")
        return value

    @field_validator("pricing_multiplier", "underwriting_strictness")
    @classmethod
    def _product_keys(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value.keys()) != PRODUCT_KEYS:
            raise ValueError(f"keys must be exactly {sorted(PRODUCT_KEYS)}")
        return value

    @field_validator("commission_rate", "marketing_spend")
    @classmethod
    def _channel_keys(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value.keys()) != CHANNEL_KEYS:
            raise ValueError(f"keys must be exactly {sorted(CHANNEL_KEYS)}")
        return value

    @field_validator("asset_allocation")
    @classmethod
    def _asset_allocation_valid(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value.keys()) != ASSET_KEYS:
            raise ValueError(f"keys must be exactly {sorted(ASSET_KEYS)}")
        for v in value.values():
            if v < 0:
                raise ValueError("asset_allocation values must be non-negative")
        if abs(sum(value.values()) - 1.0) > 1e-6:
            raise ValueError("asset_allocation values must sum to 1.0")
        return value


class ConfigResponse(BaseModel):
    products: dict
    channels: dict
