<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PhSignOut, PhIdentificationCard } from '@phosphor-icons/vue'
import { useAuthStore } from './stores/authStore'

const authStore = useAuthStore()
const router = useRouter()

onMounted(() => {
  authStore.initialize()
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen">
    <div v-if="authStore.status === 'unknown'" class="flex min-h-screen items-center justify-center">
      <p class="font-display text-lg text-ink-soft">인증 상태를 확인하는 중...</p>
    </div>
    <template v-else>
      <header
        v-if="authStore.status === 'authenticated'"
        class="flex items-center justify-end gap-3 px-6 py-3"
      >
        <span class="flex items-center gap-1.5 text-sm font-semibold text-ink-soft">
          <PhIdentificationCard :size="16" weight="bold" />
          {{ authStore.user?.email }}
        </span>
        <button
          class="flex items-center gap-1.5 rounded-full border-2 border-ink bg-white px-3 py-1.5 text-xs font-bold text-ink shadow-[2px_2px_0_rgba(43,42,76,0.2)] transition hover:bg-coral/10 hover:text-coral-deep active:translate-y-0.5 cursor-pointer"
          @click="handleLogout"
        >
          <PhSignOut :size="14" weight="bold" />
          로그아웃
        </button>
      </header>
      <router-view />
    </template>
  </div>
</template>
