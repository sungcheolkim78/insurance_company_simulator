# 보드게임 비주얼 아이덴티티 디자인 스펙

## 배경 및 목표

현재 프론트엔드는 Tailwind 기본 톤(흰 배경, `slate-200` 테두리, 시스템 폰트)의 관리자 대시보드 느낌으로, 경영 "게임"을 플레이하는 느낌이 약하다. 이 스펙은 프론트엔드 전체에 **밝고 재미있는 보드게임 스타일** 비주얼 아이덴티티를 적용하는 작업을 정의한다.

**승인된 방향** (목업: https://claude.ai/code/artifact/93bf4cd3-a66a-46b6-a915-22b1d3479d67 에서 시각적으로 확인·승인됨):
- 크림색 보드판 배경 + 코랄/틸/머스타드/플럼 4색 "게임 말" 팔레트 (단일 액센트色이 아닌 다색 구성)
- Jua(디스플레이) + Gowun Dodum(본문) 한글 서체 페어링
- 모든 섹션을 두꺼운 테두리 + 오프셋 그림자의 "보드 타일" 카드로 통일, 색상 헤더 배너 + 아이콘
- 시그니처 요소: 턴 진행을 보드게임 경로(path) 위의 말(pawn)로 표현하는 턴 트래커, 시장 국면에 따라 경로 색이 바뀜

**스코프 경계**: 순수 시각적 레이어 변경이다. API 호출, 상태관리, 데이터 형태, 비즈니스 로직(엔진 계산식)은 전혀 건드리지 않는다. 다크모드는 이번 스코프에서 제외한다 — 사용자가 명시적으로 "밝고" 재미있는 방향을 요청했으므로 단일 라이트("보드") 테마만 구현한다 (목업 아티팩트 자체는 아티팩트 플랫폼 규칙상 라이트/다크 모두 지원하지만, 실제 배포되는 앱은 이 요구사항에 매이지 않는다).

## 1. 디자인 토큰

### 1.1 색상 (Tailwind v4 `@theme` — `frontend/src/style.css`)

| 토큰명 | 값 | 용도 |
|---|---|---|
| `--color-board-cream` | `#FBF1DE` | 페이지 배경 (보드판) |
| `--color-board-cream-deep` | `#F3E4C6` | 배경 위 은은한 구획 (경로 트랙 바탕, 구분선) |
| `--color-ink` | `#2B2A4C` | 기본 텍스트, 타일 테두리 |
| `--color-ink-soft` | `#5B5A7E` | 보조 텍스트(라벨) |
| `--color-tile` | `#FFFDF6` | 타일(카드) 배경 |
| `--color-coral` | `#E8604C` | 1번 액센트 — 경고/부정/CTA |
| `--color-coral-deep` | `#C8492F` | 코랄의 그림자/딥 변형 (버튼 눌림 효과, 강조 텍스트) |
| `--color-teal` | `#2A9D8F` | 2번 액센트 — 성장/긍정/시장·자산 |
| `--color-teal-deep` | `#1F7A6E` | 틸 딥 변형 |
| `--color-mustard` | `#F2A93B` | 3번 액센트 — 강조/하이라이트/CSM 카드 헤더 |
| `--color-mustard-deep` | `#D48F1F` | 머스타드 딥 변형 |
| `--color-plum` | `#7B5EA7` | 4번 액센트 — 차트/시계열, 특수 지표 |
| `--color-plum-deep` | `#5F4682` | 플럼 딥 변형 |

Tailwind v4 문법으로 `frontend/src/style.css`에 추가:
```css
@import "tailwindcss";

@theme {
  --color-board-cream: #FBF1DE;
  --color-board-cream-deep: #F3E4C6;
  --color-ink: #2B2A4C;
  --color-ink-soft: #5B5A7E;
  --color-tile: #FFFDF6;
  --color-coral: #E8604C;
  --color-coral-deep: #C8492F;
  --color-teal: #2A9D8F;
  --color-teal-deep: #1F7A6E;
  --color-mustard: #F2A93B;
  --color-mustard-deep: #D48F1F;
  --color-plum: #7B5EA7;
  --color-plum-deep: #5F4682;
  --font-display: 'Jua', 'Gowun Dodum', sans-serif;
  --font-body: 'Gowun Dodum', 'Pretendard', sans-serif;
}

body {
  background-color: var(--color-board-cream);
  color: var(--color-ink);
  font-family: var(--font-body);
}
```
이렇게 하면 `bg-coral`, `text-teal-deep`, `border-ink`, `font-display` 같은 Tailwind 유틸리티 클래스를 프로젝트 전역에서 즉시 사용할 수 있다 (Tailwind v4는 `@theme`의 `--color-*`/`--font-*` 토큰을 자동으로 유틸리티로 노출한다).

### 1.2 타이포그래피

- **디스플레이**: [Jua](https://fonts.google.com/specimen/Jua) — 둥글둥글한 손글씨풍 한글 디스플레이 서체. 용도: `<h1>`, 턴 트래커 숫자, KPI 큰 수치, 타일 헤더 배너 텍스트.
- **본문**: [Gowun Dodum](https://fonts.google.com/specimen/Gowun+Dodum) — 부드럽고 가독성 좋은 한글 서체. 용도: 표, 라벨, 입력 필드, 일반 본문 텍스트 전부.
- 숫자가 표에서 세로로 정렬되는 곳(재무제표, KPI 카드 등)은 `tabular-nums` 유틸리티(`font-variant-numeric: tabular-nums`)를 적용한다.

`frontend/index.html`의 `<head>`에 Google Fonts 링크 추가:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap" rel="stylesheet">
```

### 1.3 아이콘

목업에서는 속도를 위해 이모지를 사용했지만, 실제 구현에서는 폰트/OS마다 렌더링이 다른 이모지 대신 **`@phosphor-icons/vue`** (신규 의존성)의 `duotone` 또는 `fill` weight를 사용한다 — 보드게임의 통통하고 친근한 느낌과 잘 맞고, 플랫폼 간 일관된 렌더링을 보장한다.

섹션별 아이콘 매핑 (모두 Phosphor 아이콘명):
| 섹션 | 아이콘 |
|---|---|
| 자본총계 KPI | `Coins` |
| 순이익 KPI | `ChartLineUp` / `ChartLineDown` (부호에 따라) |
| 총 준비금 KPI | `Bank` |
| 시장 & 자산운용 | `TrendUp` |
| 계약 포트폴리오 & 영업성과 | `Handshake` |
| 위험손해율 & 계약유지 | `ShieldWarning` |
| 수익성 & 사업비 | `ChartPieSlice` |
| 재무건전성 | `Vault` |
| 계약서비스마진(CSM) | `PiggyBank` |
| 손익계산서 | `Receipt` |
| 재무상태표 | `Scales` |
| 이번 턴 결정(DecisionPanel) | `DiceFive` |
| 자동 진행(TurnControl) | `FastForward` |
| 설정 | `GearSix` |
| 게임 종료 | `DoorOpen` |
| 게임 설정 모달의 상품/채널 표 | `Package`, `UsersFour` |
| 국면 타임라인(RegimeTimeline) | 평온=`Cloud`, 호황=`Rocket`, 위기=`Fire` |

## 2. 레이아웃 개념 — "보드 타일" 시스템

모든 카드형 UI 블록(현재 `rounded border border-slate-200 p-4` 패턴)을 다음 클래스 조합으로 통일한다:

```html
<div class="rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)] overflow-hidden">
  <div class="flex items-center gap-2 px-4 py-2.5 font-display text-white bg-{accent}">
    <PhosphorIcon :size="18" />
    <span>{{ 섹션 제목 }}</span>
  </div>
  <div class="p-4">...본문...</div>
</div>
```

- 테두리는 항상 `border-ink` 3px, 그림자는 항상 우하단으로 5px 오프셋 (물리적 카드가 살짝 들려있는 느낌).
- 헤더 배너 색상(`bg-coral`/`bg-teal`/`bg-mustard`/`bg-plum`)은 섹션 성격에 따라 로테이션하되, 같은 화면 안에서 인접한 타일끼리는 다른 색을 쓰도록 배치한다 (현재 3컬럼 레이아웃 기준 배치는 §3 참조).
- 버튼은 `rounded-full`(pill) + 아래쪽 그림자로 "눌리는" 느낌(`shadow-[0_4px_0_var(--color-coral-deep)]`, active 시 `translate-y-[3px]` + 그림자 축소)을 준다.
- 입력 필드는 `rounded-[10px] border-2 border-board-cream-deep bg-board-cream`으로 통일.

## 3. 시그니처 요소 — 턴 경로 트래커

새 컴포넌트 `frontend/src/components/TurnPathTracker.vue`가 `DashboardView.vue` 상단의 `<h1>턴 X / Y</h1>` 텍스트를 대체한다.

**Props**: `currentTurn: Number`, `gameLengthTurns: Number`, `stockRegime: String` (normal/boom/crisis)

**렌더링**:
- 상단에 `턴 {currentTurn} / {gameLengthTurns}` 텍스트 + 국면 칩(§1.3 국면 아이콘 + 라벨, 배경색은 §1.1 팔레트: normal=`board-cream-deep`, boom=`teal`, crisis=`coral`)
- 그 아래 가로 트랙(`bg-board-cream-deep`, `border-2 border-ink`, `rounded-full`): 진행률(`currentTurn / gameLengthTurns`)만큼 `teal→mustard` 그라디언트로 채워짐
- 트랙 위, 진행률 위치에 원형 "말"(pawn) — `bg-coral`, 흰 테두리, 현재 턴 숫자 표시
- 국면이 crisis인 동안에는 트랙 채움 그라디언트가 `coral` 계열로 바뀜 (위기감 표현)

`ResultView.vue`의 기존 `RegimeTimeline.vue`(국면 변화 이력 목록)는 이 시그니처 요소와 시각적으로 통일되도록 색상만 §1.1 팔레트로 맞추고(현재 slate/green/red → board-cream-deep/teal/coral), 구조는 그대로 유지한다.

## 4. 컴포넌트별 적용 범위

전부 스타일(템플릿의 클래스/구조)만 변경, `<script setup>`의 로직·props·이벤트는 변경하지 않는다.

| 파일 | 변경 내용 |
|---|---|
| `frontend/index.html` | Google Fonts 링크 추가 |
| `frontend/src/style.css` | `@theme` 토큰 추가 (§1.1) |
| `frontend/package.json` | `@phosphor-icons/vue` 의존성 추가 |
| `frontend/src/views/NewGameView.vue` | 시작 화면을 보드게임 표지처럼 재구성 (타이틀 배너 + 입력 필드 보드타일화) |
| `frontend/src/views/DashboardView.vue` | 헤더를 시그니처 요소(`TurnPathTracker`)로 교체, 버튼 pill화, 3컬럼 배치의 헤더 배너 색상 지정 |
| `frontend/src/components/TurnPathTracker.vue` | **신규** — §3 |
| `frontend/src/components/KpiCards.vue` | 보드타일 + 아이콘 헤더로 재구성 |
| `frontend/src/components/MonitoringPanel.vue` | 5개 그룹 각각 보드타일 + 아이콘 헤더 (§1.3 매핑) |
| `frontend/src/components/HistoryCharts.vue` | Chart.js `borderColor`를 §1.1 팔레트(coral/teal/mustard/plum)로 교체, 타일 래핑 |
| `frontend/src/components/FinancialStatements.vue` | 보드타일 + 아이콘 헤더, 표 스타일 정리 |
| `frontend/src/components/DecisionPanel.vue` | 보드타일 + 아이콘 헤더, 입력 필드/버튼 스타일 교체 |
| `frontend/src/components/TurnControl.vue` | 보드타일 + 아이콘, 버튼 pill화 |
| `frontend/src/components/GameSettingsPanel.vue` | 모달을 보드타일 스타일로, 표 안 아이콘 추가 |
| `frontend/src/components/RegimeTimeline.vue` | 색상만 §1.1 팔레트로 교체 |
| `frontend/src/views/ResultView.vue` | 결과 카드를 보드게임 "게임 오버/승리" 배너처럼 재구성 |

## 5. 자기검토 (Self-Review)

- **Placeholder 스캔**: TBD/TODO 없음, 모든 색상값/폰트명/컴포넌트 경로가 구체적으로 명시됨.
- **내부 일관성**: §1.1 팔레트가 §2(레이아웃)·§3(시그니처 요소)·§4(컴포넌트 매핑) 전체에서 동일하게 참조됨. 다크모드 제외 방침이 배경 설명과 §1 모두에서 일관됨.
- **스코프**: 프론트엔드 시각 레이어로 한정, 단일 계획으로 다루기에 적절한 크기 (컴포넌트 13개 + 신규 1개, 의존성 1개 추가).
- **모호성 점검**: "아이콘"을 이모지에서 Phosphor로 명확화했고, 각 섹션의 헤더 배너 색상 로테이션 원칙(인접 타일 다른 색)을 명시해 구현자가 임의로 정하지 않도록 했다.

## 6. 검증 방법

기존 세션 관례대로 `podman-compose` 스택(프론트엔드 전용, 백엔드 변경 없음 — DB 재생성 불필요)에서 Playwright로 각 화면(NewGame/Dashboard/ResultView, 설정 모달 포함)을 스크린샷 확인한다. 자동화 테스트는 없는 프로젝트이므로 시각 검증이 유일한 검증 수단이다.
