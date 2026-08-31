<script setup>
import { computed, onMounted } from 'vue'
import { useGameStore } from '../stores/gameStore'
import { GameSummaryView } from './GameSummaryView.vue'
import { useRouter } from 'vue-router'
import { useGameStore as gameStore } from '../stores/gameStore'

const router = useRouter()

// Load past games from history
const loadPastGames = async () => {
  // Get all games from the database
  const games = await apiClient.get('/games/')
  // Filter out the current game (if any) and get their IDs
  const pastGameIds = [...new Set(games.map(g => g.id))].filter(id => !gameStore.gameId)
  
  // Fetch summary for each past game
  const summaries = await Promise.all(
    pastGameIds.map(id => gameStore.getGameId(id))
  )
  
  // Store in reactive state
  const pastGames = computed(() => {
    return summaries
  })
}

const handleSelectPastGame = async (gameId: string) => {
  await gameStore.handleSelectGame(gameId)
  router.push(`/games/${gameId}/summary`)
}

onMounted(loadPastGames)
</script>

<template>
  <div v-if="store.snapshot" class="mx-auto max-w-6xl space-y-6 p-8">
    <!-- Past Games List -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="(game, index) in pastGames" :key="index" class="bg-tile rounded-xl border-2 border-dashed border-transparent p-4 hover:border-ink/50 cursor-pointer">
        <div class="flex items-center gap-3 mb-2">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xl">
            {{ index + 1 }}
          </div>
          <div>
            <p class="font-medium text-ink">게임 ID</p>
            <p class="text-sm text-ink">{{ game.id }}</p>
          </div>
        </div>
        <div class="text-sm text-ink">{{ game.status }} — {{ game.current_turn }} 턴</div>
      </div>
    </div>

    <!-- Current Game Info -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-if="store.snapshot" class="bg-tile rounded-xl border-2 border-ink p-4">
        <h3 class="mb-2 flex items-center gap-1 font-display text-ink">게임 상태</h3>
        <div class="space-y-3">
          <div>
            <p class="text-sm text-ink">ID</p>
            <p class="font-medium text-ink">{{ store.gameId }}</p>
          </div>
          <div>
            <p class="text-sm text-ink">현재 턴</p>
            <p class="font-medium text-ink">{{ store.currentTurn }}</p>
          </div>
          <div>
            <p class="text-sm text-ink">상태</p>
            <p class="font-medium text-ink">{{ store.status }}</p>
          </div>
          <div>
            <p class="text-sm text-ink">총 턴 수</p>
            <p class="font-medium text-ink">{{ store.gameLengthTurns }}</p>
          </div>
        </div>
      </div>

      <div v-else class="bg-tile rounded-xl border-2 border-dashed border-transparent p-4">
        <p class="text-sm text-ink-soft">게임이 없습니다.</p>
      </div>
    </div>

    <!-- Game Summary View (for past games) -->
    <GameSummaryView :game-id="store.gameId" @select="handleSelectPastGame" />
  </div>
</template>
