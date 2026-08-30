<script setup>
import { onMounted } from 'vue'
import { PhConfetti, PhSkull } from '@phosphor-icons/vue'
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
    <div
      class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile p-8 text-center shadow-[6px_6px_0_rgba(43,42,76,0.28)]"
    >
      <div class="mb-3 flex items-center justify-center gap-2 font-display text-3xl" :class="store.status === 'bankrupt' ? 'text-coral-deep' : 'text-teal-deep'">
        <component :is="store.status === 'bankrupt' ? PhSkull : PhConfetti" :size="32" weight="fill" />
        {{ store.status === 'bankrupt' ? '파산' : '경영 종료' }}
      </div>
      <p class="mb-2 tabular-nums text-ink-soft">최종 턴: {{ store.currentTurn }} / {{ store.gameLengthTurns }}</p>
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
