<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createGame } from '../api/client'

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
  <div class="mx-auto mt-24 max-w-md rounded-lg border border-slate-200 p-8 shadow-sm">
    <h1 class="mb-6 text-2xl font-bold text-slate-800">보험회사 운영 시뮬레이션</h1>
    <label class="mb-1 block text-sm font-medium text-slate-600">초기 자본</label>
    <input v-model="initialCapital" type="number" class="mb-4 w-full rounded border border-slate-300 px-3 py-2" />
    <label class="mb-1 block text-sm font-medium text-slate-600">시드 (선택)</label>
    <input v-model="rngSeed" type="number" placeholder="비워두면 무작위" class="mb-4 w-full rounded border border-slate-300 px-3 py-2" />
    <label class="mb-1 block text-sm font-medium text-slate-600">최종 턴 수 (1~600)</label>
    <input
      v-model="gameLengthTurns"
      type="number"
      min="1"
      max="600"
      class="mb-6 w-full rounded border border-slate-300 px-3 py-2"
    />
    <button
      class="w-full rounded bg-slate-800 px-4 py-2 font-semibold text-white disabled:opacity-50"
      :disabled="isCreating"
      @click="handleCreate"
    >
      새 게임 시작
    </button>
    <p v-if="errorMessage" class="mt-4 text-sm text-red-600">{{ errorMessage }}</p>
  </div>
</template>
