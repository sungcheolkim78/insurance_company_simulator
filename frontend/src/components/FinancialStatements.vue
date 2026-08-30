<script setup>
import { computed } from 'vue'
import { PhReceipt, PhScales } from '@phosphor-icons/vue'

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
            <tr><td class="pl-3">보험료수입</td><td class="tabular-nums text-right">{{ formatWon(snapshot.premium_income) }}</td></tr>
            <tr><td class="pl-3">투자수익</td><td class="tabular-nums text-right">{{ formatWon(snapshot.investment_income) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3">수익 합계</td><td class="tabular-nums text-right">{{ formatWon(revenueTotal) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">비용</td></tr>
            <tr><td class="pl-3">사망보험금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.death_claims) }}</td></tr>
            <tr><td class="pl-3">해약환급금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.surrender_payouts) }}</td></tr>
            <tr><td class="pl-3">만기보험금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.maturity_payouts) }}</td></tr>
            <tr><td class="pl-3">신계약수수료</td><td class="tabular-nums text-right">{{ formatWon(snapshot.commission_expense) }}</td></tr>
            <tr><td class="pl-3">마케팅비</td><td class="tabular-nums text-right">{{ formatWon(snapshot.marketing_expense) }}</td></tr>
            <tr><td class="pl-3">일반관리비</td><td class="tabular-nums text-right">{{ formatWon(snapshot.opex) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3">비용 합계</td><td class="tabular-nums text-right">{{ formatWon(expenseTotal) }}</td></tr>

            <tr><td class="pt-3">책임준비금전입액</td><td class="tabular-nums pt-3 text-right">{{ formatWon(snapshot.reserve_change) }}</td></tr>
            <tr><td class="pt-1">CSM 순증감</td><td class="tabular-nums pt-1 text-right">{{ formatWon(snapshot.csm_change) }}</td></tr>
            <tr><td>손실부담계약손실</td><td class="tabular-nums text-right">{{ formatWon(snapshot.onerous_loss) }}</td></tr>
            <tr class="border-t-[3px] border-ink text-base font-bold">
              <td class="pt-2">당기순이익</td>
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
            <tr><td class="pl-3">예금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.deposit_balance) }}</td></tr>
            <tr><td class="pl-3">채권</td><td class="tabular-nums text-right">{{ formatWon(snapshot.bond_balance) }}</td></tr>
            <tr><td class="pl-3">주식</td><td class="tabular-nums text-right">{{ formatWon(snapshot.stock_balance) }}</td></tr>
            <tr class="border-t border-board-cream-deep font-medium"><td class="pl-3">자산총계</td><td class="tabular-nums text-right">{{ formatWon(assetsTotal) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">부채</td></tr>
            <tr><td class="pl-3">책임준비금</td><td class="tabular-nums text-right">{{ formatWon(snapshot.total_reserve) }}</td></tr>
            <tr><td class="pl-3">계약서비스마진 (CSM)</td><td class="tabular-nums text-right">{{ formatWon(snapshot.total_csm) }}</td></tr>

            <tr class="text-ink-soft"><td colspan="2" class="pt-3 font-medium">자본</td></tr>
            <tr class="border-t-[3px] border-ink text-base font-bold">
              <td class="pl-3 pt-2">자본총계 (Equity)</td>
              <td class="tabular-nums pt-2 text-right">{{ formatWon(snapshot.equity) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
