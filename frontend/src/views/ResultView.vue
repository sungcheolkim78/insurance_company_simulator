<script setup>
import { onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'
import HistoryCharts from '../components/HistoryCharts.vue'
import RegimeTimeline from '../components/RegimeTimeline.vue'

const props = defineProps({ id: String })
const store = useGameStore()

onMounted(() => {
  if (store.gameId !== Number(props.id)) store.load(Number(props.id))
})
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-8">
    <div class="rounded-lg border border-slate-200 p-8 text-center shadow-sm">
      <h1 class="mb-4 text-2xl font-bold" :class="store.status === 'bankrupt' ? 'text-red-600' : 'text-emerald-600'">
        {{ store.status === 'bankrupt' ? '파산' : '경영 종료' }}
      </h1>
      <p class="mb-2 text-slate-600">최종 턴: {{ store.currentTurn }} / {{ store.gameLengthTurns }}</p>
      <p class="text-3xl font-bold">{{ new Intl.NumberFormat('ko-KR').format(Math.round(store.snapshot.equity)) }}원</p>
      <router-link to="/" class="mt-6 inline-block text-sm text-slate-500 underline">새 게임 시작</router-link>
    </div>

    <RegimeTimeline :history="store.history" />

    <div>
      <h2 class="mb-3 text-lg font-semibold text-slate-800">지표 변화 추이</h2>
      <HistoryCharts :history="store.history" />
    </div>
  </div>
  <div v-else class="p-8 text-slate-500">불러오는 중...</div>
</template>
