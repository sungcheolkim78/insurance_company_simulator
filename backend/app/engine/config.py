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

CSM_RISK_ADJUSTMENT_COEF = 0.05
CSM_WHOLE_LIFE_HORIZON_CAP_TURNS = 600
