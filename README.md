# 보험회사 운영 시뮬레이션 (Insurance Company Simulator)

턴제(월 단위, 총 120턴/10년) 보험회사 경영 시뮬레이션 웹 애플리케이션입니다.  
플레이어는 보험사의 최고경영자(CEO)가 되어 매월 신계약 판매, 언더라이팅, 영업채널 수수료/마케팅, 자산 배분, 배당 결정을 내리며 10년 후 **최종 순자산(자본총계)**을 극대화하는 것을 목표로 합니다.

---

## 📖 핵심 게임 시스템

### 1. 주요 의사결정 영역
- **상품 가격 및 언더라이팅**:
  - `whole_life` (종신보험): 사망보장 중심 상품. 언더라이팅을 강화하면 사망률이 감소하지만 승인율이 하락합니다.
  - `savings` (저축성보험): 5년(60턴) 만기 적립/이자부리 상품. 만기 시 원리금이 지급됩니다.
- **영업채널 관리**:
  - `captive` (전속설계사): 안정적인 판매량, 마케팅비 및 수수료율 민감도 반응.
  - `ga` (법인대리점): 높은 수수료율 민감도와 판매 생산성.
- **자산 배분 (신규 현금흐름 기준)**:
  - `deposit` (예금): 고정 안전 금리.
  - `bond` (채권): 시장금리 연동 이자수익.
  - `stock` (주식): 국면(Normal/Boom/Crisis)에 따른 마코프 체인 기반 확률적 고위험·고수익.
- **배당 정책**:
  - `dividend_payout`: 주주 배당금 지급 및 자본 관리.

### 2. 시뮬레이션 파이프라인 (매 턴)
```
1. 영업채널 역량 계산 (마케팅비, 수수료율)
2. 신계약 청약 및 인수심사(언더라이팅) 통과율 산출 -> 새 코호트 생성
3. 기존 코호트 전이 (사망, 해지, 만기금 지급 및 준비금 갱신)
4. 시장 상태 갱신 (금리 평균회귀 + 주가 레짐 마코프 체인)
5. 자산운용 수익 인식 및 신규 순현금흐름 자산 배분
6. 손익계산서(P&L) 및 재무상태표(B/S) 롤포워드 -> 순자산(Equity) 갱신
```

### 3. 게임 종료 조건
- **정상 종료 (`completed`)**: 120턴(10년) 완주 시 종료.
- **파산 (`bankrupt`)**: 턴 종료 시점 순자산(자본총계) $\le$ 0 일 경우 즉시 파산 처리.

---

## 🛠 기술 스택 & 아키텍처

- **Backend**: Python 3.11+, FastAPI, SQLModel (SQLAlchemy 2.0 + Pydantic), SQLite
- **Simulation Engine**: `backend/app/engine/` (DB/웹 의존성이 없는 순수 Python + NumPy 시뮬레이션 엔진)
- **Frontend**: Vue 3 (Composition API), Vite, Tailwind CSS v4, Pinia, Vue Router, Chart.js (`vue-chartjs`)
- **Containers**: Podman Compose / Docker Compose

---

## 🚀 빠른 시작 (Container)

권장 실행 환경은 `podman-compose` 또는 `docker-compose`입니다.

```bash
# 컨테이너 빌드 및 실행
podman-compose up --build
# 또는
docker-compose up --build
```

- **Frontend**: [http://localhost:5173](http://localhost:5173)  
  *(⚠️ 주의: 백엔드 CORS 설정에 따라 `127.0.0.1`이 아닌 `localhost`로 접속해야 합니다.)*
- **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

종료:
```bash
podman-compose down
```

> ⚠️ **DB 스키마 변경 시 주의**: 이 프로젝트에는 마이그레이션 도구가 없습니다. `init_db()`(`backend/app/db.py`)는 `SQLModel.metadata.create_all()`을 호출하는데, 이는 존재하지 않는 테이블만 새로 생성할 뿐 기존 테이블의 컬럼은 변경하지 않습니다. `backend/app/models.py`를 건드린 변경사항을 pull한 뒤에는 기존 DB를 반드시 재생성해야 합니다:
> - 컨테이너 환경: `podman-compose down` 후 `podman volume rm <project>_backend-data` 실행, 그다음 `podman-compose up --build -d`
> - 로컬 실행: `backend/data/simulator.db` 파일 삭제
>
> 재생성하지 않으면 이전 스키마의 DB 파일에 접근하는 모든 요청이 500 에러를 반환합니다.

---

## 💻 로컬 개발 환경 실행

### 1. 백엔드 (Backend)

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 패키지 및 개발 의존성 설치
pip install -e ".[dev]"

# 개발 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 2. 프론트엔드 (Frontend)

별도의 터미널에서 실행:

```bash
cd frontend

# 의존성 설치
npm install

# Vite 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
```

---

## 🧪 테스트 실행

백엔드는 `pytest` 기반 단위 및 통합 테스트를 제공합니다.

```bash
# 가상환경이 활성화된 상태에서
cd backend
pytest -v

# 또는 루트 디렉토리에서 바로 실행
backend/.venv/bin/pytest backend/tests -v
```

---

## 📡 API 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| `POST` | `/games` | 새 게임 생성 (`initial_capital`, `rng_seed`) |
| `GET` | `/games` | 저장된 게임 목록 조회 |
| `GET` | `/games/{id}` | 특정 게임 상태 및 최신 재무 스냅샷 조회 |
| `GET` | `/games/{id}/config` | 게임 기본 설정(상품 및 채널 메타데이터) 조회 |
| `GET` | `/games/{id}/history` | 게임 전체 턴 재무 스냅샷 히스토리 조회 |
| `POST` | `/games/{id}/turn` | 의사결정 제출 및 다음 턴(1턴) 진행 |
| `DELETE` | `/games/{id}` | 게임 및 연관 데이터(코호트, 스냅샷 등) 삭제 |
| `GET` | `/health` | 서버 상태 점검 |

---

## 📂 프로젝트 디렉토리 구조

```
insurance_company_simulator/
├── backend/                      # FastAPI 백엔드 & 시뮬레이션 엔진
│   ├── app/
│   │   ├── api/                  # REST API 라우터 (/games)
│   │   ├── engine/               # 독립된 순수 Python 시뮬레이션 코어
│   │   ├── db.py                 # SQLite DB 세션 및 테이블 초기화
│   │   ├── models.py             # SQLModel 엔티티 정의
│   │   ├── repository.py         # DB 트랜잭션 및 엔진 연동 레포지토리
│   │   ├── schemas.py            # API 요청/응답 Pydantic 스키마
│   │   └── main.py               # FastAPI 애플리케이션 진입점
│   ├── tests/                    # pytest 테스트 스위트 (엔진 및 API)
│   ├── pyproject.toml            # 파이썬 의존성 설정
│   └── Dockerfile
├── frontend/                     # Vue 3 SPA 프론트엔드
│   ├── src/
│   │   ├── api/                  # Axios HTTP 클라이언트
│   │   ├── components/           # UI 컴포넌트 (의사결정 패널, 차트, KPI 카드)
│   │   ├── stores/               # Pinia 게임 상태 관리
│   │   ├── views/                # 화면 뷰 (게임 생성, 대시보드, 결과)
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docs/                         # 상세 기획 및 아키텍처 스펙 문서
│   └── superpowers/
│       ├── specs/2026-08-29-insurance-simulator-phase1-design.md
│       └── plans/2026-08-29-insurance-simulator-phase1.md
├── docker-compose.yml            # 멀티 컨테이너 오케스트레이션 설정
├── CLAUDE.md                     # AI 어시스턴트 개발 가이드
└── README.md
```

---

## 📚 관련 문서
- [시뮬레이션 수식 및 아키텍처 명세서](docs/simulation/simulation_formulas.md)
- [Phase 1 설계 스펙](docs/superpowers/specs/2026-08-29-insurance-simulator-phase1-design.md)
- [Phase 1 구현 계획서](docs/superpowers/plans/2026-08-29-insurance-simulator-phase1.md)
