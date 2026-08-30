<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createGame } from '../api/client'
import { PhPlayCircle } from '@phosphor-icons/vue'

const router = useRouter()
const initialCapital = ref(10000000000)
const rngSeed = ref('')
const gameLengthTurns = ref(120)
const isCreating = ref(false)
const errorMessage = ref('')

async function handleCreate() {
  isCreating.value = true
  errorMessage.value = ''
  try {
    const seed = rngSeed.value === '' ? null : Number(rngSeed.value)
    const game = await createGame(Number(initialCapital.value), seed, Number(gameLengthTurns.value))
    router.push(`/games/${game.id}`)
  } catch (err) {
    errorMessage.value = '게임 생성에 실패했습니다.'
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-24 max-w-md overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile shadow-[6px_6px_0_rgba(43,42,76,0.28)]">
    <div class="bg-coral px-6 py-4 text-center font-display text-2xl text-white">보험회사 운영 시뮬레이션</div>
    <div class="p-6">
      <label class="mb-1 block text-sm font-medium text-ink-soft">초기 자본</label>
      <input v-model="initialCapital" type="number" class="mb-4 w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-3 py-2" />
      <label class="mb-1 block text-sm font-medium text-ink-soft">시드 (선택)</label>
      <input v-model="rngSeed" type="number" placeholder="비워두면 무작위" class="mb-4 w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-3 py-2" />
      <label class="mb-1 block text-sm font-medium text-ink-soft">최종 턴 수 (1~600)</label>
      <input
        v-model="gameLengthTurns"
        type="number"
        min="1"
        max="600"
        class="mb-6 w-full rounded-[10px] border-2 border-board-cream-deep bg-board-cream px-3 py-2"
      />
      <button
        class="flex w-full items-center justify-center gap-2 rounded-full bg-coral py-3 font-display text-lg text-white shadow-[0_4px_0_var(--color-coral-deep)] disabled:opacity-50 active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-coral-deep)]"
        :disabled="isCreating"
        @click="handleCreate"
      >
        <PhPlayCircle :size="20" weight="fill" />
        새 게임 시작
      </button>
      <p v-if="errorMessage" class="mt-4 text-sm text-coral-deep">{{ errorMessage }}</p>
    </div>
  </div>
</template>
