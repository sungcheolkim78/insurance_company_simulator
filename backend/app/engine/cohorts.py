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
    flows = CohortFlows(
        premium_income=premium,
        death_claims=death_claims,
        surrender_payouts=surrender_payout,
        deaths=deaths,
        lapses=lapses,
    )

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
