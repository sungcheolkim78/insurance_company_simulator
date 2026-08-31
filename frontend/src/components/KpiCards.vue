<script setup>
import { PhBank, PhChartLineDown, PhChartLineUp, PhCoins } from '@phosphor-icons/vue'
import MetricLabel from './MetricLabel.vue'

defineProps({ snapshot: Object })

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
</script>

<template>
  <div class="grid grid-cols-1 gap-4 @2xl:grid-cols-3">
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-coral px-4 py-2.5 font-display text-white">
        <PhCoins :size="18" weight="fill" />
        <MetricLabel metric="equity" label="자본총계" />
      </div>
      <div class="p-4">
        <div class="tabular-nums text-xl font-bold">{{ formatWon(snapshot.equity) }}</div>
      </div>
    </div>
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-teal px-4 py-2.5 font-display text-white">
        <component :is="snapshot.net_income >= 0 ? PhChartLineUp : PhChartLineDown" :size="18" weight="fill" />
        <MetricLabel metric="net_income" label="이번 턴 순이익" />
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
        <MetricLabel metric="total_reserve" label="총 준비금" />
      </div>
      <div class="p-4">
        <div class="tabular-nums text-xl font-bold">{{ formatWon(snapshot.total_reserve) }}</div>
      </div>
    </div>
  </div>
</template>
