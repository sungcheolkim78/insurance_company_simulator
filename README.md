# 보험회사 운영 시뮬레이션 (Insurance Company Simulator)

턴제(월 단위) 보험회사 경영 시뮬레이션 게임. 10년(120턴) 동안 보험 판매, 자산운용, 영업채널 운영을
결정하며 최종 순자산을 최대화하는 것이 목표입니다.

설계 스펙: `docs/superpowers/specs/2026-08-29-insurance-simulator-phase1-design.md`
구현 계획: `docs/superpowers/plans/2026-08-29-insurance-simulator-phase1.md`

## Run with podman-compose (recommended)

```bash
podman-compose up --build
```

- Backend: http://localhost:8000 (docs at http://localhost:8000/docs)
- Frontend: http://localhost:5173

**Important:** open the frontend at `http://localhost:5173`, not `http://127.0.0.1:5173` — the
backend's CORS policy only allows the `localhost` origin.

Stop with `podman-compose down`.

## Run locally without containers

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

## Run backend tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```
