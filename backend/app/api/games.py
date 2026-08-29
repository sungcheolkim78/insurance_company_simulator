import random

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .. import repository
from ..db import get_session
from ..engine.config import DEFAULT_CHANNEL_CONFIGS, DEFAULT_PRODUCT_CONFIGS
from ..engine.types import ChannelCode, Decision, ProductCode
from ..models import CohortRow, DecisionRow, FinancialSnapshotRow, GameRow, MarketStateRow
from ..schemas import ConfigResponse, CreateGameRequest, GameStateResponse, GameSummary, SnapshotResponse, TurnRequest

router = APIRouter(prefix="/games", tags=["games"])


def _snapshot_to_schema(row: FinancialSnapshotRow) -> SnapshotResponse:
    return SnapshotResponse(**row.model_dump(exclude={"id", "game_id"}))


def _game_state(session: Session, game: GameRow) -> GameStateResponse:
    snapshot = repository.latest_snapshot(session, game.id)
    return GameStateResponse(
        id=game.id,
        current_turn=game.current_turn,
        status=game.status,
        game_length_turns=game.game_length_turns,
        snapshot=_snapshot_to_schema(snapshot),
    )


def _config_dict(cfg) -> dict:
    data = vars(cfg).copy()
    data["code"] = data["code"].value
    return data


@router.post("", response_model=GameStateResponse)
def create_game(payload: CreateGameRequest, session: Session = Depends(get_session)) -> GameStateResponse:
    seed = payload.rng_seed if payload.rng_seed is not None else random.randint(0, 2**31 - 1)
    game = repository.create_game(session, payload.initial_capital, seed, payload.game_length_turns)
    return _game_state(session, game)


@router.get("", response_model=list[GameSummary])
def list_games(session: Session = Depends(get_session)) -> list[GameSummary]:
    games = session.exec(select(GameRow)).all()
    return [
        GameSummary(id=g.id, current_turn=g.current_turn, status=g.status, game_length_turns=g.game_length_turns)
        for g in games
    ]


@router.get("/{game_id}", response_model=GameStateResponse)
def get_game(game_id: int, session: Session = Depends(get_session)) -> GameStateResponse:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    return _game_state(session, game)


@router.get("/{game_id}/config", response_model=ConfigResponse)
def get_config(game_id: int, session: Session = Depends(get_session)) -> ConfigResponse:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    return ConfigResponse(
        products={code.value: _config_dict(cfg) for code, cfg in DEFAULT_PRODUCT_CONFIGS.items()},
        channels={code.value: _config_dict(cfg) for code, cfg in DEFAULT_CHANNEL_CONFIGS.items()},
    )


def _decision_from_request(payload: TurnRequest) -> Decision:
    return Decision(
        pricing_multiplier={ProductCode(k): v for k, v in payload.pricing_multiplier.items()},
        underwriting_strictness={ProductCode(k): v for k, v in payload.underwriting_strictness.items()},
        commission_rate={ChannelCode(k): v for k, v in payload.commission_rate.items()},
        marketing_spend={ChannelCode(k): v for k, v in payload.marketing_spend.items()},
        asset_allocation=payload.asset_allocation,
        dividend_payout=payload.dividend_payout,
    )


@router.get("/{game_id}/history", response_model=list[SnapshotResponse])
def get_history(game_id: int, session: Session = Depends(get_session)) -> list[SnapshotResponse]:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    rows = session.exec(
        select(FinancialSnapshotRow).where(FinancialSnapshotRow.game_id == game_id).order_by(FinancialSnapshotRow.turn)
    ).all()
    return [_snapshot_to_schema(row) for row in rows]


@router.post("/{game_id}/turn", response_model=GameStateResponse)
def submit_turn(game_id: int, payload: TurnRequest, session: Session = Depends(get_session)) -> GameStateResponse:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    try:
        repository.apply_turn(session, game_id, _decision_from_request(payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    session.refresh(game)
    return _game_state(session, game)


@router.delete("/{game_id}")
def delete_game(game_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    game = session.get(GameRow, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    for model in (CohortRow, MarketStateRow, DecisionRow, FinancialSnapshotRow):
        for row in session.exec(select(model).where(model.game_id == game_id)).all():
            session.delete(row)
    session.delete(game)
    session.commit()
    return {"deleted": True}
