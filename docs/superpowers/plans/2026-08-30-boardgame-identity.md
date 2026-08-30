# 보드게임 비주얼 아이덴티티 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 프론트엔드 전체에 밝고 재미있는 보드게임 비주얼 아이덴티티(크림 배경 + 4색 팔레트, Jua/Gowun Dodum 서체, "보드 타일" 카드 시스템, 턴 경로 트래커 시그니처 요소)를 적용한다.

**Architecture:** Tailwind v4 `@theme` 토큰(`frontend/src/style.css`)으로 색상/폰트를 전역 유틸리티 클래스(`bg-coral`, `font-display` 등)로 노출하고, `@phosphor-icons/vue`로 아이콘을 통일한다. 13개 기존 컴포넌트를 순수 템플릿/클래스 레벨로 재작성하고(`<script setup>` 로직은 변경 없음), 신규 컴포넌트 `TurnPathTracker.vue`가 시그니처 요소를 담당한다. 백엔드는 전혀 건드리지 않는다.

**Tech Stack:** Vue 3 `<script setup>`, Tailwind CSS v4 (CSS-first `@theme` config), `@phosphor-icons/vue`(신규), Chart.js/vue-chartjs(기존, 색상만 변경). 검증은 자동화 테스트가 없는 프로젝트 특성상 `podman-compose` 스택 + Playwright 스크린샷으로 진행한다(백엔드/DB 변경 없음 — 볼륨 재생성 불필요).

**Spec:** `docs/superpowers/specs/2026-08-30-boardgame-identity-design.md` — §1(디자인 토큰), §2(레이아웃/보드타일), §3(시그니처 요소), §4(컴포넌트별 적용 범위)를 구현 전 전체 통독할 것.

## Global Constraints

- `<script setup>` 블록의 로직(props, computed, 함수, emit)은 **어떤 태스크에서도 변경하지 않는다** — 템플릿의 클래스/구조, 그리고 아이콘 컴포넌트 import만 추가한다.
- 모든 카드형 블록은 스펙 §2의 "보드 타일" 패턴을 따른다:
  ```html
  <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
    <div class="flex items-center gap-2 bg-{accent} px-4 py-2.5 font-display text-white">
      <PhIconName :size="18" weight="fill" />
      <span>{{ 섹션 제목 }}</span>
    </div>
    <div class="p-4">...본문...</div>
  </div>
  ```
  `{accent}`는 `coral`/`teal`/`mustard`/`plum` 중 하나이며, 같은 화면에서 인접한 타일끼리는 반드시 다른 색을 쓴다(스펙 §2).
- `mustard` 헤더 배너는 밝은 색이라 `text-white` 대신 `text-ink`를 쓴다 (가독성).
- 버튼은 pill(`rounded-full`) + 아래쪽 그림자(`shadow-[0_4px_0_var(--color-{accent}-deep)]`), 클릭 시 `active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-{accent}-deep)]`.
- 입력 필드는 `rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1`.
- 숫자가 세로로 정렬되는 곳(표, KPI)에는 `tabular-nums` 클래스를 추가한다.
- 각 태스크가 끝나면 `podman restart insurance_company_simulator_frontend_1` 후 Playwright로 해당 화면을 스크린샷하여 육안 검증한다 (이 프로젝트는 Vite 핫리로드가 바인드 마운트를 통해 파일 변경을 못 잡는 경우가 있음 — 알려진 이슈).
- 이 계획의 모든 `Ph*` 아이콘 이름은 Phosphor 아이콘셋 명명 규칙에 따라 고른 것이지만, 네트워크 접근 없이 작성되어 실제 `@phosphor-icons/vue` 패키지에 정확히 그 이름으로 존재하는지 확인되지 않았다. 각 태스크에서 아이콘을 import할 때, 브라우저 콘솔에 `does not provide an export named 'Ph...'` 같은 에러가 뜨면 해당 아이콘 이름이 실제 패키지에 없다는 뜻이다 — `node_modules/@phosphor-icons/vue`의 타입 정의나 https://phosphoricons.com 목록에서 가장 가까운 실제 아이콘명으로 교체하고, 무엇을 왜 바꿨는지 태스크 리포트에 기록한다.

---

### Task 1: 전역 디자인 토큰, 폰트, 아이콘 라이브러리

**Files:**
- Modify: `frontend/src/style.css`
- Modify: `frontend/index.html`
- Modify: `frontend/package.json`
- Modify: `frontend/src/App.vue` (임시 검증 후 원복)

**Interfaces:**
- Produces: Tailwind 유틸리티 `bg-board-cream`, `bg-board-cream-deep`, `text-ink`, `text-ink-soft`, `bg-tile`, `bg-coral`/`border-coral`/`text-coral`(및 `-deep` 변형), `bg-teal`/`bg-mustard`/`bg-plum`(및 `-deep` 변형), `font-display`, `font-body` — Task 2~10에서 전부 소비.
- `@phosphor-icons/vue`의 `Ph*` 아이콘 컴포넌트 — Task 2~9에서 소비.

- [ ] **Step 1: `style.css`에 `@theme` 토큰 추가**

`frontend/src/style.css`를 다음으로 교체:

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

- [ ] **Step 2: `index.html`에 Google Fonts 링크 추가**

`frontend/index.html`의 `<head>` 안, `<title>` 태그 바로 뒤에 추가:

```html
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap" rel="stylesheet" />
```

- [ ] **Step 3: `@phosphor-icons/vue` 의존성 추가**

`frontend/package.json`의 `dependencies`에 추가 (알파벳 순서 유지):

```json
    "@phosphor-icons/vue": "^2.2.1",
```

전체 `dependencies` 블록은 다음과 같아야 함:

```json
  "dependencies": {
    "@phosphor-icons/vue": "^2.2.1",
    "axios": "^1.20.0",
    "chart.js": "^4.5.1",
    "pinia": "^4.0.3",
    "vue": "^3.5.41",
    "vue-chartjs": "^5.3.4",
    "vue-router": "^5.3.0"
  },
```

- [ ] **Step 4: 컨테이너 재빌드 (새 의존성 설치)**

의존성이 추가됐으므로 `--build`로 재빌드해야 한다 (단순 재시작으로는 새 npm 패키지가 설치되지 않음):

```bash
cd /Users/skim/CoreData/Local_Keep/git_repos/insurance_company_simulator
podman-compose up --build -d frontend
```

Expected: 빌드 로그에 `@phosphor-icons/vue` 설치 로그가 보이고, 컨테이너가 정상 기동됨.

- [ ] **Step 5: 임시 검증 스니펫으로 토큰/폰트 확인**

`frontend/src/App.vue`를 임시로 다음처럼 바꾼다:

```vue
<template>
  <div class="bg-coral p-8 font-display text-2xl text-white">토큰 테스트 · Jua 폰트</div>
  <router-view />
</template>
```

Playwright로 아무 경로(`http://localhost:5173/`)를 열어 스크린샷 확인: 코랄색(#E8604C) 배경 위에 흰색 Jua 폰트(둥글둥글한 손글씨풍)로 "토큰 테스트 · Jua 폰트"가 렌더링되어야 한다. 브라우저 콘솔에 에러가 없어야 한다.

- [ ] **Step 6: 임시 스니펫 원복**

`frontend/src/App.vue`를 원래대로 되돌린다:

```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 7: 커밋**

```bash
git add frontend/src/style.css frontend/index.html frontend/package.json frontend/package-lock.json
git commit -m "feat(identity): add boardgame design tokens, fonts, and icon library"
```

(`package-lock.json`이 `npm install`로 갱신됐다면 함께 커밋. `App.vue`는 원복했으므로 diff 없음 — 커밋 대상에서 자동 제외됨.)

---

### Task 2: 시그니처 요소 — `TurnPathTracker.vue` + `DashboardView.vue` 헤더

**Files:**
- Create: `frontend/src/components/TurnPathTracker.vue`
- Modify: `frontend/src/views/DashboardView.vue`

**Interfaces:**
- Consumes: Task 1의 색상/폰트 토큰.
- Produces: `TurnPathTracker` 컴포넌트 (props: `currentTurn: Number`, `gameLengthTurns: Number`, `stockRegime: String`) — `DashboardView.vue`가 소비.

- [ ] **Step 1: `TurnPathTracker.vue` 작성**

```vue
<script setup>
import { computed } from 'vue'
import { PhCloud, PhFire, PhRocket } from '@phosphor-icons/vue'

const props = defineProps({
  currentTurn: { type: Number, required: true },
  gameLengthTurns: { type: Number, required: true },
  stockRegime: { type: String, default: 'normal' },
})

const REGIME_LABELS = { normal: '평온', boom: '호황', crisis: '위기' }
const REGIME_ICONS = { normal: PhCloud, boom: PhRocket, crisis: PhFire }
const REGIME_CHIP_CLASS = {
  normal: 'bg-board-cream-deep text-ink-soft',
  boom: 'bg-teal text-white',
  crisis: 'bg-coral text-white',
}

const progressPercent = computed(() =>
  Math.min(100, Math.max(0, (props.currentTurn / props.gameLengthTurns) * 100)),
)

const trackGradient = computed(() =>
  props.stockRegime === 'crisis'
    ? 'linear-gradient(90deg, var(--color-coral), var(--color-coral-deep))'
    : 'linear-gradient(90deg, var(--color-teal), var(--color-mustard))',
)

const regimeIcon = computed(() => REGIME_ICONS[props.stockRegime] ?? PhCloud)
const regimeChipClass = computed(() => REGIME_CHIP_CLASS[props.stockRegime] ?? REGIME_CHIP_CLASS.normal)
const regimeLabel = computed(() => REGIME_LABELS[props.stockRegime] ?? props.stockRegime)
</script>

<template>
  <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
    <div class="mb-2 flex items-center justify-between text-sm text-ink-soft">
      <span class="font-display text-base text-ink">턴 {{ currentTurn }} / {{ gameLengthTurns }}</span>
      <span class="flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold" :class="regimeChipClass">
        <component :is="regimeIcon" :size="14" weight="fill" />
        {{ regimeLabel }} 국면
      </span>
    </div>
    <div class="relative h-[34px] rounded-full border-2 border-ink bg-board-cream-deep">
      <div
        class="absolute inset-y-0 left-0 rounded-full transition-[width] duration-500"
        :style="{ width: `${progressPercent}%`, backgroundImage: trackGradient }"
      />
      <div
        class="absolute top-1/2 flex h-[30px] w-[30px] -translate-y-1/2 items-center justify-center rounded-full border-[3px] border-tile bg-coral text-xs font-bold text-white shadow-[0_2px_0_rgba(43,42,76,0.28)] transition-[left] duration-500"
        :style="{ left: `${progressPercent}%`, transform: 'translate(-50%, -50%)' }"
      >
        {{ currentTurn }}
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: `DashboardView.vue` 헤더를 `TurnPathTracker`로 교체**

`frontend/src/views/DashboardView.vue`의 `<script setup>` 상단 import에 추가:

```js
import TurnPathTracker from '../components/TurnPathTracker.vue'
```

템플릿에서 다음 블록:

```html
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-800">턴 {{ store.currentTurn }} / {{ store.gameLengthTurns }}</h1>
      <div class="flex gap-2">
        <button
          class="rounded border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          @click="showSettings = true"
        >
          설정
        </button>
        <button
          class="rounded border border-red-300 px-3 py-1.5 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
          :disabled="isBusy"
          @click="handleEndGame"
        >
          게임 종료 &amp; 새 시뮬레이션
        </button>
      </div>
    </div>
```

을 다음으로 교체:

```html
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div class="w-full sm:max-w-md">
        <TurnPathTracker
          :current-turn="store.currentTurn"
          :game-length-turns="store.gameLengthTurns"
          :stock-regime="store.snapshot.stock_regime"
        />
      </div>
      <div class="flex gap-2">
        <button
          class="rounded-full border-2 border-ink bg-tile px-4 py-2 text-sm font-bold text-ink shadow-[3px_3px_0_rgba(43,42,76,0.28)] active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(43,42,76,0.28)]"
          @click="showSettings = true"
        >
          ⚙ 설정
        </button>
        <button
          class="rounded-full border-2 border-coral-deep bg-tile px-4 py-2 text-sm font-bold text-coral-deep shadow-[3px_3px_0_rgba(200,73,47,0.35)] disabled:opacity-50 active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(200,73,47,0.35)]"
          :disabled="isBusy"
          @click="handleEndGame"
        >
          게임 종료 &amp; 새 시뮬레이션
        </button>
      </div>
    </div>
```

(주의: `store.snapshot.stock_regime`은 이미 로드된 스냅샷의 필드이므로 `v-if="store.snapshot"` 블록 안쪽이라 안전하게 접근 가능.)

- [ ] **Step 3: 페이지 여백 클래스 확인**

같은 파일에서 최상위 컨테이너 `<div v-if="store.snapshot" class="mx-auto max-w-6xl space-y-6 p-8">`는 그대로 둔다 (배경은 Task 1의 `body` 전역 스타일로 이미 크림색).

- [ ] **Step 4: 시각 검증**

`podman restart insurance_company_simulator_frontend_1` 후 Playwright로 `/games/{id}` 접속, 헤더 영역 스크린샷. 확인 항목: 턴 경로 트랙(원형 말이 진행률 위치에 있음), 국면 칩(평온/호황/위기에 따라 회색/틸/코랄), 설정·게임종료 버튼이 pill 모양으로 렌더링. 콘솔 에러 없음.

- [ ] **Step 5: 커밋**

```bash
git add frontend/src/components/TurnPathTracker.vue frontend/src/views/DashboardView.vue
git commit -m "feat(identity): add turn path tracker signature element"
```

---

### Task 3: `KpiCards.vue` 보드타일화

**Files:**
- Modify: `frontend/src/components/KpiCards.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`.

- [ ] **Step 1: 전체 파일 교체**

```vue
<script setup>
import { PhBank, PhChartLineDown, PhChartLineUp, PhCoins } from '@phosphor-icons/vue'

defineProps({ snapshot: Object })

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
</script>

<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-coral px-4 py-2.5 font-display text-white">
        <PhCoins :size="18" weight="fill" />
        <span>자본총계</span>
      </div>
      <div class="p-4">
        <div class="tabular-nums text-xl font-bold">{{ formatWon(snapshot.equity) }}</div>
      </div>
    </div>
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-teal px-4 py-2.5 font-display text-white">
        <component :is="snapshot.net_income >= 0 ? PhChartLineUp : PhChartLineDown" :size="18" weight="fill" />
        <span>이번 턴 순이익</span>
      </div>
      <div class="p-4">
        <div class="tabular-nums text-xl font-bold" :class="snapshot.net_income >= 0 ? 'text-teal-deep' : 'text-coral-deep'">
          {{ formatWon(snapshot.net_income) }}
        </div>
      </div>
    </div>
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-mustard px-4 py-2.5 font-display text-ink">
        <PhBank :size="18" weight="fill" />
        <span>총 준비금</span>
      </div>
      <div class="p-4">
        <div class="tabular-nums text-xl font-bold">{{ formatWon(snapshot.total_reserve) }}</div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 시각 검증**

컨테이너 재시작 후 `/games/{id}` 스크린샷: 3개 KPI 타일이 코랄/틸/머스타드 헤더 배너로 구분되어 렌더링되는지 확인. 순이익이 음수일 때 `PhChartLineDown` 아이콘 + 코랄 텍스트로 바뀌는지 확인(현재 진행 중인 테스트 게임은 순이익이 음수이므로 바로 확인 가능).

- [ ] **Step 3: 커밋**

```bash
git add frontend/src/components/KpiCards.vue
git commit -m "feat(identity): restyle KPI cards as board tiles"
```

---

### Task 4: `MonitoringPanel.vue` 보드타일화 (6개 그룹)

**Files:**
- Modify: `frontend/src/components/MonitoringPanel.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`. 6개 그룹 각각 색상 로테이션: 시장&자산운용=teal, 계약포트폴리오=mustard, 위험손해율=coral, 수익성&사업비=plum, 재무건전성=teal, CSM=mustard (인접 타일 다른 색 원칙 준수).

- [ ] **Step 1: `<script setup>` 상단에 아이콘 import 추가**

기존 `import { computed } from 'vue'` 바로 아래에 추가:

```js
import { PhBank, PhChartPieSlice, PhHandshake, PhPiggyBank, PhShieldWarning, PhTrendUp } from '@phosphor-icons/vue'
```

`<script setup>`의 나머지 내용(모든 `const`, `function`, `props`)은 **전혀 변경하지 않는다**.

- [ ] **Step 2: 템플릿을 다음으로 교체**

`<template>` 전체를 다음으로 교체 (스크립트 블록은 Step 1의 import 한 줄 추가 외 그대로 유지):

```html
<template>
  <div class="space-y-4">
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-teal px-4 py-2.5 font-display text-white">
        <PhTrendUp :size="18" weight="fill" />
        <span>시장 &amp; 자산운용</span>
      </div>
      <div class="p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">시장금리 (목표 3.0%)</div>
            <div class="tabular-nums font-bold">{{ formatPct(snapshot.interest_rate) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">주가 국면</div>
            <div class="font-bold">{{ REGIME_LABELS[snapshot.stock_regime] ?? snapshot.stock_regime }}</div>
          </div>
          <div>
            <div class="text-ink-soft">주식 실현수익률(월)</div>
            <div class="tabular-nums font-bold">{{ formatPct(snapshot.stock_return_realized) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">포트폴리오 운용수익률(월)</div>
            <div class="tabular-nums font-bold">{{ formatPct(portfolioReturnMonthly) }}</div>
          </div>
        </div>
        <div class="mt-3 text-sm">
          <div class="text-ink-soft">자산군별 비중 (예금 / 채권 / 주식)</div>
          <div class="tabular-nums font-bold">
            {{ formatPct(assetWeights.deposit, 1) }} / {{ formatPct(assetWeights.bond, 1) }} / {{ formatPct(assetWeights.stock, 1) }}
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-mustard px-4 py-2.5 font-display text-ink">
        <PhHandshake :size="18" weight="fill" />
        <span>계약 포트폴리오 &amp; 영업성과</span>
      </div>
      <div class="p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">총 보유계약수</div>
            <div class="tabular-nums font-bold">{{ Math.round(snapshot.total_in_force).toLocaleString('ko-KR') }}건</div>
          </div>
          <div>
            <div class="text-ink-soft">이번 턴 신계약</div>
            <div class="tabular-nums font-bold">{{ newPoliciesTotal.toLocaleString('ko-KR') }}건</div>
          </div>
          <div>
            <div class="text-ink-soft">신계약 (종신/저축)</div>
            <div class="tabular-nums font-bold">
              {{ snapshot.new_policies_by_product.whole_life }} / {{ snapshot.new_policies_by_product.savings }}
            </div>
          </div>
          <div>
            <div class="text-ink-soft">신계약 (전속/GA)</div>
            <div class="tabular-nums font-bold">
              {{ snapshot.new_policies_by_channel.captive }} / {{ snapshot.new_policies_by_channel.ga }}
            </div>
          </div>
          <div>
            <div class="text-ink-soft">초회 보험료</div>
            <div class="tabular-nums font-bold">{{ formatWon(newBusinessPremiumTotal) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">계속 보험료</div>
            <div class="tabular-nums font-bold">{{ formatWon(renewalPremium) }}</div>
          </div>
        </div>
        <div class="mt-3 grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">채널효율성 (전속)</div>
            <div class="tabular-nums font-bold">{{ channelEfficiency ? formatPct(channelEfficiency.captive, 0) : '—' }}</div>
          </div>
          <div>
            <div class="text-ink-soft">채널효율성 (GA)</div>
            <div class="tabular-nums font-bold">{{ channelEfficiency ? formatPct(channelEfficiency.ga, 0) : '—' }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-coral px-4 py-2.5 font-display text-white">
        <PhShieldWarning :size="18" weight="fill" />
        <span>위험손해율 &amp; 계약유지</span>
      </div>
      <div class="p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">위험손해율 (종신)</div>
            <div class="tabular-nums font-bold" :class="toneLowerIsBetter(lossRatio, 0.5)">{{ formatPct(lossRatio, 1) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">해지율 (월 / 연환산)</div>
            <div class="tabular-nums font-bold">{{ formatPct(lapseRatioMonthly, 2) }} / {{ formatPct(lapseRatioAnnual, 1) }}</div>
          </div>
          <div class="col-span-2">
            <div class="text-ink-soft">해지·만기 유출액 비율</div>
            <div class="tabular-nums font-bold" :class="toneLowerIsBetter(surrenderRatio, 0.3)">{{ formatPct(surrenderRatio, 1) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-plum px-4 py-2.5 font-display text-white">
        <PhChartPieSlice :size="18" weight="fill" />
        <span>수익성 &amp; 사업비</span>
      </div>
      <div class="p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">사업비율</div>
            <div class="tabular-nums font-bold" :class="toneLowerIsBetter(expenseRatio, 0.3)">{{ formatPct(expenseRatio, 1) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">합산비율</div>
            <div class="tabular-nums font-bold" :class="toneLowerIsBetter(combinedRatio, 1.0)">{{ formatPct(combinedRatio, 1) }}</div>
          </div>
          <div class="col-span-2">
            <div class="text-ink-soft">ROE (연환산)</div>
            <div class="tabular-nums font-bold" :class="toneHigherIsBetter(roeAnnual, 0)">{{ formatPct(roeAnnual, 1) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-teal px-4 py-2.5 font-display text-white">
        <PhBank :size="18" weight="fill" />
        <span>재무건전성</span>
      </div>
      <div class="p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">자본총계</div>
            <div class="tabular-nums font-bold">{{ formatWon(snapshot.equity) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">자본완충비율 (자본/준비금)</div>
            <div class="tabular-nums font-bold" :class="toneHigherIsBetter(solvencyProxy, 0.9)">
              {{ formatPct(solvencyProxy, 1) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-mustard px-4 py-2.5 font-display text-ink">
        <PhPiggyBank :size="18" weight="fill" />
        <span>계약서비스마진 (CSM)</span>
      </div>
      <div class="p-4">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-ink-soft">총 CSM 잔액</div>
            <div class="tabular-nums font-bold">{{ formatWon(snapshot.total_csm) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">이번 턴 CSM 환입액</div>
            <div class="tabular-nums font-bold">{{ formatWon(snapshot.csm_release) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">신규 CSM 설정액</div>
            <div class="tabular-nums font-bold">{{ formatWon(snapshot.csm_new_business) }}</div>
          </div>
          <div>
            <div class="text-ink-soft">CSM / 자본총계</div>
            <div class="tabular-nums font-bold">{{ formatPct(csmToEquityRatio, 1) }}</div>
          </div>
          <div class="col-span-2">
            <div class="text-ink-soft">손실부담계약손실 (이번 턴)</div>
            <div class="tabular-nums font-bold" :class="snapshot.onerous_loss > 0 ? 'text-coral-deep' : 'text-ink'">
              {{ formatWon(snapshot.onerous_loss) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: 시각 검증**

컨테이너 재시작 후 `/games/{id}` 좌측 컬럼 스크린샷: 6개 타일이 teal/mustard/coral/plum/teal/mustard 순서로 색상 배너를 가지며, 각 아이콘이 렌더링되는지 확인. 인접한 타일(위-아래)이 서로 다른 색인지 확인. 콘솔 에러 없음.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/components/MonitoringPanel.vue
git commit -m "feat(identity): restyle monitoring panel as board tiles"
```

---

### Task 5: `HistoryCharts.vue` 팔레트 적용

**Files:**
- Modify: `frontend/src/components/HistoryCharts.vue`

**Interfaces:**
- Consumes: Task 1 토큰(색상 hex 값은 CSS 변수가 아니라 Chart.js에 직접 hex 문자열로 전달 — Chart.js는 CSS 변수를 직접 못 읽으므로 토큰과 동일한 hex 값을 하드코딩).

- [ ] **Step 1: 차트 색상을 팔레트 hex로 교체**

`frontend/src/components/HistoryCharts.vue`에서 다음 6줄:

```js
const equityChartData = buildChartData('자본총계', (row) => row.equity, '#1e293b', { isMoney: true })
const premiumIncomeChartData = buildChartData('보험료수입', (row) => row.premium_income, '#0284c7', { isMoney: true })
const investmentIncomeChartData = buildChartData(
  '투자수익',
  (row) => row.investment_income,
  '#0ea5e9',
  { isMoney: true },
)
const expenseTotalChartData = buildChartData('비용합계', totalExpense, '#dc2626', { isMoney: true })
const totalReserveChartData = buildChartData('책임준비금', (row) => row.total_reserve, '#ea580c', { isMoney: true })
const inForceChartData = buildChartData('총 보유계약수', (row) => row.total_in_force, '#16a34a')
const csmChartData = buildChartData('총 CSM 잔액', (row) => row.total_csm, '#a855f7', { isMoney: true })
```

를 다음으로 교체 (팔레트: 자본총계=ink, 보험료수입=teal, 투자수익=teal-deep, 비용합계=coral, 책임준비금=mustard-deep, 총보유계약수=teal, CSM=plum):

```js
const equityChartData = buildChartData('자본총계', (row) => row.equity, '#2B2A4C', { isMoney: true })
const premiumIncomeChartData = buildChartData('보험료수입', (row) => row.premium_income, '#2A9D8F', { isMoney: true })
const investmentIncomeChartData = buildChartData(
  '투자수익',
  (row) => row.investment_income,
  '#1F7A6E',
  { isMoney: true },
)
const expenseTotalChartData = buildChartData('비용합계', totalExpense, '#E8604C', { isMoney: true })
const totalReserveChartData = buildChartData('책임준비금', (row) => row.total_reserve, '#D48F1F', { isMoney: true })
const inForceChartData = buildChartData('총 보유계약수', (row) => row.total_in_force, '#2A9D8F')
const csmChartData = buildChartData('총 CSM 잔액', (row) => row.total_csm, '#7B5EA7', { isMoney: true })
```

- [ ] **Step 2: 차트 타일 테두리를 보드타일 스타일로 교체**

같은 파일의 `<template>`에서 7개의 `<div class="h-48 rounded border border-slate-200 p-4">`를 전부 `<div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">`로 교체 (7곳 모두 동일하게, `replace_all` 적용 가능).

- [ ] **Step 3: 시각 검증**

컨테이너 재시작 후 `/games/{id}` 가운데 컬럼 스크린샷: 7개 차트가 새 팔레트 색상 라인으로 렌더링되고 타일 테두리/그림자가 적용됐는지 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/components/HistoryCharts.vue
git commit -m "feat(identity): apply boardgame palette to history charts"
```

---

### Task 6: `FinancialStatements.vue` 보드타일화

**Files:**
- Modify: `frontend/src/components/FinancialStatements.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`.

- [ ] **Step 1: `<script setup>` 상단에 아이콘 import 추가**

기존 `import { computed } from 'vue'` 바로 아래에 추가:

```js
import { PhReceipt, PhScales } from '@phosphor-icons/vue'
```

나머지 스크립트 로직은 변경하지 않는다.

- [ ] **Step 2: 템플릿 교체**

`<template>` 전체를 다음으로 교체:

```html
<template>
  <div class="space-y-4">
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-coral px-4 py-2.5 font-display text-white">
        <PhReceipt :size="18" weight="fill" />
        <span>손익계산서 (이번 턴)</span>
      </div>
      <div class="p-4">
        <table class="w-full text-sm">
          <tbody>
            <tr class="text-ink-soft"><td colspan="2" class="pt-1 font-medium">영업수익</td></tr>
            <tr><td class="pl-3">보험료수입</td><td class="tabular-nums text-right">{{ formatWon(snapshot.premium_income) }}</td></tr>
            <tr><td class="pl-3">투자수익</td><td class="tabular-nums text-right">{{ formatWon(snapshot.investment_income) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3">수익 합계</td><td class="tabular-nums text-right">{{ formatWon(revenueTotal) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">비용</td></tr>
            <tr><td class="pl-3">사망보험금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.death_claims) }}</td></tr>
            <tr><td class="pl-3">해약환급금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.surrender_payouts) }}</td></tr>
            <tr><td class="pl-3">만기보험금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.maturity_payouts) }}</td></tr>
            <tr><td class="pl-3">신계약수수료</td><td class="tabular-nums text-right">{{ formatWon(snapshot.commission_expense) }}</td></tr>
            <tr><td class="pl-3">마케팅비</td><td class="tabular-nums text-right">{{ formatWon(snapshot.marketing_expense) }}</td></tr>
            <tr><td class="pl-3">일반관리비</td><td class="tabular-nums text-right">{{ formatWon(snapshot.opex) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3">비용 합계</td><td class="tabular-nums text-right">{{ formatWon(expenseTotal) }}</td></tr>

            <tr><td class="pt-3">책임준비금전입액</td><td class="tabular-nums pt-3 text-right">{{ formatWon(snapshot.reserve_change) }}</td></tr>
            <tr><td class="pt-1">CSM 순증감</td><td class="tabular-nums pt-1 text-right">{{ formatWon(snapshot.csm_change) }}</td></tr>
            <tr><td>손실부담계약손실</td><td class="tabular-nums text-right">{{ formatWon(snapshot.onerous_loss) }}</td></tr>
            <tr class="border-t-[3px] border-ink text-base font-bold">
              <td class="pt-2">당기순이익</td>
              <td class="tabular-nums pt-2 text-right" :class="snapshot.net_income >= 0 ? 'text-teal-deep' : 'text-coral-deep'">
                {{ formatWon(snapshot.net_income) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-plum px-4 py-2.5 font-display text-white">
        <PhScales :size="18" weight="fill" />
        <span>재무상태표 (기말)</span>
      </div>
      <div class="p-4">
        <table class="w-full text-sm">
          <tbody>
            <tr class="text-ink-soft"><td colspan="2" class="pt-1 font-medium">자산</td></tr>
            <tr><td class="pl-3">예금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.deposit_balance) }}</td></tr>
            <tr><td class="pl-3">채권</td><td class="tabular-nums text-right">{{ formatWon(snapshot.bond_balance) }}</td></tr>
            <tr><td class="pl-3">주식</td><td class="tabular-nums text-right">{{ formatWon(snapshot.stock_balance) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3">자산총계</td><td class="tabular-nums text-right">{{ formatWon(assetsTotal) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">부채</td></tr>
            <tr><td class="pl-3">책임준비금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.total_reserve) }}</td></tr>
            <tr><td class="pl-3">계약서비스마진 (CSM)</td><td class="tabular-nums text-right">{{ formatWon(snapshot.total_csm) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">자본</td></tr>
            <tr class="border-t-[3px] border-ink text-base font-bold">
              <td class="pl-3 pt-2">자본총계 (Equity)</td>
              <td class="tabular-nums pt-2 text-right">{{ formatWon(snapshot.equity) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: 시각 검증**

컨테이너 재시작 후 `/games/{id}` 우측 컬럼 스크린샷: 손익계산서(coral 헤더)/재무상태표(plum 헤더) 타일이 보드타일 스타일로 렌더링되는지 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/components/FinancialStatements.vue
git commit -m "feat(identity): restyle financial statements as board tiles"
```

---

### Task 7: `DecisionPanel.vue` + `TurnControl.vue` 보드타일화

**Files:**
- Modify: `frontend/src/components/DecisionPanel.vue`
- Modify: `frontend/src/components/TurnControl.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`.

- [ ] **Step 1: `DecisionPanel.vue` — 아이콘 import 추가**

`<script setup>` 상단(`import { reactive } from 'vue'` 다음 줄)에 추가:

```js
import { PhDiceFive } from '@phosphor-icons/vue'
```

`form`/`handleSubmit` 로직은 변경하지 않는다.

- [ ] **Step 2: `DecisionPanel.vue` 템플릿 교체**

`<template>` 전체를 다음으로 교체:

```html
<template>
  <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
    <div class="flex items-center gap-2 bg-coral px-4 py-2.5 font-display text-white">
      <PhDiceFive :size="18" weight="fill" />
      <span>이번 턴 결정</span>
    </div>
    <div class="space-y-4 p-4">
      <div>
        <h3 class="mb-2 font-display text-ink">상품 가격 / 언더라이팅</h3>
        <div v-for="product in ['whole_life', 'savings']" :key="product" class="mb-2 grid grid-cols-3 items-center gap-2">
          <span class="text-sm">{{ product }}</span>
          <label class="text-xs">가격배수
            <input v-model.number="form.pricing_multiplier[product]" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
          </label>
          <label class="text-xs">엄격도
            <input v-model.number="form.underwriting_strictness[product]" type="number" step="0.05" min="0" max="1" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
          </label>
        </div>
        <p class="text-xs text-ink-soft">
          가격배수↑: 건당 보험료·마진 증가, 수요 급감 및 해지율 상승. 엄격도↑: 손해율 최대 30% 개선, 승인율 최대 40% 감소.
        </p>
      </div>
      <div>
        <h3 class="mb-2 font-display text-ink">채널</h3>
        <div v-for="channel in ['captive', 'ga']" :key="channel" class="mb-2 grid grid-cols-3 items-center gap-2">
          <span class="text-sm">{{ channel }}</span>
          <label class="text-xs">수수료율
            <input v-model.number="form.commission_rate[channel]" type="number" step="0.01" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
          </label>
          <label class="text-xs">모집비
            <input v-model.number="form.marketing_spend[channel]" type="number" step="1000000" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
          </label>
        </div>
        <p class="text-xs text-ink-soft">
          수수료율↑: 판매 유인 확대로 신계약 급증, 단기 수수료 비용 즉시 증가. 모집비↑: 생산성 확장(제곱근 체감), 과도하면 현금 낭비.
        </p>
      </div>
      <div>
        <h3 class="mb-2 font-display text-ink">자산배분 (합 1.0)</h3>
        <div class="grid grid-cols-3 gap-2">
          <label class="text-xs">예금 <input v-model.number="form.asset_allocation.deposit" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" /></label>
          <label class="text-xs">채권 <input v-model.number="form.asset_allocation.bond" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" /></label>
          <label class="text-xs">주식 <input v-model.number="form.asset_allocation.stock" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" /></label>
        </div>
        <p class="text-xs text-ink-soft">
          주식↑: 호황기 초과수익 기대, 위기 국면 시 대규모 손실 위험. 채권·예금↑: 안정적 이자수익, 기회비용 발생 가능.
        </p>
      </div>
      <div>
        <label class="block text-sm">배당 지급액
          <input v-model.number="form.dividend_payout" type="number" step="1000000" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
        </label>
        <p class="text-xs text-ink-soft">배당↑: 주주환원 및 ROE 제고, 자본총계(파산 위험 완충력) 감소.</p>
      </div>
      <button
        class="w-full rounded-full bg-coral py-3 font-display text-lg text-white shadow-[0_4px_0_var(--color-coral-deep)] active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-coral-deep)]"
        @click="handleSubmit"
      >
        턴 실행 ▶
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 3: `TurnControl.vue` — 아이콘 import 추가**

`<script setup>` 상단(`import { ref } from 'vue'` 다음 줄)에 추가:

```js
import { PhFastForward } from '@phosphor-icons/vue'
```

`autoTurns`/`defineProps`/`defineEmits` 로직은 변경하지 않는다.

- [ ] **Step 4: `TurnControl.vue` 템플릿 교체**

```html
<template>
  <div class="flex items-center gap-3 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
    <span class="text-sm text-ink-soft">가장 최근 결정으로 자동 진행:</span>
    <input v-model.number="autoTurns" type="number" min="1" max="24" class="w-16 rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
    <button
      class="flex items-center gap-1 rounded-full border-2 border-teal-deep bg-tile px-4 py-2 font-bold text-teal-deep shadow-[3px_3px_0_rgba(31,122,110,0.35)] disabled:opacity-50 active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(31,122,110,0.35)]"
      :disabled="disabled"
      @click="emit('run-turns', autoTurns)"
    >
      <PhFastForward :size="16" weight="fill" />
      자동 진행
    </button>
  </div>
</template>
```

- [ ] **Step 5: 시각 검증**

컨테이너 재시작 후 스크린샷: 결정 패널이 주사위 아이콘 + coral 헤더 타일로, "턴 실행" 버튼이 pill+그림자로, 자동진행 패널이 별도 타일로 렌더링되는지 확인. "턴 실행" 버튼 클릭 시 정상적으로 턴이 진행되는지(기능 회귀 없음) 확인.

- [ ] **Step 6: 커밋**

```bash
git add frontend/src/components/DecisionPanel.vue frontend/src/components/TurnControl.vue
git commit -m "feat(identity): restyle decision panel and turn control as board tiles"
```

---

### Task 8: `GameSettingsPanel.vue` 보드타일화

**Files:**
- Modify: `frontend/src/components/GameSettingsPanel.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`.

- [ ] **Step 1: 아이콘 import 추가**

`<script setup>` 최상단에 추가:

```js
import { PhGearSix, PhPackage, PhUsersFour, PhX } from '@phosphor-icons/vue'
```

`defineProps`/`defineEmits`/`PRODUCT_LABELS`/`CHANNEL_LABELS`/`formatWon`/`formatPct`는 변경하지 않는다.

- [ ] **Step 2: 템플릿 교체**

`<template>` 전체를 다음으로 교체:

```html
<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4" @click.self="emit('close')">
    <div class="max-h-[85vh] w-full max-w-2xl overflow-y-auto overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[8px_8px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center justify-between bg-plum px-6 py-3 font-display text-white">
        <span class="flex items-center gap-2"><PhGearSix :size="20" weight="fill" /> 게임 설정</span>
        <button class="flex items-center gap-1 text-sm hover:opacity-80" @click="emit('close')">
          <PhX :size="16" weight="bold" /> 닫기
        </button>
      </div>

      <div class="p-6">
        <div class="mb-6">
          <div class="text-sm text-ink-soft">최종 턴 수</div>
          <div class="tabular-nums font-display text-lg">{{ gameLengthTurns }}턴</div>
        </div>

        <div v-if="config" class="space-y-6">
          <div>
            <h3 class="mb-2 flex items-center gap-1 font-display text-ink"><PhPackage :size="16" weight="fill" /> 상품 기본 설정</h3>
            <div class="overflow-x-auto rounded-[14px] border-2 border-board-cream-deep">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-board-cream-deep text-left text-ink-soft">
                    <th class="p-2">상품</th>
                    <th class="p-2">가입금액</th>
                    <th class="p-2">기본 원가율</th>
                    <th class="p-2">사업비 로딩</th>
                    <th class="p-2">기본 해지율</th>
                    <th class="p-2">준비금 적립률</th>
                    <th class="p-2">부리 스프레드</th>
                    <th class="p-2">만기(턴)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(product, code) in config.products" :key="code" class="border-t border-board-cream-deep">
                    <td class="p-2 font-medium">{{ PRODUCT_LABELS[code] ?? code }}</td>
                    <td class="tabular-nums p-2">{{ formatWon(product.unit_size) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.base_cost_rate_annual) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.expense_loading) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.base_lapse_rate_annual) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.reserve_accrual_ratio) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.credited_rate_spread) }}</td>
                    <td class="tabular-nums p-2">{{ product.maturity_turns ?? '종신' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3 class="mb-2 flex items-center gap-1 font-display text-ink"><PhUsersFour :size="16" weight="fill" /> 채널 기본 설정</h3>
            <div class="overflow-x-auto rounded-[14px] border-2 border-board-cream-deep">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-board-cream-deep text-left text-ink-soft">
                    <th class="p-2">채널</th>
                    <th class="p-2">기준 생산성</th>
                    <th class="p-2">기본 수수료율</th>
                    <th class="p-2">수수료 민감도</th>
                    <th class="p-2">마케팅비 기준액</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(channel, code) in config.channels" :key="code" class="border-t border-board-cream-deep">
                    <td class="p-2 font-medium">{{ CHANNEL_LABELS[code] ?? code }}</td>
                    <td class="tabular-nums p-2">{{ channel.base_productivity }}건/월</td>
                    <td class="tabular-nums p-2">{{ formatPct(channel.base_commission_rate) }}</td>
                    <td class="tabular-nums p-2">{{ channel.commission_sensitivity }}</td>
                    <td class="tabular-nums p-2">{{ formatWon(channel.reference_spend) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-ink-soft">설정을 불러오는 중...</div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: 시각 검증**

컨테이너 재시작 후 "설정" 버튼 클릭 → 모달 스크린샷: plum 헤더 배너, 표에 은은한 크림색 헤더 행, 닫기 버튼 정상 동작 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/components/GameSettingsPanel.vue
git commit -m "feat(identity): restyle game settings modal as board tile"
```

---

### Task 9: `RegimeTimeline.vue` 팔레트 적용 + `ResultView.vue` 보드타일화

**Files:**
- Modify: `frontend/src/components/RegimeTimeline.vue`
- Modify: `frontend/src/views/ResultView.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`.

- [ ] **Step 1: `RegimeTimeline.vue` 색상 팔레트 교체**

`REGIME_COLORS` 상수를:

```js
const REGIME_COLORS = { normal: '#94a3b8', boom: '#22c55e', crisis: '#ef4444' }
```

에서 다음으로 교체 (그 외 로직은 변경 없음):

```js
const REGIME_COLORS = { normal: '#F3E4C6', boom: '#2A9D8F', crisis: '#E8604C' }
```

템플릿의 바깥 컨테이너 `<div class="rounded border border-slate-200 p-4">`를 `<div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">`로 교체. 제목 `<h2 class="mb-3 font-semibold text-slate-800">`를 `<h2 class="mb-3 font-display text-ink">`로 교체. 나머지 `text-slate-500`/`text-slate-600`은 각각 `text-ink-soft`로 교체.

- [ ] **Step 2: `ResultView.vue` — 아이콘 import 추가**

`<script setup>` 상단에 추가:

```js
import { PhConfetti, PhSkull } from '@phosphor-icons/vue'
```

나머지 로직은 변경하지 않는다.

- [ ] **Step 3: `ResultView.vue` 템플릿 교체**

`<template>` 전체를 다음으로 교체:

```html
<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-8">
    <div
      class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile p-8 text-center shadow-[6px_6px_0_rgba(43,42,76,0.28)]"
    >
      <div class="mb-3 flex items-center justify-center gap-2 font-display text-3xl" :class="store.status === 'bankrupt' ? 'text-coral-deep' : 'text-teal-deep'">
        <component :is="store.status === 'bankrupt' ? PhSkull : PhConfetti" :size="32" weight="fill" />
        {{ store.status === 'bankrupt' ? '파산' : '경영 종료' }}
      </div>
      <p class="mb-2 text-ink-soft">최종 턴: {{ store.currentTurn }} / {{ store.gameLengthTurns }}</p>
      <p class="tabular-nums font-display text-3xl">{{ new Intl.NumberFormat('ko-KR').format(Math.round(store.snapshot.equity)) }}원</p>
      <router-link
        to="/"
        class="mt-6 inline-block rounded-full border-2 border-ink bg-board-cream px-4 py-2 text-sm font-bold text-ink shadow-[3px_3px_0_rgba(43,42,76,0.28)]"
      >
        새 게임 시작
      </router-link>
    </div>

    <RegimeTimeline :history="store.history" />

    <div>
      <h2 class="mb-3 font-display text-lg text-ink">지표 변화 추이</h2>
      <HistoryCharts :history="store.history" />
    </div>
  </div>
  <div v-else class="p-8 text-ink-soft">불러오는 중...</div>
</template>
```

- [ ] **Step 4: 시각 검증**

`/games/{id}/result`로 이동해 스크린샷: 결과 배너가 보드타일 스타일 + 트로피/해골 아이콘으로 렌더링, 국면 타임라인 색상이 새 팔레트로 바뀌었는지 확인.

- [ ] **Step 5: 커밋**

```bash
git add frontend/src/components/RegimeTimeline.vue frontend/src/views/ResultView.vue
git commit -m "feat(identity): restyle result screen and regime timeline"
```

---

### Task 10: `NewGameView.vue` 보드타일화

**Files:**
- Modify: `frontend/src/views/NewGameView.vue`

**Interfaces:**
- Consumes: Task 1 토큰, `@phosphor-icons/vue`.

- [ ] **Step 1: 아이콘 import 추가**

`<script setup>` 상단에 추가:

```js
import { PhPlayCircle } from '@phosphor-icons/vue'
```

`initialCapital`/`rngSeed`/`gameLengthTurns`/`handleCreate` 로직은 변경하지 않는다.

- [ ] **Step 2: 템플릿 교체**

`<template>` 전체를 다음으로 교체:

```html
<template>
  <div class="mx-auto mt-24 max-w-md overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile shadow-[6px_6px_0_rgba(43,42,76,0.28)]">
    <div class="bg-coral px-6 py-4 text-center font-display text-2xl text-white">보험회사 운영 시뮬레이션</div>
    <div class="p-6">
      <label class="mb-1 block text-sm font-medium text-ink-soft">초기 자본</label>
      <input v-model="initialCapital" type="number" class="mb-4 w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-3 py-2" />
      <label class="mb-1 block text-sm font-medium text-ink-soft">시드 (선택)</label>
      <input v-model="rngSeed" type="number" placeholder="비워두면 무작위" class="mb-4 w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-3 py-2" />
      <label class="mb-1 block text-sm font-medium text-ink-soft">최종 턴 수 (1~600)</label>
      <input
        v-model="gameLengthTurns"
        type="number"
        min="1"
        max="600"
        class="mb-6 w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-3 py-2"
      />
      <button
        class="flex w-full items-center justify-center gap-2 rounded-full bg-coral py-3 font-display text-lg text-white shadow-[0_4px_0_var(--color-coral-deep)] disabled:opacity-50 active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-coral-deep)]"
        :disabled="isCreating"
        @click="handleCreate"
      >
        <PhPlayCircle :size="20" weight="fill" />
        새 게임 시작
      </button>
      <p v-if="errorMessage" class="mt-4 text-sm text-coral-deep">{{ errorMessage }}</p>
    </div>
  </div>
</template>
```

- [ ] **Step 3: 시각 검증**

컨테이너 재시작 후 `/` 스크린샷: 코랄색 타이틀 배너 + 보드타일 카드, "새 게임 시작" 버튼이 pill+그림자로 렌더링되는지 확인. 실제로 게임 생성이 되는지(폼 제출 회귀 없음) 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/views/NewGameView.vue
git commit -m "feat(identity): restyle new-game screen as board tile"
```

---

### Task 11: 전체 화면 최종 시각 검증

**Files:** 없음 (검증 전용, 발견된 이슈가 있으면 해당 파일만 소폭 수정)

- [ ] **Step 1: 전체 플로우 재생**

`podman restart insurance_company_simulator_frontend_1` 후 Playwright로 다음을 순서대로 확인:
1. `/` (새 게임 시작 화면) — 스크린샷
2. 새 게임 생성 → `/games/{id}` (턴 진행 화면) — 스크린샷, 턴 1회 실행 후 재스크린샷(턴 경로 말이 이동하는지 확인)
3. "설정" 버튼 클릭 → 모달 — 스크린샷, 닫기 확인
4. "자동 진행" 클릭 후 여러 턴 진행 — 스크린샷 (차트에 데이터 포인트가 쌓이는지 확인)
5. 게임을 파산/종료까지 진행하기 어려우므로, 기존 게임을 `/games/{id}/result`로 직접 접속 — 스크린샷

- [ ] **Step 2: 일관성 점검**

각 화면에서: (a) 인접 타일 색상이 겹치지 않는지, (b) 모든 타일이 동일한 테두리 두께/그림자 오프셋을 쓰는지, (c) Jua/Gowun Dodum 폰트가 실제로 로드되어 적용됐는지(네트워크 탭 또는 `getComputedStyle` 확인 불필요 — 스크린샷상 손글씨풍 렌더링으로 육안 확인 가능), (d) 브라우저 콘솔에 에러/폰트 로드 실패 경고가 없는지.

- [ ] **Step 3: 발견된 문제 수정**

이슈가 있으면 해당 컴포넌트 파일만 수정하고 재검증한다. 새 기능이나 리팩터링을 추가하지 않는다(이 태스크는 검증·버그수정 전용).

- [ ] **Step 4: 커밋 (수정사항이 있는 경우에만)**

```bash
git add <수정된 파일>
git commit -m "fix(identity): polish visual inconsistencies found in end-to-end pass"
```

수정사항이 없으면 커밋하지 않는다.
