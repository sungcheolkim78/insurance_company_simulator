<script setup>
import { onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'
import KpiCards from '../components/KpiCards.vue'
import HistoryCharts from '../components/HistoryCharts.vue'

const props = defineProps({ id: String })
const store = useGameStore()

onMounted(() => store.load(Number(props.id)))
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-4xl space-y-6 p-8">
    <h1 class="text-2xl font-bold text-slate-800">턴 {{ store.currentTurn }} / 120</h1>
    <KpiCards :snapshot="store.snapshot" />
    <HistoryCharts :history="store.history" />
  </div>
  <div v-else class="p-8 text-slate-500">불러오는 중...</div>
</template>
