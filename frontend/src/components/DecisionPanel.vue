<script setup>
import { reactive } from 'vue'

const emit = defineEmits(['submit'])

const form = reactive({
  pricing_multiplier: { whole_life: 1.0, savings: 1.0 },
  underwriting_strictness: { whole_life: 0.3, savings: 0.0 },
  commission_rate: { captive: 0.3, ga: 0.45 },
  marketing_spend: { captive: 10000000, ga: 15000000 },
  asset_allocation: { deposit: 0.3, bond: 0.4, stock: 0.3 },
  dividend_payout: 0,
})

function handleSubmit() {
  emit('submit', JSON.parse(JSON.stringify(form)))
}
</script>

<template>
  <div class="space-y-4 p-4">
    <div>
      <h3 class="mb-2 font-display text-ink">상품 가격 / 언더라이팅</h3>
      <div v-for="product in ['whole_life', 'savings']" :key="product" class="mb-2 grid grid-cols-3 items-center gap-2">
        <span class="text-sm">{{ product }}</span>
        <label class="text-xs">가격배수
          <input v-model.number="form.pricing_multiplier[product]" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
        </label>
        <label class="text-xs">엄격도
          <input v-model.number="form.underwriting_strictness[product]" type="number" step="0.05" min="0" max="1" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
        </label>
      </div>
      <p class="text-xs text-ink-soft">
        가격배수↑: 건당 보험료·마진 증가, 수요 급감 및 해지율 상승. 엄격도↑: 손해율 최대 30% 개선, 승인율 최대 40% 감소.
      </p>
    </div>
    <div>
      <h3 class="mb-2 font-display text-ink">채널</h3>
      <div v-for="channel in ['captive', 'ga']" :key="channel" class="mb-2 grid grid-cols-3 items-center gap-2">
        <span class="text-sm">{{ channel }}</span>
        <label class="text-xs">수수료율
          <input v-model.number="form.commission_rate[channel]" type="number" step="0.01" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
        </label>
        <label class="text-xs">모집비
          <input v-model.number="form.marketing_spend[channel]" type="number" step="1000000" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
        </label>
      </div>
      <p class="text-xs text-ink-soft">
        수수료율↑: 판매 유인 확대로 신계약 급증, 단기 수수료 비용 즉시 증가. 모집비↑: 생산성 확장(제곱근 체감), 과도하면 현금 낭비.
      </p>
    </div>
    <div>
      <h3 class="mb-2 font-display text-ink">자산배분 (합 1.0)</h3>
      <div class="grid grid-cols-3 gap-2">
        <label class="text-xs">예금 <input v-model.number="form.asset_allocation.deposit" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" /></label>
        <label class="text-xs">채권 <input v-model.number="form.asset_allocation.bond" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" /></label>
        <label class="text-xs">주식 <input v-model.number="form.asset_allocation.stock" type="number" step="0.05" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" /></label>
      </div>
      <p class="text-xs text-ink-soft">
        주식↑: 호황기 초과수익 기대, 위기 국면 시 대규모 손실 위험. 채권·예금↑: 안정적 이자수익, 기회비용 발생 가능.
      </p>
    </div>
    <div>
      <label class="block text-sm">배당 지급액
        <input v-model.number="form.dividend_payout" type="number" step="1000000" class="w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
      </label>
      <p class="text-xs text-ink-soft">배당↑: 주주환원 및 ROE 제고, 자본총계(파산 위험 완충력) 감소.</p>
    </div>
    <button
      class="w-full rounded-full bg-coral py-3 font-display text-lg text-white shadow-[0_4px_0_var(--color-coral-deep)] active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-coral-deep)]"
      @click="handleSubmit"
    >
      턴 실행 ▶
    </button>
  </div>
</template>
