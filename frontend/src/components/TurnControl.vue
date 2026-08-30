<script setup>
import { ref } from 'vue'
import { PhFastForward } from '@phosphor-icons/vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['run-turns'])
const autoTurns = ref(6)
</script>

<template>
  <div class="flex items-center gap-3 p-4">
    <span class="text-sm text-ink-soft">가장 최근 결정으로 자동 진행:</span>
    <input v-model.number="autoTurns" type="number" min="1" max="24" class="w-16 rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-2 py-1" />
    <button
      class="flex items-center gap-1 rounded-full border-2 border-teal-deep bg-tile px-4 py-2 font-bold text-teal-deep shadow-[3px_3px_0_rgba(31,122,110,0.35)] disabled:opacity-50 active:translate-y-[2px] active:shadow-[1px_1px_0_rgba(31,122,110,0.35)]"
      :disabled="disabled"
      @click="emit('run-turns', autoTurns)"
    >
      <PhFastForward :size="16" weight="fill" />
      자동 진행
    </button>
  </div>
</template>
