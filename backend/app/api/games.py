import random

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .. import repository
from ..db import get_session
from ..engine.config import DEFAULT_CHANNEL_CONFIGS, DEFAULT_PRODUCT_CONFIGS
from ..models import FinancialSnapshotRow, GameRow
from ..schemas import ConfigResponse, CreateGameRequest, GameStateResponse, GameSummary, SnapshotResponse

router = APIRouter(prefix="/games", tags=["games"])


def _snapshot_to_schema(row: FinancialSnapshotRow) -> SnapshotResponse:
    return SnapshotResponse(**row.model_dump(exclude={"id", "game_id"}))


def _game_state(session: Session, game: GameRow) -> GameStateResponse:
    snapshot = repository.latest_snapshot(session, game.id)
    return GameStateResponse(
        id=game.id, current_turn=game.current_turn, status=game.status, snapshot=_snapshot_to_schema(snapshot)
    )


def _config_dict(cfg) -> dict:
    data = vars(cfg).copy()
    data["code"] = data["code"].value
    return data


@router.post("", response_model=GameStateResponse)
def create_game(payload: CreateGameRequest, session: Session = Depends(get_session)) -> GameStateResponse:
    seed = payload.rng_seed if payload.rng_seed is not None else random.randint(0, 2**31 - 1)
    game = repository.create_game(session, payload.initial_capital, seed)
    return _game_state(session, game)


@router.get("", response_model=list[GameSummary])
def list_games(session: Session = Depends(get_session)) -> list[GameSummary]:
    games = session.exec(select(GameRow)).all()
    return [GameSummary(id=g.id, current_turn=g.current_turn, status=g.status) for g in games]


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
