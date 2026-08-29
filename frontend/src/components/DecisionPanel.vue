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
  <div class="space-y-4 rounded border border-slate-200 p-4">
    <div>
      <h2 class="mb-2 font-semibold">상품 가격 / 언더라이팅</h2>
      <div v-for="product in ['whole_life', 'savings']" :key="product" class="mb-2 grid grid-cols-3 items-center gap-2">
        <span class="text-sm">{{ product }}</span>
        <label class="text-xs">가격배수
          <input v-model.number="form.pricing_multiplier[product]" type="number" step="0.05" class="w-full rounded border px-2 py-1" />
        </label>
        <label class="text-xs">엄격도
          <input v-model.number="form.underwriting_strictness[product]" type="number" step="0.05" min="0" max="1" class="w-full rounded border px-2 py-1" />
        </label>
      </div>
    </div>
    <div>
      <h2 class="mb-2 font-semibold">채널</h2>
      <div v-for="channel in ['captive', 'ga']" :key="channel" class="mb-2 grid grid-cols-3 items-center gap-2">
        <span class="text-sm">{{ channel }}</span>
        <label class="text-xs">수수료율
          <input v-model.number="form.commission_rate[channel]" type="number" step="0.01" class="w-full rounded border px-2 py-1" />
        </label>
        <label class="text-xs">모집비
          <input v-model.number="form.marketing_spend[channel]" type="number" step="1000000" class="w-full rounded border px-2 py-1" />
        </label>
      </div>
    </div>
    <div>
      <h2 class="mb-2 font-semibold">자산배분 (합 1.0)</h2>
      <div class="grid grid-cols-3 gap-2">
        <label class="text-xs">예금 <input v-model.number="form.asset_allocation.deposit" type="number" step="0.05" class="w-full rounded border px-2 py-1" /></label>
        <label class="text-xs">채권 <input v-model.number="form.asset_allocation.bond" type="number" step="0.05" class="w-full rounded border px-2 py-1" /></label>
        <label class="text-xs">주식 <input v-model.number="form.asset_allocation.stock" type="number" step="0.05" class="w-full rounded border px-2 py-1" /></label>
      </div>
    </div>
    <label class="block text-sm">배당 지급액
      <input v-model.number="form.dividend_payout" type="number" step="1000000" class="w-full rounded border px-2 py-1" />
    </label>
    <button class="w-full rounded bg-slate-800 px-4 py-2 font-semibold text-white" @click="handleSubmit">
      턴 실행
    </button>
  </div>
</template>
