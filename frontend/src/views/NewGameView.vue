<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createGame, listGames, deleteGame as apiDeleteGame } from '../api/client'
import {
  PhPlayCircle,
  PhClockCounterClockwise,
  PhChartLineUp,
  PhCheckCircle,
  PhSkull,
  PhHourglass,
  PhTrash,
  PhArrowsClockwise,
  PhFileText,
  PhCaretRight,
} from '@phosphor-icons/vue'

const router = useRouter()

// New game form state
const initialCapital = ref(10000000000)
const rngSeed = ref('')
const gameLengthTurns = ref(120)
const isCreating = ref(false)
const errorMessage = ref('')

// Past games list state
const pastGames = ref([])
const isLoadingGames = ref(false)
const listError = ref('')
const deletingId = ref(null)

async function fetchGames() {
  isLoadingGames.value = true
  listError.value = ''
  try {
    const data = await listGames()
    pastGames.value = data
  } catch (err) {
    listError.value = err.response?.status === 401
      ? '세션이 만료되었습니다. 다시 로그인해주세요.'
      : '게임 목록을 불러오는 데 실패했습니다.'
  } finally {
    isLoadingGames.value = false
  }
}

async function handleCreate() {
  isCreating.value = true
  errorMessage.value = ''
  try {
    const seed = rngSeed.value === '' ? null : Number(rngSeed.value)
    const game = await createGame(Number(initialCapital.value), seed, Number(gameLengthTurns.value))
    router.push(`/games/${game.id}`)
  } catch (err) {
    errorMessage.value = err.response?.status === 401
      ? '세션이 만료되었습니다. 다시 로그인해주세요.'
      : '게임 생성에 실패했습니다.'
  } finally {
    isCreating.value = false
  }
}

function handleSelectSummary(gameId) {
  router.push(`/games/${gameId}/result`)
}

function handleContinuePlay(gameId) {
  router.push(`/games/${gameId}`)
}

async function handleDelete(e, gameId) {
  e.stopPropagation()
  if (!confirm(`게임 #${gameId} 기록을 삭제하시겠습니까?`)) return

  deletingId.value = gameId
  try {
    await apiDeleteGame(gameId)
    pastGames.value = pastGames.value.filter((g) => g.id !== gameId)
  } catch (err) {
    alert('게임 삭제에 실패했습니다.')
  } finally {
    deletingId.value = null
  }
}

function formatMoney(val) {
  if (val === null || val === undefined) return '-'
  const rounded = Math.round(val)
  return new Intl.NumberFormat('ko-KR').format(rounded) + '원'
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${yyyy}.${mm}.${dd} ${hh}:${min}`
  } catch {
    return isoStr
  }
}

onMounted(() => {
  fetchGames()
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8">
    <!-- Header Title -->
    <header class="mb-8 text-center">
      <h1 class="font-display text-4xl text-ink tracking-tight sm:text-5xl">
        보험회사 운영 시뮬레이션
      </h1>
      <p class="mt-2 text-base text-ink-soft sm:text-lg">
        상품 개발, 언더라이팅, 채널 영업, 자산 운용을 총괄하여 건전한 보험사를 경영하세요.
      </p>
    </header>

    <!-- Main Grid: Left for New Game, Right for Past Games -->
    <div class="grid grid-cols-1 gap-8 lg:grid-cols-12 items-start">
      
      <!-- Left Column: New Game Form -->
      <section class="lg:col-span-5">
        <div
          class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile shadow-[6px_6px_0_rgba(43,42,76,0.28)]"
        >
          <div class="bg-coral px-6 py-4 flex items-center justify-between">
            <h2 class="font-display text-xl text-white flex items-center gap-2">
              <PhPlayCircle :size="24" weight="fill" />
              새 게임 시작
            </h2>
            <span class="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-bold text-white">NEW</span>
          </div>

          <div class="p-6 space-y-4">
            <div>
              <label class="mb-1 block text-sm font-semibold text-ink">
                초기 자본
                <span class="text-xs font-normal text-ink-soft">(기본: 100억 원)</span>
              </label>
              <input
                v-model="initialCapital"
                type="number"
                step="1000000000"
                class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 font-medium text-ink transition focus:border-ink focus:outline-none"
              />
              <p class="mt-1 text-xs text-ink-soft">
                {{ formatMoney(initialCapital) }}
              </p>
            </div>

            <div>
              <label class="mb-1 block text-sm font-semibold text-ink">
                난수 시드 (선택)
              </label>
              <input
                v-model="rngSeed"
                type="number"
                placeholder="비워두면 무작위 생성"
                class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 text-ink placeholder:text-ink-soft/60 transition focus:border-ink focus:outline-none"
              />
              <p class="mt-1 text-xs text-ink-soft">
                동일한 시드로 플레이하면 시장 환경과 고객 유입이 재현됩니다.
              </p>
            </div>

            <div>
              <label class="mb-1 block text-sm font-semibold text-ink">
                경영 기간 (턴 수, 1~600)
                <span class="text-xs font-normal text-ink-soft">(기본: 120턴 = 10년)</span>
              </label>
              <input
                v-model="gameLengthTurns"
                type="number"
                min="1"
                max="600"
                class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 font-medium text-ink transition focus:border-ink focus:outline-none"
              />
              <p class="mt-1 text-xs text-ink-soft">
                1턴 = 1개월 (120턴 = 10년, 240턴 = 20년)
              </p>
            </div>

            <div class="pt-2">
              <button
                class="flex w-full items-center justify-center gap-2 rounded-full bg-coral py-3.5 font-display text-lg text-white shadow-[0_4px_0_var(--color-coral-deep)] transition hover:brightness-105 active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-coral-deep)] disabled:opacity-50 cursor-pointer"
                :disabled="isCreating"
                @click="handleCreate"
              >
                <PhPlayCircle :size="22" weight="fill" />
                <span>{{ isCreating ? '생성 중...' : '시뮬레이션 시작' }}</span>
              </button>
            </div>

            <p v-if="errorMessage" class="text-center text-sm font-semibold text-coral-deep">
              {{ errorMessage }}
            </p>
          </div>
        </div>
      </section>

      <!-- Right Column: Past Games List -->
      <section class="lg:col-span-7">
        <div
          class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile shadow-[6px_6px_0_rgba(43,42,76,0.28)]"
        >
          <div class="bg-teal-deep px-6 py-4 flex items-center justify-between">
            <h2 class="font-display text-xl text-white flex items-center gap-2">
              <PhClockCounterClockwise :size="24" weight="bold" />
              과거 게임 기록
            </h2>
            <button
              class="flex items-center gap-1 rounded-full bg-white/20 px-3 py-1 text-xs font-bold text-white transition hover:bg-white/30 cursor-pointer"
              :disabled="isLoadingGames"
              @click="fetchGames"
            >
              <PhArrowsClockwise :size="14" :class="{ 'animate-spin': isLoadingGames }" />
              새로고침
            </button>
          </div>

          <div class="p-6">
            <!-- Loading State -->
            <div v-if="isLoadingGames" class="py-12 text-center text-ink-soft">
              <PhArrowsClockwise :size="32" class="mx-auto mb-2 animate-spin text-teal-deep" />
              <p>플레이 기록을 불러오는 중입니다...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="listError" class="py-10 text-center">
              <p class="text-sm font-semibold text-coral-deep mb-3">{{ listError }}</p>
              <button
                class="rounded-full border-2 border-ink bg-board-cream px-4 py-1.5 text-xs font-bold text-ink transition hover:bg-board-cream-deep"
                @click="fetchGames"
              >
                다시 시도
              </button>
            </div>

            <!-- Empty State -->
            <div
              v-else-if="pastGames.length === 0"
              class="rounded-[16px] border-2 border-dashed border-board-cream-deep bg-board-cream/50 py-12 px-6 text-center"
            >
              <PhFileText :size="48" class="mx-auto mb-3 text-ink-soft/40" />
              <p class="font-display text-lg text-ink">아직 저장된 게임이 없습니다</p>
              <p class="mt-1 text-sm text-ink-soft">
                왼쪽 메뉴에서 새 게임을 생성하고 첫 시뮬레이션을 시작해보세요!
              </p>
            </div>

            <!-- Games List -->
            <div v-else class="space-y-3 max-h-[540px] overflow-y-auto pr-1">
              <div
                v-for="g in pastGames"
                :key="g.id"
                class="group relative flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-[16px] border-2 border-ink bg-board-cream p-4 shadow-[3px_3px_0_rgba(43,42,76,0.2)] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_rgba(43,42,76,0.28)] hover:bg-white cursor-pointer"
                @click="handleSelectSummary(g.id)"
              >
                <!-- Game Info -->
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="font-display text-base text-ink">게임 #{{ g.id }}</span>
                    
                    <!-- Status Badge -->
                    <span
                      v-if="g.status === 'running'"
                      class="inline-flex items-center gap-1 rounded-full bg-teal/15 px-2.5 py-0.5 text-xs font-bold text-teal-deep border border-teal/30"
                    >
                      <PhHourglass :size="12" weight="bold" />
                      진행 중
                    </span>
                    <span
                      v-else-if="g.status === 'completed'"
                      class="inline-flex items-center gap-1 rounded-full bg-mustard/20 px-2.5 py-0.5 text-xs font-bold text-mustard-deep border border-mustard/40"
                    >
                      <PhCheckCircle :size="12" weight="fill" />
                      경영 완료
                    </span>
                    <span
                      v-else-if="g.status === 'bankrupt'"
                      class="inline-flex items-center gap-1 rounded-full bg-coral/15 px-2.5 py-0.5 text-xs font-bold text-coral-deep border border-coral/30"
                    >
                      <PhSkull :size="12" weight="fill" />
                      파산
                    </span>

                    <span v-if="g.created_at" class="text-xs text-ink-soft/70 hidden sm:inline">
                      {{ formatDate(g.created_at) }}
                    </span>
                  </div>

                  <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-soft">
                    <span>
                      진행: <strong class="text-ink font-semibold">{{ g.current_turn }}</strong> / {{ g.game_length_turns }} 턴
                    </span>
                    <span v-if="g.equity !== null">
                      순자산: <strong class="text-ink font-semibold">{{ formatMoney(g.equity) }}</strong>
                    </span>
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex items-center gap-2 self-end sm:self-center" @click.stop>
                  <!-- View Summary Button (Navigates to ResultView) -->
                  <button
                    class="flex items-center gap-1 rounded-full border-2 border-ink bg-white px-3 py-1.5 text-xs font-bold text-ink shadow-[2px_2px_0_rgba(43,42,76,0.2)] transition hover:bg-board-cream active:translate-y-0.5 cursor-pointer"
                    title="게임 요약 및 성과 추이 보기"
                    @click="handleSelectSummary(g.id)"
                  >
                    <PhChartLineUp :size="14" weight="bold" />
                    서머리 보기
                  </button>

                  <!-- Continue Play Button for running games -->
                  <button
                    v-if="g.status === 'running'"
                    class="flex items-center gap-1 rounded-full border-2 border-ink bg-teal-deep px-3 py-1.5 text-xs font-bold text-white shadow-[2px_2px_0_rgba(43,42,76,0.2)] transition hover:brightness-110 active:translate-y-0.5 cursor-pointer"
                    title="게임 화면으로 이동하여 이어서 플레이"
                    @click="handleContinuePlay(g.id)"
                  >
                    <span>이어서 플레이</span>
                    <PhCaretRight :size="12" weight="bold" />
                  </button>

                  <!-- Delete Game Button -->
                  <button
                    class="flex items-center justify-center rounded-full border-2 border-ink bg-white p-1.5 text-ink-soft shadow-[2px_2px_0_rgba(43,42,76,0.2)] transition hover:bg-coral/10 hover:text-coral-deep hover:border-coral-deep active:translate-y-0.5 cursor-pointer"
                    :disabled="deletingId === g.id"
                    title="기록 삭제"
                    @click="(e) => handleDelete(e, g.id)"
                  >
                    <PhTrash :size="14" />
                  </button>
                </div>
              </div>
            </div>

            <p class="mt-4 text-center text-xs text-ink-soft">
              목록의 게임 카드를 클릭하거나 [서머리 보기]를 누르면 상세 경영 성과와 그래프를 확인할 수 있습니다.
            </p>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>
