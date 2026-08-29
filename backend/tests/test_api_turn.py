import pytest


def turn_payload():
    return {
        "pricing_multiplier": {"whole_life": 1.0, "savings": 1.0},
        "underwriting_strictness": {"whole_life": 0.3, "savings": 0.0},
        "commission_rate": {"captive": 0.30, "ga": 0.45},
        "marketing_spend": {"captive": 10_000_000, "ga": 15_000_000},
        "asset_allocation": {"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        "dividend_payout": 0.0,
    }


def test_submit_turn_advances_game_and_matches_engine_reference(client):
    create = client.post("/games", json={"initial_capital": 10_000_000_000, "rng_seed": 42})
    game_id = create.json()["id"]

    response = client.post(f"/games/{game_id}/turn", json=turn_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["current_turn"] == 1
    assert body["snapshot"]["turn"] == 1
    assert body["snapshot"]["premium_income"] == pytest.approx(10121850.0)
    # equity fixture reflects create_game's actual starting allocation (100% deposit, per
    # repository.py's create_game — NOT Task 7's engine-test starting mix of 3e9/4e9/3e9,
    # which was an illustrative input for testing run_turn in isolation, not a claim about
    # what a newly created game's portfolio looks like)
    assert body["snapshot"]["equity"] == pytest.approx(9987254466.40991)

    history = client.get(f"/games/{game_id}/history")
    assert history.status_code == 200
    assert [row["turn"] for row in history.json()] == [0, 1]


def test_submit_turn_on_missing_game_returns_404(client):
    response = client.post("/games/999/turn", json=turn_payload())
    assert response.status_code == 404


def test_delete_game_removes_it(client):
    created = client.post("/games", json={})
    game_id = created.json()["id"]

    response = client.delete(f"/games/{game_id}")
    assert response.status_code == 200
    assert client.get(f"/games/{game_id}").status_code == 404
