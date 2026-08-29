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
