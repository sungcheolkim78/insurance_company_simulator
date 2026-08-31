<script setup>
import { onMounted, computed } from 'vue'
import {
  PhConfetti,
  PhSkull,
  PhChartLineUp,
  PhHouse,
  PhPlayCircle,
  PhCaretRight,
} from '@phosphor-icons/vue'
import { useGameStore } from '../stores/gameStore'
import HistoryCharts from '../components/HistoryCharts.vue'
import RegimeTimeline from '../components/RegimeTimeline.vue'

const props = defineProps({ id: String })
const store = useGameStore()

onMounted(() => {
  if (store.gameId !== Number(props.id)) {
    store.load(Number(props.id))
  }
})

const statusConfig = computed(() => {
  if (store.status === 'bankrupt') {
    return {
      title: '경영 실패 (파산)',
      icon: PhSkull,
      colorClass: 'text-coral-deep',
      bgBadge: 'bg-coral/15 text-coral-deep border-coral/30',
    }
  }
  if (store.status === 'completed') {
    return {
      title: '경영 종료 (목표 달성)',
      icon: PhConfetti,
      colorClass: 'text-teal-deep',
      bgBadge: 'bg-teal/15 text-teal-deep border-teal/30',
    }
  }
  return {
    title: '경영 진행 중 (중간 요약)',
    icon: PhChartLineUp,
    colorClass: 'text-plum-deep',
    bgBadge: 'bg-plum/15 text-plum-deep border-plum/30',
  }
})
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-6 sm:p-8">
    <!-- Top Result / Summary Card -->
    <div
      class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile p-6 sm:p-8 text-center shadow-[6px_6px_0_rgba(43,42,76,0.28)]"
    >
      <div class="mb-3 flex items-center justify-center gap-2 font-display text-2xl sm:text-3xl" :class="statusConfig.colorClass">
        <component :is="statusConfig.icon" :size="34" weight="fill" />
        {{ statusConfig.title }}
      </div>

      <div class="mb-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-sm text-ink-soft">
        <span>게임 #{{ store.gameId }}</span>
        <span>•</span>
        <span class="tabular-nums">진행 턴: {{ store.currentTurn }} / {{ store.gameLengthTurns }}</span>
      </div>

      <div class="my-3">
        <span class="text-xs font-semibold text-ink-soft uppercase tracking-wider block mb-1">
          {{ store.status === 'running' ? '현재 순자산 (Equity)' : '최종 순자산 (Equity)' }}
        </span>
        <p class="tabular-nums font-display text-3xl sm:text-4xl text-ink">
          {{ new Intl.NumberFormat('ko-KR').format(Math.round(store.snapshot.equity)) }}원
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="mt-6 flex flex-wrap items-center justify-center gap-3">
        <router-link
          to="/"
          class="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-board-cream px-5 py-2 text-sm font-bold text-ink shadow-[3px_3px_0_rgba(43,42,76,0.28)] transition hover:bg-board-cream-deep active:translate-y-0.5 cursor-pointer"
        >
          <PhHouse :size="16" weight="bold" />
          시작 화면으로
        </router-link>

        <router-link
          v-if="store.status === 'running'"
          :to="`/games/${store.gameId}`"
          class="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-teal-deep px-5 py-2 text-sm font-bold text-white shadow-[3px_3px_0_rgba(43,42,76,0.28)] transition hover:brightness-110 active:translate-y-0.5 cursor-pointer"
        >
          <span>이어서 플레이하기</span>
          <PhCaretRight :size="14" weight="bold" />
        </router-link>

        <router-link
          to="/"
          class="inline-flex items-center gap-1.5 rounded-full bg-coral px-5 py-2 text-sm font-bold text-white shadow-[0_3px_0_var(--color-coral-deep)] transition hover:brightness-105 active:translate-y-0.5 active:shadow-[0_1px_0_var(--color-coral-deep)] cursor-pointer"
        >
          <PhPlayCircle :size="16" weight="fill" />
          새 게임 만들기
        </router-link>
      </div>
    </div>

    <!-- Stock Market Regime Timeline -->
    <RegimeTimeline :history="store.history" />

    <!-- Historical Metric Charts -->
    <div>
      <h2 class="mb-3 font-display text-xl text-ink">경영 지표 변화 추이</h2>
      <HistoryCharts :history="store.history" />
    </div>
  </div>
  <div v-else class="p-12 text-center text-ink-soft">
    <p>경영 성과 데이터를 불러오는 중입니다...</p>
  </div>
</template>
