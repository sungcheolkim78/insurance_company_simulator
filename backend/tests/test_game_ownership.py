def turn_payload():
    return {
        "pricing_multiplier": {"whole_life": 1.0, "savings": 1.0},
        "underwriting_strictness": {"whole_life": 0.3, "savings": 0.0},
        "commission_rate": {"captive": 0.30, "ga": 0.45},
        "marketing_spend": {"captive": 10_000_000, "ga": 15_000_000},
        "asset_allocation": {"deposit": 0.3, "bond": 0.4, "stock": 0.3},
        "dividend_payout": 0.0,
    }


def test_unauthenticated_game_requests_return_401(client):
    from tests.conftest import csrf_headers

    assert client.get("/games").status_code == 401
    assert client.get("/games/1").status_code == 401
    assert client.get("/games/1/config").status_code == 401
    assert client.get("/games/1/history").status_code == 401
    assert client.post("/games", json={}, headers=csrf_headers(client)).status_code == 401
    assert client.post("/games/1/turn", json=turn_payload(), headers=csrf_headers(client)).status_code == 401
    assert client.delete("/games/1", headers=csrf_headers(client)).status_code == 401


def test_user_sees_only_own_games_in_list(two_users):
    alice, bob = two_users
    alice.post("/games", json={"initial_capital": 5_000_000_000})
    alice.post("/games", json={"initial_capital": 6_000_000_000})
    bob.post("/games", json={"initial_capital": 7_000_000_000})

    alice_games = alice.get("/games").json()
    bob_games = bob.get("/games").json()

    assert len(alice_games) == 2
    assert all(game["equity"] in (5_000_000_000, 6_000_000_000) for game in alice_games)
    assert len(bob_games) == 1
    assert bob_games[0]["equity"] == 7_000_000_000


def test_other_user_gets_404_for_foreign_game(two_users):
    alice, bob = two_users
    game_id = alice.post("/games", json={}).json()["id"]

    assert bob.get(f"/games/{game_id}").status_code == 404
    assert bob.get(f"/games/{game_id}/config").status_code == 404
    assert bob.get(f"/games/{game_id}/history").status_code == 404
    assert bob.post(f"/games/{game_id}/turn", json=turn_payload()).status_code == 404
    assert bob.delete(f"/games/{game_id}").status_code == 404


def test_missing_game_returns_404_for_authenticated_user(client):
    from tests.conftest import register_user

    register_user(client, "alice@example.com")
    assert client.get("/games/999").status_code == 404


def test_deletion_by_owner_removes_game(two_users):
    alice, bob = two_users
    game_id = alice.post("/games", json={}).json()["id"]

    response = alice.delete(f"/games/{game_id}")

    assert response.status_code == 200
    assert alice.get(f"/games/{game_id}").status_code == 404
