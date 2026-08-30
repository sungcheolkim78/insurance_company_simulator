<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)
ChartJS.defaults.font.family = "'Gowun Dodum', 'Pretendard', sans-serif"
ChartJS.defaults.color = '#2B2A4C'

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

const equityChartData = buildChartData('자본총계', (row) => row.equity, '#2B2A4C', { isMoney: true })
const premiumIncomeChartData = buildChartData('보험료수입', (row) => row.premium_income, '#2A9D8F', { isMoney: true })
const investmentIncomeChartData = buildChartData(
  '투자수익',
  (row) => row.investment_income,
  '#1F7A6E',
  { isMoney: true },
)
const expenseTotalChartData = buildChartData('비용합계', totalExpense, '#E8604C', { isMoney: true })
const totalReserveChartData = buildChartData('책임준비금', (row) => row.total_reserve, '#D48F1F', { isMoney: true })
const inForceChartData = buildChartData('총 보유계약수', (row) => row.total_in_force, '#2A9D8F')
const csmChartData = buildChartData('총 CSM 잔액', (row) => row.total_csm, '#7B5EA7', { isMoney: true })

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="space-y-4">
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="equityChartData" :options="chartOptions" />
    </div>
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="premiumIncomeChartData" :options="chartOptions" />
    </div>
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="investmentIncomeChartData" :options="chartOptions" />
    </div>
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="expenseTotalChartData" :options="chartOptions" />
    </div>
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="totalReserveChartData" :options="chartOptions" />
    </div>
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="inForceChartData" :options="chartOptions" />
    </div>
    <div class="h-48 overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <Line :data="csmChartData" :options="chartOptions" />
    </div>
  </div>
</template>
