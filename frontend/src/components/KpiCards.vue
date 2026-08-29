<script setup>
defineProps({ snapshot: Object })

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
</script>

<template>
  <div class="grid grid-cols-3 gap-4">
    <div class="rounded border border-slate-200 p-4">
      <div class="text-sm text-slate-500">자본총계</div>
      <div class="text-xl font-bold">{{ formatWon(snapshot.equity) }}</div>
    </div>
    <div class="rounded border border-slate-200 p-4">
      <div class="text-sm text-slate-500">이번 턴 순이익</div>
      <div class="text-xl font-bold" :class="snapshot.net_income >= 0 ? 'text-emerald-600' : 'text-red-600'">
        {{ formatWon(snapshot.net_income) }}
      </div>
    </div>
    <div class="rounded border border-slate-200 p-4">
      <div class="text-sm text-slate-500">총 준비금</div>
      <div class="text-xl font-bold">{{ formatWon(snapshot.total_reserve) }}</div>
    </div>
  </div>
</template>
