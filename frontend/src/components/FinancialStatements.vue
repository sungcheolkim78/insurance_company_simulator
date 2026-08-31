<script setup>
import { computed } from 'vue'
import { PhReceipt, PhScales } from '@phosphor-icons/vue'
import MetricLabel from './MetricLabel.vue'

const props = defineProps({ snapshot: { type: Object, required: true } })

function formatWon(value) {
  const rounded = Math.round(value)
  const sign = rounded < 0 ? '-' : ''
  return `${sign}${new Intl.NumberFormat('ko-KR').format(Math.abs(rounded))}원`
}

const revenueTotal = computed(() => props.snapshot.premium_income + props.snapshot.investment_income)
const expenseTotal = computed(
  () =>
    props.snapshot.death_claims +
    props.snapshot.surrender_payouts +
    props.snapshot.maturity_payouts +
    props.snapshot.commission_expense +
    props.snapshot.marketing_expense +
    props.snapshot.opex,
)
const assetsTotal = computed(() => props.snapshot.deposit_balance + props.snapshot.bond_balance + props.snapshot.stock_balance)
</script>

<template>
  <div class="space-y-4">
    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-coral px-4 py-2.5 font-display text-white">
        <PhReceipt :size="18" weight="fill" />
        <span>손익계산서 (이번 턴)</span>
      </div>
      <div class="p-4">
        <table class="w-full text-sm">
          <tbody>
            <tr class="text-ink-soft"><td colspan="2" class="pt-1 font-medium">영업수익</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="premium_income" label="보험료수입" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.premium_income) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="investment_income" label="투자수익" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.investment_income) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3"><MetricLabel metric="revenue_total" label="수익 합계" /></td><td class="tabular-nums text-right">{{ formatWon(revenueTotal) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">비용</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="death_claims" label="사망보험금" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.death_claims) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="surrender_payouts" label="해약환급금" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.surrender_payouts) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="maturity_payouts" label="만기보험금" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.maturity_payouts) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="commission_expense" label="신계약수수료" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.commission_expense) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="marketing_expense" label="마케팅비" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.marketing_expense) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="opex" label="일반관리비" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.opex) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3"><MetricLabel metric="expense_total" label="비용 합계" /></td><td class="tabular-nums text-right">{{ formatWon(expenseTotal) }}</td></tr>

            <tr><td class="pt-3"><MetricLabel metric="reserve_change" label="책임준비금전입액" /></td><td class="tabular-nums pt-3 text-right">{{ formatWon(snapshot.reserve_change) }}</td></tr>
            <tr><td class="pt-1"><MetricLabel metric="csm_change" label="CSM 순증감" /></td><td class="tabular-nums pt-1 text-right">{{ formatWon(snapshot.csm_change) }}</td></tr>
            <tr><td><MetricLabel metric="onerous_loss" label="손실부담계약손실" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.onerous_loss) }}</td></tr>
            <tr class="border-t-[3px] border-ink text-base font-bold">
              <td class="pt-2"><MetricLabel metric="net_income" label="당기순이익" /></td>
              <td class="tabular-nums pt-2 text-right" :class="snapshot.net_income >= 0 ? 'text-teal-deep' : 'text-coral-deep'">
                {{ formatWon(snapshot.net_income) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center gap-2 bg-plum px-4 py-2.5 font-display text-white">
        <PhScales :size="18" weight="fill" />
        <span>재무상태표 (기말)</span>
      </div>
      <div class="p-4">
        <table class="w-full text-sm">
          <tbody>
            <tr class="text-ink-soft"><td colspan="2" class="pt-1 font-medium">자산</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="deposit" label="예금" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.deposit_balance) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="bond" label="채권" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.bond_balance) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="stock" label="주식" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.stock_balance) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3"><MetricLabel metric="assets_total" label="자산총계" /></td><td class="tabular-nums text-right">{{ formatWon(assetsTotal) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">부채</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="total_reserve" label="책임준비금" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.total_reserve) }}</td></tr>
            <tr><td class="pl-3"><MetricLabel metric="total_csm" label="계약서비스마진 (CSM)" /></td><td class="tabular-nums text-right">{{ formatWon(snapshot.total_csm) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">자본</td></tr>
            <tr class="border-t-[3px] border-ink text-base font-bold">
              <td class="pl-3 pt-2"><MetricLabel metric="equity" label="자본총계 (Equity)" /></td>
              <td class="tabular-nums pt-2 text-right">{{ formatWon(snapshot.equity) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
