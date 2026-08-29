def test_create_and_get_game(client):
    response = client.post("/games", json={"initial_capital": 5_000_000_000, "rng_seed": 7})
    assert response.status_code == 200
    body = response.json()
    game_id = body["id"]
    assert body["current_turn"] == 0
    assert body["snapshot"]["equity"] == 5_000_000_000

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["id"] == game_id


def test_list_games(client):
    client.post("/games", json={})
    client.post("/games", json={})
    response = client.get("/games")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_config(client):
    created = client.post("/games", json={})
    game_id = created.json()["id"]
    response = client.get(f"/games/{game_id}/config")
    assert response.status_code == 200
    body = response.json()
    assert "whole_life" in body["products"]
    assert "captive" in body["channels"]


def test_get_missing_game_returns_404(client):
    response = client.get("/games/999")
    assert response.status_code == 404
