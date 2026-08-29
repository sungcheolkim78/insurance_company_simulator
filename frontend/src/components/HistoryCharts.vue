<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({ history: Array })

const chartData = computed(() => ({
  labels: props.history.map((row) => row.turn),
  datasets: [
    { label: '자본총계', data: props.history.map((row) => row.equity), borderColor: '#1e293b', tension: 0.2 },
  ],
}))

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="h-64 rounded border border-slate-200 p-4">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
