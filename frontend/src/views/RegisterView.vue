<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhUserPlus } from '@phosphor-icons/vue'
import { useAuthStore } from '../stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (!email.value.trim() || !password.value) {
    errorMessage.value = '이메일과 비밀번호를 입력해주세요.'
    return
  }
  if (password.value.length < 8) {
    errorMessage.value = '비밀번호는 8자 이상이어야 합니다.'
    return
  }
  if (password.value !== passwordConfirm.value) {
    errorMessage.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await authStore.register(email.value.trim(), password.value)
    router.push('/')
  } catch (err) {
    errorMessage.value = err.response?.status === 409
      ? '이 이메일로 가입할 수 없습니다. 다른 이메일을 사용해주세요.'
      : '회원가입에 실패했습니다. 입력 값을 확인해주세요.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md px-4 py-16">
    <header class="mb-8 text-center">
      <h1 class="font-display text-3xl text-ink tracking-tight">회원가입</h1>
      <p class="mt-2 text-sm text-ink-soft">새 계정을 만들고 보험사 경영을 시작하세요.</p>
    </header>

    <div class="overflow-hidden rounded-[24px] border-[3px] border-ink bg-tile shadow-[6px_6px_0_rgba(43,42,76,0.28)]">
      <div class="bg-coral px-6 py-4">
        <h2 class="font-display text-xl text-white flex items-center gap-2">
          <PhUserPlus :size="24" weight="bold" />
          새 계정 만들기
        </h2>
      </div>

      <form class="p-6 space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label class="mb-1 block text-sm font-semibold text-ink" for="register-email">이메일</label>
          <input
            id="register-email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 text-ink placeholder:text-ink-soft/60 transition focus:border-ink focus:outline-none"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm font-semibold text-ink" for="register-password">비밀번호</label>
          <input
            id="register-password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 text-ink transition focus:border-ink focus:outline-none"
          />
          <p class="mt-1 text-xs text-ink-soft">8자 이상 입력해주세요.</p>
        </div>

        <div>
          <label class="mb-1 block text-sm font-semibold text-ink" for="register-password-confirm">비밀번호 확인</label>
          <input
            id="register-password-confirm"
            v-model="passwordConfirm"
            type="password"
            autocomplete="new-password"
            class="w-full rounded-[12px] border-2 border-board-cream-deep bg-board-cream px-3.5 py-2.5 text-ink transition focus:border-ink focus:outline-none"
          />
        </div>

        <button
          type="submit"
          class="flex w-full items-center justify-center gap-2 rounded-full bg-coral py-3 font-display text-lg text-white shadow-[0_4px_0_var(--color-coral-deep)] transition hover:brightness-105 active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-coral-deep)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          :disabled="isSubmitting"
        >
          <PhUserPlus :size="22" weight="bold" />
          <span>{{ isSubmitting ? '가입 중...' : '회원가입' }}</span>
        </button>

        <p v-if="errorMessage" class="text-center text-sm font-semibold text-coral-deep">
          {{ errorMessage }}
        </p>
      </form>
    </div>

    <p class="mt-6 text-center text-sm text-ink-soft">
      이미 계정이 있으신가요?
      <router-link to="/login" class="font-bold text-teal-deep hover:underline">로그인</router-link>
    </p>
  </div>
</template>
