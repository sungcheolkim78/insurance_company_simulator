<script setup>
import { computed } from 'vue'
import { PhCloud, PhFire, PhRocket } from '@phosphor-icons/vue'

const props = defineProps({
  currentTurn: { type: Number, required: true },
  gameLengthTurns: { type: Number, required: true },
  stockRegime: { type: String, default: 'normal' },
})

const REGIME_LABELS = { normal: '평온', boom: '호황', crisis: '위기' }
const REGIME_ICONS = { normal: PhCloud, boom: PhRocket, crisis: PhFire }
const REGIME_CHIP_CLASS = {
  normal: 'bg-board-cream-deep text-ink-soft',
  boom: 'bg-teal text-white',
  crisis: 'bg-coral text-white',
}

const progressPercent = computed(() =>
  Math.min(100, Math.max(0, (props.currentTurn / props.gameLengthTurns) * 100)),
)

const trackGradient = computed(() =>
  props.stockRegime === 'crisis'
    ? 'linear-gradient(90deg, var(--color-coral), var(--color-coral-deep))'
    : 'linear-gradient(90deg, var(--color-teal), var(--color-mustard))',
)

const regimeIcon = computed(() => REGIME_ICONS[props.stockRegime] ?? PhCloud)
const regimeChipClass = computed(() => REGIME_CHIP_CLASS[props.stockRegime] ?? REGIME_CHIP_CLASS.normal)
const regimeLabel = computed(() => REGIME_LABELS[props.stockRegime] ?? props.stockRegime)
</script>

<template>
  <div class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile p-4 shadow-[5px_5px_0_rgba(43,42,76,0.28)]">
    <div class="mb-2 flex items-center justify-between text-sm text-ink-soft">
      <span class="font-display text-base text-ink">턴 {{ currentTurn }} / {{ gameLengthTurns }}</span>
      <span class="flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold" :class="regimeChipClass">
        <component :is="regimeIcon" :size="14" weight="fill" />
        {{ regimeLabel }} 국면
      </span>
    </div>
    <div class="relative h-[34px] rounded-full border-2 border-ink bg-board-cream-deep">
      <div
        class="absolute inset-y-0 left-0 rounded-full transition-[width] duration-500"
        :style="{ width: `${progressPercent}%`, backgroundImage: trackGradient }"
      />
      <div
        class="absolute top-1/2 flex h-[30px] w-[30px] -translate-y-1/2 items-center justify-center rounded-full border-[3px] border-tile bg-coral text-xs font-bold text-white shadow-[0_2px_0_rgba(43,42,76,0.28)] transition-[left] duration-500"
        :style="{ left: `${progressPercent}%`, transform: 'translate(-50%, -50%)' }"
      >
        {{ currentTurn }}
      </div>
    </div>
  </div>
</template>
