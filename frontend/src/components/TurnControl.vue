<script setup>
import { ref } from 'vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['run-turns'])
const autoTurns = ref(6)
</script>

<template>
  <div class="flex items-center gap-2 rounded border border-slate-200 p-4">
    <span class="text-sm text-slate-600">가장 최근 결정으로 자동 진행:</span>
    <input v-model.number="autoTurns" type="number" min="1" max="24" class="w-16 rounded border px-2 py-1" />
    <button
      class="rounded border border-slate-800 px-4 py-2 font-semibold text-slate-800 disabled:opacity-50"
      :disabled="disabled"
      @click="emit('run-turns', autoTurns)"
    >
      자동 진행
    </button>
  </div>
</template>
