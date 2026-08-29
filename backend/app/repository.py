import numpy as np
from sqlmodel import Session, select

from .engine.config import LONG_RUN_RATE
from .engine.turn import run_turn
from .engine.types import (
    AssetBalances,
    ChannelCode,
    CohortState,
    Decision,
    GameStatus,
    MarketState,
    ProductCode,
    StockRegime,
)
from .models import CohortRow, DecisionRow, FinancialSnapshotRow, GameRow, MarketStateRow


def create_game(session: Session, initial_capital: float, rng_seed: int) -> GameRow:
    game = GameRow(rng_seed=rng_seed, initial_capital=initial_capital, current_turn=0, status=GameStatus.RUNNING.value)
    session.add(game)
    session.commit()
    session.refresh(game)

    session.add(
        MarketStateRow(
            game_id=game.id,
            turn=0,
            interest_rate=LONG_RUN_RATE,
            stock_regime=StockRegime.NORMAL.value,
            stock_return_realized=None,
        )
    )
    session.add(
        FinancialSnapshotRow(
            game_id=game.id,
            turn=0,
            premium_income=0.0,
            investment_income=0.0,
            death_claims=0.0,
            surrender_payouts=0.0,
            maturity_payouts=0.0,
            commission_expense=0.0,
            marketing_expense=0.0,
            opex=0.0,
            reserve_change=0.0,
            net_income=0.0,
            deposit_balance=initial_capital * 0.3,
            bond_balance=initial_capital * 0.4,
            stock_balance=initial_capital * 0.3,
            total_reserve=0.0,
            equity=initial_capital,
            status=GameStatus.RUNNING.value,
        )
    )
    session.commit()
    return game


def latest_market_state(session: Session, game_id: int) -> MarketState:
    row = session.exec(
        select(MarketStateRow).where(MarketStateRow.game_id == game_id).order_by(MarketStateRow.turn.desc())
    ).first()
    return MarketState(
        turn=row.turn,
        interest_rate=row.interest_rate,
        stock_regime=StockRegime(row.stock_regime),
        stock_return_realized=row.stock_return_realized,
    )


def latest_snapshot(session: Session, game_id: int) -> FinancialSnapshotRow:
    return session.exec(
        select(FinancialSnapshotRow)
        .where(FinancialSnapshotRow.game_id == game_id)
        .order_by(FinancialSnapshotRow.turn.desc())
    ).first()


def active_cohorts(session: Session, game_id: int) -> list[CohortState]:
    rows = session.exec(select(CohortRow).where(CohortRow.game_id == game_id)).all()
    return [
        CohortState(
            product=ProductCode(row.product),
            channel=ChannelCode(row.channel),
            issue_turn=row.issue_turn,
            in_force_count=row.in_force_count,
            unit_size=row.unit_size,
            reserve_balance=row.reserve_balance,
        )
        for row in rows
    ]


def apply_turn(session: Session, game_id: int, decision: Decision) -> FinancialSnapshotRow:
    game = session.get(GameRow, game_id)
    if game.status != GameStatus.RUNNING.value:
        raise ValueError(f"game {game_id} is not running (status={game.status})")

    market_state = latest_market_state(session, game_id)
    snapshot = latest_snapshot(session, game_id)
    assets = AssetBalances(deposit=snapshot.deposit_balance, bond=snapshot.bond_balance, stock=snapshot.stock_balance)
    cohorts = active_cohorts(session, game_id)

    rng = np.random.default_rng(game.rng_seed + game.current_turn)
    result = run_turn(game.current_turn, cohorts, market_state, assets, snapshot.equity, decision, rng)

    session.add(
        DecisionRow(
            game_id=game_id,
            turn=result.snapshot.turn,
            pricing_multiplier={k.value: v for k, v in decision.pricing_multiplier.items()},
            underwriting_strictness={k.value: v for k, v in decision.underwriting_strictness.items()},
            commission_rate={k.value: v for k, v in decision.commission_rate.items()},
            marketing_spend={k.value: v for k, v in decision.marketing_spend.items()},
            asset_allocation=decision.asset_allocation,
            dividend_payout=decision.dividend_payout,
        )
    )

    for row in session.exec(select(CohortRow).where(CohortRow.game_id == game_id)).all():
        session.delete(row)
    for cohort in result.cohorts:
        session.add(
            CohortRow(
                game_id=game_id,
                product=cohort.product.value,
                channel=cohort.channel.value,
                issue_turn=cohort.issue_turn,
                in_force_count=cohort.in_force_count,
                unit_size=cohort.unit_size,
                reserve_balance=cohort.reserve_balance,
            )
        )

    session.add(
        MarketStateRow(
            game_id=game_id,
            turn=result.market_state.turn,
            interest_rate=result.market_state.interest_rate,
            stock_regime=result.market_state.stock_regime.value,
            stock_return_realized=result.market_state.stock_return_realized,
        )
    )

    snapshot_row = FinancialSnapshotRow(
        game_id=game_id,
        turn=result.snapshot.turn,
        premium_income=result.snapshot.premium_income,
        investment_income=result.snapshot.investment_income,
        death_claims=result.snapshot.death_claims,
        surrender_payouts=result.snapshot.surrender_payouts,
        maturity_payouts=result.snapshot.maturity_payouts,
        commission_expense=result.snapshot.commission_expense,
        marketing_expense=result.snapshot.marketing_expense,
        opex=result.snapshot.opex,
        reserve_change=result.snapshot.reserve_change,
        net_income=result.snapshot.net_income,
        deposit_balance=result.snapshot.deposit_balance,
        bond_balance=result.snapshot.bond_balance,
        stock_balance=result.snapshot.stock_balance,
        total_reserve=result.snapshot.total_reserve,
        equity=result.snapshot.equity,
        status=result.snapshot.status.value,
    )
    session.add(snapshot_row)

    game.current_turn = result.snapshot.turn
    game.status = result.snapshot.status.value
    session.add(game)

    session.commit()
    session.refresh(snapshot_row)
    return snapshot_row
