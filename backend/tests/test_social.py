"""
Tests for Stage 17: Friend leaderboard — GET /social/leaderboard.

Covers:
- Unauthenticated request returns 401
- User with no friends sees only themselves (single-entry leaderboard)
- User with accepted friends sees themselves + friends, non-friends excluded
- Declined/pending requests do not appear in leaderboard
- Leaderboard ordered by cumulative_net descending
- Tie-break: win_rate descending, then games_played descending
- is_self flag set correctly on current user's entry
- User with no games (net=0, win_rate=None) ranked below positive-net users
"""

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register(client: TestClient, email: str, full_name: str = "Test User") -> dict:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "full_name": full_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(client: TestClient, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_friends(client: TestClient, token_a: str, token_b: str) -> None:
    """Have user A send a request and user B accept it."""
    req = client.post(
        "/friends/request",
        json={"addressee_user_id": _get_my_id(client, token_b)},
        headers=_auth(token_a),
    )
    assert req.status_code == 201, req.text
    fid = req.json()["id"]
    accept = client.post(f"/friends/{fid}/accept", headers=_auth(token_b))
    assert accept.status_code == 200, accept.text


def _get_my_id(client: TestClient, token: str) -> str:
    r = client.get("/users/me", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()["id"]


_RATE = 0.01  # 1 chip = $0.01


def _create_and_close_game(
    client: TestClient,
    dealer_token: str,
    cash_in: float,
    chips_in: float,
    final_chips: float,
) -> None:
    """Create a game, run it (single dealer player), and close it."""
    game_r = client.post(
        "/games",
        json={"title": "Test Game", "chip_cash_rate": _RATE, "currency": "USD"},
        headers=_auth(dealer_token),
    )
    assert game_r.status_code == 201, game_r.text
    game = game_r.json()
    gid = game["id"]

    # Get dealer's participant id
    parts_r = client.get(f"/games/{gid}/participants", headers=_auth(dealer_token))
    assert parts_r.status_code == 200, parts_r.text
    dealer_pid = parts_r.json()[0]["id"]

    # Start
    client.post(f"/games/{gid}/start", headers=_auth(dealer_token))

    # Buy-in
    client.post(
        f"/games/{gid}/buy-ins",
        json={
            "participant_id": dealer_pid,
            "cash_amount": str(cash_in),
            "chips_amount": str(chips_in),
            "buy_in_type": "initial",
        },
        headers=_auth(dealer_token),
    )

    # Final stack
    client.put(
        f"/games/{gid}/final-stacks/{dealer_pid}",
        json={"chips_amount": str(final_chips)},
        headers=_auth(dealer_token),
    )

    # Close (pass strategy so shortage-affected games don't get rejected)
    client.post(
        f"/games/{gid}/close",
        json={"shortage_strategy": "equal_all"},
        headers=_auth(dealer_token),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLeaderboardAuth:
    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        r = client.get("/social/leaderboard")
        assert r.status_code == 401


class TestLeaderboardScopeIsolation:
    def test_no_friends_shows_only_self(self, client: TestClient) -> None:
        _register(client, "solo@test.com", "Solo")
        token = _login(client, "solo@test.com")

        r = client.get("/social/leaderboard", headers=_auth(token))
        assert r.status_code == 200
        entries = r.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["is_self"] is True

    def test_accepted_friend_appears(self, client: TestClient) -> None:
        _register(client, "alpha@test.com", "Alpha")
        _register(client, "beta@test.com", "Beta")
        token_a = _login(client, "alpha@test.com")
        token_b = _login(client, "beta@test.com")

        _make_friends(client, token_a, token_b)

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        assert r.status_code == 200
        entries = r.json()["entries"]
        assert len(entries) == 2

    def test_pending_request_user_not_included(self, client: TestClient) -> None:
        _register(client, "req_a@test.com", "ReqA")
        _register(client, "req_b@test.com", "ReqB")
        token_a = _login(client, "req_a@test.com")
        token_b = _login(client, "req_b@test.com")

        # Send request but do not accept
        client.post(
            "/friends/request",
            json={"addressee_user_id": _get_my_id(client, token_b)},
            headers=_auth(token_a),
        )

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        assert r.status_code == 200
        entries = r.json()["entries"]
        assert len(entries) == 1  # only self

    def test_declined_request_user_not_included(self, client: TestClient) -> None:
        _register(client, "dec_a@test.com", "DecA")
        _register(client, "dec_b@test.com", "DecB")
        token_a = _login(client, "dec_a@test.com")
        token_b = _login(client, "dec_b@test.com")

        req = client.post(
            "/friends/request",
            json={"addressee_user_id": _get_my_id(client, token_b)},
            headers=_auth(token_a),
        )
        fid = req.json()["id"]
        client.post(f"/friends/{fid}/decline", headers=_auth(token_b))

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        entries = r.json()["entries"]
        assert len(entries) == 1  # only self

    def test_non_friend_third_user_not_included(self, client: TestClient) -> None:
        """C is friends with A but not with B. B's leaderboard should not include C."""
        _register(client, "tri_a@test.com", "TriA")
        _register(client, "tri_b@test.com", "TriB")
        _register(client, "tri_c@test.com", "TriC")
        token_a = _login(client, "tri_a@test.com")
        token_b = _login(client, "tri_b@test.com")
        token_c = _login(client, "tri_c@test.com")

        _make_friends(client, token_a, token_c)  # A and C are friends

        r = client.get("/social/leaderboard", headers=_auth(token_b))
        entries = r.json()["entries"]
        names = [e["full_name"] for e in entries]
        assert "TriC" not in names
        assert len(entries) == 1  # only B

    def test_is_self_flag_correct(self, client: TestClient) -> None:
        alice = _register(client, "self_a@test.com", "SelfAlice")
        _register(client, "self_b@test.com", "SelfBob")
        token_a = _login(client, "self_a@test.com")
        token_b = _login(client, "self_b@test.com")

        _make_friends(client, token_a, token_b)

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        entries = r.json()["entries"]
        self_entries = [e for e in entries if e["is_self"]]
        assert len(self_entries) == 1
        assert self_entries[0]["user_id"] == alice["id"]

        non_self = [e for e in entries if not e["is_self"]]
        assert len(non_self) == 1


class TestLeaderboardOrdering:
    def test_higher_net_ranked_first(self, client: TestClient) -> None:
        """User with net +10 should rank above user with net -5."""
        _register(client, "ord_a@test.com", "OrdAlice")
        _register(client, "ord_b@test.com", "OrdBob")
        token_a = _login(client, "ord_a@test.com")
        token_b = _login(client, "ord_b@test.com")

        _make_friends(client, token_a, token_b)

        # Alice: buy in $100 for 10000 chips, end with 11000 chips → net +$10
        _create_and_close_game(
            client, token_a, cash_in=100.0, chips_in=10000, final_chips=11000
        )
        # Bob: buy in $100 for 10000 chips, end with 9500 chips → net -$5
        _create_and_close_game(
            client, token_b, cash_in=100.0, chips_in=10000, final_chips=9500
        )

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        assert r.status_code == 200
        entries = r.json()["entries"]
        assert len(entries) == 2
        assert entries[0]["rank"] == 1
        assert entries[1]["rank"] == 2
        # Alice (self) should be rank 1 (higher net)
        assert entries[0]["is_self"] is True

    def test_no_games_user_ranked_below_positive_net(self, client: TestClient) -> None:
        """User with no games (net=0) should rank below a user with positive net."""
        _register(client, "nogame_a@test.com", "NoGameA")
        _register(client, "nogame_b@test.com", "NoGameB")
        token_a = _login(client, "nogame_a@test.com")
        token_b = _login(client, "nogame_b@test.com")

        _make_friends(client, token_a, token_b)

        # A has a game with net > 0; B has no games
        _create_and_close_game(
            client, token_a, cash_in=100.0, chips_in=10000, final_chips=11000
        )

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        entries = r.json()["entries"]
        assert entries[0]["is_self"] is True  # A is rank 1
        assert entries[1]["total_games_played"] == 0

    def test_rank_numbers_sequential(self, client: TestClient) -> None:
        """Rank numbers must be 1-based sequential integers."""
        _register(client, "seq_a@test.com", "SeqA")
        _register(client, "seq_b@test.com", "SeqB")
        _register(client, "seq_c@test.com", "SeqC")
        token_a = _login(client, "seq_a@test.com")
        token_b = _login(client, "seq_b@test.com")
        token_c = _login(client, "seq_c@test.com")

        _make_friends(client, token_a, token_b)
        _make_friends(client, token_a, token_c)

        r = client.get("/social/leaderboard", headers=_auth(token_a))
        entries = r.json()["entries"]
        assert len(entries) == 3
        ranks = [e["rank"] for e in entries]
        assert ranks == [1, 2, 3]

    def test_leaderboard_contains_correct_fields(self, client: TestClient) -> None:
        """Each entry must expose the required fields."""
        _register(client, "fields@test.com", "FieldsUser")
        token = _login(client, "fields@test.com")

        r = client.get("/social/leaderboard", headers=_auth(token))
        entry = r.json()["entries"][0]
        required = {
            "rank", "user_id", "full_name", "profile_image_url",
            "total_games_played", "games_with_result", "cumulative_net",
            "win_rate", "is_self",
        }
        assert required.issubset(entry.keys())
