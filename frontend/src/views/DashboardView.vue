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
