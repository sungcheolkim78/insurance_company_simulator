<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/gameStore'

const router = useRouter()

// Fetch game summary when navigating to this view
const fetchGameSummary = async (gameId: string) => {
  const response = await apiClient.get(`/games/${gameId}/summary`)
  return response.data
}

const gameSummary = computed(() => {
  const gameId = store.gameId
  if (gameId) {
    return await fetchGameSummary(gameId)
  }
  return null
})

const handleGoToSummary = async (gameId: string) => {
  await fetchGameSummary(gameId)
  router.push(`/games/${gameId}/summary`)
}
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6 p-8">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div class="w-full sm:max-w-md">
        <h3 class="mb-2 flex items-center gap-1 font-display text-ink">게임 요약</h3>
        <div class="space-y-4">
          <div class="bg-tile rounded-xl border-2 border-ink p-4">
            <p class="text-sm text-ink">게임 ID</p>
            <p class="font-medium text-ink">{{ gameSummary?.id }}</p>
          </div>
          
          <div class="bg-tile rounded-xl border-2 border-ink p-4">
            <p class="text-sm text-ink">현재 턴</p>
            <p class="font-medium text-ink">{{ gameSummary?.current_turn }}</p>
          </div>
          
          <div class="bg-tile rounded-xl border-2 border-ink p-4">
            <p class="text-sm text-ink">상태</p>
            <p class="font-medium text-ink">{{ gameSummary?.status }}</p>
          </div>
          
          <div class="bg-tile rounded-xl border-2 border-ink p-4">
            <p class="text-sm text-ink">총 턴 수</p>
            <p class="font-medium text-ink">{{ gameSummary?.game_length_turns }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

import { apiClient } from '../api/client'
