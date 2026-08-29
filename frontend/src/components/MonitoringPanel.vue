<script setup>
import { computed } from 'vue'

const props = defineProps({
  snapshot: { type: Object, required: true },
  prevSnapshot: { type: Object, default: null },
  decision: { type: Object, default: null },
})

const REGIME_LABELS = { normal: '평온 (Normal)', boom: '호황 (Boom)', crisis: '위기 (Crisis)' }

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
function formatPct(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}
function safeDiv(numerator, denominator) {
  if (!denominator) return null
  return numerator / denominator
}

const assetsTotal = computed(() => props.snapshot.deposit_balance + props.snapshot.bond_balance + props.snapshot.stock_balance)
const prevAssetsTotal = computed(() =>
  props.prevSnapshot ? props.prevSnapshot.deposit_balance + props.prevSnapshot.bond_balance + props.prevSnapshot.stock_balance : null,
)

const portfolioReturnMonthly = computed(() => safeDiv(props.snapshot.investment_income, prevAssetsTotal.value))

const assetWeights = computed(() => ({
  deposit: safeDiv(props.snapshot.deposit_balance, assetsTotal.value),
  bond: safeDiv(props.snapshot.bond_balance, assetsTotal.value),
  stock: safeDiv(props.snapshot.stock_balance, assetsTotal.value),
}))

const newPoliciesTotal = computed(() =>
  Object.values(props.snapshot.new_policies_by_product).reduce((a, b) => a + b, 0),
)

const newBusinessPremiumTotal = computed(() =>
  Object.values(props.snapshot.new_business_premium_by_channel).reduce((a, b) => a + b, 0),
)
const renewalPremium = computed(() => props.snapshot.premium_income - newBusinessPremiumTotal.value)

const channelEfficiency = computed(() => {
  if (!props.decision) return null
  return ['captive', 'ga'].reduce((acc, channel) => {
    const marketingSpend = props.decision.marketing_spend[channel] ?? 0
    const denom = (props.snapshot.commission_expense_by_channel[channel] ?? 0) + marketingSpend
    acc[channel] = safeDiv(props.snapshot.new_business_premium_by_channel[channel] ?? 0, denom)
    return acc
  }, {})
})

const lossRatio = computed(() => safeDiv(props.snapshot.death_claims, props.snapshot.premium_income_by_product.whole_life))
const lapseRatioMonthly = computed(() => safeDiv(props.snapshot.lapses_count, props.snapshot.total_in_force))
const lapseRatioAnnual = computed(() => (lapseRatioMonthly.value === null ? null : lapseRatioMonthly.value * 12))
const surrenderRatio = computed(() =>
  safeDiv(props.snapshot.surrender_payouts + props.snapshot.maturity_payouts, props.snapshot.premium_income),
)

const expenseRatio = computed(() =>
  safeDiv(
    props.snapshot.commission_expense + props.snapshot.marketing_expense + props.snapshot.opex,
    props.snapshot.premium_income,
  ),
)
const combinedRatio = computed(() =>
  safeDiv(
    props.snapshot.death_claims +
      props.snapshot.surrender_payouts +
      props.snapshot.maturity_payouts +
      props.snapshot.commission_expense +
      props.snapshot.marketing_expense +
      props.snapshot.opex,
    props.snapshot.premium_income,
  ),
)
const roeAnnual = computed(() => {
  if (!props.prevSnapshot || props.prevSnapshot.equity <= 0) return null
  return (props.snapshot.net_income / props.prevSnapshot.equity) * 12
})
const solvencyProxy = computed(() => safeDiv(props.snapshot.equity, props.snapshot.total_reserve))

function toneLowerIsBetter(value, threshold) {
  if (value === null) return 'text-slate-500'
  return value <= threshold ? 'text-emerald-600' : 'text-red-600'
}
function toneHigherIsBetter(value, threshold) {
  if (value === null) return 'text-slate-500'
  return value >= threshold ? 'text-emerald-600' : 'text-red-600'
}
</script>

<template>
  <div class="space-y-4">
    <div class="rounded border border-slate-200 p-4">
      <h2 class="mb-3 font-semibold text-slate-800">시장 &amp; 자산운용</h2>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">시장금리 (목표 3.0%)</div>
          <div class="font-bold">{{ formatPct(snapshot.interest_rate) }}</div>
        </div>
        <div>
          <div class="text-slate-500">주가 국면</div>
          <div class="font-bold">{{ REGIME_LABELS[snapshot.stock_regime] ?? snapshot.stock_regime }}</div>
        </div>
        <div>
          <div class="text-slate-500">주식 실현수익률(월)</div>
          <div class="font-bold">{{ formatPct(snapshot.stock_return_realized) }}</div>
        </div>
        <div>
          <div class="text-slate-500">포트폴리오 운용수익률(월)</div>
          <div class="font-bold">{{ formatPct(portfolioReturnMonthly) }}</div>
        </div>
      </div>
      <div class="mt-3 text-sm">
        <div class="text-slate-500">자산군별 비중 (예금 / 채권 / 주식)</div>
        <div class="font-bold">
          {{ formatPct(assetWeights.deposit, 1) }} / {{ formatPct(assetWeights.bond, 1) }} / {{ formatPct(assetWeights.stock, 1) }}
        </div>
      </div>
    </div>

    <div class="rounded border border-slate-200 p-4">
      <h2 class="mb-3 font-semibold text-slate-800">계약 포트폴리오 &amp; 영업성과</h2>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">총 보유계약수</div>
          <div class="font-bold">{{ Math.round(snapshot.total_in_force).toLocaleString('ko-KR') }}건</div>
        </div>
        <div>
          <div class="text-slate-500">이번 턴 신계약</div>
          <div class="font-bold">{{ newPoliciesTotal.toLocaleString('ko-KR') }}건</div>
        </div>
        <div>
          <div class="text-slate-500">신계약 (종신/저축)</div>
          <div class="font-bold">
            {{ snapshot.new_policies_by_product.whole_life }} / {{ snapshot.new_policies_by_product.savings }}
          </div>
        </div>
        <div>
          <div class="text-slate-500">신계약 (전속/GA)</div>
          <div class="font-bold">
            {{ snapshot.new_policies_by_channel.captive }} / {{ snapshot.new_policies_by_channel.ga }}
          </div>
        </div>
        <div>
          <div class="text-slate-500">초회 보험료</div>
          <div class="font-bold">{{ formatWon(newBusinessPremiumTotal) }}</div>
        </div>
        <div>
          <div class="text-slate-500">계속 보험료</div>
          <div class="font-bold">{{ formatWon(renewalPremium) }}</div>
        </div>
      </div>
      <div class="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">채널효율성 (전속)</div>
          <div class="font-bold">{{ channelEfficiency ? formatPct(channelEfficiency.captive, 0) : '—' }}</div>
        </div>
        <div>
          <div class="text-slate-500">채널효율성 (GA)</div>
          <div class="font-bold">{{ channelEfficiency ? formatPct(channelEfficiency.ga, 0) : '—' }}</div>
        </div>
      </div>
    </div>

    <div class="rounded border border-slate-200 p-4">
      <h2 class="mb-3 font-semibold text-slate-800">위험손해율 &amp; 계약유지</h2>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">위험손해율 (종신)</div>
          <div class="font-bold" :class="toneLowerIsBetter(lossRatio, 0.5)">{{ formatPct(lossRatio, 1) }}</div>
        </div>
        <div>
          <div class="text-slate-500">해지율 (월 / 연환산)</div>
          <div class="font-bold">{{ formatPct(lapseRatioMonthly, 2) }} / {{ formatPct(lapseRatioAnnual, 1) }}</div>
        </div>
        <div class="col-span-2">
          <div class="text-slate-500">해지·만기 유출액 비율</div>
          <div class="font-bold" :class="toneLowerIsBetter(surrenderRatio, 0.3)">{{ formatPct(surrenderRatio, 1) }}</div>
        </div>
      </div>
    </div>

    <div class="rounded border border-slate-200 p-4">
      <h2 class="mb-3 font-semibold text-slate-800">수익성 &amp; 사업비</h2>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">사업비율</div>
          <div class="font-bold" :class="toneLowerIsBetter(expenseRatio, 0.3)">{{ formatPct(expenseRatio, 1) }}</div>
        </div>
        <div>
          <div class="text-slate-500">합산비율</div>
          <div class="font-bold" :class="toneLowerIsBetter(combinedRatio, 1.0)">{{ formatPct(combinedRatio, 1) }}</div>
        </div>
        <div class="col-span-2">
          <div class="text-slate-500">ROE (연환산)</div>
          <div class="font-bold" :class="toneHigherIsBetter(roeAnnual, 0)">{{ formatPct(roeAnnual, 1) }}</div>
        </div>
      </div>
    </div>

    <div class="rounded border border-slate-200 p-4">
      <h2 class="mb-3 font-semibold text-slate-800">재무건전성</h2>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div class="text-slate-500">자본총계</div>
          <div class="font-bold">{{ formatWon(snapshot.equity) }}</div>
        </div>
        <div>
          <div class="text-slate-500">자본완충비율 (자본/준비금)</div>
          <div class="font-bold" :class="toneHigherIsBetter(solvencyProxy, 0.9)">
            {{ formatPct(solvencyProxy, 1) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
