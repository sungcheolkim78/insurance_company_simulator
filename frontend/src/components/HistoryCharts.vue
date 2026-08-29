<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({ history: Array })

const MONEY_UNIT = 10_000_000

const labels = computed(() => props.history.map((row) => row.turn))

function buildChartData(label, getValue, color, { isMoney = false } = {}) {
  const displayLabel = isMoney ? `${label} (천만원)` : label
  return computed(() => ({
    labels: labels.value,
    datasets: [
      {
        label: displayLabel,
        data: props.history.map((row) => (isMoney ? getValue(row) / MONEY_UNIT : getValue(row))),
        borderColor: color,
        tension: 0.2,
      },
    ],
  }))
}

function totalExpense(row) {
  return (
    row.death_claims +
    row.surrender_payouts +
    row.maturity_payouts +
    row.commission_expense +
    row.marketing_expense +
    row.opex
  )
}

const equityChartData = buildChartData('자본총계', (row) => row.equity, '#1e293b', { isMoney: true })
const premiumIncomeChartData = buildChartData('보험료수입', (row) => row.premium_income, '#0284c7', { isMoney: true })
const investmentIncomeChartData = buildChartData(
  '투자수익',
  (row) => row.investment_income,
  '#0ea5e9',
  { isMoney: true },
)
const expenseTotalChartData = buildChartData('비용합계', totalExpense, '#dc2626', { isMoney: true })
const totalReserveChartData = buildChartData('책임준비금', (row) => row.total_reserve, '#ea580c', { isMoney: true })
const inForceChartData = buildChartData('총 보유계약수', (row) => row.total_in_force, '#16a34a')
const csmChartData = buildChartData('총 CSM 잔액', (row) => row.total_csm, '#a855f7', { isMoney: true })

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="space-y-4">
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="equityChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="premiumIncomeChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="investmentIncomeChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="expenseTotalChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="totalReserveChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="inForceChartData" :options="chartOptions" />
    </div>
    <div class="h-48 rounded border border-slate-200 p-4">
      <Line :data="csmChartData" :options="chartOptions" />
    </div>
  </div>
</template>
