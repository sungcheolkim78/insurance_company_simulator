# User Authentication and Game Ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add email/password accounts with PostgreSQL-backed server sessions, protect all game data by ownership, and support login persistence on the Render deployment.

**Architecture:** FastAPI creates and validates opaque session tokens stored as SHA-256 hashes in PostgreSQL; the browser receives only an HttpOnly Secure cookie. A `get_current_user` dependency authenticates requests, and every game query includes the authenticated user's ID. Vue keeps authentication state in a Pinia store, restores it through `/auth/me`, and guards game routes.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel, PostgreSQL via `psycopg[binary]`, Alembic, Argon2 via `argon2-cffi`, Vue 3, Pinia, Vue Router, Axios, pytest, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-31-authentication-design.md`

## Global Constraints

- `backend/app/engine/` remains pure Python and does not import FastAPI, SQLModel, database sessions, or HTTP clients.
- Passwords use Argon2id; plaintext passwords and raw session tokens are never logged or persisted.
- Session cookie name is `insurance_session`; production attributes are `HttpOnly`, `Secure`, `SameSite=None`, and `Path=/`.
- Render production uses PostgreSQL through `DATABASE_URL`; local development may fall back to SQLite.
- CORS uses exact configured origins and `allow_credentials=True`; wildcard origins are forbidden.
- Unauthenticated game requests return `401`; authenticated requests for another user's game return `404`.
- Existing simulation behavior and engine tests must remain unchanged.
- Each task ends with a focused test run and a separate commit.

## File Map

- Create `backend/app/auth.py`: password hashing, session token operations, current-user dependency, and cookie/CSRF helpers.
- Create `backend/app/api/auth.py`: register, login, logout, and current-user routes.
- Create `backend/alembic.ini`, `backend/migrations/env.py`, and `backend/migrations/versions/0001_auth_and_game_ownership.py`: migration configuration and schema migration.
- Create `backend/tests/test_auth.py`: authentication API and security tests.
- Create `backend/tests/test_game_ownership.py`: cross-user game isolation tests.
- Create `frontend/src/stores/authStore.js`: authentication state and actions.
- Create `frontend/src/views/LoginView.vue` and `frontend/src/views/RegisterView.vue`: auth forms.
- Modify `backend/pyproject.toml`: PostgreSQL, Argon2, and Alembic dependencies.
- Modify `backend/app/models.py`: user, session, login-attempt models, and game owner relation.
- Modify `backend/app/schemas.py`: auth payload and user schemas.
- Modify `backend/app/db.py`: configurable PostgreSQL/SQLite engine creation.
- Modify `backend/app/main.py`: auth router, CORS credentials, and CSRF middleware/configuration.
- Modify `backend/app/api/games.py` and `backend/app/repository.py`: authenticated ownership-aware operations.
- Modify `backend/tests/conftest.py`: isolated auth test database setup and helpers.
- Modify `frontend/src/api/client.js`: credentialed requests and auth API functions.
- Modify `frontend/src/main.js`: auth routes and navigation guard.
- Modify `frontend/src/App.vue` and `frontend/src/views/NewGameView.vue`: initialization, user display, logout, and authenticated home behavior.
- Modify `frontend/package.json` only if a router/store testing dependency is required by the existing setup.
- Modify `render.yaml` and `docker-compose.yml`: database/session/CORS environment configuration.
- Modify `README.md`: setup, migration, and authentication API documentation.

---

### Task 1: Add authentication dependencies and database configuration

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/db.py`
- Modify: `backend/tests/conftest.py`
- Modify: `docker-compose.yml`
- Modify: `render.yaml`
- Test: `backend/tests/test_main.py`

**Interfaces:**
- Produces `create_app_engine(database_url: str | None = None) -> Engine` in `app.db`.
- `DATABASE_URL` is read from the environment; `postgres://` is normalized to `postgresql+psycopg://`.
- Existing `get_session()` continues to yield a SQLModel `Session`.

- [ ] **Step 1: Write the failing configuration tests**

Add tests for SQLite fallback and PostgreSQL URL normalization without opening a live PostgreSQL connection:

```python
def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert str(db.database_url()).startswith("sqlite")

def test_postgres_url_is_normalized(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host/db")
    assert db.database_url() == "postgresql+psycopg://user:pass@host/db"
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `backend/.venv/bin/pytest backend/tests/test_main.py -q`

Expected: FAIL because `database_url` and the new dependency configuration do not exist.

- [ ] **Step 3: Add dependencies and configurable engine creation**

Add `alembic`, `argon2-cffi`, and `psycopg[binary]` to the backend dependencies. Implement `database_url()` and `create_app_engine()`, preserving SQLite's `check_same_thread=False` and using the PostgreSQL URL for Render. Keep module-level `engine` and `get_session()` behavior compatible with current tests.

- [ ] **Step 4: Run the focused tests and the existing backend suite**

Run: `backend/.venv/bin/pytest backend/tests/test_main.py backend/tests/engine -q`

Expected: PASS; no engine behavior changes.

- [ ] **Step 5: Add environment keys to local and Render configuration**

Add `DATABASE_URL` as an unset/sync-required variable in `render.yaml`, and document the optional local value in `docker-compose.yml` without committing credentials.

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/app/db.py backend/tests/test_main.py backend/tests/conftest.py docker-compose.yml render.yaml
git commit -m "build: configure postgres authentication dependencies"
```

### Task 2: Add user, session, and login-attempt models with Alembic migration

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/0001_auth_and_game_ownership.py`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_repository.py`

**Interfaces:**
- `UserRow`, `SessionRow`, and `LoginAttemptRow` are SQLModel tables.
- `GameRow.user_id` is a non-null foreign key to `users.id` in the new schema.
- `SQLModel.metadata` includes all auth tables before test database creation.

- [ ] **Step 1: Write model and migration assertions**

Add tests that create a user, session, login-attempt, and owned game in the test database, then assert foreign-key fields and uniqueness constraints are available.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `backend/.venv/bin/pytest backend/tests/test_repository.py -q`

Expected: FAIL because the auth models and `GameRow.user_id` do not exist.

- [ ] **Step 3: Implement the SQLModel tables**

Use UTC-aware timestamps. Add indexed `user_id`, `token_hash`, `expires_at`, `normalized_email`, `client_ip`, and `attempted_at` fields. Make `users.email` and `sessions.token_hash` unique. Add `GameRow.user_id` and update repository-created games to require an owner once Task 5 is implemented.

- [ ] **Step 4: Create Alembic configuration and revision**

Configure Alembic to import `SQLModel.metadata`, read the same normalized `DATABASE_URL`, and generate an explicit revision that creates `users`, `sessions`, and `login_attempts`, then adds the non-null `games.user_id` column for a new PostgreSQL schema. The migration must not silently assign existing games to a user.

- [ ] **Step 5: Run tests and migration validation**

Run: `backend/.venv/bin/pytest backend/tests/test_repository.py -q` and `cd backend && alembic check`.

Expected: PASS for model tests; `alembic check` reports no pending model changes after the revision is applied to a clean database.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models.py backend/alembic.ini backend/migrations backend/tests/conftest.py backend/tests/test_repository.py
git commit -m "feat: add auth and game ownership schema"
```

### Task 3: Implement password hashing, sessions, CSRF, and current-user dependency

**Files:**
- Create: `backend/app/auth.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- `hash_password(password: str) -> str`
- `verify_password(password: str, password_hash: str) -> bool`
- `create_session(session: Session, user: UserRow, response: Response) -> None`
- `get_current_user(request: Request, session: Session) -> UserRow`
- `require_csrf(request: Request) -> None`

- [ ] **Step 1: Write failing unit tests**

Test that Argon2 hashes differ from plaintext, valid passwords verify, invalid passwords fail, session tokens are not stored raw, expired sessions raise HTTP 401, inactive users raise HTTP 401, and unsafe requests without a matching CSRF header/cookie raise HTTP 403.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `backend/.venv/bin/pytest backend/tests/test_auth.py -q`

Expected: FAIL because `app.auth` is absent.

- [ ] **Step 3: Implement the minimal auth primitives**

Use `argon2.PasswordHasher` for password operations and `secrets.token_urlsafe(32)` for session tokens. Hash tokens with SHA-256 before database lookup. Set the session cookie with the configured `HttpOnly`, `Secure`, `SameSite`, `Path`, and 30-day `max_age` values. Generate a separate non-HttpOnly CSRF cookie and compare it with the `X-CSRF-Token` header on POST, PUT, PATCH, and DELETE requests.

- [ ] **Step 4: Add request dependencies and middleware wiring**

Make `get_current_user` retrieve the cookie, hash it, join `SessionRow` to `UserRow`, reject expiration/inactive users, update `last_used_at`, and raise `HTTPException(status_code=401)`. Add an origin check for unsafe cross-origin requests using the configured exact origins before CSRF validation.

- [ ] **Step 5: Run unit and main tests**

Run: `backend/.venv/bin/pytest backend/tests/test_auth.py backend/tests/test_main.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/auth.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: add secure server session primitives"
```

### Task 4: Add authentication API routes

**Files:**
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- `POST /auth/register` returns `UserResponse` with HTTP 201 and establishes a session.
- `POST /auth/login` returns `UserResponse` with HTTP 200 and establishes a session.
- `POST /auth/logout` returns `{"logged_out": true}` and clears the session cookie.
- `GET /auth/me` returns `UserResponse` or HTTP 401.

- [ ] **Step 1: Write failing API tests**

Cover valid registration, invalid email, short password, duplicate email, successful login, wrong credentials, 15-minute/5-attempt rate limit returning 429, `/auth/me` before and after login, logout invalidation, and cookie attributes.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `backend/.venv/bin/pytest backend/tests/test_auth.py -q`

Expected: FAIL because auth schemas/routes do not exist.

- [ ] **Step 3: Add schemas and registration/login helpers**

Define `RegisterRequest`, `LoginRequest`, and `UserResponse`. Normalize email with trim/lowercase. Require a valid email and a password of at least 8 characters. Use one generic 401 message for missing user, wrong password, or inactive account. Record failed attempts in `login_attempts`; reject the sixth recent attempt for the same email/IP pair with 429; clear old attempts after successful login.

- [ ] **Step 4: Implement and mount the auth router**

Create users and sessions in one transaction. On logout, delete the session represented by the current cookie and expire both session and CSRF cookies. Ensure `/auth/me` does not trigger a recursive 401 redirect in the frontend client.

- [ ] **Step 5: Run backend auth and regression tests**

Run: `backend/.venv/bin/pytest backend/tests/test_auth.py backend/tests/test_main.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/auth.py backend/app/schemas.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: add registration and login API"
```

### Task 5: Enforce game ownership in API and repository

**Files:**
- Modify: `backend/app/api/games.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_game_ownership.py`
- Modify: `backend/tests/test_api_games_crud.py`
- Modify: `backend/tests/test_api_turn.py`

**Interfaces:**
- `repository.create_game(session, user_id: int, initial_capital: float, seed: int, game_length_turns: int) -> GameRow`
- `repository.get_owned_game(session, game_id: int, user_id: int) -> GameRow | None`
- Every `/games` route receives `current_user: UserRow = Depends(get_current_user)`.

- [ ] **Step 1: Update tests to create authenticated users**

Add a test helper that registers two accounts and returns two `TestClient` instances sharing the test database. Update existing CRUD/turn tests to authenticate before creating games. Add assertions that unauthenticated requests return 401, user A sees only A's games, and user B receives 404 for A's game detail/config/history/turn/delete endpoints.

- [ ] **Step 2: Run ownership tests and verify failure**

Run: `backend/.venv/bin/pytest backend/tests/test_game_ownership.py backend/tests/test_api_games_crud.py backend/tests/test_api_turn.py -q`

Expected: FAIL because existing game routes are global and `create_game` has no user ID.

- [ ] **Step 3: Make repository operations owner-aware**

Add `user_id` to game creation and add `get_owned_game`. Replace direct `session.get(GameRow, game_id)` in all game handlers with owner-scoped lookup. Filter list queries by `GameRow.user_id == current_user.id`. Preserve the current response models and simulation repository transaction behavior.

- [ ] **Step 4: Apply authentication to every game route**

Protect create, list, get, config, history, turn, and delete routes. Keep missing/foreign games as 404. Confirm deletion only removes related rows after the owner check.

- [ ] **Step 5: Run the full backend suite**

Run: `backend/.venv/bin/pytest backend/tests -q`

Expected: PASS, including engine, repository, auth, ownership, and existing API tests.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/games.py backend/app/repository.py backend/tests/conftest.py backend/tests/test_game_ownership.py backend/tests/test_api_games_crud.py backend/tests/test_api_turn.py
git commit -m "feat: restrict games to authenticated owners"
```

### Task 6: Add frontend authentication state and screens

**Files:**
- Create: `frontend/src/stores/authStore.js`
- Create: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/views/RegisterView.vue`
- Modify: `frontend/src/api/client.js`
- Test: `frontend/src/stores/authStore.test.js`

**Interfaces:**
- `authStore.initialize() -> Promise<void>` loads `/auth/me` once.
- `authStore.login(email, password) -> Promise<User>`.
- `authStore.register(email, password) -> Promise<User>`.
- `authStore.logout() -> Promise<void>`.
- Store state is `user: null | User` and `status: 'unknown' | 'authenticated' | 'anonymous'`.

- [ ] **Step 1: Write failing store tests**

Mock auth API calls and verify initialization sets authenticated/anonymous state, login/register store the user, logout clears it, and an `/auth/me` 401 is treated as anonymous.

- [ ] **Step 2: Run focused frontend tests and verify failure**

Run: `cd frontend && npm run test -- src/stores/authStore.test.js`

Expected: FAIL because the store and auth client methods do not exist.

- [ ] **Step 3: Add credentialed API functions and CSRF handling**

Set Axios `withCredentials: true`. Add `register`, `login`, `logout`, and `getCurrentUser`. Read the non-HttpOnly CSRF cookie and send `X-CSRF-Token` for unsafe requests. Do not redirect on 401 from `/auth/me`, `/auth/login`, or `/auth/register`.

- [ ] **Step 4: Implement the Pinia store**

Implement the stated methods and state transitions. Ensure initialization is idempotent so `main.js` and `App.vue` cannot issue duplicate `/auth/me` calls.

- [ ] **Step 5: Build login and registration views**

Use the existing boardgame design tokens and Composition API. Validate required fields client-side, show generic server errors, disable submit while pending, link between login and registration, and navigate to `/` after success.

- [ ] **Step 6: Run frontend tests and build**

Run: `cd frontend && npm run test && npm run build`

Expected: PASS and successful Vite production build.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/stores/authStore.js frontend/src/stores/authStore.test.js frontend/src/views/LoginView.vue frontend/src/views/RegisterView.vue frontend/src/api/client.js
git commit -m "feat: add frontend authentication flow"
```

### Task 7: Add route guards, user header, and authenticated home behavior

**Files:**
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/NewGameView.vue`
- Test: `frontend/src/utils/authRouting.test.js`

**Interfaces:**
- Routes `/games/:id` and `/games/:id/result` require authentication.
- Routes `/login` and `/register` redirect authenticated users to `/`.
- `App.vue` provides a visible logout action when authenticated.

- [ ] **Step 1: Write failing route behavior tests**

Test that an anonymous user attempting a protected route is redirected to `/login`, an authenticated user can access game routes, and an authenticated user visiting `/login` is redirected home.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `cd frontend && npm run test -- src/utils/authRouting.test.js`

Expected: FAIL because auth routes and guards do not exist.

- [ ] **Step 3: Register routes and navigation guard**

Add `/login` and `/register` routes. Await `authStore.initialize()` before the first protected navigation. Preserve the requested route in `query.redirect` and return there after login when present.

- [ ] **Step 4: Add app initialization and logout UI**

Render a small authenticated header with the user's email and logout button. Display a loading state while auth status is `unknown`. Keep game content in the existing views.

- [ ] **Step 5: Update the home view for authenticated API behavior**

Keep new-game and past-game functionality, but handle 401 by letting the shared auth flow redirect to login. Replace generic load errors with a session-expired message when appropriate.

- [ ] **Step 6: Run frontend tests and build**

Run: `cd frontend && npm run test && npm run build`

Expected: PASS and successful production build.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/main.js frontend/src/App.vue frontend/src/views/NewGameView.vue frontend/src/utils/authRouting.test.js
git commit -m "feat: protect frontend game routes"
```

### Task 8: Configure deployment, document operations, and verify end to end

**Files:**
- Modify: `render.yaml`
- Modify: `docker-compose.yml`
- Modify: `README.md`
- Modify: `backend/tests/test_main.py`
- Create: `backend/tests/test_postgres_compatibility.py`

**Interfaces:**
- Render backend receives `DATABASE_URL`, `CORS_ALLOWED_ORIGINS`, `SESSION_COOKIE_SECURE=true`, and `SESSION_COOKIE_SAMESITE=none`.
- Alembic is the schema deployment command: `cd backend && alembic upgrade head`.
- `/health` remains unauthenticated and returns `{"status": "ok"}`.

- [ ] **Step 1: Add deployment/configuration tests**

Assert `/health` works without a cookie and that production settings reject wildcard CORS when credentials are enabled. Add a PostgreSQL URL parser test using a URL string only, without requiring a live database.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `backend/.venv/bin/pytest backend/tests/test_main.py backend/tests/test_postgres_compatibility.py -q`

Expected: FAIL until deployment settings and validation are added.

- [ ] **Step 3: Update Render and local container configuration**

Add the PostgreSQL `DATABASE_URL` sync variable and session settings to `render.yaml`. Keep the frontend origin in `CORS_ALLOWED_ORIGINS`. Add documented local environment names to `docker-compose.yml` without secrets.

- [ ] **Step 4: Update operational documentation**

Document account creation, login, PostgreSQL provisioning, `alembic upgrade head`, required Render environment variables, cookie/CORS requirements, and the fact that old SQLite games are not automatically assigned to users.

- [ ] **Step 5: Run full verification**

Run:

```bash
backend/.venv/bin/pytest backend/tests -q
cd frontend && npm run test && npm run build
cd ../backend && alembic check
```

Expected: all backend and frontend tests pass, frontend builds, and Alembic reports no pending model changes.

- [ ] **Step 6: Perform manual Render smoke test**

In the deployed HTTPS environment, register two accounts, verify session persistence after refresh, create a game as account A, confirm account B cannot list or access it, verify a turn can be submitted by A, log out, and confirm protected requests return to `/login`.

- [ ] **Step 7: Commit**

```bash
git add render.yaml docker-compose.yml README.md backend/tests/test_main.py backend/tests/test_postgres_compatibility.py
git commit -m "docs: configure render auth deployment"
```

## Plan Self-Review

- Spec coverage: account lifecycle is covered by Tasks 3–4; sessions and cookie security by Task 3; PostgreSQL and migrations by Tasks 1–2 and 8; ownership by Task 5; Vue state and routing by Tasks 6–7; rate limiting and CSRF by Tasks 3–4; tests and deployment verification by Task 8.
- Placeholder scan: no `TODO`, `TBD`, or unspecified implementation choices remain in the task steps.
- Interface consistency: Task 3 produces `get_current_user`; Task 4 mounts auth routes; Task 5 consumes the dependency and owner-aware repository signatures; Tasks 6–7 consume the exact auth client/store methods defined above.
- Existing untracked `.claude/` files are unrelated and must not be staged by any task.
