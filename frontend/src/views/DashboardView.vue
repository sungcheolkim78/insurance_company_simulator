<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/gameStore'
import KpiCards from '../components/KpiCards.vue'
import HistoryCharts from '../components/HistoryCharts.vue'
import DecisionPanel from '../components/DecisionPanel.vue'
import TurnControl from '../components/TurnControl.vue'

const props = defineProps({ id: String })
const store = useGameStore()
const router = useRouter()
const lastDecision = ref(null)
const isBusy = ref(false)
const errorMessage = ref('')

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
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-8">
    <h1 class="text-2xl font-bold text-slate-800">턴 {{ store.currentTurn }} / 120</h1>
    <p v-if="errorMessage" class="text-sm text-red-600">{{ errorMessage }}</p>
    <KpiCards :snapshot="store.snapshot" />
    <HistoryCharts :history="store.history" />
    <DecisionPanel @submit="handleDecisionSubmit" />
    <TurnControl :disabled="isBusy || store.status !== 'running'" @run-turns="runTurns" />
  </div>
  <div v-else class="p-8 text-slate-500">불러오는 중...</div>
</template>
