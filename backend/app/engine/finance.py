import math

from .config import OPEX_BASE
from .market import bond_monthly_return, deposit_monthly_return, stock_monthly_return
from .types import AssetBalances, FinancialSnapshot, GameStatus, MarketState


def investment_income_and_returns(assets: AssetBalances, market: MarketState) -> tuple[float, AssetBalances]:
    deposit_ret = deposit_monthly_return(market)
    bond_ret = bond_monthly_return(market)
    stock_ret = stock_monthly_return(market)

    income = assets.deposit * deposit_ret + assets.bond * bond_ret + assets.stock * stock_ret
    grown = AssetBalances(
        deposit=assets.deposit * (1 + deposit_ret),
        bond=assets.bond * (1 + bond_ret),
        stock=assets.stock * (1 + stock_ret),
    )
    return income, grown


def invest_net_cashflow(assets_after_returns: AssetBalances, to_invest: float, allocation: dict[str, float]) -> AssetBalances:
    if to_invest >= 0:
        return AssetBalances(
            deposit=assets_after_returns.deposit + allocation["deposit"] * to_invest,
            bond=assets_after_returns.bond + allocation["bond"] * to_invest,
            stock=assets_after_returns.stock + allocation["stock"] * to_invest,
        )

    total = assets_after_returns.total
    if total <= 0:
        return AssetBalances(deposit=0.0, bond=0.0, stock=0.0)

    return AssetBalances(
        deposit=max(0.0, assets_after_returns.deposit + (assets_after_returns.deposit / total) * to_invest),
        bond=max(0.0, assets_after_returns.bond + (assets_after_returns.bond / total) * to_invest),
        stock=max(0.0, assets_after_returns.stock + (assets_after_returns.stock / total) * to_invest),
    )


def compute_opex(total_in_force: float) -> float:
    return OPEX_BASE * (1 + 0.02 * math.log(1 + total_in_force))


def compute_snapshot(
    turn: int,
    premium_income: float,
    investment_income: float,
    death_claims: float,
    surrender_payouts: float,
    maturity_payouts: float,
    commission_expense: float,
    marketing_expense: float,
    opex: float,
    reserve_change: float,
    equity_start: float,
    dividend_payout: float,
    assets: AssetBalances,
    total_reserve: float,
) -> FinancialSnapshot:
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
    )
    equity = equity_start + net_income - dividend_payout
    status = GameStatus.BANKRUPT if equity <= 0 else GameStatus.RUNNING

    return FinancialSnapshot(
        turn=turn,
        premium_income=premium_income,
        investment_income=investment_income,
        death_claims=death_claims,
        surrender_payouts=surrender_payouts,
        maturity_payouts=maturity_payouts,
        commission_expense=commission_expense,
        marketing_expense=marketing_expense,
        opex=opex,
        reserve_change=reserve_change,
        net_income=net_income,
        deposit_balance=assets.deposit,
        bond_balance=assets.bond,
        stock_balance=assets.stock,
        total_reserve=total_reserve,
        equity=equity,
        status=status,
    )
