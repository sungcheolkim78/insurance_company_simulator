from .config import DEFAULT_PRODUCT_CONFIGS
from .csm import step_csm_cohort
from .products import effective_cost_rate_annual, gross_premium_per_policy_monthly, lapse_rate_monthly
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

    lapses = cohort.in_force_count * lapse_rate_monthly(product, pricing_multiplier)

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
