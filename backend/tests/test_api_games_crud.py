from tests.conftest import register_user


def test_create_and_get_game(client):
    register_user(client, "alice@example.com")
    response = client.post("/games", json={"initial_capital": 5_000_000_000, "rng_seed": 7})
    assert response.status_code == 200
    body = response.json()
    game_id = body["id"]
    assert body["current_turn"] == 0
    assert body["snapshot"]["equity"] == 5_000_000_000
    assert body["game_length_turns"] == 120

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["id"] == game_id


def test_create_game_with_custom_game_length_turns(client):
    register_user(client, "alice@example.com")
    response = client.post(
        "/games", json={"initial_capital": 5_000_000_000, "rng_seed": 7, "game_length_turns": 240}
    )
    assert response.status_code == 200
    assert response.json()["game_length_turns"] == 240


def test_create_game_rejects_game_length_turns_out_of_range(client):
    register_user(client, "alice@example.com")
    response = client.post(
        "/games", json={"initial_capital": 5_000_000_000, "rng_seed": 7, "game_length_turns": 601}
    )
    assert response.status_code == 422


def test_list_games(client):
    register_user(client, "alice@example.com")
    client.post("/games", json={"initial_capital": 5_000_000_000})
    client.post("/games", json={"initial_capital": 8_000_000_000})
    response = client.get("/games")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 2
    assert games[0]["equity"] == 8_000_000_000
    assert games[1]["equity"] == 5_000_000_000
    assert "created_at" in games[0]


def test_get_config(client):
    register_user(client, "alice@example.com")
    created = client.post("/games", json={})
    game_id = created.json()["id"]
    response = client.get(f"/games/{game_id}/config")
    assert response.status_code == 200
    body = response.json()
    assert "whole_life" in body["products"]
    assert "captive" in body["channels"]


def test_get_missing_game_returns_404(client):
    register_user(client, "alice@example.com")
    response = client.get("/games/999")
    assert response.status_code == 404
