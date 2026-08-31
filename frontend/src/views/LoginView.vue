<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhSignIn } from '@phosphor-icons/vue'
import { useAuthStore } from '../stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (!email.value.trim() || !password.value) {
    errorMessage.value = '이메일과 비밀번호를 입력해주세요.'
    return
  }
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await authStore.login(email.value.trim(), password.value)
    router.push(typeof route.query.redirect === 'string' ? route.query.redirect : '/')
  } catch (err) {
    errorMessage.value = err.response?.status === 429
      ? '로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.'
      : '이메일 또는 비밀번호가 올바르지 않습니다.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md px-4 py-16">
    <header class="mb-8 text-center">
      <h1 class="font-display text-3xl text-ink tracking-tight">로그인</h1>
      <p class="mt-2 text-sm text-ink-soft">계정에 로그인하면 어디서든 게임을 이어서 할 수 있습니다.</p>
    </header>

    <div class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile shadow-[6px_6px_0_rgba(43,42,76,0.28)]">
      <div class="bg-teal-deep px-6 py-4">
        <h2 class="font-display text-xl text-white flex items-center gap-2">
          <PhSignIn :size="24" weight="bold" />
          계정 로그인
        </h2>
      </div>

      <form class="p-6 space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label class="mb-1 block text-sm font-semibold text-ink" for="login-email">이메일</label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 text-ink placeholder:text-ink-soft/60 transition focus:border-ink focus:outline-none"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm font-semibold text-ink" for="login-password">비밀번호</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 text-ink transition focus:border-ink focus:outline-none"
          />
        </div>

        <button
          type="submit"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-teal-deep py-3 font-display text-lg text-white shadow-[0_4px_0_rgba(43,42,76,0.35)] transition hover:brightness-110 active:translate-y-[3px] active:shadow-[0_1px_0_rgba(43,42,76,0.35)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          :disabled="isSubmitting"
        >
          <PhSignIn :size="22" weight="bold" />
          <span>{{ isSubmitting ? '로그인 중...' : '로그인' }}</span>
        </button>

        <p v-if="errorMessage" class="text-center text-sm font-semibold text-coral-deep">
          {{ errorMessage }}
        </p>
      </form>
    </div>

    <p class="mt-6 text-center text-sm text-ink-soft">
      계정이 없으신가요?
      <router-link to="/register" class="font-bold text-teal-deep hover:underline">회원가입</router-link>
    </p>
  </div>
</template>
