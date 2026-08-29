<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/gameStore'
import { deleteGame } from '../api/client'
import KpiCards from '../components/KpiCards.vue'
import HistoryCharts from '../components/HistoryCharts.vue'
import MonitoringPanel from '../components/MonitoringPanel.vue'
import FinancialStatements from '../components/FinancialStatements.vue'
import DecisionPanel from '../components/DecisionPanel.vue'
import TurnControl from '../components/TurnControl.vue'
import GameSettingsPanel from '../components/GameSettingsPanel.vue'

const props = defineProps({ id: String })
const store = useGameStore()
const router = useRouter()
const lastDecision = ref(null)
const isBusy = ref(false)
const errorMessage = ref('')
const showSettings = ref(false)

const prevSnapshot = computed(() =>
  store.history.length >= 2 ? store.history[store.history.length - 2] : null,
)

onMounted(() => store.load(Number(props.id)))

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
    <p v-if="errorMessage" class="text-sm text-red-600">{{ errorMessage }}</p>
    <KpiCards :snapshot="store.snapshot" />
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="space-y-6">
        <MonitoringPanel :snapshot="store.snapshot" :prev-snapshot="prevSnapshot" :decision="lastDecision" />
      </div>
      <div class="space-y-6">
        <HistoryCharts :history="store.history" />
      </div>
      <div class="space-y-6">
        <FinancialStatements :snapshot="store.snapshot" />
        <DecisionPanel @submit="handleDecisionSubmit" />
        <TurnControl :disabled="isBusy || store.status !== 'running'" @run-turns="runTurns" />
      </div>
    </div>
    <GameSettingsPanel
      v-if="showSettings"
      :config="store.config"
      :game-length-turns="store.gameLengthTurns"
      @close="showSettings = false"
    />
  </div>
  <div v-else class="p-8 text-slate-500">불러오는 중...</div>
</template>
