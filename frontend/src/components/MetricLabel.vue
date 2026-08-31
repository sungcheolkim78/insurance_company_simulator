<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { PhQuestion } from '@phosphor-icons/vue'
import { METRIC_DESCRIPTIONS } from '../utils/metricDescriptions'

const props = defineProps({
  metric: { type: String, required: true },
  label: { type: String, default: '' },
})

const trigger = ref(null)
const visible = ref(false)
const position = ref({ top: 0, left: 0 })
const description = computed(() => METRIC_DESCRIPTIONS[props.metric] ?? '')
const tooltipId = `metric-tooltip-${Math.random().toString(36).slice(2)}`

function updatePosition() {
  if (!trigger.value) return
  const rect = trigger.value.getBoundingClientRect()
  const width = Math.min(288, window.innerWidth - 24)
  const left = Math.min(Math.max(12, rect.left + rect.width / 2 - width / 2), window.innerWidth - width - 12)
  position.value = { top: rect.bottom + 8, left, width }
}

async function show() {
  visible.value = true
  await nextTick()
  updatePosition()
  window.addEventListener('scroll', updatePosition, true)
  window.addEventListener('resize', updatePosition)
}

function hide() {
  visible.value = false
  window.removeEventListener('scroll', updatePosition, true)
  window.removeEventListener('resize', updatePosition)
}

onBeforeUnmount(hide)
</script>

<template>
  <span
    ref="trigger"
    class="inline-flex cursor-help items-center gap-1 border-b border-dotted border-current"
    tabindex="0"
    :aria-describedby="visible ? tooltipId : undefined"
    @mouseenter="show"
    @mouseleave="hide"
    @focus="show"
    @blur="hide"
    @keydown.esc="hide"
  >
    <slot>{{ label }}</slot>
    <PhQuestion :size="13" weight="bold" aria-hidden="true" />
  </span>
  <Teleport to="body">
    <Transition name="metric-tooltip">
      <div
        v-if="visible"
        :id="tooltipId"
        role="tooltip"
        class="pointer-events-none fixed z-[100] rounded-xl border-2 border-ink bg-ink px-3 py-2 text-left text-xs font-normal leading-relaxed text-white shadow-[3px_3px_0_rgba(232,96,76,0.55)]"
        :style="{ top: `${position.top}px`, left: `${position.left}px`, width: `${position.width}px` }"
      >
        {{ description }}
        <span class="absolute -top-[7px] left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-l-2 border-t-2 border-ink bg-ink" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.metric-tooltip-enter-active,
.metric-tooltip-leave-active { transition: opacity 120ms ease, transform 120ms ease; }
.metric-tooltip-enter-from,
.metric-tooltip-leave-to { opacity: 0; transform: translateY(-3px); }
</style>
