<script setup>
defineProps({ config: Object, gameLengthTurns: Number })
const emit = defineEmits(['close'])

const PRODUCT_LABELS = { whole_life: '종신보험', savings: '저축성보험' }
const CHANNEL_LABELS = { captive: '전속설계사', ga: '법인대리점' }

function formatWon(value) {
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`
}
function formatPct(value) {
  return `${(value * 100).toFixed(2)}%`
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="emit('close')">
    <div class="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-bold text-slate-800">게임 설정</h2>
        <button class="text-sm text-slate-500 hover:text-slate-800" @click="emit('close')">닫기 ✕</button>
      </div>

      <div class="mb-6">
        <div class="text-sm text-slate-500">최종 턴 수</div>
        <div class="font-bold">{{ gameLengthTurns }}턴</div>
      </div>

      <div v-if="config" class="space-y-6">
        <div>
          <h3 class="mb-2 font-semibold text-slate-700">상품 기본 설정</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-slate-500">
                  <th class="pb-1 pr-3">상품</th>
                  <th class="pb-1 pr-3">가입금액</th>
                  <th class="pb-1 pr-3">기본 원가율</th>
                  <th class="pb-1 pr-3">사업비 로딩</th>
                  <th class="pb-1 pr-3">기본 해지율</th>
                  <th class="pb-1 pr-3">준비금 적립률</th>
                  <th class="pb-1 pr-3">부리 스프레드</th>
                  <th class="pb-1">만기(턴)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(product, code) in config.products" :key="code" class="border-t border-slate-100">
                  <td class="py-1 pr-3 font-medium">{{ PRODUCT_LABELS[code] ?? code }}</td>
                  <td class="py-1 pr-3">{{ formatWon(product.unit_size) }}</td>
                  <td class="py-1 pr-3">{{ formatPct(product.base_cost_rate_annual) }}</td>
                  <td class="py-1 pr-3">{{ formatPct(product.expense_loading) }}</td>
                  <td class="py-1 pr-3">{{ formatPct(product.base_lapse_rate_annual) }}</td>
                  <td class="py-1 pr-3">{{ formatPct(product.reserve_accrual_ratio) }}</td>
                  <td class="py-1 pr-3">{{ formatPct(product.credited_rate_spread) }}</td>
                  <td class="py-1">{{ product.maturity_turns ?? '종신' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 class="mb-2 font-semibold text-slate-700">채널 기본 설정</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-slate-500">
                  <th class="pb-1 pr-3">채널</th>
                  <th class="pb-1 pr-3">기준 생산성</th>
                  <th class="pb-1 pr-3">기본 수수료율</th>
                  <th class="pb-1 pr-3">수수료 민감도</th>
                  <th class="pb-1">마케팅비 기준액</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(channel, code) in config.channels" :key="code" class="border-t border-slate-100">
                  <td class="py-1 pr-3 font-medium">{{ CHANNEL_LABELS[code] ?? code }}</td>
                  <td class="py-1 pr-3">{{ channel.base_productivity }}건/월</td>
                  <td class="py-1 pr-3">{{ formatPct(channel.base_commission_rate) }}</td>
                  <td class="py-1 pr-3">{{ channel.commission_sensitivity }}</td>
                  <td class="py-1">{{ formatWon(channel.reference_spend) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div v-else class="text-sm text-slate-500">설정을 불러오는 중...</div>
    </div>
  </div>
</template>
