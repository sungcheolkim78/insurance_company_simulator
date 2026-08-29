import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.engine.types import ChannelCode, Decision, ProductCode
from app.models import GameRow
from app.repository import apply_turn, create_game


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def base_decision() -> Decision:
    return Decision(
        pricing_multiplier={ProductCode.WHOLE_LIFE: 1.0, ProductCode.SAVINGS: 1.0},
        underwriting_strictness={ProductCode.WHOLE_LIFE: 0.3, ProductCode.SAVINGS: 0.0},
        commission_rate={ChannelCode.CAPTIVE: 0.30, ChannelCode.GA: 0.45},
        marketing_spend={ChannelCode.CAPTIVE: 10_000_000, ChannelCode.GA: 15_000_000},
        asset_allocation={"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        dividend_payout=0.0,
    )


def test_create_game_seeds_initial_snapshot():
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)

    assert game.id is not None
    assert game.current_turn == 0
    assert game.status == "running"


def test_apply_turn_persists_snapshot_and_advances_game():
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)

    snapshot = apply_turn(session, game.id, base_decision())

    assert snapshot.turn == 1
    assert snapshot.status == "running"
    assert snapshot.premium_income == pytest.approx(10121850.0)
    assert snapshot.total_csm > 0
    refreshed = session.get(GameRow, game.id)
    assert refreshed.current_turn == 1


def test_apply_turn_second_turn_releases_csm_from_surviving_cohorts():
    """A cohort's csm_balance/csm_locked_in_rate_monthly/csm_straight_line_release/
    csm_periods_remaining fields make a full DB round-trip (CohortRow -> active_cohorts()
    -> CohortState -> back to CohortRow) between apply_turn calls. A single apply_turn call
    can't catch a silently-dropped field here, since a turn-1 cohort's CSM fields are only
    ever *read back* from the DB on turn 2. Calling apply_turn twice for the same game and
    asserting csm_release > 0 on the second call exercises that round-trip.

    Turn 2 uses zero marketing_spend so channel_capacity (and thus new business) is exactly
    zero — see products.channel_capacity, which multiplies by sqrt(marketing_spend / ...).
    That isolates the assertion to turn-1 cohorts genuinely surviving the round-trip and
    still releasing CSM on turn 2, rather than being satisfied by turn 2's own brand-new
    cohorts (which would mask a silently-dropped field on the surviving ones).
    """
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)

    apply_turn(session, game.id, base_decision())
    turn_2_decision = base_decision()
    turn_2_decision.marketing_spend = {ChannelCode.CAPTIVE: 0.0, ChannelCode.GA: 0.0}
    snapshot_2 = apply_turn(session, game.id, turn_2_decision)

    assert snapshot_2.turn == 2
    assert snapshot_2.new_policies_by_product == {"whole_life": 0, "savings": 0}
    assert snapshot_2.csm_release > 0


def test_apply_turn_rejects_finished_game():
    session = make_session()
    game = create_game(session, initial_capital=10_000_000_000.0, rng_seed=42)
    game.status = "bankrupt"
    session.add(game)
    session.commit()

    with pytest.raises(ValueError):
        apply_turn(session, game.id, base_decision())
