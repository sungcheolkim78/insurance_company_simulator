<script setup>
import { PhGearSix, PhPackage, PhUsersFour, PhX } from '@phosphor-icons/vue'
import MetricLabel from './MetricLabel.vue'

defineProps({ config: Object, gameLengthTurns: Number })
const emit = defineEmits(['close'])

const PRODUCT_LABELS = {
  whole_life: { label: '종신보험', metric: 'product_whole_life' },
  savings: { label: '저축성보험', metric: 'product_savings' },
}

const CHANNEL_LABELS = {
  captive: { label: '전속설계사', metric: 'channel_captive' },
  ga: { label: '법인대리점', metric: 'channel_ga' },
}

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
function formatPct(value) {
  return `${(value * 100).toFixed(2)}%`
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4" @click.self="emit('close')">
    <div class="max-h-[85vh] w-full max-w-2xl overflow-y-auto overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[8px_8px_0_rgba(43,42,76,0.28)]">
      <div class="flex items-center justify-between bg-plum px-6 py-3 font-display text-white">
        <span class="flex items-center gap-2"><PhGearSix :size="20" weight="fill" /> 게임 설정</span>
        <button class="flex items-center gap-1 text-sm hover:opacity-80" @click="emit('close')">
          <PhX :size="16" weight="bold" /> 닫기
        </button>
      </div>

      <div class="p-6">
        <div class="mb-6">
          <div class="text-sm text-ink-soft">최종 턴 수</div>
          <div class="tabular-nums font-display text-lg">{{ gameLengthTurns }}턴</div>
        </div>

        <div v-if="config" class="space-y-6">
          <div>
            <h3 class="mb-2 flex items-center gap-1 font-display text-ink"><PhPackage :size="16" weight="fill" /> 상품 기본 설정</h3>
            <div class="overflow-x-auto rounded-[14px] border-2 border-board-cream-deep">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-board-cream-deep text-left text-ink-soft">
                    <th class="p-2">상품</th>
                    <th class="p-2"><MetricLabel metric="unit_size" label="가입금액" /></th>
                    <th class="p-2"><MetricLabel metric="base_cost_rate_annual" label="기본 원가율" /></th>
                    <th class="p-2"><MetricLabel metric="expense_loading" label="사업비 로딩" /></th>
                    <th class="p-2"><MetricLabel metric="base_lapse_rate_annual" label="기본 해지율" /></th>
                    <th class="p-2"><MetricLabel metric="reserve_accrual_ratio" label="준비금 적립률" /></th>
                    <th class="p-2"><MetricLabel metric="credited_rate_spread" label="부리 스프레드" /></th>
                    <th class="p-2"><MetricLabel metric="maturity_turns" label="만기(턴)" /></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(product, code) in config.products" :key="code" class="border-t border-board-cream-deep">
                    <td class="p-2 font-medium">
                      <MetricLabel v-if="PRODUCT_LABELS[code]" :metric="PRODUCT_LABELS[code].metric" :label="PRODUCT_LABELS[code].label" />
                      <span v-else>{{ code }}</span>
                    </td>
                    <td class="tabular-nums p-2">{{ formatWon(product.unit_size) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.base_cost_rate_annual) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.expense_loading) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.base_lapse_rate_annual) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.reserve_accrual_ratio) }}</td>
                    <td class="tabular-nums p-2">{{ formatPct(product.credited_rate_spread) }}</td>
                    <td class="tabular-nums p-2">{{ product.maturity_turns ?? '종신' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3 class="mb-2 flex items-center gap-1 font-display text-ink"><PhUsersFour :size="16" weight="fill" /> 채널 기본 설정</h3>
            <div class="overflow-x-auto rounded-[14px] border-2 border-board-cream-deep">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-board-cream-deep text-left text-ink-soft">
                    <th class="p-2">채널</th>
                    <th class="p-2"><MetricLabel metric="base_productivity" label="기준 생산성" /></th>
                    <th class="p-2"><MetricLabel metric="base_commission_rate" label="기본 수수료율" /></th>
                    <th class="p-2"><MetricLabel metric="commission_sensitivity" label="수수료 민감도" /></th>
                    <th class="p-2"><MetricLabel metric="reference_spend" label="마케팅비 기준액" /></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(channel, code) in config.channels" :key="code" class="border-t border-board-cream-deep">
                    <td class="p-2 font-medium">
                      <MetricLabel v-if="CHANNEL_LABELS[code]" :metric="CHANNEL_LABELS[code].metric" :label="CHANNEL_LABELS[code].label" />
                      <span v-else>{{ code }}</span>
                    </td>
                    <td class="tabular-nums p-2">{{ channel.base_productivity }}건/월</td>
                    <td class="tabular-nums p-2">{{ formatPct(channel.base_commission_rate) }}</td>
                    <td class="tabular-nums p-2">{{ channel.commission_sensitivity }}</td>
                    <td class="tabular-nums p-2">{{ formatWon(channel.reference_spend) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-ink-soft">설정을 불러오는 중...</div>
      </div>
    </div>
  </div>
</template>
