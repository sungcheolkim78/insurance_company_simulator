# 대시보드 드래그 재배치 레이아웃 디자인 스펙

## 배경 및 목표

현재 턴 화면(`DashboardView.vue`)은 KPI 카드(전체폭 배너) + 3컬럼 그리드(모니터링 패널 / 히스토리 차트 / 재무제표+의사결정+턴컨트롤)로 고정되어 있다. 이 스펙은 사용자가 6개의 패널(정보/기능 블록)을 **드래그로 자유롭게 재배치**하고, 그 배치를 브라우저에 기억시키는 기능을 정의한다.

**스코프**: 순서/위치 재배치만 지원한다. 패널 크기 조절(리사이즈), 게임별 서버 저장, 키보드 전용 재배치는 이번 스코프에서 제외한다 (아래 "제외 범위" 참고). 보드게임 비주얼 아이덴티티(`2026-08-30-boardgame-identity-design.md`)에서 확립된 토큰·타일 패턴을 그대로 따른다 — 새 색상 토큰을 추가하지 않는다.

## 1. 데이터 모델

### 1.1 패널 레지스트리

재배치 가능한 6개 "패널 단위"를 키로 정의한다. 각 패널은 기존 Vue 컴포넌트 하나에 대응한다 (컴포넌트 내부를 쪼개지 않는다).

| 패널 키 | 컴포넌트 | 그립 손잡이 색상 | 대표 아이콘 |
|---|---|---|---|
| `kpi` | `KpiCards.vue` | `bg-coral` | `PhCoins` |
| `monitoring` | `MonitoringPanel.vue` | `bg-teal` | `PhChartBar` |
| `charts` | `HistoryCharts.vue` | `bg-mustard` | `PhChartLineUp` |
| `financials` | `FinancialStatements.vue` | `bg-plum` | `PhScales` |
| `decision` | `DecisionPanel.vue` | `bg-coral-deep` | `PhDiceFive` |
| `turncontrol` | `TurnControl.vue` | `bg-teal-deep` | `PhFastForward` |

(대표 아이콘은 플랜 작성 시 `@phosphor-icons/vue@2.2.1`에 실제로 존재하는지 검증한다. 없으면 가장 가까운 실제 아이콘명으로 대체한다.)

`TurnPathTracker`와 상단 헤더(설정/게임종료/레이아웃 초기화 버튼)는 재배치 대상이 아니며 항상 최상단 고정 위치에 남는다.

### 1.2 컬럼 상태

기존 3컬럼 구조를 그대로 데이터 모델화한다: 각 컬럼은 패널 키의 순서 있는 배열이다.

```js
// DashboardView.vue의 반응형 상태
const columns = ref([
  ['kpi', 'monitoring'],
  ['charts'],
  ['financials', 'decision', 'turncontrol'],
])
```

이 배열이 곧 "기본 레이아웃"이며, 현재 화면과 시각적으로 동일하게 보이도록 구성되어 있다 (KPI 카드는 원래 전체폭 배너였으나, 컴포넌트 단위 재배치 대상이 되면서 컬럼1 맨 위로 편입된다).

### 1.3 localStorage 저장

- **키**: `dashboard-layout-v1`
- **값**: `{ "columns": [["kpi","monitoring"], ["charts"], ["financials","decision","turncontrol"]] }`
- **범위**: 브라우저 전역 (게임 ID와 무관). 게임 데이터가 아니라 사용자의 화면 취향이므로, 게임을 종료하고 새 게임을 시작해도 레이아웃은 유지된다.
- **버전 접미사(`-v1`)**: 향후 저장 형식이 바뀌면 키 이름을 올려 예전 값과 충돌하지 않게 한다.

### 1.4 검증 및 폴백

레이아웃을 불러올 때 (`main.js` 로드 시점이 아니라 `DashboardView.vue`가 마운트될 때) 다음을 검증하는 순수 함수 `loadLayout()` / `saveLayout(columns)`를 별도 파일(`frontend/src/utils/dashboardLayout.js`)에 둔다:

1. `localStorage.getItem('dashboard-layout-v1')`이 없거나 JSON 파싱에 실패하면 → 기본 레이아웃 사용.
2. 저장된 값에 알 수 없는 패널 키(레지스트리에 없는 키)가 있으면 → 그 키를 무시하고 제거.
3. 레지스트리에는 있지만 저장된 값 어디에도 없는 패널 키(예: 나중에 패널이 추가된 경우)가 있으면 → 컬럼1의 맨 끝에 자동으로 추가.
4. 저장된 값에 같은 키가 중복으로 존재하면 → 처음 등장한 위치만 남기고 중복 제거.
5. 컬럼 개수가 3이 아니면(형식이 깨졌으면) → 기본 레이아웃으로 완전히 폴백.

이 함수는 순수 로직이라 단위 테스트로 검증한다 (프론트엔드에 테스트 스크립트가 없으므로, 이 유틸만을 위한 최소 테스트 설정을 추가할지 여부는 구현 계획 단계에서 결정한다).

## 2. 컴포넌트 구조

### 2.1 신규 컴포넌트: `DraggablePanel.vue`

6개 패널 각각을 감싸는 얇은 래퍼. Props: `panelKey`, `title`, `icon`(컴포넌트), `colorClass`(예: `'bg-coral'`). 슬롯으로 실제 패널 컴포넌트를 받는다.

```html
<template>
  <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
    <div
      class="drag-handle flex cursor-grab items-center gap-2 px-4 py-2 font-display text-white active:cursor-grabbing"
      :class="colorClass"
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

내부 패널 컴포넌트(`KpiCards` 등)는 자기 자신의 보드타일 테두리/그림자를 이미 가지고 있으므로, `DraggablePanel`이 이를 다시 감싸면 이중 테두리가 생긴다. 따라서 구현 시 각 패널 컴포넌트의 최상위 요소가 가진 `rounded-[20px] border-[3px] border-ink bg-tile shadow-[...]` 클래스를 제거하고, 그 시각적 책임을 `DraggablePanel`로 옮긴다 (6개 컴포넌트 모두 소폭 수정 필요 — 그러나 각 컴포넌트가 내부에 여러 서브 타일을 가진 경우, 예: 모니터링 패널의 6개 그룹, 재무제표의 2개 표는 그 서브 타일들의 테두리는 그대로 유지한다. 최상위 감싸는 테두리 1겹만 제거).

### 2.2 `DashboardView.vue` 변경

- `columns` ref 추가, `onMounted`에서 `loadLayout()`으로 초기화.
- 패널 키 → `{ component, title, icon, colorClass }` 매핑 테이블 하나 정의.
- 기존 3개의 `<div class="space-y-6">...</div>` 블록을 각각 다음으로 교체:

```html
<draggable
  v-model="columns[i]"
  group="dashboard-panels"
  item-key="itself"
  handle=".drag-handle"
  class="min-h-[80px] space-y-6 rounded-[14px] border-2 border-dashed border-transparent transition-colors"
  ghost-class="opacity-40"
  @change="saveLayout(columns)"
>
  <template #item="{ element }">
    <DraggablePanel v-bind="panelMeta[element]">
      <component :is="panelMeta[element].component" v-bind="panelProps[element]" />
    </DraggablePanel>
  </template>
</draggable>
```

(각 패널이 필요로 하는 props—`snapshot`, `history`, `prev-snapshot` 등—는 `panelProps` 객체로 별도 정리해 전달한다. `@submit`, `@run-turns` 같은 이벤트도 패널별로 그대로 연결한다.)

- 헤더에 **"레이아웃 초기화"** 버튼 추가 (설정 버튼 왼쪽 또는 오른쪽): 클릭 시 `localStorage.removeItem('dashboard-layout-v1')` 후 `columns.value`를 기본값으로 되돌림.

### 2.3 신규 의존성

`vuedraggable`(Vue 3용, 예: `vuedraggable@^4.1.0` — SortableJS 래퍼)을 `frontend/package.json`에 추가한다. 정확한 API(`item-key`, `group`, `handle`, `ghost-class` prop 이름 등)는 구현 계획 작성 시 실제 설치된 버전의 문서로 재확인한다 — 이 스펙의 코드 스니펫은 방향성을 보여주는 것이며 API 이름이 실제와 다를 수 있음을 명시한다.

## 3. 인터랙션 및 시각 동작

- **드래그 시작**: 그립 손잡이(색상 배너) 위에서만 가능. 패널 본문(입력창, 버튼 등)을 클릭해도 드래그가 시작되지 않는다.
- **드래그 중**: 원래 위치는 반투명(`opacity-40`)해지고, 드롭 가능한 위치에 플레이스홀더가 표시된다 (vuedraggable/SortableJS 기본 동작).
- **컬럼 간 이동**: 세 컬럼 모두 같은 `group="dashboard-panels"`를 공유하므로, 패널을 다른 컬럼으로도 드래그할 수 있다.
- **빈 컬럼**: 컬럼의 모든 패널이 다른 곳으로 옮겨지면 `min-h-[80px]`의 점선 테두리 영역만 남아 "여기로 드롭 가능"함을 시각적으로 알린다.
- **저장 시점**: 드래그가 끝나 순서가 바뀔 때마다(`@change`) 즉시 `localStorage`에 저장한다 — 별도의 "저장" 버튼 없음.
- **반응형**: 좁은 화면(`lg` 미만)에서는 기존과 동일하게 3컬럼이 세로로(컬럼1→2→3 순서로) 쌓인다. 재배치 데이터 모델 자체는 화면 크기와 무관하게 3컬럼으로 유지된다.

## 4. 제외 범위 (이번 스펙에 포함하지 않음)

- **패널 리사이즈**: 패널 크기는 항상 컬럼 폭에 맞춰 고정. 크기 조절 핸들 없음.
- **서버(게임별) 저장**: 레이아웃은 브라우저 로컬 설정으로만 존재. 백엔드 스키마/API 변경 없음.
- **키보드 전용 재배치**: 방향키 등으로 순서를 바꾸는 접근성 기능은 이번 범위에서 제외. 필요 시 추후 별도 과제로 다룬다.
- **컴포넌트 내부 세분화**: 모니터링 패널의 6개 그룹, 히스토리 차트의 8개 그래프 등은 각각 독립적으로 재배치할 수 없다 — 항상 소속 컴포넌트 전체가 하나의 단위로 움직인다.

## 5. 테스트 관점

- `dashboardLayout.js`의 `loadLayout`/`saveLayout` 순수 함수: 정상 케이스, 손상된 JSON, 알 수 없는 키 포함, 키 누락, 컬럼 개수 불일치 등 §1.4의 5가지 폴백 규칙 각각을 검증.
- 수동/Playwright 시각 검증: 드래그로 패널을 다른 컬럼에 옮긴 뒤 새로고침해도 위치가 유지되는지, "레이아웃 초기화" 버튼이 정상 동작하는지, 모바일 뷰포트에서 터치 드래그가 동작하는지.
