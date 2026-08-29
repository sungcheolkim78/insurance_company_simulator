# CLAUDE.md

Guidance and instructions for working on the **Insurance Company Simulator** project.

---

## Project Overview

**Insurance Company Simulator (보험회사 운영 시뮬레이션)** is a turn-based (monthly, 120 turns / 10 years) single-player insurance company management simulation game.

The player acts as CEO / chief management making strategic decisions each month:
- **Product Pricing & Underwriting:** Whole Life (`whole_life`) & Savings (`savings`)
- **Sales Channel Management:** Direct / Captive Agents (`captive`) & General Agencies (`ga`)
- **Asset Allocation:** Deposits (`deposit`), Bonds (`bond`), and Equities (`stock`)
- **Capital & Dividend Policy:** Dividend payouts and capital preservation

### Core Simulation Loop
```
Channel Marketing & Commissions -> New Policy Applications & Underwriting -> In-Force Cohorts Update
  -> Premium Income & Reserve Accruals -> Asset Allocation & Investment Returns
  -> Decrement (Death Claims / Surrenders / Maturities) & Expenses (Commissions / Marketing / Opex)
  -> Net Income & Balance Sheet Update -> Equity Roll-forward
```

### Game Termination & Scoring
- **Max Turns:** 120 turns (10 years, status: `completed`).
- **Bankruptcy:** If equity $\le$ 0 at end of turn (status: `bankrupt`).
- **Score:** Final equity at turn 120 (or bankrupt turn and final equity).

---

## Architecture & Codebase Structure

```
insurance_company_simulator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── games.py          # FastAPI REST routes (/games, /games/{id}/turn, etc.)
│   │   ├── engine/               # Pure Python simulation engine (NO DB/web dependencies)
│   │   │   ├── cohorts.py        # Policy cohort transition (mortality, lapses, reserves)
│   │   │   ├── config.py         # Default product/channel parameters and constants
│   │   │   ├── finance.py        # Investment income, expenses, cashflows, balance sheets
│   │   │   ├── market.py         # Stochastic interest rate & stock regime Markov chain
│   │   │   ├── products.py       # Channel capacity & new business pricing elasticity
│   │   │   └── types.py          # Engine dataclasses & enums
│   │   ├── db.py                 # SQLite engine & session dependency
│   │   ├── models.py             # SQLModel table definitions (GameRow, CohortRow, etc.)
│   │   ├── repository.py         # DB orchestration connecting engine with DB models
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   └── main.py               # FastAPI app entry point & CORS configuration
│   ├── tests/
│   │   ├── engine/               # Unit tests for pure engine modules
│   │   │   ├── test_cohorts.py
│   │   │   ├── test_config.py
│   │   │   ├── test_finance.py
│   │   │   ├── test_market.py
│   │   │   ├── test_products.py
│   │   │   └── test_turn.py
│   │   ├── conftest.py           # Pytest SQLite fixtures & API test client
│   │   ├── test_api_games_crud.py# API CRUD tests
│   │   ├── test_api_turn.py      # Game progression API tests
│   │   ├── test_main.py          # App health check tests
│   │   └── test_repository.py    # Repository layer tests
│   ├── pyproject.toml            # Backend dependencies & metadata
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js         # Axios API client for backend endpoints
│   │   ├── components/
│   │   │   ├── DecisionPanel.vue # Input controls for pricing, strictness, channels, assets
│   │   │   ├── HistoryCharts.vue # Chart.js equity time series
│   │   │   ├── KpiCards.vue      # Current equity, net income, reserve cards
│   │   │   └── TurnControl.vue   # Auto-advance turns component
│   │   ├── stores/
│   │   │   └── gameStore.js      # Pinia state management for game & history
│   │   ├── views/
│   │   │   ├── DashboardView.vue # Main dashboard view for active gameplay
│   │   │   ├── NewGameView.vue   # Game setup screen (capital, seed)
│   │   │   └── ResultView.vue    # Game over / completion result screen
│   │   ├── App.vue
│   │   ├── main.js               # Vue app initialization and Vue Router setup
│   │   └── style.css             # Tailwind CSS imports
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docs/                         # Specifications and implementation plans
│   ├── simulation/               # Detailed simulation formulas and architecture docs
│   │   └── simulation_formulas.md
│   └── superpowers/
│       ├── specs/2026-08-29-insurance-simulator-phase1-design.md
│       └── plans/2026-08-29-insurance-simulator-phase1.md
├── docker-compose.yml
└── README.md
```

---

## Development & Testing Commands

### 1. Running with Containers (Podman / Docker)

```bash
# Start all services with rebuild
podman-compose up --build
# or
docker-compose up --build

# Tear down services
podman-compose down
```
- Backend API: `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`)
- Frontend Web: `http://localhost:5173` *(Access via `localhost`, not `127.0.0.1` due to CORS)*

---

### 2. Running Locally

#### Backend
```bash
cd backend

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install editable package with dev dependencies
pip install -e ".[dev]"

# Run FastAPI dev server
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

### 3. Running Backend Tests

```bash
# From repo root (using backend venv)
backend/.venv/bin/pytest backend/tests -v

# Or inside backend/ directory with activated venv
cd backend
source .venv/bin/activate
pytest -v
```

---

## Key Development Conventions & Guidelines

### 1. Engine vs. Application Layer Isolation
- `backend/app/engine/` must remain **pure Python** (plus `numpy`).
- Never import FastAPI, SQLModel, database sessions, or external HTTP clients inside `backend/app/engine/`.
- All engine functions should be deterministic when supplied with `numpy.random.Generator(seed)`.
- All DB mutations and session lifecycle must be managed in `backend/app/repository.py` and `backend/app/api/`.

### 2. Backend Coding Standards
- Python 3.11+ type hints (`dict[str, Any]`, `list[CohortState]`, `float | None`).
- Use `SQLModel` for ORM models (`app/models.py`) and Pydantic models for request/response payloads (`app/schemas.py`).
- Maintain SQLite database schema compatibility; tables are initialized via `init_db()` in `app/db.py`.

### 3. Frontend Coding Standards
- Vue 3 Composition API using `<script setup>` SFCs.
- State management strictly in Pinia stores (`src/stores/gameStore.js`).
- Tailwind CSS v4 for utility classes.
- Charting with `chart.js` and `vue-chartjs`.

### 4. API Endpoints Reference
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/games` | Create a new game instance (`initial_capital`, `rng_seed`) |
| `GET` | `/games` | List all saved games |
| `GET` | `/games/{id}` | Get current game state and snapshot |
| `GET` | `/games/{id}/config` | Get product and channel configurations |
| `GET` | `/games/{id}/history` | Get full turn snapshots history |
| `POST` | `/games/{id}/turn` | Submit player decisions and advance 1 turn |
| `DELETE` | `/games/{id}` | Delete game and all related records |
| `GET` | `/health` | Healthcheck endpoint |
