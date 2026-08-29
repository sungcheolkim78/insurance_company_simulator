import numpy as np

from .cohorts import step_cohort
from .config import DEFAULT_PRODUCT_CONFIGS, GAME_LENGTH_TURNS
from .finance import compute_opex, compute_snapshot, invest_net_cashflow, investment_income_and_returns
from .market import advance_market_state
from .products import compute_new_business
from .types import AssetBalances, ChannelCode, CohortState, Decision, GameStatus, MarketState, ProductCode, TurnResult


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

    updated_cohorts: list[CohortState] = []
    premium_income = death_claims = surrender_payouts = maturity_payouts = commission_expense = 0.0
    deaths_count = lapses_count = 0.0
    premium_income_by_product = {p.value: 0.0 for p in ProductCode}
    new_business_premium_by_channel = {c.value: 0.0 for c in ChannelCode}
    commission_expense_by_channel = {c.value: 0.0 for c in ChannelCode}
    for cohort in working_cohorts:
        is_new = cohort.issue_turn == next_turn
        updated, flows = step_cohort(cohort, decision, next_turn, portfolio_return_monthly)
        premium_income += flows.premium_income
        premium_income_by_product[cohort.product.value] += flows.premium_income
        death_claims += flows.death_claims
        surrender_payouts += flows.surrender_payouts
        maturity_payouts += flows.maturity_payouts
        deaths_count += flows.deaths
        lapses_count += flows.lapses
        if is_new:
            cohort_commission = flows.premium_income * decision.commission_rate[cohort.channel]
            commission_expense += cohort_commission
            commission_expense_by_channel[cohort.channel.value] += cohort_commission
            new_business_premium_by_channel[cohort.channel.value] += flows.premium_income
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
        interest_rate=new_market.interest_rate,
        stock_regime=new_market.stock_regime.value,
        stock_return_realized=new_market.stock_return_realized,
        total_in_force=total_in_force,
        deaths_count=deaths_count,
        lapses_count=lapses_count,
        new_policies_by_product=new_policies_by_product,
        new_policies_by_channel=new_policies_by_channel,
        premium_income_by_product=premium_income_by_product,
        new_business_premium_by_channel=new_business_premium_by_channel,
        commission_expense_by_channel=commission_expense_by_channel,
    )
    if snapshot.status == GameStatus.RUNNING and next_turn >= GAME_LENGTH_TURNS:
        snapshot.status = GameStatus.COMPLETED

    return TurnResult(cohorts=updated_cohorts, market_state=new_market, assets=assets_final, snapshot=snapshot)
