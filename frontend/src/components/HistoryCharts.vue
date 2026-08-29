<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({ history: Array })

const labels = computed(() => props.history.map((row) => row.turn))

function buildChartData(label, field, color) {
  return computed(() => ({
    labels: labels.value,
    datasets: [{ label, data: props.history.map((row) => row[field]), borderColor: color, tension: 0.2 }],
  }))
}

const equityChartData = buildChartData('자본총계', 'equity', '#1e293b')
const netIncomeChartData = buildChartData('당기순이익', 'net_income', '#0284c7')
const inForceChartData = buildChartData('총 보유계약수', 'total_in_force', '#16a34a')
const csmChartData = buildChartData('총 CSM 잔액', 'total_csm', '#a855f7')

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="space-y-4">
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="equityChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="netIncomeChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="inForceChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="csmChartData" :options="chartOptions" />
    </div>
  </div>
</template>
