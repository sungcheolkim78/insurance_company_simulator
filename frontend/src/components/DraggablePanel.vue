<script setup>
import { computed } from 'vue'
import { PhDotsSixVertical } from '@phosphor-icons/vue'

const props = defineProps({
  panelKey: { type: String, required: true },
  title: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  colorClass: { type: String, required: true },
})

const textClass = computed(() => (props.colorClass === 'bg-mustard' ? 'text-ink' : 'text-white'))
</script>

<template>
  <div
    :data-panel-key="panelKey"
    class="overflow-hidden rounded-[20px] border-[3px] border-ink bg-tile shadow-[5px_5px_0_rgba(43,42,76,0.28)]"
  >
    <div
      class="drag-handle flex cursor-grab items-center gap-2 px-4 py-2 font-display active:cursor-grabbing"
      :class="[colorClass, textClass]"
    >
      <PhDotsSixVertical :size="16" weight="bold" />
      <component :is="icon" :size="16" weight="fill" />
      <span>{{ title }}</span>
    </div>
    <div class="p-1">
      <slot />
    </div>
  </div>
</template>
