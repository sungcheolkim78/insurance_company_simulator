# 대시보드 드래그 재배치 레이아웃 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 턴 화면(`DashboardView.vue`)의 6개 정보/기능 패널(KPI카드, 모니터링패널, 히스토리차트, 재무제표, 의사결정패널, 턴컨트롤)을 사용자가 드래그로 3컬럼 그리드 안에서 자유롭게 재배치할 수 있게 하고, 그 배치를 브라우저 `localStorage`에 저장해 새로고침/게임 전환 후에도 유지되게 한다.

**Architecture:** `vuedraggable`(SortableJS Vue 3 래퍼)로 3개의 드래그 가능한 컬럼을 만들고, 각 컬럼은 패널 키 문자열의 배열을 담는다. 각 패널은 새 `DraggablePanel.vue` 래퍼(고유 색상 그립 손잡이 + 보드타일 테두리)로 감싸 렌더링한다. 레이아웃 상태는 `frontend/src/utils/dashboardLayout.js`의 순수 함수(`loadLayout`/`saveLayout`/`resetLayout`)를 통해 `localStorage`와 동기화한다.

**Tech Stack:** Vue 3 `<script setup>`, Tailwind CSS v4, `vuedraggable@^4.1.0`(신규 의존성, SortableJS 기반), `@phosphor-icons/vue@2.2.1`(기존 의존성), `vitest@^4.1.11` + `jsdom@^30.0.1`(신규 — 이 프로젝트 프론트엔드 최초의 자동화 테스트 인프라).

**Spec:** `docs/superpowers/specs/2026-08-30-dashboard-draggable-layout-design.md`

## Global Constraints

- 재배치 단위는 **컴포넌트 단위** 6개뿐이다: `kpi`, `monitoring`, `charts`, `financials`, `decision`, `turncontrol`. 각 컴포넌트 내부(모니터링패널의 6개 그룹, 히스토리차트의 8개 그래프 등)는 절대 쪼개지 않는다.
- 재배치 기능은 **순서/위치 변경만** 지원한다. 리사이즈, 게임별 서버 저장, 키보드 전용 재배치는 이번 스코프에서 완전히 제외한다.
- 레이아웃은 `localStorage` 키 `dashboard-layout-v1`에 브라우저 전역으로 저장한다 (게임 ID와 무관).
- 기본 레이아웃(현재 화면과 동일하게 보이도록): `[["kpi","monitoring"], ["charts"], ["financials","decision","turncontrol"]]`.
- 그립 손잡이 색상은 패널마다 겹치지 않게 고정 배정한다: `kpi`=`bg-coral`, `monitoring`=`bg-teal`, `charts`=`bg-mustard`, `financials`=`bg-plum`, `decision`=`bg-coral-deep`, `turncontrol`=`bg-teal-deep`. `bg-mustard` 배너는 흰 글자 대비가 나빠(과거 최종 리뷰에서 지적됨) `text-ink`를 쓰고, 나머지는 `text-white`를 쓴다.
- `TurnPathTracker`와 상단 헤더 버튼(설정/게임종료/레이아웃 초기화)은 재배치 대상이 아니며 항상 최상단 고정 위치에 남는다.
- 프론트엔드에는 지금까지 자동화 테스트가 전혀 없었다. 이번 플랜에서 자동화 테스트를 붙이는 대상은 **`dashboardLayout.js` 순수 함수 하나뿐**이다 (비-시각적 로직에 5가지 명시적 폴백 규칙이 있어 회귀 위험이 큼). Vue 컴포넌트(`DraggablePanel.vue`, `DashboardView.vue` 등)는 이 프로젝트의 기존 관행대로 Playwright 수동/자동 시각 검증으로 확인한다 — Vue Test Utils 등 컴포넌트 테스트 도구는 이번 플랜에서 새로 들이지 않는다.
- 이 워크트리/컨테이너 환경에서 프론트엔드 컨테이너 이름은 실행 시점의 podman-compose 프로젝트 이름에 따라 다르다 (`podman ps`로 확인). Vite 개발 서버는 `frontend/src`와 `frontend/index.html`만 바인드마운트되어 있어 호스트 파일 변경을 놓치는 경우가 있으므로, 변경 후 반영이 안 되면 `podman restart <컨테이너명>`으로 해결한다.
- `@phosphor-icons/vue@2.2.1`에서 이 플랜이 사용하는 모든 아이콘명(`PhCoins`, `PhChartBar`, `PhChartLineUp`, `PhScales`, `PhDiceFive`, `PhFastForward`, `PhDotsSixVertical`, `PhArrowCounterClockwise`)은 계획 작성 시점에 `frontend/node_modules/@phosphor-icons/vue/dist/icons/`에 실제 파일이 존재함을 확인했다 — 이전 플랜(보드게임 아이덴티티)과 달리 이번엔 검증된 값이다.

---

### Task 1: `dashboardLayout.js` 유틸 + 테스트 인프라

**Files:**
- Create: `frontend/src/utils/dashboardLayout.js`
- Create: `frontend/src/utils/dashboardLayout.test.js`
- Modify: `frontend/package.json` (devDependencies에 `vitest`, `jsdom` 추가, `scripts`에 `test` 추가)
- Modify: `frontend/vite.config.js` (vitest `test` 설정 추가)

**Interfaces:**
- Produces: `PANEL_KEYS: string[]`, `DEFAULT_LAYOUT: string[][]`, `loadLayout(): string[][]`, `saveLayout(columns: string[][]): void`, `resetLayout(): string[][]` — Task 3(DashboardView.vue 통합)이 이 5개를 그대로 import해서 쓴다.

- [ ] **Step 1: 테스트 파일 작성**

`frontend/src/utils/dashboardLayout.test.js`:

```js
import { beforeEach, describe, expect, it } from 'vitest'
import { DEFAULT_LAYOUT, PANEL_KEYS, loadLayout, resetLayout, saveLayout } from './dashboardLayout'

const STORAGE_KEY = 'dashboard-layout-v1'

beforeEach(() => {
  localStorage.clear()
})

describe('PANEL_KEYS / DEFAULT_LAYOUT', () => {
  it('기본 레이아웃은 6개 패널 키를 정확히 한 번씩만 포함한다', () => {
    const flat = DEFAULT_LAYOUT.flat()
    expect(flat.sort()).toEqual([...PANEL_KEYS].sort())
  })

  it('기본 레이아웃은 3개 컬럼으로 구성된다', () => {
    expect(DEFAULT_LAYOUT).toHaveLength(3)
  })
})

describe('loadLayout', () => {
  it('저장된 값이 없으면 기본 레이아웃을 반환한다', () => {
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('저장된 JSON이 깨져 있으면 기본 레이아웃으로 폴백한다', () => {
    localStorage.setItem(STORAGE_KEY, 'not-json{')
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('columns 필드가 없거나 배열이 아니면 기본 레이아웃으로 폴백한다', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ foo: 'bar' }))
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('컬럼 개수가 3이 아니면 기본 레이아웃으로 완전히 폴백한다', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ columns: [['kpi'], ['charts']] }))
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('알 수 없는 패널 키는 무시하고 제거한다', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ columns: [['kpi', 'bogus', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']] }),
    )
    expect(loadLayout()).toEqual([['kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']])
  })

  it('레지스트리에는 있지만 저장된 값에 없는 키는 컬럼1 끝에 자동으로 추가한다', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ columns: [['kpi'], ['charts'], ['financials', 'decision', 'turncontrol']] }),
    )
    expect(loadLayout()).toEqual([['kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']])
  })

  it('중복된 키는 처음 등장한 위치만 남기고 제거한다', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ columns: [['kpi', 'kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']] }),
    )
    expect(loadLayout()).toEqual([['kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']])
  })

  it('정상적인 커스텀 레이아웃은 그대로 반환한다', () => {
    const custom = [['monitoring'], ['kpi', 'charts'], ['financials', 'decision', 'turncontrol']]
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ columns: custom }))
    expect(loadLayout()).toEqual(custom)
  })
})

describe('saveLayout', () => {
  it('전달받은 columns를 그대로 localStorage에 JSON으로 저장한다', () => {
    const custom = [['monitoring'], ['kpi', 'charts'], ['financials', 'decision', 'turncontrol']]
    saveLayout(custom)
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual({ columns: custom })
  })
})

describe('resetLayout', () => {
  it('저장된 값을 지우고 기본 레이아웃을 반환한다', () => {
    saveLayout([['monitoring'], ['kpi', 'charts'], ['financials', 'decision', 'turncontrol']])
    const result = resetLayout()
    expect(result).toEqual(DEFAULT_LAYOUT)
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})
```

- [ ] **Step 2: 테스트 인프라 설치**

```bash
cd frontend
npm install -D vitest@^4.1.11 jsdom@^30.0.1
```

`frontend/vite.config.js`를 다음으로 교체:

```js
/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: { port: 5173 },
  test: {
    environment: 'jsdom',
  },
})
```

`frontend/package.json`의 `scripts`에 추가:

```json
"test": "vitest run"
```

- [ ] **Step 3: 테스트 실행 → 실패 확인**

Run: `cd frontend && npm test`
Expected: FAIL — `dashboardLayout.js` 모듈이 아직 없어서 import 에러 발생.

- [ ] **Step 4: `dashboardLayout.js` 구현**

`frontend/src/utils/dashboardLayout.js`:

```js
export const PANEL_KEYS = ['kpi', 'monitoring', 'charts', 'financials', 'decision', 'turncontrol']

export const DEFAULT_LAYOUT = [
  ['kpi', 'monitoring'],
  ['charts'],
  ['financials', 'decision', 'turncontrol'],
]

const STORAGE_KEY = 'dashboard-layout-v1'

function cloneDefaultLayout() {
  return DEFAULT_LAYOUT.map((column) => [...column])
}

export function loadLayout() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return cloneDefaultLayout()

  let parsed
  try {
    parsed = JSON.parse(raw)
  } catch (err) {
    return cloneDefaultLayout()
  }

  if (!parsed || !Array.isArray(parsed.columns) || parsed.columns.length !== 3) {
    return cloneDefaultLayout()
  }

  const seen = new Set()
  const columns = parsed.columns.map((column) => {
    if (!Array.isArray(column)) return []
    const deduped = []
    for (const key of column) {
      if (!PANEL_KEYS.includes(key)) continue
      if (seen.has(key)) continue
      seen.add(key)
      deduped.push(key)
    }
    return deduped
  })

  const missingKeys = PANEL_KEYS.filter((key) => !seen.has(key))
  columns[0] = [...columns[0], ...missingKeys]

  return columns
}

export function saveLayout(columns) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ columns }))
}

export function resetLayout() {
  localStorage.removeItem(STORAGE_KEY)
  return cloneDefaultLayout()
}
```

- [ ] **Step 5: 테스트 실행 → 통과 확인**

Run: `cd frontend && npm test`
Expected: PASS — 11개 테스트 모두 통과 (`PANEL_KEYS`/`DEFAULT_LAYOUT` 2개 + `loadLayout` 7개 + `saveLayout` 1개 + `resetLayout` 1개).

- [ ] **Step 6: 커밋**

```bash
git add frontend/src/utils/dashboardLayout.js frontend/src/utils/dashboardLayout.test.js frontend/package.json frontend/package-lock.json frontend/vite.config.js
git commit -m "$(cat <<'EOF'
feat(dashboard-layout): add layout persistence utility with tests

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(주의: `npm install`이 `frontend/package-lock.json`을 갱신한다. 이 프로젝트는 podman 컨테이너 안에서 `npm install`을 실행하면 락파일이 호스트에 동기화되지 않는 문제가 과거에 있었다 — 반드시 **호스트에서** `npm install`을 실행하고, 갱신된 `package-lock.json`이 실제로 diff에 포함됐는지 커밋 전에 `git status`로 확인한다.)

---

### Task 2: `DecisionPanel.vue` + `TurnControl.vue` — 자체 배너/테두리 제거

**Files:**
- Modify: `frontend/src/components/DecisionPanel.vue`
- Modify: `frontend/src/components/TurnControl.vue`

**Interfaces:**
- Consumes: 없음 (기존 두 파일의 `defineEmits`/`defineProps`/폼 로직은 전혀 변경하지 않는다).
- Produces: 두 컴포넌트의 최상위 루트 엘리먼트가 더 이상 자체 보드타일 테두리/그림자를 갖지 않는다 — Task 3의 `DraggablePanel.vue`가 그 시각적 책임(테두리+그림자+타이틀 배너)을 대신 맡는다는 전제로 동작한다.

**왜 이 두 파일만 수정하는가:** `KpiCards.vue`/`MonitoringPanel.vue`/`HistoryCharts.vue`/`FinancialStatements.vue`는 최상위 루트가 이미 `<div class="space-y-4">`(또는 grid) 같은 순수 레이아웃 컨테이너이고, 테두리는 그 안의 여러 서브 타일(모니터링의 6개 그룹, 재무제표의 2개 표 등)에 개별적으로 있다 — 이 4개 파일은 `DraggablePanel`이 감싸도 이중 테두리가 생기지 않으므로 **전혀 수정하지 않는다**. 반면 `DecisionPanel.vue`와 `TurnControl.vue`는 컴포넌트 전체가 하나의 타일이라 최상위 루트 자체에 테두리가 있어 이중 테두리가 생긴다. 추가로 `DecisionPanel.vue`는 자체 타이틀 배너("이번 턴 결정" + `PhDiceFive`)까지 갖고 있어, `DraggablePanel`이 같은 정보를 담은 배너를 또 얹으면 배너가 2개 겹친다 — 그래서 이 파일만 배너 자체도 제거한다. `TurnControl.vue`는 원래 배너가 없어(무배너 디자인) 테두리만 제거한다.

- [ ] **Step 1: `DecisionPanel.vue`에서 자체 타이틀 배너 + 테두리 제거**

`frontend/src/components/DecisionPanel.vue`의 `<script setup>` 상단에서 이제 쓰이지 않는 아이콘 import 제거:

```js
import { reactive } from 'vue'
```

(`import { PhDiceFive } from '@phosphor-icons/vue'` 줄을 삭제 — 아래에서 배너를 지우면 이 아이콘을 쓰는 곳이 없어진다.)

`<template>`을 다음으로 교체:

```html
<template>
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
</template>
```

(변경 내용: 최상위 `<div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[...]">`와 그 안의 헤더 배너 `<div class="flex items-center gap-2 bg-coral ...">...</div>`를 제거하고, 기존 콘텐츠 `<div class="space-y-4 p-4">`를 최상위 루트로 승격했다. `<script setup>`의 `form`/`handleSubmit`/`defineEmits`는 전혀 건드리지 않는다.)

- [ ] **Step 2: `TurnControl.vue`에서 테두리만 제거**

`frontend/src/components/TurnControl.vue`의 `<template>`에서 최상위 `<div>`의 class를:

```
"flex items-center gap-3 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]"
```

에서 다음으로 교체 (레이아웃/패딩 클래스는 유지, 타일 테두리/배경/그림자 클래스만 제거):

```
"flex items-center gap-3 p-4"
```

그 외 `<script setup>`과 `<template>`의 나머지 내용(`autoTurns`, `PhFastForward` import, 버튼)은 전혀 변경하지 않는다.

- [ ] **Step 3: 빌드 확인**

Run: `cd frontend && npm run build`
Expected: 에러 없이 빌드 성공 (이 시점에서는 두 컴포넌트가 아직 `DashboardView.vue`에서 예전 방식대로 렌더링되므로, 브라우저에서 보면 이 두 패널만 일시적으로 테두리 없이 "헐벗은" 모습으로 보일 것이다 — Task 3에서 `DraggablePanel`로 감싸면 정상으로 돌아온다. 이 중간 상태는 정상이다.)

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/components/DecisionPanel.vue frontend/src/components/TurnControl.vue
git commit -m "$(cat <<'EOF'
refactor(dashboard-layout): strip own tile chrome from DecisionPanel and TurnControl

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `vuedraggable` 추가 + `DraggablePanel.vue` 생성 + `DashboardView.vue` 통합

**Files:**
- Modify: `frontend/package.json` (dependencies에 `vuedraggable` 추가)
- Create: `frontend/src/components/DraggablePanel.vue`
- Modify: `frontend/src/views/DashboardView.vue`

**Interfaces:**
- Consumes: Task 1의 `loadLayout`/`saveLayout`/`resetLayout` (경로: `../utils/dashboardLayout`). Task 2에서 테두리가 제거된 `DecisionPanel.vue`/`TurnControl.vue`.
- Produces: `DraggablePanel` 컴포넌트 — props `panelKey: String`(필수), `title: String`(필수), `icon: Object|Function`(필수, Phosphor 아이콘 컴포넌트), `colorClass: String`(필수, 예: `'bg-coral'`). 기본 슬롯에 실제 패널 컴포넌트를 넣어 사용한다.

- [ ] **Step 1: `vuedraggable` 의존성 추가**

```bash
cd frontend
npm install vuedraggable@^4.1.0
```

- [ ] **Step 2: `DraggablePanel.vue` 작성**

`frontend/src/components/DraggablePanel.vue`:

```vue
<script setup>
import { computed } from 'vue'
import { PhDotsSixVertical } from '@phosphor-icons/vue'

const props = defineProps({
  panelKey: { type: String, required: true },
  title: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  colorClass: { type: String, required: true },
})

const textClass = computed(() => (props.colorClass === 'bg-mustard' ? 'text-ink' : 'text-white'))
</script>

<template>
  <div
    :data-panel-key="panelKey"
    class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]"
  >
    <div
      class="drag-handle flex cursor-grab items-center gap-2 px-4 py-2 font-display active:cursor-grabbing"
      :class="[colorClass, textClass]"
    >
      <PhDotsSixVertical :size="16" weight="bold" />
      <component :is="icon" :size="16" weight="fill" />
      <span>{{ title }}</span>
    </div>
    <div class="p-1">
      <slot />
    </div>
  </div>
</template>
```

- [ ] **Step 3: `DashboardView.vue` 전체 교체**

`frontend/src/views/DashboardView.vue`를 다음으로 교체:

```vue
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import { useGameStore } from '../stores/gameStore'
import { deleteGame } from '../api/client'
import KpiCards from '../components/KpiCards.vue'
import HistoryCharts from '../components/HistoryCharts.vue'
import MonitoringPanel from '../components/MonitoringPanel.vue'
import FinancialStatements from '../components/FinancialStatements.vue'
import DecisionPanel from '../components/DecisionPanel.vue'
import TurnControl from '../components/TurnControl.vue'
import GameSettingsPanel from '../components/GameSettingsPanel.vue'
import TurnPathTracker from '../components/TurnPathTracker.vue'
import DraggablePanel from '../components/DraggablePanel.vue'
import {
  PhArrowCounterClockwise,
  PhChartBar,
  PhChartLineUp,
  PhCoins,
  PhDiceFive,
  PhDoorOpen,
  PhFastForward,
  PhGearSix,
  PhScales,
} from '@phosphor-icons/vue'
import { loadLayout, resetLayout, saveLayout } from '../utils/dashboardLayout'

const props = defineProps({ id: String })
const store = useGameStore()
const router = useRouter()
const lastDecision = ref(null)
const isBusy = ref(false)
const errorMessage = ref('')
const showSettings = ref(false)
const columns = ref([[], [], []])

const prevSnapshot = computed(() =>
  store.history.length >= 2 ? store.history[store.history.length - 2] : null,
)

const PANEL_META = {
  kpi: { component: KpiCards, title: 'KPI 카드', icon: PhCoins, colorClass: 'bg-coral' },
  monitoring: { component: MonitoringPanel, title: '모니터링 지표', icon: PhChartBar, colorClass: 'bg-teal' },
  charts: { component: HistoryCharts, title: '히스토리 차트', icon: PhChartLineUp, colorClass: 'bg-mustard' },
  financials: { component: FinancialStatements, title: '재무제표', icon: PhScales, colorClass: 'bg-plum' },
  decision: { component: DecisionPanel, title: '의사결정', icon: PhDiceFive, colorClass: 'bg-coral-deep' },
  turncontrol: { component: TurnControl, title: '턴 진행', icon: PhFastForward, colorClass: 'bg-teal-deep' },
}

function bindingsFor(key) {
  if (key === 'kpi') return { snapshot: store.snapshot }
  if (key === 'monitoring') {
    return { snapshot: store.snapshot, prevSnapshot: prevSnapshot.value, decision: lastDecision.value }
  }
  if (key === 'charts') return { history: store.history }
  if (key === 'financials') return { snapshot: store.snapshot }
  if (key === 'decision') return { onSubmit: handleDecisionSubmit }
  if (key === 'turncontrol') {
    return { disabled: isBusy.value || store.status !== 'running', onRunTurns: runTurns }
  }
  return {}
}

function persistLayout() {
  saveLayout(columns.value)
}

function handleResetLayout() {
  columns.value = resetLayout()
}

onMounted(() => {
  store.load(Number(props.id))
  columns.value = loadLayout()
})

async function handleDecisionSubmit(decision) {
  lastDecision.value = decision
  await runTurns(1)
}

async function runTurns(count) {
  if (!lastDecision.value || isBusy.value) return
  isBusy.value = true
  errorMessage.value = ''
  try {
    for (let i = 0; i < count; i++) {
      if (store.status !== 'running') break
      // eslint-disable-next-line no-await-in-loop
      await store.advanceTurn(lastDecision.value)
    }
  } catch (err) {
    errorMessage.value = '턴 처리에 실패했습니다. 입력값을 확인하고 다시 시도해주세요.'
  } finally {
    isBusy.value = false
  }
  if (store.status !== 'running') {
    router.push(`/games/${props.id}/result`)
  }
}

async function handleEndGame() {
  if (isBusy.value) return
  if (!window.confirm('현재 게임을 종료하고 새 시뮬레이션을 시작할까요? 진행 상황은 삭제됩니다.')) return
  isBusy.value = true
  try {
    await deleteGame(Number(props.id))
    router.push('/')
  } catch (err) {
    errorMessage.value = '게임 종료에 실패했습니다. 다시 시도해주세요.'
    isBusy.value = false
  }
}
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-6xl space-y-6 p-8">
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
          class="flex items-center gap-1 rounded-full border-2 border-ink bg-tile px-4 py-2 text-sm font-bold text-ink shadow-[3px_3px_0_rgba(43,42,76,0.28)] active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(43,42,76,0.28)]"
          @click="handleResetLayout"
        >
          <PhArrowCounterClockwise :size="16" weight="fill" />
          레이아웃 초기화
        </button>
        <button
          class="flex items-center gap-1 rounded-full border-2 border-ink bg-tile px-4 py-2 text-sm font-bold text-ink shadow-[3px_3px_0_rgba(43,42,76,0.28)] active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(43,42,76,0.28)]"
          @click="showSettings = true"
        >
          <PhGearSix :size="16" weight="fill" />
          설정
        </button>
        <button
          class="flex items-center gap-1 rounded-full border-2 border-coral-deep bg-tile px-4 py-2 text-sm font-bold text-coral-deep shadow-[3px_3px_0_rgba(200,73,47,0.35)] disabled:opacity-50 active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(200,73,47,0.35)]"
          :disabled="isBusy"
          @click="handleEndGame"
        >
          <PhDoorOpen :size="16" weight="fill" />
          게임 종료 &amp; 새 시뮬레이션
        </button>
      </div>
    </div>
    <p v-if="errorMessage" class="text-sm text-coral-deep">{{ errorMessage }}</p>
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <draggable
        v-model="columns[0]"
        :item-key="(key) => key"
        group="dashboard-panels"
        handle=".drag-handle"
        ghost-class="opacity-40"
        class="min-h-[80px] space-y-6 rounded-[14px] border-2 border-dashed border-transparent transition-colors"
        @change="persistLayout"
      >
        <template #item="{ element }">
          <DraggablePanel
            :panel-key="element"
            :title="PANEL_META[element].title"
            :icon="PANEL_META[element].icon"
            :color-class="PANEL_META[element].colorClass"
          >
            <component :is="PANEL_META[element].component" v-bind="bindingsFor(element)" />
          </DraggablePanel>
        </template>
      </draggable>
      <draggable
        v-model="columns[1]"
        :item-key="(key) => key"
        group="dashboard-panels"
        handle=".drag-handle"
        ghost-class="opacity-40"
        class="min-h-[80px] space-y-6 rounded-[14px] border-2 border-dashed border-transparent transition-colors"
        @change="persistLayout"
      >
        <template #item="{ element }">
          <DraggablePanel
            :panel-key="element"
            :title="PANEL_META[element].title"
            :icon="PANEL_META[element].icon"
            :color-class="PANEL_META[element].colorClass"
          >
            <component :is="PANEL_META[element].component" v-bind="bindingsFor(element)" />
          </DraggablePanel>
        </template>
      </draggable>
      <draggable
        v-model="columns[2]"
        :item-key="(key) => key"
        group="dashboard-panels"
        handle=".drag-handle"
        ghost-class="opacity-40"
        class="min-h-[80px] space-y-6 rounded-[14px] border-2 border-dashed border-transparent transition-colors"
        @change="persistLayout"
      >
        <template #item="{ element }">
          <DraggablePanel
            :panel-key="element"
            :title="PANEL_META[element].title"
            :icon="PANEL_META[element].icon"
            :color-class="PANEL_META[element].colorClass"
          >
            <component :is="PANEL_META[element].component" v-bind="bindingsFor(element)" />
          </DraggablePanel>
        </template>
      </draggable>
    </div>
    <GameSettingsPanel
      v-if="showSettings"
      :config="store.config"
      :game-length-turns="store.gameLengthTurns"
      @close="showSettings = false"
    />
  </div>
  <div v-else class="p-8 text-ink-soft">불러오는 중...</div>
</template>
```

(참고: 기존에 전체폭 배너였던 `<KpiCards :snapshot="store.snapshot" />` 줄은 제거되었다 — `kpi`가 이제 컬럼1 안의 재배치 가능한 패널이 되었기 때문이다. 기본 레이아웃(`columns[0] = ['kpi', 'monitoring']`)에서 KPI 카드가 컬럼1 맨 위에 오므로 화면상 위치는 기존과 거의 동일하게 유지된다.)

- [ ] **Step 4: 컨테이너 재시작 후 시각/기능 검증**

`podman ps`로 이 워크트리의 프론트엔드 컨테이너 이름을 확인한 뒤 `podman restart <컨테이너명>`. Playwright로 진행 중인 게임의 `/games/{id}` 접속 후 확인:
1. 6개 패널이 모두 렌더링되고, 각 패널 상단에 고유 색상의 그립 손잡이(점 6개 아이콘 + 대표 아이콘 + 이름)가 보이는지.
2. 그립 손잡이를 드래그해 패널 하나를 다른 컬럼으로 옮긴 뒤, 페이지를 새로고침해도 옮긴 위치가 유지되는지.
3. "레이아웃 초기화" 버튼 클릭 시 기본 배치로 돌아가는지.
4. 의사결정 패널의 입력창을 클릭했을 때 드래그가 시작되지 않고 정상적으로 값을 입력할 수 있는지 (그립 손잡이 밖에서는 드래그가 시작되면 안 됨).
5. 브라우저 콘솔에 에러가 없는지.

- [ ] **Step 5: 커밋**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/DraggablePanel.vue frontend/src/views/DashboardView.vue
git commit -m "$(cat <<'EOF'
feat(dashboard-layout): add draggable panel reordering to dashboard

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(Task 1과 마찬가지로 `npm install`은 반드시 호스트에서 실행하고, `package-lock.json` 갱신분이 diff에 포함됐는지 커밋 전에 확인한다.)

---

### Task 4: 전체 흐름 최종 검증

**Files:** 없음 (검증 전용, 발견된 이슈가 있으면 해당 파일만 소폭 수정)

- [ ] **Step 1: 드래그 재배치 전체 시나리오**

Playwright로 다음을 순서대로 확인:
1. 진행 중인 게임의 `/games/{id}`에서 6개 패널 중 2개 이상을 서로 다른 컬럼으로 옮긴다 (예: `monitoring`을 컬럼3으로, `decision`을 컬럼1로).
2. 새로고침 후 옮긴 배치가 정확히 유지되는지 확인 (컬럼별 순서까지 정확히).
3. 다른 게임(`/games/{다른 id}`)으로 이동해도 같은 배치가 유지되는지 확인 (브라우저 전역 저장이므로).
4. "레이아웃 초기화" 클릭 → 기본 배치(`[["kpi","monitoring"], ["charts"], ["financials","decision","turncontrol"]]`)로 정확히 복귀하는지, 새로고침해도 초기화된 상태가 유지되는지(= `localStorage`에서 실제로 지워졌는지) 확인.

- [ ] **Step 2: 기존 기능 회귀 확인**

재배치 기능을 추가하기 전과 동일하게 다음이 정상 동작하는지 확인:
1. 의사결정 패널에서 값을 바꾸고 "턴 실행" 클릭 → 턴이 정상적으로 진행되는지 (턴 카운터 증가, KPI/차트/재무제표 갱신).
2. 턴 컨트롤의 "자동 진행"으로 여러 턴을 연속 진행 → 중간에 에러 없이 끝까지 진행되는지.
3. "설정" 버튼 → 모달이 정상적으로 열리고 닫히는지 (재배치 기능과 무관하게 그대로 동작해야 함).
4. "게임 종료 & 새 시뮬레이션" 버튼 → 정상 동작하는지.

- [ ] **Step 3: 반응형/모바일 확인**

Playwright 브라우저 뷰포트를 모바일 크기(예: 390x844)로 줄여서 `/games/{id}` 접속 → 3컬럼이 세로로 컬럼1→2→3 순서로 쌓이는지, 좁은 화면에서도 그립 손잡이를 터치/드래그해 순서를 바꿀 수 있는지 확인.

- [ ] **Step 4: 콘솔 에러 확인**

Step 1~3 전체 과정에서 브라우저 콘솔에 에러나 경고가 없었는지 최종 확인.

- [ ] **Step 5: 문제 발견 시 수정**

이슈가 있으면 해당 컴포넌트 파일만 최소한으로 수정하고 재검증한다. 새 기능이나 리팩터링을 추가하지 않는다(이 태스크는 검증·버그수정 전용).

- [ ] **Step 6: 커밋 (수정사항이 있는 경우에만)**

```bash
git add <수정된 파일>
git commit -m "$(cat <<'EOF'
fix(dashboard-layout): polish issues found in end-to-end pass

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

수정사항이 없으면 커밋하지 않는다.
