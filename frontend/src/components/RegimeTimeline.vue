<script setup>
import { computed } from 'vue'

const props = defineProps({ history: { type: Array, required: true } })

const REGIME_LABELS = { normal: '평온', boom: '호황', crisis: '위기' }
const REGIME_COLORS = { normal: '#94a3b8', boom: '#22c55e', crisis: '#ef4444' }

const segments = computed(() => {
  const rows = props.history
  if (rows.length === 0) return []
  const result = []
  let current = { regime: rows[0].stock_regime, startTurn: rows[0].turn, endTurn: rows[0].turn, count: 1 }
  for (let i = 1; i < rows.length; i++) {
    if (rows[i].stock_regime === current.regime) {
      current.endTurn = rows[i].turn
      current.count += 1
    } else {
      result.push(current)
      current = { regime: rows[i].stock_regime, startTurn: rows[i].turn, endTurn: rows[i].turn, count: 1 }
    }
  }
  result.push(current)
  return result
})

const transitions = computed(() => {
  const rows = props.history
  const result = []
  for (let i = 1; i < rows.length; i++) {
    if (rows[i].stock_regime !== rows[i - 1].stock_regime) {
      result.push({ turn: rows[i].turn, from: rows[i - 1].stock_regime, to: rows[i].stock_regime })
    }
  }
  return result
})

function widthPercent(segment) {
  const total = props.history.length || 1
  return `${(segment.count / total) * 100}%`
}
</script>

<template>
  <div class="rounded border border-slate-200 p-4">
    <h2 class="mb-3 font-semibold text-slate-800">주가 국면(페이즈) 변화</h2>
    <div class="flex h-6 w-full overflow-hidden rounded">
      <div
        v-for="(segment, index) in segments"
        :key="index"
        :style="{ width: widthPercent(segment), backgroundColor: REGIME_COLORS[segment.regime] }"
        :title="`턴 ${segment.startTurn}~${segment.endTurn}: ${REGIME_LABELS[segment.regime] ?? segment.regime}`"
      />
    </div>
    <div class="mt-2 flex gap-4 text-xs text-slate-500">
      <span v-for="(label, code) in REGIME_LABELS" :key="code" class="flex items-center gap-1">
        <span class="inline-block h-2 w-2 rounded-full" :style="{ backgroundColor: REGIME_COLORS[code] }" />
        {{ label }}
      </span>
    </div>
    <div v-if="transitions.length > 0" class="mt-3 space-y-1 text-sm">
      <div v-for="(t, index) in transitions" :key="index" class="text-slate-600">
        턴 {{ t.turn }}: {{ REGIME_LABELS[t.from] ?? t.from }} → {{ REGIME_LABELS[t.to] ?? t.to }}
      </div>
    </div>
    <div v-else class="mt-3 text-sm text-slate-500">게임 기간 동안 국면 변화가 없었습니다.</div>
  </div>
</template>
