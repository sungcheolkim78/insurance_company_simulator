# 보험회사 운영 시뮬레이션 게임 — Phase 1 설계 스펙

- 작성일: 2026-08-29
- 상태: 승인 대기 (사용자 검토 중)
- 범위: Phase 1 (MVP 핵심 루프)만 다룬다. Phase 2 이후는 로드맵 절만 참고용으로 기술한다.

## 1. 목표와 게임 개요

플레이어는 보험회사 경영자가 되어 매 턴(1개월) 주요 의사결정을 내리고, 10년(120턴) 동안 회사를
운영한다. 수익 구조는 다음 순환으로 구성된다.

```
영업채널(직대설계사/GA) → 신계약 판매 → 보험료 수입
      → 준비금 적립(부채) → 자산운용(예금/채권/주식) → 운용수익
      → 사망/해지 발생 시 보험금·해지환급금 지급 → 손익 → 자본(순자산) 갱신
```

싱글플레이 게임이며, 120턴 종료 시점(또는 자본잠식으로 인한 조기 파산 시점)의 **최종 순자산(자본총계)**
으로 경영 성과를 평가한다. 마케팅/사망/해지 이벤트는 대수법칙에 따라 기대값으로 처리하고(부분
확률적 모델), 시장 전체에 영향을 주는 금리·주가 변동만 시드 기반 난수로 처리하여 재현성(리플레이,
난이도 조절)을 확보한다.

## 2. 기술 스택

- 백엔드: FastAPI + SQLModel(= SQLAlchemy 2.0 + Pydantic 통합) + SQLite(동기 드라이버)
- 시뮬레이션 엔진: FastAPI/DB에 의존하지 않는 순수 Python 모듈로 분리 (`backend/app/engine/`).
  단위테스트와 향후 밸런싱용 CLI 배치 실행에 재사용한다.
- 프론트엔드: Vue 3 + Tailwind CSS + Pinia(상태관리) + Chart.js 또는 ECharts(차트)
- 수치 계산: 필요 시 numpy 사용 (코호트 배열 연산)

Django, Node/NestJS, 실시간 게임서버 프레임워크(Colyseus 등)는 이 게임의 요청/응답형 턴제
싱글플레이 구조에 이점이 없어 채택하지 않는다 (근거는 브레인스토밍 대화 참고).

로컬 실행 환경은 컨테이너로 표준화한다. `backend/`, `frontend/`에 각각 Dockerfile을 두고,
레포 루트의 `docker-compose.yml`로 두 서비스를 함께 기동한다. 실행은 `podman-compose up --build`
로 바로 되어야 하며(Docker Desktop 없이도 동작), 별도의 프로덕션 배포 구성(리버스 프록시, HTTPS 등)은
Phase 1 범위 밖이다.

## 3. 시간 모델 & 게임 종료 조건

- 1턴 = 1개월, 총 120턴(10년)로 게임 1회차가 종료된다.
- 매 턴: 플레이어 결정 제출 → 엔진이 신계약/기존계약/자산운용/손익/자본을 계산 → 다음 턴으로 이월.
- 조기 종료(파산): 턴 종료 시점 자본(equity) ≤ 0 이면 즉시 게임 종료, 상태를 `bankrupt`로 기록.
- 정상 종료: 120턴 도달 시 상태를 `completed`로 기록.
- 최종 점수: `completed`면 120턴 시점 자본총계, `bankrupt`면 파산 시점 자본총계(보통 0 이하)와
  파산 턴 번호를 함께 표시.
- 보조 지표(참고용 대시보드, 점수에는 미반영): ROE, 총 계약자수(in-force), 손해율(사망금+해지환급금/보험료수입).

## 4. Phase 1 범위 (의도적 단순화)

- 보험상품 2종: **종신보험**(사망보장 중심), **저축성보험**(적립/이자부리 중심)
- 자산 3종: **예금**, **채권**, **주식**
- 영업채널 2종: **직대설계사**, **GA(법인대리점)**
- 사망/해지는 코호트(가입 턴·상품·채널 단위 집계 블록)의 기대값으로 처리, 시장 이벤트(금리·주가)만 시드 난수 사용.

## 5. 도메인 모델

| 엔티티 | 주요 필드 | 비고 |
|---|---|---|
| `Game` | id, rng_seed, initial_capital, current_turn, status(running/bankrupt/completed), created_at | 세이브 슬롯 1개 = 1회차 |
| `ProductConfig` | product_code(whole_life/savings), unit_size, base_cost_rate, expense_loading, base_lapse_rate_annual | 게임 생성 시 시드 데이터로 고정, 상수는 튜닝 대상 |
| `ChannelConfig` | channel_code(captive/ga), base_productivity, base_commission_rate | 시드 데이터 |
| `PolicyCohort` | id, game_id, product_code, channel_code, issue_turn, initial_count, in_force_count, unit_size, reserve_balance | 매턴 in_force_count·reserve_balance 갱신 |
| `MarketState` | game_id, turn, interest_rate, stock_regime(normal/boom/crisis), stock_return_realized | 턴별 1행 |
| `Decision` | game_id, turn, pricing_multiplier[product], underwriting_strictness[product], commission_rate[channel], marketing_spend[channel], asset_allocation{deposit,bond,stock}, dividend_payout | 턴별 플레이어 입력 |
| `FinancialSnapshot` | game_id, turn, premium_income, investment_income, death_claims, surrender_payouts, maturity_payouts, commission_expense, marketing_expense, opex, reserve_change, net_income, deposit_balance, bond_balance, stock_balance, total_reserve, equity | 턴별 손익계산서+재무상태표 |

### 5.1 플레이어 모니터링 지표 체계 (시계열 관측 항목)

플레이어는 게임 진행 중 다음 5대 영역의 지표를 시계열 차트 및 대시보드로 모니터링하며 경영 의사결정을 내려야 한다.

1. **거시 시장 및 자산운용 동향 (Market & Investment Trends)**
   - **시장금리 (`interest_rate`)**: 채권/예금 수익률의 기준 지표 및 장기 부리 부담 평가.
   - **주식 레짐 및 월 수익률 (`stock_regime`, `stock_return_realized`)**: 호황(Boom)/평상(Normal)/위기(Crisis) 국면 파악 및 주식 편입 비중 조절 지표.
   - **총 포트폴리오 수익률 (`portfolio_return_monthly`)**: 전체 운용자산 대비 월 투자수익 비율.
   - **자산군별 잔액 및 비중 (`deposit`, `bond`, `stock`)**: 유동성/안전성/수익성 포트폴리오 배분 현황.

2. **계약 포트폴리오 및 영업 성과 지표 (Policy & Channel Portfolio)**
   - **상품별/채널별 보유계약수 (`in_force_count`)**: 유지 중인 유효 계약자 규모의 성장/정체 추이.
   - **월간 신계약 건수 (`new_policies`)**: 각 채널(전속/GA) 및 상품(종신/저축성)별 신규 유입량.
   - **보험료 수입 분해 (`premium_income`)**: 신계약 초회보험료 및 유지계약 계속보험료 규모.
   - **채널별 생산성 (`channel_capacity`)**: 마케팅비 및 수수료율 집행 대비 실제 판매 역량.

3. **위험 및 계약 이탈 지표 (Risk & Decrement Metrics)**
   - **사망보험금 및 위험손해율 (`death_claims / premium_income`)**: 언더라이팅 엄격도에 따른 사망 리스크 통제 효과.
   - **월간 및 연환산 해지율 (`lapse_rate`) & 해지환급금 (`surrender_payouts`)**: 가격 인상에 따른 계약 이탈 및 유동성 유출 감시.
   - **만기지급금 추이 (`maturity_payouts`)**: 저축성보험 만기 도달(60턴)에 따른 대규모 자금 유출 사전 대비.

4. **손익 및 경영 효율성 지표 (P&L & Profitability)**
   - **보험손익 vs 투자손익 분해**: 보험영업 마진(보험료 - 보험금 - 사업비)과 자산운용 마진의 기여도 분석.
   - **사업비율 (`expense_ratio = (commission + marketing + opex) / premium_income`)**: 과도한 판관비/수수료 집행 여부 점검.
   - **합산비율 (`combined_ratio = (claims + surrenders + expenses) / premium_income`)**: 100% 초과 시 보험영업 적자.
   - **월간 당기순이익 (`net_income`) 및 누적 손익**: 흑자/적자 지속 여부 모니터링.

5. **재무 건전성 및 자본 지표 (Balance Sheet & Solvency)**
   - **순자산(자본총계, `equity`)**: 최종 점수이자 파산 위험(Equity $\le 0$) 회피의 핵심 완충 자본.
   - **총 책임준비금 (`total_reserve`)**: 장래 보험금 지급을 위한 부채 규모.
   - **자본완충비율 (Solvency Proxy = `equity / total_reserve`)**: 부채 대비 순자산 여력.

## 6. 시뮬레이션 엔진 — 턴 처리 파이프라인

### 6.0 의사결정 조정 요소(Decision Controls) 가이드 및 트레이드오프

플레이어가 매 턴 조정할 수 있는 6가지 결정 변수의 메커니즘과 상충관계(Trade-off)는 다음과 같다.

1. **상품 가격 배수 (`pricing_multiplier[product]`)**
   - **효과**: 기준 가격에 곱해져 1건당 수취하는 월 보험료를 결정.
   - **Trade-off**: 가격을 올리면 건당 마진과 보험료 수입이 증가하지만, 가격 탄력도($-2.0$)에 의해 신계약 수요가 급감하고 계약자 해지율($1.5$승)이 상승함.

2. **언더라이팅 엄격도 (`underwriting_strictness[product]`, $0 \sim 1$)**
   - **효과**: 신계약 인수 심사의 엄격성 수준.
   - **Trade-off**: 엄격하게 설정할수록 경험 사망률과 원가율이 최대 30% 개선되지만, 청약 승인율이 최대 40%까지 하락하여 신규 가입자 수가 감소함.

3. **채널 수수료율 (`commission_rate[channel]`)**
   - **효과**: 신계약 유치 시 설계사/GA에 지급하는 초회 수수료율.
   - **Trade-off**: 수수료율을 높이면 채널 생산성($\text{Capacity}$)이 증가하여 신계약이 확대되지만, 초회 신계약 수수료 비용($\text{CommissionExpense}$)이 즉시 증가해 단기 순이익이 악화됨. (GA 채널의 민감도가 전속보다 높음)

4. **채널 마케팅비 (`marketing_spend[channel]`)**
   - **효과**: 브랜드 인지도 및 영업 지원을 위한 채널별 예산 투입.
   - **Trade-off**: 투입 시 신계약 창출 능력이 확장되나 제곱근($\sqrt{\cdot}$) 체감 효과가 적용되므로 과도한 지출은 사업비 낭비와 현금 유출을 초래함.

5. **신규 현금 자산 배분 비중 (`asset_allocation`: 예금, 채권, 주식)**
   - **효과**: 매 턴 발생하는 신규 순현금흐름(흑자분)을 어떤 자산에 배분할지 결정 (합계 100%).
   - **Trade-off**: 
     - **예금(Deposit)**: 시장금리-0.5% 수준의 안전한 고정 수익.
     - **채권(Bond)**: 시장금리 연동 안정적 이자 수익.
     - **주식(Stock)**: 높은 기대수익(호황 시 최대 +1.5%/월)을 제공하나 Crisis 국면(-3.0%/월 및 8% 변동성) 시 대규모 자산 가치 훼손 발생.

6. **배당금 지급액 (`dividend_payout`)**
   - **효과**: 턴 종료 시 사외로 유출되는 주주 배당금.
   - **Trade-off**: 이익 잉여금을 환원하는 수단이나, 자본(순자산)을 직접 차감하므로 불필요하게 많이 지급하면 급격한 시장 충격 시 자본잠식(파산) 위험에 노출됨.

아래 상수(요율, 탄력성 등)는 **초기 밸런스 기본값**이며 `ProductConfig`/`ChannelConfig` 시드
데이터로 관리되어 코드 수정 없이 조정 가능해야 한다.

### 6.1 신계약 발생

```
channel_capacity(channel) = base_productivity
    * (1 + commission_sensitivity * (commission_rate - base_commission_rate))
    * sqrt(marketing_spend / reference_spend)          # 체감효과

price_elasticity(pricing_multiplier) = pricing_multiplier ^ (-elasticity)   # elasticity=2.0 기본

approval_rate(strictness) = 1 - 0.4 * strictness        # 0=관대, 1=엄격

new_applications(product, channel) = channel_capacity(channel)
    * product_channel_split(product, channel)           # 채널별 상품 판매 비중, 시드값
    * price_elasticity(pricing_multiplier[product])

new_policies(product, channel) = floor(new_applications * approval_rate(underwriting_strictness[product]))
```

신계약은 해당 턴에 새 `PolicyCohort` 행으로 생성된다 (issue_turn=현재턴, in_force_count=new_policies).

### 6.2 보험료 산출

```
effective_cost_rate(product, t_duration) = base_cost_rate(product) * (1.03 ^ t_duration_years)
    # 종신: 사망률 성격, 저축성: 부리원가 성격. duration이 길수록 완만히 상승(연령효과 근사)

gross_premium_per_policy(product, t_duration) = unit_size(product)
    * effective_cost_rate(product, t_duration) * (1 + expense_loading(product))
    * pricing_multiplier[product]

underwriting_effect: strictness가 높을수록 실제 경험 사망/해지가 낮아짐
    effective_cost_rate *= (1 - 0.3 * underwriting_strictness[product])
```

### 6.3 기존 코호트 감소(사망/해지) 및 준비금

매 코호트마다:

```
expected_decrement_rate_monthly = effective_cost_rate(product, duration) / 12   # 사망형 코호트
expected_lapse_rate_monthly = (base_lapse_rate_annual(product) * pricing_multiplier[product] ^ 1.5) / 12

deaths = in_force_count * expected_decrement_rate_monthly        # 종신에만 사망금 지급
lapses = in_force_count * expected_lapse_rate_monthly

surrender_value_per_policy ≈ reserve_balance / in_force_count    # 해지환급금은 준비금 기준

in_force_count_next = in_force_count - deaths - lapses
premium_income_cohort = in_force_count * gross_premium_per_policy(product, duration)

reserve_per_policy = reserve_balance / in_force_count
death_reserve_release = deaths * reserve_per_policy              # 사망분에 해당하는 준비금은 해제(자산에서 보험금 지급으로 상쇄)

reserve_balance_next = reserve_balance
    + premium_income_cohort * reserve_accrual_ratio(product)     # 순보험료 중 적립분, 시드값
    - surrender_value_per_policy * lapses
    - death_reserve_release
    + reserve_balance * credited_rate_monthly(product)           # 저축성은 자산운용 수익률 연동 부리(종신은 0)
```

저축성보험 만기(가입 후 60턴=5년 고정)에는 잔여 in_force 전액을 `maturity_payouts`로 지급하고
코호트를 종료 처리한다.

### 6.4 자산운용

- 시장상태(`MarketState`)는 게임 seed로 초기화된 PRNG에서 매턴 갱신:
  - 금리: 평균회귀 랜덤워크 `rate(t+1) = rate(t) + k*(long_run_rate - rate(t)) + noise`
  - 주가 레짐: {normal, boom, crisis} 마코프 체인 (normal→crisis 3%/턴, crisis→normal 20%/턴 등)
  - 주식 월수익률 = 레짐별 드리프트 + 변동성 * N(0,1)
- 자산군별 월수익률: 예금=고정금리/12, 채권=시장금리/12(시가평가 없이 표면금리 인식, Phase 1 단순화),
  주식=위 랜덤워크 결과
- 리밸런싱: 기존 자산 잔액은 각자 수익률로 그대로 굴리고, **이번 턴 신규 순현금흐름(보험료수입 -
  사망금 - 해지환급금 - 만기금 - 사업비)만** 플레이어가 설정한 목표 배분 비중(`asset_allocation`)대로
  예금/채권/주식에 배분한다. (전체 포트폴리오를 매턴 강제 재조정하지 않아 슬라이더 조작만으로 비현실적인
  자산 회전이 생기지 않도록 함.)

### 6.5 손익계산서 & 재무상태표 롤포워드

```
premium_income   = Σ cohorts premium_income_cohort
investment_income = Σ assets (balance * monthly_return)
death_claims     = Σ whole_life cohorts (deaths * unit_size)
surrender_payouts = Σ cohorts (lapses * surrender_value_per_policy)
maturity_payouts  = Σ 만기 도달 코호트 (in_force_count * (reserve_balance/in_force_count))
commission_expense = Σ channels (신계약 premium_income * commission_rate[channel])
marketing_expense  = Σ channels marketing_spend[channel]
opex = fixed_overhead * (1 + 0.02 * log(1 + total_in_force_count))   # 계약 규모에 따른 완만한 증가
reserve_change = total_reserve(t+1) - total_reserve(t)

net_income = premium_income + investment_income
    - death_claims - surrender_payouts - maturity_payouts
    - commission_expense - marketing_expense - opex - reserve_change

equity(t+1) = equity(t) + net_income - dividend_payout
assets(t+1) = deposit_balance + bond_balance + stock_balance
```

파산 조건: `equity(t+1) <= 0` → `status=bankrupt`, 해당 턴에서 게임 종료.

### 6.6 재현성 (RNG)

- `Game.rng_seed`는 게임 생성 시 지정(없으면 자동 생성 후 저장).
- 게임당 하나의 결정론적 PRNG 스트림(`numpy.random.default_rng(seed)`)을 사용하고, 매 턴 소비되는
  난수 개수를 고정해 같은 seed + 같은 결정 입력이면 항상 동일한 결과가 나오도록 한다(리플레이/난이도
  검증 목적).

## 7. API 설계 (Phase 1)

| Method | Path | 설명 |
|---|---|---|
| POST | `/games` | 새 게임 생성 (seed 선택 입력, initial_capital) |
| GET | `/games` | 세이브 목록 |
| GET | `/games/{id}` | 현재 상태(최신 FinancialSnapshot, in-force 요약, MarketState) |
| GET | `/games/{id}/history` | 턴별 FinancialSnapshot 시계열 |
| POST | `/games/{id}/turn` | 이번 턴 `Decision` 제출 → 엔진 실행(6.1~6.5) → 다음 턴 상태 반환 |
| GET | `/games/{id}/config` | 상품/채널 기준정보(현재 pricing 등 UI 슬라이더 초기값) |
| DELETE | `/games/{id}` | 세이브 삭제 |

`POST /games/{id}/turn`은 결정 검증(값 범위) → 엔진 실행 → `FinancialSnapshot` 생성 → 파산/종료
판정까지 하나의 DB 트랜잭션으로 처리하여, 항상 일관된 상태만 영속화한다.

## 8. 프론트엔드 구조

```
frontend/src/
  views/
    NewGameView.vue        # seed/초기자본 설정 후 게임 생성
    DashboardView.vue      # 메인 플레이 화면
    ResultView.vue         # 종료/파산 시 최종 리포트
  components/
    DecisionPanel.vue      # 상품별 pricing/underwriting, 채널별 commission/marketing, 자산배분, 배당
    KpiCards.vue           # 자본, 계약자수, ROE 등 요약 카드
    HistoryCharts.vue      # 자본추이, 손익분해, in-force 추이 차트
    TurnControl.vue        # "턴 실행" 버튼 + 오토플레이(N턴 자동진행) 옵션
  stores/
    useGameStore.ts         # Pinia: 현재 상태, 결정 초안, 히스토리 캐시. 백엔드가 source of truth
  api/
    client.ts               # REST 호출 wrapper
```

## 9. 디렉터리 구조 (레포 전체)

```
backend/
  app/
    main.py
    api/games.py
    models/           # SQLModel 테이블 정의
    schemas/           # 요청/응답 Pydantic 스키마 (모델과 다를 때만 분리)
    engine/           # 순수 Python 시뮬레이션 엔진 (FastAPI/DB 비의존)
      market.py       # 6.4 금리/주가 레짐
      products.py     # 6.1, 6.2 신계약/보험료
      cohorts.py      # 6.3 사망/해지/준비금
      finance.py      # 6.5 손익/재무상태표 롤포워드
      turn.py         # 파이프라인 오케스트레이션
    config/           # 상품/채널 기본 상수 시드 데이터 (JSON)
    db.py
  tests/
    test_engine_*.py   # 엔진 유닛테스트 (고정 seed+decision → 스냅샷 비교)
    test_api_*.py       # FastAPI TestClient 통합테스트
frontend/
  src/ ... (8절 참고)
  Dockerfile
docs/superpowers/specs/  # 이 스펙 및 향후 스펙 문서
docker-compose.yml        # backend/frontend 컨테이너를 함께 기동 (podman-compose 호환)
```

`backend/Dockerfile`도 위 `backend/` 트리 최상위에 위치한다.

## 10. 테스트 전략

- 엔진: FastAPI/DB 없이 순수 함수 단위테스트. 고정 seed + 고정 Decision 시퀀스로 N턴 실행 후
  기대 결과(자본, in-force 등)를 스냅샷 비교. 불변식 테스트(예: 자본 변화 = net_income - dividend,
  화폐가 임의로 생성/소멸되지 않는지) 포함.
- API: FastAPI `TestClient`로 `/games` 생성 → `/turn` 반복 호출 → 상태 일관성 검증.
- 프론트엔드: Phase 1에서는 수동 브라우저 검증 위주. 컴포넌트 테스트는 Phase 2 이후 필요 시 추가.

## 11. Phase 로드맵 (참고용, Phase 1 범위 아님)

- **Phase 2**: 상품 다양화(건강보험 등), 재보험, 감독 지급여력비율 유사 지표, 경기순환/시장 이벤트
  다양화, AI 경쟁사 비교 대시보드
- **Phase 3**: 난이도/시나리오 선택, 도전과제, 세이브 슬롯 다중화, 튜토리얼
- **Phase 4(선택)**: 멀티플레이/랭킹, 밸런스 조정 도구(관리자 화면 또는 CLI)

## 12. Phase 1에서 의도적으로 다루지 않는 것

- 개별 계약자 단위 시뮬레이션 (코호트 집계로 대체)
- 채권 시가평가/듀레이션 정밀 모델링 (표면금리 인식으로 단순화)
- 재보험, 규제 자본비율, 세금
- 멀티플레이/인증/사용자 계정 (로컬 단일 사용자, SQLite 파일 하나로 세이브 관리)
